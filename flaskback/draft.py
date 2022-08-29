# coding=utf-8
import json
import random
import pymongo
import traceback
import sys
import uuid
from operator import methodcaller as mc
from bson import json_util

from flask_cors import *
from flask import Flask, request
# import flask_restful as restful
from flask_restful import Api, Resource, reqparse


from config import *  # Parameter, API_BASE_DEV, API_BASE_PROD, DEVELOPING, DB_SECRET

API_BASE = API_BASE_DEV if DEVELOPING else API_BASE_PROD


#


# from flask_pymongo import PyMongo
# mongo = PyMongo(app, uri="mongodb://localhost:27017/Sp22Anno")  # 开启数据库

app = Flask(__name__, static_url_path="")
CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": "*"}})

api = Api(app)


#


mongo_client = pymongo.MongoClient('127.0.0.1', 27017)
db = mongo_client["Sp22Anno"]  # 数据库名
table_users = db["Users"]
table_entry = db["Entry"]
table_anno = db["Annotations"]
table_task = db["Task"]


#


def get_err():
    traceback.print_exc()  # 打印异常信息
    exc_type, exc_value, exc_traceback = sys.exc_info()
    error = str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
    return error


# 根目录
class Annotator(Resource):
    @staticmethod
    def get():
        return {'test': 'success'}


# 初始化：给用户分配文件
class Init(Resource):
    @staticmethod
    def post():  # post请求需要传递username、密码和topic，只有管理员可以分配标记文件
        request_data = request.get_json()
        username = request_data['user_id']
        password = request_data['password']
        # admin验证
        if not (username == 'admin' and password == 'admin2022'):
            res = {'err': 'Not Admin or Wrong Password'}
            return json.loads(json_util.dumps(res))

        # 获取topic
        topic = request_data['topic']
        # 当前annotation的id
        # task_id = table_task.count_documents({})
        # task_id += 1
        task_id = 1
        # 获取语料数目
        entry_cnt = table_entry.count_documents({})
        # 获取用户表大小
        user_cnt = table_users.count_documents({})
        # 事先从语料池中，选出 allocate_cnt 条语料
        allocate_cnt = int(Parameter.STACK_SIZE / Parameter.X * user_cnt)
        entry_ids = random.sample([i for i in range(1, entry_cnt + 1)], allocate_cnt)
        entry_ids = list(map(lambda x: str(x), entry_ids))
        print('entry_ids:', entry_ids)
        for entry_id in entry_ids:
            task = {
                'id': str(task_id),
                'topic': topic,
                'eId': entry_id,
                'to': [],
                'submitters': [],
                'dropped_count': 0,
                'skipped_count': 0,
                'valid_count': 0,
                'enough': False
            }
            # 随机选取X个用户
            user_ids = random.sample([i for i in range(1, user_cnt + 1)], Parameter.X)
            user_ids = list(map(lambda x: str(x), user_ids))
            task['to'] = user_ids
            print('user_ids:', user_ids)
            # 插入数据库
            try:
                table_task.insert_one(task)
                # table_task.insert_one(task)
            except Exception as e:
                error = get_err()
                res = {'err': error}
                return json.loads(json_util.dumps(res))
            # 修改用户的task字段
            for user_id in user_ids:
                try:
                    user_task = table_users.find_one({'id': user_id}, {'task': 1})['task']
                    user_task.append(str(task_id))
                    new_values = {"$set": {'task': user_task}}
                    table_users.update_one({'id': user_id}, new_values)
                except Exception as e:
                    error = get_err()
                    res = {'err': error}
                    return json.loads(json_util.dumps(res))
            task_id += 1

        return json.loads(json_util.dumps({'err': ''}))


