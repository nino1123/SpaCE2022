# coding=utf-8

import time
import json
import random
import pymongo
import traceback
import uuid
import os
import sys
sys.path.append(r'C:\Users\xingd\AppData\Local\Programs\Python\Python36\Lib\site-packages')
sys.path.append(r'c:\users\xingd\appdata\local\programs\python\python36\flask-restful-master\flask-restful-master')

from pymongo import ReturnDocument

from operator import methodcaller as mc  # 用于万能接口
from bson import json_util

# 引入 flask 及其插件
from flask import Flask, request
from flask_cors import *
from flask_restful import Api, Resource, reqparse
from flask_httpauth import HTTPTokenAuth
from gevent import pywsgi
#


# 引入本项目的其他模块
from models import User, Entry, Task, Anno
from config import *  # Parameter, DB_SECRET, API_BASE_DEV, API_BASE_PROD, DEVELOPING, API_BASE
from assign_tasks import assign_tasks
#


# ## 实用函数 ## 开始

# 处理 topic 历史遗留混乱 用于 find()
def topic_tags(topic):
    ll0 = ['t0', '第0期', '清洗', '0', 'clean', 'check']
    if topic in ll0:
        return ll0
    ll1 = ['t1', '第1期', '正确性', '1']
    if topic in ll1:
        return ll1
    ll2 = ['t2', '第2期', '同义性', '2']
    if topic in ll2:
        return ll2
    ll2r = ['t2r', '第2期R', 'task2r', '2']
    if topic in ll2r:
        return ll2r
    ll3 = ['t3', '第3期', '归因', '3', 'reason']
    if topic in ll3:
        return ll3
    ll4 = ['t4', '第4期', '精标', '4', 'detail']
    if topic in ll4:
        return ll4
    ll5 = ['Eval1', '测试1']
    if topic in ll5:
        return ll5
    ll6 = ['Eval2', '测试2']
    if topic in ll6:
        return ll6
    return [topic]


# 处理 topic 历史遗留混乱 用于 Task task.topic
def topic_regulation(topic):
    ll0 = ['t0', '第0期', '清洗', '0', 'clean', 'check']
    if topic in ll0:
        return '清洗'
    ll1 = ['t1', '第1期', '正确性', '1']
    if topic in ll1:
        return '第1期'
    ll2 = ['t2', '第2期', '同义性', '2']
    if topic in ll2:
        return '第2期'
    ll2r = ['t2r', '第2期R', 'task2r', '2']
    if topic in ll2r:
        return '第2期R'
    ll3 = ['t3', '第3期', '归因', '3', 'reason']
    if topic in ll3:
        return '归因'
    ll4 = ['t4', '第4期', '精标', '4', 'detail']
    if topic in ll4:
        return '精标'
    ll5 = ['Eval1', '测试1']
    if topic in ll5:
        return '测试1'
    ll6 = ['Eval2', '测试2']
    if topic in ll6:
        return '测试2'
    return topic


# 处理 topic 历史遗留混乱 用于 User user.currTask
def topic_to_tag(topic):
    ll0 = ['t0', '第0期', '清洗', '0', 'clean', 'check']
    if topic in ll0:
        return 't0'
    ll1 = ['t1', '第1期', '正确性', '1']
    if topic in ll1:
        return 't1'
    ll2 = ['t2', '第2期', '同义性', '2']
    if topic in ll2:
        return 't2'
    ll2r = ['t2r', '第2期R', 'task2r', '2']
    if topic in ll2r:
        return 't2rs'
    ll3 = ['t3', '第3期', '归因', '3', 'reason']
    if topic in ll3:
        return 't3'
    ll4 = ['t4', '第4期', '精标', '4', 'detail']
    if topic in ll4:
        return 't4'
    ll5 = ['Eval1', '测试1']
    if topic in ll5:
        return 'Eval1'
    ll6 = ['Eval2', '测试2']
    if topic in ll6:
        return 'Eval2'
    return topic


# 相对方便的字典取值函数
def kv(d, k):
    if not d:
        return None
    if k in d:
        return d[k]
    return None


# 获取当前时间字符串
def localtime():
    return time.asctime(time.localtime(time.time()))


def time_string():
    return time.strftime("%y%m%d-%H%M%S", time.localtime())


# 获取异常信息 by Xu or Ren
def get_err():
    traceback.print_exc()
    exc_type, exc_value, exc_traceback = sys.exc_info()
    error = str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
    return error


# 在 update 文档之前 修复 多余的 _id    但可能没用到 因为其实干脆直接把 _id 删了
def fix_oid(dct):
    if '_id' in dct:
        if '$oid' in dct['_id']:
            dct['_id'] = dct['_id']['$oid']
    return dct


# 构造新的 id
def new_int_str_id(table):
    count = db[table].count_documents({})
    if count == 0:
        count += 1
    while db[table].find_one({'id': str(count)}, {'id': 1}):
        count += 1
    return str(count)
##

# ## 实用函数 ## 结束


# 封装 任务分配函数 by Wang XiHao
def assignment(topic,
               user_tag=None,
               task_tag=None,
               users_per_task=2,
               tasks_per_user=20,
               exclusion=None,
               polygraphs_per_user=None):
    print([2, localtime()])
    if topic is None:
        return []
    if users_per_task is None:
        users_per_task = 2
    if tasks_per_user is None:
        tasks_per_user = 20
    if exclusion is None:
        exclusion = []
    if polygraphs_per_user is None:
        polygraphs_per_user = {}
    users_found = db_User.find({'currTask': {'$in': topic_tags(topic)}, 'tags': user_tag, 'quitted': {'$ne': True}})
    users = [User(user_found).packed() for user_found in users_found]
    tasks_found = db_Task.find({'topic': {'$in': topic_tags(topic)}, 'tags': task_tag, 'deleted': {'$ne': True}})
    tasks = [Task(task_found).packed() for task_found in tasks_found]
    e_ids = [task['entry'] for task in tasks]
    entries = []
    for e_id in e_ids:
        entry_found = db_Entry.find_one({'id': e_id, 'deleted': {'$ne': True}})
        if entry_found:
            entries.append(entry_found)
    print(['len(entries)', len(entries)])
    print(['len(users)', len(users)])
    print(['len(tasks)', len(tasks)])
    print(['topic', topic_regulation(topic)])
    print(['users_per_task', users_per_task])
    print(['tasks_per_user', tasks_per_user])
    print(['start', localtime()])

    # # debug 时将参数输出到文件看看情况
    # e_id_s = [entry.pop('_id') for entry in entries]
    # u_id_s = [user.pop('_id') for user in users]
    # t_id_s = [task.pop('_id') for task in tasks]
    # xxx = {
    #     'entries': entries,
    #     'users': users,
    #     'tasks': tasks,
    #     'topic': topic_regulation(topic),
    #     'exclusion': exclusion,
    #     'users_per_task': users_per_task,
    #     'tasks_per_user': tasks_per_user,
    #     'polygraphs_per_user': polygraphs_per_user,
    # }
    # yyy = json.dumps(xxx, ensure_ascii=False, indent=2)
    # with open('yyy.json', 'w') as fff:
    #     fff.write(yyy)

    tasks_to_update = assign_tasks(entries, users, tasks,
                                   topic_regulation(topic), exclusion,
                                   users_per_task, tasks_per_user, polygraphs_per_user)
    print(['end', localtime()])
    return tasks_to_update
    pass
