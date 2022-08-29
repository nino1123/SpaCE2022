import pymongo
from config import Parameter, DB_SECRET, API_BASE_DEV, API_BASE_PROD, DEVELOPING, API_BASE
#


#
mongo_client = pymongo.MongoClient('127.0.0.1', 27017)  # 建立 MongoBD 数据库连接
db = mongo_client["Sp22Anno"]  # 数据库名
#


#
class User:
    def __init__(self, user):
        self.core = user

    def packed(self):
        user = self.core
        user['tasks'] = self.tasks()
        user['annos'] = self.annos()
        return user

    def tasks(self):
        return [task['id'] for task in db['Task'].find({'to': self.core['id']}, {'id': 1})]

    def annos(self):
        return [anno['id'] for anno in db['Anno'].find({'user': self.core['id']}, {'id': 1})]


class Entry:
    def __init__(self, entry):
        self.core = entry

    def packed(self):
        entry = self.core
        return entry

    def tasks(self):
        return [task['id'] for task in db['Task'].find({'entry': self.core['id']}, {'id': 1})]

    def annos(self):  # using index
        task_ids = [task['id'] for task in db['Task'].find({'entry': self.core['id']}, {'id': 1})]
        items = []
        for task_id in task_ids:
            anno_ids = [anno['id'] for anno in db['Anno'].find({'task': task_id}, {'id': 1})]
            items.extend(anno_ids)
        return items

    def annos_(self):  # without index
        return [anno['id'] for anno in db['Anno'].find({'entry': self.core['id']}, {'id': 1})]


class Task:
    def __init__(self, task):
        self.core = task

    def packed(self, standard=Parameter.X):
        task = self.core
        task['submitters'] = self.submitters()
        task['dropped_count'] = self.dropped_count()
        task['valid_count'] = self.valid_count()
        task['enough'] = self.enough(standard)
        return task

    def submitters(self):
        return [anno['user'] for anno in db['Anno'].find({'task': self.core['id']}, {'user': 1})]

    def dropped_count(self):
        items = [anno['dropped'] for anno in db['Anno'].find({'task': self.core['id']}, {'dropped': 1})]
        return items.count(True)

    def valid_count(self):
        items = [anno['valid'] for anno in db['Anno'].find({'task': self.core['id']}, {'valid': 1})]
        return items.count(True)

    def enough(self, standard=Parameter.X):
        items = [anno['id'] for anno in db['Anno'].find({'task': self.core['id']}, {'id': 1})]
        return len(items) >= standard


class Anno:
    def __init__(self, anno):
        self.core = anno

    def packed(self):
        anno = self.core
        anno['task'] = self.task()
        anno['entry'] = self.entry()
        anno['topic'] = self.topic()
        return anno

    def task(self):
        if 'task' not in self.core:
            if 'task_id' not in self.core:
                return None
            return self.core['task_id']
        return self.core['task']

    def entry(self):
        if 'entry' in self.core:
            return self.core['entry']
        task_id = self.task()
        if not task_id:
            return None
        task = db['Task'].find_one({'id': task_id})
        if not task:
            return None
        if 'entry' not in task:
            if 'eId' not in task:
                return None
            return task['eId']
        return task['entry']

    def topic(self):
        if 'topic' in self.core:
            return self.core['topic']
        task_id = self.task()
        if not task_id:
            return None
        task = db['Task'].find_one({'id': task_id})
        if not task:
            return None
        if 'topic' not in task:
            return None
        return task['topic']
#
