# coding=utf-8
# import json
from app import *


if __name__ == '__main':
    # with open('files/220330-备用测谎题语料rpId列表.json', 'r') as ft:
    #     ll = json.load(ft)
    # print(len(ll))

    with open('files/220330-备用测谎题语料待入库.json', 'r') as ft:
        tt = json.load(ft)
    print(len(tt))

    entries = []
    result = {
        'replaced': 0,
        'inserted': 0,
        'strange': 0,
    }
    for it in tt:
        ta = {'$set': {
            'content.material': it['material'],
            'polygraph': it['label'],
            'version': '220330'
        }}
        result_one = db_Entry.update_one({'info.rpId': it['rpId']}, ta)
        if result_one.modified_count == 1:
            entry = db_Entry.find_one({'info.rpId': it['rpId']})
            if entry:
                result['replaced'] += 1
        else:
            result['strange'] += 1
    print(result)
    pass

if __name__ == '__main':
    result = db_User.delete_many({})
    print(result.deleted_count)
    result = db_Task.delete_many({})
    print(result.deleted_count)
    result = db_Anno.delete_many({})
    print(result.deleted_count)

if __name__ == '__main':
    with open('files/Task-select-example.json', 'r') as ft:
        waiting_tasks = json.load(ft)
        for waiting_task in waiting_tasks:
            t_id = kv(waiting_task, 'id')
            if t_id:
                if '_id' in waiting_task:
                    waiting_task.pop('_id')
                xx = db_Task.find_one_and_replace({'id': t_id}, waiting_task)
                print(xx)
    pass

if __name__ == '__main':
    print(db_Entry.count_documents({'version': '220328'}))
    print(db_Entry.count_documents({'info.hasDVerb': True}))
    with open('files/220328-Newest-Entry-table-with-id-ABDEGH-update-mark-dverb.json', 'r') as ft:
        waiting_entries = json.load(ft)
        for waiting_entry in waiting_entries:
            e_id = kv(waiting_entry, 'id')
            if e_id:
                if '_id' in waiting_entry:
                    waiting_task.pop('_id')
                xx = db_Entry.find_one_and_replace({'id': e_id}, waiting_entry)
                print(xx)
    print(db_Entry.count_documents({'version': '220328'}))
    print(db_Entry.count_documents({'info.hasDVerb': True}))
    pass

if __name__ == '__main':
    ll = []
    print(db_Entry.count_documents({'version': '220328'}))
    with open('files/220328-Newest-Entry-table-with-id-ABDEGH-insert.json', 'r') as ft:
        waiting_entries = json.load(ft)
        for waiting_entry in waiting_entries:
            e_id = kv(waiting_entry, 'id')
            if e_id:
                if '_id' in waiting_entry:
                    waiting_task.pop('_id')
                xx = db_Entry.find_one_and_replace({'id': e_id}, waiting_entry, upsert=True)
                print(xx)
            else:
                ll.append(waiting_entry)
    print(ll)
    print(len(ll))
    print(db_Entry.count_documents({'version': '220328'}))
    print(db_Entry.count_documents({'info.hasDVerb': True}))
    pass


def fix_tasks_delete():
    oc = db_Task.count_documents({'deleted': True})
    cc = 0
    for task in db_Task.find({}):
        entry = db_Entry.find_one({'id': task['entry'], 'deleted': {'$ne': True}})
        if not entry:
            db_Task.find_one_and_update({'id': task['id']}, {'$set': {'deleted': True}})
            cc += 1
        else:
            db_Task.find_one_and_update({'id': task['id']}, {'$unset': {'deleted': None}})
    ac = db_Task.count_documents({'deleted': True})
    print([oc, ac, cc])


if __name__ == '__main':
    fix_tasks_delete()
    pass
