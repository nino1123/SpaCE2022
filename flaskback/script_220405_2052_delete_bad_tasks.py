# coding=utf-8
from app import *

if __name__ == '__main':
    with open('files/ids-to-delete.json', 'r') as ft:
        entry_ids_to_remove = json.load(ft)
        print(entry_ids_to_remove)

    tasks = [task for task in db_Task.find({})]
    # 那么我要做的处理是：对于每个已有的 task
    for task in tasks:
        task.pop('_id')
        batch = kv(task, 'batch')
        # 检查 batch
        if not batch:
            # 如果是 undefined ， "batchName": "清洗-第1批"
            task['batchName'] = "清洗-第1批"
        elif batch == 1220405110053 or batch == 1220405162057:
            # 如果是 1220405110053 ，
            # "batchName": "清洗-第2批"
            task['batchName'] = "清洗-第2批"
            # 根据 task.entry 判断，
            if task['entry'] in entry_ids_to_remove:
                # 要删→ "deleted": true
                task['deleted'] = True
            pass
        else:
            # 其他情况，不可能
            task['batchName'] = "不应该啊"
            pass
        lastEditAt = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        task['lastEditAt'] = lastEditAt
        db_Task.find_one_and_replace({'id': task['id']}, task)