#


# 下面两行是多余的，之前同学用了两种 pymongo 接口，现在已经统一改写为一种。
# from flask_pymongo import PyMongo
# mongo = PyMongo(app, uri="    ")  # 开启数据库
# 不过以后维护的同学可以学习一下 flask_pymongo ，看看有没有什么更好的地方。


# 创建 Flask 应用
app = Flask(__name__, static_url_path="")
# 使用 flask_cors 的 CORS 跨域访问管理模块
CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": "*"}})
# 使用 flask_restful 提供的 API 配置器
api = Api(app)
# 使用 flask_restful 提供的 请求解析器
parser = reqparse.RequestParser()  # TODO
# 使用 flask_httpauth 提供的 token 鉴权模块
auth_token = HTTPTokenAuth(scheme='Bearer')


# 接下来几个函数是对 auth_token 所涉细节的具体定义
# 参看： https://flask-httpauth.readthedocs.io

# ## auth_token 相关定义 ## 开始

# 1、对于需要使用 token 鉴权的操作，进行以下处理，并返回当前 user 对象
@auth_token.verify_token
def verify_token(token):
    # print('verify_token '+token)
    user = db_User.find_one({'token': token})
    if user:
        return user


# 2、为 user 鉴别 role
@auth_token.get_user_roles
def get_user_roles(user):
    if kv(user, 'role'):
        # print(kv(user, 'role'))
        return kv(user, 'role')
    # print([])
    return []


# 3、对于鉴权发生错误的情形，进行以下处理
@auth_token.error_handler
def auth_error(status):
    # print(status)
    return "Access Denied", status

# ## auth_token 相关定义 ## 结束


# ## 创建数据库相关接口 ## 开始
mongo_client = pymongo.MongoClient('127.0.0.1', 27017)  # 建立 MongoBD 数据库连接
db = mongo_client["Sp22Anno"]  # 数据库名
db_User = db["User"]  # # 用户表
db_Entry = db["Entry"]  # 语料表
db_Task = db["Task"]  # # 任务表
db_Anno = db["Anno"]  # # 标注表
# ## 创建数据库相关接口 ## 结束


#
def db_log():
    me = auth_token.current_user()
    me_id = kv(me, 'id')
    headers = dict([(k, v) for k, v in request.headers.items()])
    log_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    path = request.path
    db['Log'].insert_one({'user': me_id, 'path': path, 'headers': headers, 'logAt': log_at})


def db_get_value(key):
    found = db['Var'].find_one({'key': key})
    if found:
        return json.loads(found.get('value'))
    return None


def db_set_value(key, value):
    doc = {'key': key, 'value': json.dumps(value)}
    db['Var'].replace_one({'key': key}, doc, upsert=True)
    return db_get_value(key)


def make_backup(tasks_filter=None, entries_filter=None, annos_filter=None, need_backup=False, with_content=False):
    print("make_backup start")

    # if tasks_filter is None:
    #     tasks_filter = {}
    # if entries_filter is None:
    #     entries_filter = {}
    # if annos_filter is None:
    #     annos_filter = {}

    tasks = get_filtered_tasks(tasks_filter)
    for task in tasks:
        if '_id' in task:
            task.pop('_id')
    print(len(tasks))
    print(tasks[0])

    entries = get_filtered_entries_in_filtered_tasks(tasks_filter, entries_filter, with_content)
    print(len(entries))
    print(entries[0])

    annos = get_filtered_annos_in_filtered_tasks(tasks_filter, annos_filter)
    print(len(annos))
    print(annos[0])

    users = [user for user in db['User'].find({})]
    for user in users:
        if '_id' in user:
            user.pop('_id')
    print(len(users))
    print(users[0])

    db_name = f"DB-{time_string()}.json"

    db_dict = {
        "entries": entries,
        "tasks": tasks,
        "annos": annos,
        "users": users,
        "_meta": {
            "filters": {
                "tasks_filter": tasks_filter,
                "entries_filter": entries_filter,
                "annos_filter": annos_filter,
                "var_tasks_filter": db_get_value('tasks_filter'),
                "var_entries_filter": db_get_value('entries_filter'),
                "var_annos_filter": db_get_value('annos_filter'),
            },
            "name": db_name,
            # "path": file_path,
        },
    }

    db_json = json.dumps(db_dict, ensure_ascii=False)

    if need_backup:
        cwd = os.getcwd()
        bkup_path = os.path.join(cwd, "backups")
        print(bkup_path)
        file_path = os.path.join(bkup_path, db_name)
        db_dict["_meta"]["path"] = file_path
        if not os.path.exists(bkup_path):
            os.mkdir(bkup_path)
        with open(file_path, 'w') as ff:
            ff.write(db_json)
            pass

    print("make_backup ending")
    return db_dict
#


class ApiVar(Resource):
    @staticmethod
    def get(key):
        value = db_get_value(key)
        return json.loads(json_util.dumps({'code': 200, 'data': value}))
        pass

    @staticmethod
    @auth_token.login_required(role=['admin'])
    def put(key):
        db_log()
        data_in = request.get_json()
        if 'value' not in data_in:
            return json.loads(json_util.dumps({'code': 400, 'msg': 'value is required!'}))
        new_value = db_set_value(key, data_in['value'])
        return json.loads(json_util.dumps({'code': 200, 'data': new_value}))
        pass


# # - api.add_resource(ApiAssigmentPlan, '/api/assigment-plan')
# class ApiAssigmentPlan(Resource):
#     @staticmethod
#     @auth_token.login_required(role=['admin', 'manager'])
#     def post():
#         db_log()
#
#         data_in = request.get_json()
#         print([1, localtime()])
#         tables_to_update = assignment(
#             kv(data_in, 'topic'),
#             kv(data_in, 'user_tag'),
#             kv(data_in, 'task_tag'),
#             kv(data_in, 'users_per_task'),
#             kv(data_in, 'tasks_per_user'),
#             kv(data_in, 'exclusion'),
#             kv(data_in, 'polygraphs_per_user'),
#         )
#         print([5, localtime()])
#         return json.loads(json_util.dumps({'code': 200, 'data': tables_to_update}))


