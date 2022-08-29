# coding=utf-8
from app import *

if __name__ == '__main__':
    print(db_Entry.count_documents({'version': '220405'}))
    with open('files/Polygraph-220405.json', 'r') as ft:
        waiting_entries = json.load(ft)
        for waiting_entry in waiting_entries:
            e_id = kv(waiting_entry, 'id')
            if e_id:
                if '_id' in waiting_entry:
                    waiting_entry.pop('_id')
                xx = db_Entry.find_one_and_replace({'id': e_id}, waiting_entry)
                print(xx)
    print(db_Entry.count_documents({'version': '220405'}))
    pass