# 给user安排count个任务
class NewTask(Resource):
    @staticmethod
    def post():
        # check
        request_data = request.get_json()
        user_id = str(request_data['user_id'])
        # password = request_data['password']
        # try:
        #     pwd_true = table_users.find_one({'id': user_id})['password']
        # except Exception as e:
        #     error = get_err()
        #     return json.loads(json_util.dumps({'err': error}))
        # if password != pwd_true:
        #     return json.loads(json_util.dumps({'err': 'Wrong Password or Other ERROR.'}))

        count = request_data['count']
        topic = request_data['topic']
        try:
            find_res = table_users.find_one({'id': user_id}, {'task': 1, 'annotated': 1})
            if not find_res:
                return json.loads(json_util.dumps({'err': 'Wrong User ID or Task not Empty.'}))
            user_task = find_res['task']
            user_annotated = find_res['annotated']
        except Exception as e:
            error = get_err()
            return json.loads(json_util.dumps({'err': error}))
        # 1.遍历task，获取未标记的、标记一次的entry id
        try:
            assigned_entry = []
            assigned_one_entry = []
            for task in table_task.find({}):
                topic = task['topic']
                if topic != Parameter.TOPIC:
                    continue
                id = task['eId']
                to = task['to']
                # if id in user_annotated or user_id in to:  # 保证分配新的entry
                #     continue
                assigned_entry.append(id)
                if 0 < len(to) < Parameter.X and user_id not in to:
                    assigned_one_entry.append(id)
            entry_cnt = table_entry.count_documents({})
            if len(assigned_entry) == len(assigned_one_entry):
                no_assigned_entry = []
            else:
                ids = [str(i) for i in range(1, entry_cnt + 1)]
                random.shuffle(ids)
                no_assigned_entry = [i for i in ids if str(i) not in assigned_entry]
                # no_assigned_entry = [str(i) for i in range(1, entry_cnt + 1) if str(i) not in assigned_entry]
        except Exception as e:
            error = get_err()
            return json.loads(json_util.dumps({'err': error}))
        if count <= len(no_assigned_entry):
            no_assigned_entry = no_assigned_entry[:count]
            assigned_one_entry = []
        else:
            assigned_one_entry = assigned_one_entry[:count - len(no_assigned_entry)]
        # print('assigned_entry:', assigned_entry)
        # print('assigned_one_entry:', assigned_one_entry)
        # print('no_assigned_entry:', no_assigned_entry)

        if not assigned_one_entry and not no_assigned_entry:
            return json.loads(json_util.dumps({'err': 'No more entry to allocate'}))

        random.shuffle(no_assigned_entry)
        random.shuffle(assigned_one_entry)
        print('assigned_entry:', assigned_entry)
        print('assigned_one_entry:', assigned_one_entry)
        print('no_assigned_entry:', no_assigned_entry)

        # 3.建立task
        for entry_id in assigned_one_entry:
            try:
                # 更新task
                task = table_task.find_one({'eId': entry_id}, {'id': 1, 'to': 1})
                task_id = task['id']
                to = task['to']
                to.append(user_id)
                new_values = {"$set": {"to": to}}
                table_task.update_one({'id': task_id}, new_values)
                user_task.append(task_id)
            except Exception as e:
                error = get_err()
                return json.loads(json_util.dumps({'err': error}))

        task_id = table_task.count_documents({}) + 1
        for entry_id in no_assigned_entry:
            task_id += 1
            task = {
                'id': str(task_id),
                'topic': topic,
                'eId': str(entry_id),
                'to': [user_id],  # fixed
                'submitters': [],
                'dropped_count': 0,
                'skipped_count': 0,
                'valid_count': 0,
                'enough': False
            }
            table_task.insert_one(task)
            user_task.append(str(task_id))

        # print('table_task:', table_task)
        # print('user_task:', user_task)
        # print('no_assigned_entry:', no_assigned_entry)
        # print('assigned_one_entry:', assigned_one_entry)

        # 更新user的task字段
        try:
            # 更新task
            new_values = {"$set": {"task": user_task}}
            table_users.update_one({'id': user_id}, new_values)
        except Exception as e:
            error = get_err()
            return json.loads(json_util.dumps({'err': error}))

        return json.loads(json_util.dumps({'err': ''}))


# 获取所有存在弃标的 entry.origin_id
class DropSet(Resource):
    @staticmethod
    def get():
        drop_list = []
        try:
            for d in table_task.find({}):
                if d['dropped_count'] > 0:
                    drop_list.append(d['id'])
        except Exception as e:
            error = get_err()
            return json.loads(json_util.dumps({'err': error, 'drop_list': None}))
        res = {'err': '', 'drop_list': drop_list}
        return json.loads(json_util.dumps(res))


#
# api.add_resource(Annotator, '/')
# api.add_resource(Init, '/api/init/')
# api.add_resource(NewTask, '/api/new-task/')
# api.add_resource(DropSet, '/api/drop-set/')
#


# 获取annotation
class AnnotationByID(Resource):
    @staticmethod
    def post(annotation_id):
        request_data = request.get_json()
        user_id = request_data['user_id']
        res = {'err': '', 'annotation': None}
        try:
            annotation = table_anno.find_one({'id': annotation_id})
            if not annotation:
                res['err'] = 'No Such Annotation.'
                return json.loads(json_util.dumps(res))
            if annotation['user'] != user_id:
                res['err'] = 'Not your Annotation.'
                return json.loads(json_util.dumps(res))
        except Exception as e:
            error = get_err()
            res['err'] = error
            return json.loads(json_util.dumps(res))
        res['annotation'] = annotation
        return json.loads(json_util.dumps(res))


api.add_resource(AnnotationByID, '/api/annotation/<string:annotation_id>')


# 获取当前 user 应该标的task和标过的全部task
class AllTask(Resource):
    @staticmethod
    def get(user_id):
        res = {'err': '', 'task': None, 'annotated': None}
        # noinspection PyBroadException
        try:
            user_info = db_User.find_one({'id': user_id}, {'task': 1, 'annotated': 1})
            task = user_info['task']
            annotated = user_info['annotated']
        except Exception:
            error = get_err()
            res['err'] = error
            return json.loads(json_util.dumps(res))
        res['task'] = task
        res['annotated'] = annotated
        return json.loads(json_util.dumps(res))


api.add_resource(AllTask, '/api/all-task/<string:user_id>')
#


# class TopicAPI(Resource):
#     @staticmethod
#     def get():
#         res = {
#             'topic': Parameter.TOPIC,
#             'err': '',
#             # 'data_in': data_in,
#         }
#         return json.loads(json_util.dumps(res))


# api.add_resource(TopicAPI, '/api/topic/')
