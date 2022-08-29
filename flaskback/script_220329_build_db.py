# coding=utf-8
from app import *
import random

# 已经构建好了 Entry 表之后运行此脚本

if __name__ == '__main__':
    result = db_Task.delete_many({})
    print(result.deleted_count)
    # 构建 Task 表
    e_ids_A = [entry['id'] for entry in db_Entry.find(
        {
            'info.countSpatialPOS.0': {'$gte': 1},
            'info.weightedValue.1': {'$gte': 0.25},
            'info.sourceID': {'$regex': '^A.+', '$options': 'm'}
        },
        {'id': True}
    )]
    print(len(e_ids_A))
    e_ids_D = [entry['id'] for entry in db_Entry.find(
        {
            'info.countSpatialPOS.0': {'$gte': 1},
            'info.weightedValue.1': {'$gte': 0.2},
            'info.sourceID': {'$regex': '^D.+', '$options': 'm'}
        },
        {'id': True}
    )]
    print(len(e_ids_D))
    e_ids_C = [entry['id'] for entry in db_Entry.find(
        {
            'info.countSpatialPOS.0': {'$gte': 2},
            'info.weightedValue.1': {'$gte': 0.35},
            'info.sourceID': {'$regex': '^C.+', '$options': 'm'}
        },
        {'id': True}
    )]
    print(len(e_ids_C))
    e_ids = e_ids_A + e_ids_D + e_ids_C
    random.shuffle(e_ids)
    random.shuffle(e_ids)
    t_id = db_Task.count_documents({}) + 1
    for e_id in e_ids:
        task = {
            'id': f"{t_id}",
            'topic': '清洗',
            'entry': e_id,
            'to': [],
        }
        db_Task.insert_one(task)
        t_id += 1
    pass