# - api.add_resource(ApiAssigmentAct, '/api/assigment-act')
class ApiAssigmentAct(Resource):
    @staticmethod
    @auth_token.login_required(role=['admin'])
    def post():
        db_log()

        data_in = request.get_json()
        if 'plans' not in data_in:
            return json.loads(json_util.dumps({'code': 400, 'msg': 'plans are required!'}))

        result = {
            'replaced': 0,
            'inserted': 0,
            'strange': 0,
        }
        for plan in data_in['plans']:
            if '_id' in plan:
                plan.pop('_id')
            task = db_Task.find_one_and_replace(
                {'id': plan['id']}, plan, projection={'id': True}, upsert=True)
            if not task:
                if db_Task.find_one({'id': plan['id']}, {'id': True}):
                    result['inserted'] += 1
                else:
                    result['strange'] += 1
            else:
                result['replaced'] += 1

        return json.loads(json_util.dumps({'code': 200, 'data': result}))
        pass
#


#
def build_tasks(settings):
    print('build_tasks start')
    filter_ = kv(settings, 'filter') or {'_id': None}
    topic = topic_regulation(kv(settings, 'topic'))
    batch_name = topic_regulation(kv(settings, 'batchName'))
    assert len(topic) > 0
    assert len(batch_name) > 0
    e_ids = [entry['id'] for entry in db_Entry.find(filter_, {'id': True})]
    random.shuffle(e_ids)
    random.shuffle(e_ids)
    print(['len(e_ids)', len(e_ids)])
    result = {
        'existed': 0,
        'inserted': 0,
        'strange': 0,
    }
    for e_id in e_ids:
        task_found = db_Task.find_one({'entry': e_id, 'topic': topic})
        if task_found:
            print(task_found)
            result['existed'] += 1
            continue
        task = {
            'id': new_int_str_id('Task'),
            'topic': topic,
            'batchName': batch_name,
            'entry': e_id,
            'to': [],
            'builtAt': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        }
        reb = db_Task.insert_one(task)
        result['inserted'] += 1
    print(['result', result])
    print('build_tasks end')
    return result
    pass


# - api.add_resource(ApiBuildTasks, '/api/build-tasks')
class ApiBuildTasks(Resource):
    @staticmethod
    @auth_token.login_required(role=['admin'])
    def post():
        db_log()

        data_in = request.get_json()
        if 'settings' not in data_in:
            return json.loads(json_util.dumps({'code': 400, 'msg': 'settings are required!'}))

        data_out = build_tasks(data_in['settings'])
        return json.loads(json_util.dumps({'code': 200, 'data': data_out}))
#


class ApiBackup(Resource):
    @staticmethod
    @auth_token.login_required(role=['admin'])
    def post():
        db_log()

        data_in = request.get_json()
        if 'settings' not in data_in:
            return json.loads(json_util.dumps({'code': 400, 'msg': 'settings are required!'}))

        db_bkup = make_backup(
            data_in['settings'].get("tasks_filter"),
            data_in['settings'].get("entries_filter"),
            data_in['settings'].get("annos_filter"),
            data_in['settings'].get("need_backup"),
            data_in['settings'].get("with_content"),
        )

        if not data_in['settings'].get("need_download"):
            db_bkup.pop("tasks")
            db_bkup.pop("entries")
            db_bkup.pop("annos")
            db_bkup.pop("users")

        return json.loads(json_util.dumps({'code': 200, 'data': db_bkup}))


##


def insert_new_task(it: dict):  # 待检查
    if 'entry' not in it:
        raise Exception("'entry' not in it")
    task = {
        'id': new_int_str_id('Task'),
        'topic': it['topic'],
        'entry': it['eId'],
        'to': [],
        # 'submitters': [],
        # 'dropped_count': 0,
        # 'skipped_count': 0,
        # 'valid_count': 0,
        # 'enough': False,
    }
    print(task)
    return db_Task.insert_one(task)
    pass


def fix_task_table(topic):  # 废弃！！！
    e_ids = [entry['id'] for entry in db_Entry.find({'topic': topic}, {'id': True})]
    print(e_ids)
    missing_e_ids = []
    for e_id in e_ids:
        task = db_Task.find_one({'entry': e_id})
        if not task:
            missing_e_ids.append(e_id)
            it = {
                'entry': e_id,
                'topic': topic,
            }
            xx = insert_new_task(it)
            print(xx)
        #
    #
    pass


def random_items(table, size):  # 暂时好像没用到，有其他做法实现相似功能了
    samples = db[table].aggregate([{'$sample': {'size': size}}])
    return samples


# UserAPI start
@auth_token.login_required
def get_user_me():
    # noinspection PyBroadException
    user = auth_token.current_user()
    if user:
        return json.loads(json_util.dumps({'code': 200, 'data': user}))


@auth_token.login_required(role=['admin', 'manager', 'inspector', 'super-inspector'])
def get_user_by_id(user_id):
    user = db_User.find_one({'id': user_id})
    if user:
        roles = auth_token.current_user().get('role') or []
        if 'manager' not in roles and 'admin' not in roles:
            if 'token' in user:
                user.pop('token')
        return json.loads(json_util.dumps({'code': 200, 'data': user}))


# - api.add_resource(ApiUsersAll, '/api/users')
class ApiUsersAll(Resource):
    @staticmethod
    @auth_token.login_required(role=['admin', 'manager', 'inspector', 'super-inspector'])
    def get():
        users = [user for user in db_User.find({})]
        roles = auth_token.current_user().get('role') or []

        # if 'manager' not in roles and 'admin' not in roles:
        #     for user in users:
        #         his_roles = user.get('role') or []
        #         if 'token' in user and ('manager' in his_roles or 'admin' in his_roles):
        #             user.pop('token')

        # print(users)
        return json.loads(json_util.dumps({'code': 200, 'data': users}))
        pass

    @staticmethod
    @auth_token.login_required(role=['admin', 'manager'])
    def post():
        db_log()
        user_new = request.get_json()
        if 'name' not in user_new:
            return json.loads(json_util.dumps({'code': 1, 'msg': "name required!"}))
        named_user = db['User'].find_one({'name': user_new['name']})
        if named_user:
            return json.loads(json_util.dumps({'code': 1, 'msg': "user name exists!"}))
        if '_id' in user_new:
            user_new.pop('_id')  # 这个自动生成的字段容易出 bug ，删掉也没事，反正用不到。
        if 'id' in user_new:
            user_new.pop('id')
        if 'token' not in user_new:
            user_new['token'] = str(uuid.uuid4())
        if 'createdAt' not in user_new:
            user_new['createdAt'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        if True:
            user_id = new_int_str_id('User')
            user_new['id'] = user_id
            db['User'].insert_one(user_new)
        user = db['User'].find_one({'id': user_id})
        if not user:
            return json.loads(json_util.dumps({'code': 500, 'msg': "strange: new user not found"}))
        return json.loads(json_util.dumps({'code': 200, 'data': user}))


# - api.add_resource(ApiUser, '/api/users/<string:user_id>')
class ApiUser(Resource):
    @staticmethod
    def get(user_id):
        return get_user_by_id(user_id)

    @staticmethod
    @auth_token.login_required
    def put(user_id):
        data_in = request.get_json()
        me = auth_token.current_user()
        roles = me.get('role') or []
        if 'manager' not in roles and 'admin' not in roles and me.get('id') != user_id:
            return json.loads(json_util.dumps({'code': 401, 'msg': "permission denied"}))
        if 'item' not in data_in:
            return json.loads(json_util.dumps({'code': 1, 'msg': "arg item needed"}))
        user = data_in['item']  # TODO
        if kv(user, 'id') != user_id:
            return json.loads(json_util.dumps({'code': 1, 'msg': f"user id differs ({kv(user, 'id')} != {user_id})"}))
        if '_id' in user:
            user.pop('_id')
        if 'modifiedAt' not in data_in:
            user['modifiedAt'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        result = db_User.update_one({'id': user['id']}, {'$set': user})
        if result.modified_count != 1:
            return json.loads(json_util.dumps({
                'code': 11,
                'msg': f"result.modified_count: {result.modified_count}",
                'info': {'data': user}
            }))
        info = {
            'modified_count': result.modified_count,
            'upserted_id': result.upserted_id,
            'raw_result': result.raw_result,
            'acknowledged': result.acknowledged,
            'matched_count': result.matched_count,
        }
        new_user = db_User.find_one({'id': user['id']})
        if not new_user:
            return json.loads(json_util.dumps({
                'code': 500,
                'msg': 'can not retrieve user'}))
        if 'manager' not in roles and 'admin' not in roles and me.get('id') != user_id:
            if 'token' in new_user:
                new_user.pop('token')
            pass
        return json.loads(json_util.dumps({'code': 200, 'data': new_user, 'info': info}))


# - api.add_resource(ApiMe, '/api/me')
class ApiMe(Resource):
    @staticmethod
    def get():
        me = get_user_me()
        db_log()
        return me
# UserAPI end


# EntryAPI start
def get_entry(entry_id, just_info=False):
    # noinspection PyBroadException
    try:
        entry = db_Entry.find_one({'id': entry_id, 'deleted': None})
        if not entry:
            return json.loads(json_util.dumps({'code': 404, 'msg': f'No such entry ({entry_id})'}))
        if kv(entry, 'deleted'):
            return json.loads(json_util.dumps({'code': 404, 'msg': f'This entry ({entry_id}) has been deleted'}))
        if just_info:
            if '_id' in entry:
                entry.pop('_id')
            if 'content' in entry:
                entry.pop('content')
        return json.loads(json_util.dumps({'code': 200, 'data': entry}))
    except Exception:
        error = get_err()
        return json.loads(json_util.dumps({'code': 500, 'msg': error}))


def get_entry_info(entry_id):
    return get_entry(entry_id, just_info=True)


def get_filtered_entries_in_filtered_tasks(tf=None, ef=None, with_content=False):
    if tf is None:
        tf = {}
    if ef is None:
        ef = {}
    tasks_filter = tf or db_get_value('tasks_filter') or {}
    entries_filter = ef or db_get_value('entries_filter') or {}
    project = {'_id': 0, 'aggregatedTasks': 0} if with_content else {'content': 0, '_id': 0, 'aggregatedTasks': 0}
    entries = [entry for entry in db['Entry'].aggregate([
        {'$lookup': {
            'let': {
                'task_entry_id': '$id'
            },
            'from': "Task",
            # 'localField': "id",
            # 'foreignField': "entry",
            'pipeline': [
                {'$match': {'$expr': {'$eq': ['$entry', '$$task_entry_id']}}},
                {'$match': tasks_filter}
            ],
            'as': "aggregatedTasks",
        }},
        {'$match': {'$and': [{'aggregatedTasks': {'$ne': []}}, entries_filter]}},
        {'$project': project},
    ])]
    return entries


# - api.add_resource(ApiEntryInfoAll, '/api/entry-infos')
class ApiEntryInfoAll(Resource):
    @staticmethod
    @auth_token.login_required(role=['admin', 'manager', 'inspector', 'super-inspector'])
    def get():
        db_log()

        # # polygraph_entries =
        # # [entry for entry in db_Entry.find({'polygraph': {'$exists': True}, 'deleted': {'$ne': True}})]
        # tasked_entries = [entry for entry in db_Entry.aggregate([
        #     {'$lookup': {
        #         'from': "Task",
        #         'localField': "id",
        #         'foreignField': "entry",
        #         'as': "allTasks",
        #     }},
        #     # {'$match': {'$expr': {'polygraph': {'$exists': False}, 'deleted': {'$ne': True}}}},
        # ])]

        entries = get_filtered_entries_in_filtered_tasks()

        for entry in entries:
            # entry['content'] = None
            if '_id' in entry:
                entry.pop('_id')
            if 'content' in entry:
                entry.pop('content')
            if 'aggregatedTasks' in entry:
                entry.pop('aggregatedTasks')

        return json.loads(json_util.dumps({'code': 200, 'data': entries}))


# - api.add_resource(ApiEntry, '/api/entries/<string:entry_id>')
class ApiEntry(Resource):
    @staticmethod
    @auth_token.login_required
    def get(entry_id):
        return get_entry(entry_id)
# EntryAPI end


# - api.add_resource(ApiEntryInfo, '/api/entry-infos/<string:entry_id>')
class ApiEntryInfo(Resource):
    @staticmethod
    @auth_token.login_required
    def get(entry_id):
        return get_entry_info(entry_id)
# EntryAPI end


# TaskAPI start
def get_task(user_id, task_id, curr_task_topic=None):
    # noinspection PyBroadException
    try:
        if curr_task_topic:
            task = db_Task.find_one({'id': task_id, 'to': user_id, 'topic': topic_regulation(curr_task_topic)})
        else:
            task = db_Task.find_one({'id': task_id, 'to': user_id})
        if task:
            res = {'code': 200, 'data': task}
            return json.loads(json_util.dumps(res))
        else:
            return json.loads(json_util.dumps({
                'code': 404, 'msg': f'No such task ({task_id}) for this user({user_id})'
            }))
    except Exception:
        error = get_err()
        return json.loads(json_util.dumps({'code': 500, 'msg': error}))


def get_filtered_tasks(tf=None):
    if tf is None:
        tf = {}
    tasks_filter = tf or db_get_value('tasks_filter') or {}
    tasks = [task for task in db_Task.find(tasks_filter)]
    return tasks


class ApiTasksAll(Resource):
    @staticmethod
    @auth_token.login_required(role=['admin', 'manager', 'inspector', 'super-inspector'])
    def get():
        tasks = get_filtered_tasks()
        # print(tasks)
        return json.loads(json_util.dumps({'code': 200, 'data': tasks}))
        pass


class ApiTasksMatter(Resource):
    @staticmethod
    @auth_token.login_required(role=['admin', 'manager', 'inspector', 'super-inspector'])
    def get():
        tasks = [task for task in db_Task.find({'to': {'$ne': []}})]
        print(tasks)
        return json.loads(json_util.dumps({'code': 200, 'data': tasks}))
        pass


class ApiTask(Resource):
    @staticmethod
    @auth_token.login_required
    def get(user_id, task_id):
        return get_task(user_id, task_id)
# TaskAPI end


# AnnoAPI start
def get_anno(request_data):
    user_id = request_data['user_id']
    task_id = request_data['task_id']
    res = {'code': -1, 'data': None}
    # noinspection PyBroadException
    try:
        # annos = db_Anno.find({})
        anno = db_Anno.find_one({'user': user_id, 'task': task_id})
        # print(anno)
        if not anno:
            res['code'] = 404
            res['msg'] = f'Data (/annos/{user_id}/{task_id}) not found.'
            return json.loads(json_util.dumps(res))
        res['code'] = 200
        res['data'] = Anno(anno).packed()
    except Exception:
        error = get_err()
        res['code'] = 500
        res['error'] = error
    return json.loads(json_util.dumps(res))


def put_anno(data_in):
    # noinspection PyBroadException
    try:
        user_id = data_in['user']
        task_id = data_in['task']

        if 'entry' not in data_in:
            task = db_Task.find_one({'id': task_id})
            if task:
                data_in['entry'] = task['entry']

        dropped = False if 'dropped' not in data_in or not data_in['dropped'] else True
        valid = True if 'valid' not in data_in or data_in['valid'] else False
        data_in['dropped'] = dropped
        data_in['valid'] = valid

        if '_id' in data_in:
            data_in.pop('_id')  # 这个自动生成的字段容易出 bug ，删掉也没事，反正用不到。

        anno_found = db_Anno.find_one({'user': user_id, 'task': task_id})
        if not anno_found:
            anno_id = new_int_str_id('Anno')
            data_in['id'] = anno_id
            db_Anno.insert_one(data_in)
        else:
            if 'review' in anno_found.get('content') and 'review' not in data_in.get('content'):
                # print(anno_found)
                # print(data_in)
                return json.loads(json_util.dumps({'code': 500, 'msg': "审核员有所批示，请刷新检查后再处理！"}))
                pass
            anno_id = anno_found['id']
            data_in['id'] = anno_id
            db_Anno.update_one({'id': anno_id}, {"$set": data_in})

        anno_found = db_Anno.find_one({'user': user_id, 'task': task_id})
        if not anno_found:
            return json.loads(json_util.dumps({'code': 500, 'msg': "strange: updated anno not found"}))
        anno_found = Anno(anno_found).packed()
        return json.loads(json_util.dumps({'code': 200, 'data': anno_found}))
    except Exception:
        error = get_err()
        return json.loads(json_util.dumps({'code': 500, 'msg': error}))


def get_filtered_annos_in_filtered_tasks(tf=None, af=None):
    if tf is None:
        tf = {}
    if af is None:
        af = {}
    tasks_filter = tf or db_get_value('tasks_filter') or {}
    annos_filter = af or db_get_value('annos_filter') or {}
    # print(localtime())
    aggregated_annos_wraps = db['Task'].aggregate([
        {'$match': tasks_filter},
        {'$lookup': {
            'let': {
                'anno_task_id': '$id'
            },
            'from': "Anno",
            # 'localField': "id",
            # 'foreignField': "task",
            'pipeline': [
                {'$match': {'$expr': {'$eq': ['$task', '$$anno_task_id']}}},
                {'$match': annos_filter},
                {'$project': {'_id': 0}},
            ],
            'as': "aggregatedAnnos",
        }},
        {'$project': {'_id': 0, 'aggregatedAnnos': 1}},
    ])
    # print(localtime())
    annos = []
    for wrap in aggregated_annos_wraps:
        for anno in wrap['aggregatedAnnos']:
            if '_id' in anno:
                anno.pop('_id')
            annos.append(anno)
    # print(localtime())
    return annos


class ApiAnnosAll(Resource):
    @staticmethod
    @auth_token.login_required(role=['admin', 'manager', 'inspector', 'super-inspector'])
    def get():
        annos = get_filtered_annos_in_filtered_tasks()
        # print(annos)
        return json.loads(json_util.dumps({'code': 200, 'data': annos}))
        pass


class ApiAnno(Resource):
    # decorators = [auth_token.login_required]

    @staticmethod
    @auth_token.login_required
    def get(user_id, task_id):
        # request_data = request.get_json()
        request_data = {'user_id': user_id, 'task_id': task_id}
        return get_anno(request_data)

    @staticmethod
    @auth_token.login_required
    def put(user_id, task_id):
        # TODO
        request_data = request.get_json()
        # ip = request.remote_addr
        request_data['user'] = user_id
        request_data['task'] = task_id
        dct = dict([(k, v) for k, v in request.headers.items()])
        ip = kv(dct, 'X-Forwarded-For')
        request_data['ip'] = ip
        return put_anno(request_data)
# AnnoAPI end


#
class ApiEvalTeamsAll(Resource):
    @staticmethod
    # @auth_token.login_required(role=['admin', 'manager'])
    def get():
        user = auth_token.current_user()
        roles = get_user_roles(user)
        teams = []
        if 'admin' in roles or 'manager' in roles:
            teams = [team for team in db['EvalTeam'].find(
                {'deleted': {'$ne': True}})]
        else:
            teams = [team for team in db['EvalTeam'].find(
                {'deleted': {'$ne': True}}, projection={
                    '_id': 0,
                    'team_name': 1,
                    'team_type': 1,
                    'leader': 1,
                    'institution': 1,
                    'email': 1,
                })]
            for team in teams:
                team['leader'] = team.get('leader')[0]+"*"*(len(team.get('leader'))-1)
                email_units = team.get('email').split("@")
                email_tails = email_units[1].split(".")
                masked_email_tails = [span[0]+"**" for span in email_tails]
                masked_email = email_units[0][0] + "**@" + ".".join(masked_email_tails)
                team['email'] = masked_email
                # print(teams)
        return json.loads(json_util.dumps({'code': 200, 'data': teams}))
        pass

    @staticmethod
    def post():
        db_log()
        team_new = request.get_json()
        dct = dict([(k, v) for k, v in request.headers.items()])
        ip = kv(dct, 'X-Forwarded-For')
        team_new['ip'] = ip
        if '_id' in team_new:
            team_new.pop('_id')  # 这个自动生成的字段容易出 bug ，删掉也没事，反正用不到。
        if 'id' in team_new:
            team_new.pop('id')

        named_team = db['EvalTeam'].find_one({'team_name': team_new.get('team_name') or ''})
        if named_team:
            return json.loads(json_util.dumps({'code': 101, 'msg': "队伍名称已存在"}))

        ip_team = [xx for xx in db['EvalTeam'].find({'ip': team_new.get('ip') or ''})]
        if len(ip_team) >= 3:
            return json.loads(json_util.dumps({'code': 102, 'msg': "该 ip 地址报名已满3次"}))

        else:
            team_id = new_int_str_id('EvalTeam')
            team_new['id'] = team_id
            db['EvalTeam'].insert_one(team_new)

        team = db['EvalTeam'].find_one({'id': team_id})
        if not team:
            return json.loads(json_util.dumps({'code': 500, 'msg': "strange: new team not found"}))
        return json.loads(json_util.dumps({'code': 200, 'data': team}))


#
class ApiMemosAll(Resource):
    @staticmethod
    @auth_token.login_required(role=['admin', 'manager', '__inspector', '__super-inspector'])
    def get():
        memos = [memo for memo in db['Memo'].find({'deleted': {'$ne': True}})]
        # print(memos)
        return json.loads(json_util.dumps({'code': 200, 'data': memos}))
        pass

    @staticmethod
    @auth_token.login_required(role=['admin', 'manager'])
    def post():
        memo_new = request.get_json()
        dct = dict([(k, v) for k, v in request.headers.items()])
        ip = kv(dct, 'X-Forwarded-For')
        memo_new['ip'] = ip
        if '_id' in memo_new:
            memo_new.pop('_id')  # 这个自动生成的字段容易出 bug ，删掉也没事，反正用不到。
        if 'id' in memo_new:
            memo_new.pop('id')
        if True:
            memo_id = new_int_str_id('Memo')
            memo_new['id'] = memo_id
            db['Memo'].insert_one(memo_new)
        memo = db['Memo'].find_one({'id': memo_id})
        if not memo:
            return json.loads(json_util.dumps({'code': 500, 'msg': "strange: new memo not found"}))
        return json.loads(json_util.dumps({'code': 200, 'data': memo}))


class ApiMemo(Resource):
    @staticmethod
    @auth_token.login_required(role=['admin', 'manager'])
    def get(memo_id):
        memo = db['Memo'].find_one({'id': memo_id})
        # print(memo)
        return json.loads(json_util.dumps({'code': 200, 'data': memo}))
        pass

    @staticmethod
    @auth_token.login_required(role=['admin', 'manager'])
    def put(memo_id):
        memo_new = request.get_json()
        dct = dict([(k, v) for k, v in request.headers.items()])
        ip = kv(dct, 'X-Forwarded-For')
        memo_new['ip'] = ip
        if '_id' in memo_new:
            memo_new.pop('_id')  # 这个自动生成的字段容易出 bug ，删掉也没事，反正用不到。
        memo_old = db['Memo'].find_one({'id': memo_id})
        if not memo_old:
            memo_id = new_int_str_id('Memo')
            memo_new['id'] = memo_id
            db['Memo'].insert_one(memo_new)
        else:
            memo_id = memo_old['id']
            memo_new['id'] = memo_id
            db['Memo'].replace_one({'id': memo_id}, memo_new)
            pass
        memo = db['Memo'].find_one({'id': memo_id})
        if not memo:
            return json.loads(json_util.dumps({'code': 500, 'msg': "strange: replaced memo not found"}))
        return json.loads(json_util.dumps({'code': 200, 'data': memo}))
#


# 获取当前审核员的 待检清单
class CheckListForMe(Resource):
    @staticmethod
    @auth_token.login_required(role=['admin', 'manager', 'inspector', 'super-inspector'])
    def get():
        inspector = auth_token.current_user()
        roles = get_user_roles(inspector)
        if 'admin' in roles or 'super-inspector' in roles:
            users = [user for user in db_User.find({})]
            annos = [anno for anno in db_Anno.find({})]
            tasks = [task for task in db_Task.find({'$where': "function(){return this.submitters.length>0}"})]
            pass
        if 'manager' in roles or 'inspector' in roles:
            my_id = kv(inspector, 'id')
            users = [user for user in db_User.find({'manager': my_id})]
            user_ids = [kv(user, 'id') for user in users]
            annos = [anno for anno in db_Anno.find({'user': {'$in': user_ids}})]
            tasks = [task for task in db_Task.find({'submitters': {'$in': user_ids}})]
            pass
        else:
            users = []
            annos = []
            tasks = []
        res = {'code': 200, 'data': {
            'users': users,
            'annos': annos,
            'tasks': tasks,
        }}
        return json.loads(json_util.dumps(res))


# 获取当前用户的 任务清单
class WorkListForMe(Resource):
    @staticmethod
    @auth_token.login_required
    def get():
        # noinspection PyBroadException
        try:
            # check
            res_user = get_user_me()
            if 'data' not in res_user or not res_user['data']:
                return json.loads(json_util.dumps({
                    'code': 404, 'msg': 'user not found'}))
            # check over
            user = User(res_user['data']).packed()
            user_id = user['id']
            curr_task_topic = kv(user, 'currTask')
            if not curr_task_topic:
                return json.loads(json_util.dumps({
                    'code': 403, 'msg': 'This user has no task topic'}))
            tasks = user['tasks']
            work_list = []

            working_batch_names = db_get_value("working_batch_names") or []

            for task_id in tasks:
                task_res = get_task(user_id, task_id, topic_regulation(curr_task_topic))
                if 'data' not in task_res:
                    continue
                task = task_res['data']
                if task.get('batchName') not in working_batch_names:
                    continue
                work_item = {'task': task}
                anno_res = get_anno({'user_id': user_id, 'task_id': task_id})
                if 'data' not in anno_res or not anno_res['data']:
                    work_list.append(work_item)
                    continue
                anno = anno_res['data']
                work_item['anno'] = anno
                work_list.append(work_item)
            res = {'code': 200, 'data': work_list}
            return json.loads(json_util.dumps(res))
        except Exception:
            error = get_err()
            return json.loads(json_util.dumps({'code': 500, 'msg': error}))


# 获取当前 task 涉及的 entry 和 anno
class ApiThing(Resource):
    @staticmethod
    @auth_token.login_required
    def get(user_id, task_id):
        task = db_Task.find_one({'id': task_id, 'to': user_id})
        if task:
            entry = db_Entry.find_one({'id': task['entry'], 'deleted': {'$ne': True}})
            if not entry:
                return json.loads(json_util.dumps({
                    'code': 404, 'msg': f"Can not find related entry[#{task['entry']}]"
                }))
            anno = db_Anno.find_one({'user': user_id, 'task': task_id})
            if anno:
                anno = Anno(anno).packed()
            thing = {'task': task, 'entry': entry, 'anno': anno}
            res = {'code': 200, 'data': thing}
            return json.loads(json_util.dumps(res))
        else:
            res = {'code': 404, 'msg': 'No such task'}
            return json.loads(json_util.dumps(res))


# def simple(collection, count):
#     # size = len(collection)
#     pass


def give_task(user_id, topic):
    the_filter = {
        'to': {'$ne': user_id},
        'topic': topic,
        '$or': [{'to': {'$size': size}} for size in range(1, Parameter.X)]
    }
    #
    tasks_not_completely_allocated = db_Task.find(the_filter)
    if tasks_not_completely_allocated:
        sample = random.choice([task for task in tasks_not_completely_allocated])
        print(sample)
        return sample
    #
    tasks_never_allocated = db_Task.find({'to': {'$size': 0}, 'topic': topic})
    if tasks_never_allocated:
        sample = random.choice([task for task in tasks_never_allocated])
        print(sample)
        return sample
    #
    pass


def operate_db_table(table="_", data_in={}):
    # result = None
    # pp = {}
    # noinspection PyBroadException
    try:
        # print(data_in)
        # if '$$$' not in data_in or data_in['$$$'] != DB_SECRET:
        #     return json.loads(json_util.dumps({'code': 403, 'msg': "FORBIDDEN"}))
        pp = {
            'table': "_" if 'table' not in data_in or not data_in['table'] else f"{data_in['table']}",
            'operator': "_" if 'opt' not in data_in or not data_in['opt'] else f"{data_in['opt']}",
            'kwargs': {} if 'args' not in data_in or not data_in['args'] else data_in['args'],
        }
        the_table = db[table]
        if hasattr(the_table, pp['operator']):
            # result = mc(pp['operator'], **pp['kwargs'])(the_table)
            pass
        res = {
            # 'result': result,
            'code': 0,  # unknown
            'info': {'config': pp},
            # 'data_in': data_in,
        }
        rrr = json.loads(json_util.dumps(res))
    except Exception:
        err = get_err()
        return json.loads(json_util.dumps({'code': 500, 'msg': err}))
    return rrr


# - api.add_resource(DbTableAPI, '/api/db/<string:table>')
class DbTableAPI(Resource):
    @staticmethod
    @auth_token.login_required(role=['admin'])
    def post(table):
        data_in = request.get_json()
        return operate_db_table(table, data_in)


def operate_db(data_in):
    # result = None
    # pp = {}
    # noinspection PyBroadException
    try:
        # print(data_in)
        # if '$$$' not in data_in or data_in['$$$'] != DB_SECRET:
        #     return json.loads(json_util.dumps({'code': 403, 'msg': "FORBIDDEN"}))
        pp = {
            'table': "_" if 'table' not in data_in or not data_in['table'] else f"{data_in['table']}",
            'operator': "_" if 'opt' not in data_in or not data_in['opt'] else f"{data_in['opt']}",
            'kwargs': {} if 'args' not in data_in or not data_in['args'] else data_in['args'],
        }
        the_table = db[pp['table']]
        if hasattr(the_table, pp['operator']) and pp['operator'] in ['find', 'find_one', 'aggregate', 'count_documents']:
            result = mc(pp['operator'], **pp['kwargs'])(the_table)
            pass
        res = {
            'result': result,
            'code': 200,
            'info': {'config': pp},
            # 'data_in': data_in,
        }
        rrr = json.loads(json_util.dumps(res))
    except Exception:
        err = get_err()
        return json.loads(json_util.dumps({'code': 500, 'msg': err}))
    return rrr


# - api.add_resource(DbAPI, '/api/db')
class DbAPI(Resource):
    @staticmethod
    @auth_token.login_required(role=['admin'])
    def post():
        data_in = request.get_json()
        return operate_db(data_in)


# - api.add_resource(NewUserAPI, '/api/new-user/')
class NewUserAPI(Resource):
    @staticmethod
    @auth_token.login_required(role=['admin', 'manager'])
    def post():
        # noinspection PyBroadException
        try:
            data_in = request.get_json()
            # if '$$$' not in data_in or data_in['$$$'] != DB_SECRET:
            #     return json.loads(json_util.dumps({'code': 403, 'message': "FORBIDDEN"}))
            if 'name' not in data_in or not data_in['name']:
                return json.loads(json_util.dumps({"code": 1, 'msg': "Name please"}))
            name = data_in['name']
            fr = db_User.find_one({'name': name})
            if fr:
                return json.loads(json_util.dumps({"code": 1, 'msg': "Name exist"}))
            password = str(uuid.uuid1())
            idx = str(db_User.count_documents({})+1)
            user = {
                'id': idx,
                'name': name,
                'token': password,
            }
            sss = db_User.insert_one(user)
            print(sss)
            return json.loads(json_util.dumps({'code': 200, 'data': user}))
        except Exception:
            err = get_err()
            return json.loads(json_util.dumps({"code": 500, 'msg': err}))


# - api.add_resource(ApiSpeRef, '/api/spe-ref/<string:origin_id>')
class ApiSpeRef(Resource):
    @staticmethod
    @auth_token.login_required()
    def get(origin_id):
        # noinspection PyBroadException
        try:
            that = db['SPE_Ref'].find_one({'originId': origin_id})
            if that:
                return json.loads(json_util.dumps({"code": 200, 'data': that}))
            return json.loads(json_util.dumps({"code": 404, 'msg': f"SPEs for {origin_id} not found"}))
        except Exception:
            err = get_err()
            return json.loads(json_util.dumps({"code": 500, 'msg': err}))
        pass


# - api.add_resource(ApiWorkload, '/api/workload/<string:user_id>')
class ApiWorkload(Resource):
    @staticmethod
    @auth_token.login_required()
    def get(user_id):
        # noinspection PyBroadException
        try:
            if not db['User'].find_one({'id': user_id}):
                return json.loads(json_util.dumps({"code": 404, 'msg': "找不到该用户"}))
            if auth_token.current_user().get('id') != user_id:
                roles = auth_token.current_user().get('role') or []
                if 'manager' not in roles and 'admin' not in roles:
                    return json.loads(json_util.dumps({"code": 401, 'msg': "没有权限"}))
            that = db['User'].aggregate([
                {'$match': {'id': user_id}},
                {'$project': {
                    '_id': 0,
                    'id': 1,
                    'name': 1,
                    'manager': 1,
                    'currTaskGroup': 1,
                    'role': 1,
                    'tags': 1,
                    'quitted': 1,
                    'tagsBeforeTask3': 1,
                }},
                {'$lookup': {
                    'from': "Anno",
                    # 'localField': "id",
                    # 'foreignField': "user",
                    'pipeline': [
                        {'$match': {'user': user_id}},
                        {'$project': {'_id': 0, 'id': 1, 'task': 1, 'entry': 1, 'content': 1}},
                        {'$lookup': {
                            'from': "Task",
                            # 'localField': "task",
                            # 'foreignField': "id",
                            'let': {'task': "$task"},
                            'pipeline': [
                                {'$match': {'$expr': {'$eq': ["$id", "$$task"]}}},
                                # {'$match': {'to': user_id}},
                                {'$project': {
                                    '_id': 0,
                                    'topic': 1,
                                    'batchName': 1,
                                    'batch': 1,
                                    'deleted': 1,
                                    'oldBatchName': 1,
                                }},
                            ],
                            'as': "task_wrap",
                        }},
                        {'$match': {'task_wrap.0.batchName': {'$ne': "task2r-01r"}}},
                    ],
                    'as': "all_anno_items",
                }},
            ])
            if that:
                return json.loads(json_util.dumps({"code": 200, 'data': that}))
            return json.loads(json_util.dumps({"code": 404, 'msg': f"workload for {user_id} not found"}))
        except Exception:
            err = get_err()
            return json.loads(json_util.dumps({"code": 500, 'msg': err}))
        pass


# - api.add_resource(ApiWorkloadOfReviewer, '/api/workload-reviewer/<string:user_id>')
class ApiWorkloadOfReviewer(Resource):
    @staticmethod
    @auth_token.login_required()
    def get(user_id):
        # noinspection PyBroadException
        try:
            if not db['User'].find_one({'id': user_id}):
                return json.loads(json_util.dumps({"code": 404, 'msg': "找不到该用户"}))
            if auth_token.current_user().get('id') != user_id:
                roles = auth_token.current_user().get('role') or []
                if 'manager' not in roles and 'admin' not in roles:
                    return json.loads(json_util.dumps({"code": 401, 'msg': "没有权限"}))
            user_name = (db['User'].find_one({'id': user_id}) or {}).get("name")
            that = db['Anno'].aggregate([
                {'$match': {
                    "content._ctrl.timeLog": {
                        '$elemMatch': {
                            '$or': [
                                {"2.name": user_name},
                                {"2.id": user_id},
                            ]}}}},
                {'$project': {'_id': 0, 'id': 1, 'task': 1, 'content._ctrl.timeLog': 1}},
                {'$lookup': {
                    'from': "Task",
                    # 'localField': "task",
                    # 'foreignField': "id",
                    'let': {'task': "$task"},
                    'pipeline': [
                        {'$match': {'$expr': {'$eq': ["$id", "$$task"]}}},
                        {'$project': {
                            '_id': 0,
                            'topic': 1,
                            'batchName': 1,
                            'batch': 1,
                            'deleted': 1,
                            'oldBatchName': 1,
                        }},
                    ],
                    'as': "task_wrap",
                }},
                {'$match': {'task_wrap.0.batchName': {'$ne': "task2r-01r"}}},
            ])
            if that:
                return json.loads(json_util.dumps({"code": 200, 'data': {
                    'reviewed_annos': that,
                    'user_name': user_name,
                }}))
            return json.loads(json_util.dumps({"code": 404, 'msg': f"workload of reviewer {user_id} not found"}))
        except Exception:
            err = get_err()
            return json.loads(json_util.dumps({"code": 500, 'msg': err}))
        pass


#
api.add_resource(DbTableAPI, '/api/db/<string:table>')
api.add_resource(DbAPI, '/api/db')
api.add_resource(NewUserAPI, '/api/new-user/')
# api.add_resource(ApiAssigmentPlan, '/api/assigment-plan')
api.add_resource(ApiAssigmentAct, '/api/assigment-act')
api.add_resource(ApiBuildTasks, '/api/build-tasks')
api.add_resource(ApiBackup, '/api/backup')
#

# login required
api.add_resource(ApiUsersAll, '/api/users')
api.add_resource(ApiUser, '/api/users/<string:user_id>')
api.add_resource(ApiMe, '/api/me')
#
api.add_resource(ApiEntryInfoAll, '/api/entry-infos')
api.add_resource(ApiEntry, '/api/entries/<string:entry_id>')
api.add_resource(ApiEntryInfo, '/api/entry-infos/<string:entry_id>')
#
api.add_resource(ApiTasksAll, '/api/tasks')
api.add_resource(ApiTasksMatter, '/api/tasks-matter')
# api.add_resource(ApiTasksForUser, '/api/tasks/<string:user_id>')
api.add_resource(ApiTask, '/api/tasks/<string:user_id>/<string:task_id>')
#
api.add_resource(ApiAnnosAll, '/api/annos')
# api.add_resource(ApiAnnosForUser, '/api/annos/<string:user_id>')
api.add_resource(ApiAnno, '/api/annos/<string:user_id>/<string:task_id>')
#
# api.add_resource(ApiThingsAll, '/api/things')
# api.add_resource(ApiThingsForUser, '/api/things/<string:user_id>')
api.add_resource(ApiThing, '/api/things/<string:user_id>/<string:task_id>')
#
api.add_resource(WorkListForMe, '/api/work-list-for-me')
#
api.add_resource(CheckListForMe, '/api/check-list-for-me')
#
api.add_resource(ApiMemosAll, '/api/memos')
api.add_resource(ApiMemo, '/api/memos/<string:memo_id>')
api.add_resource(ApiVar, '/api/var/<string:key>')
#
api.add_resource(ApiEvalTeamsAll, '/api/eval-register')
#
api.add_resource(ApiSpeRef, '/api/spe-ref/<string:origin_id>')
#
api.add_resource(ApiWorkload, '/api/workload/<string:user_id>')
api.add_resource(ApiWorkloadOfReviewer, '/api/workload-reviewer/<string:user_id>')


@app.route('/')
def index():
    return 'hello'


#
if __name__ == '__main__':
    # server = pywsgi.WSGIServer('0.0.0.0', 6000, app)
    # server.serve_forever()
    if __name__ == '__main__':
        app.run(debug=False, host="0.0.0.0", port='8888')
    # if DEVELOPING:
    #     app.run()
    #     # server = pywsgi.WSGIServer(('http://192.168.124.5:8888'), app)
    #     # server.serve_forever()
    # else:
    #     app.run(debug=True, host="0.0.0.0", port=8000)
    #

