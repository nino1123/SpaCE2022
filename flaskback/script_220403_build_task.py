# coding=utf-8
from app import *
import random

if __name__ == '__main':
    found = [xx for xx in db_Entry.find({'_id': None})]
    print(found)
    # print(time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()))

if __name__ == '__main':
    result = db_Task.delete_many({'$where': 'function(){return +this.id>5604}'})
    print(result.deleted_count)

if __name__ == '__main':
    # 构建 Task 表
    build_tasks({
        'filter': {"$or": [
            {"info.countSpatialPOS.0": {"$gte": 1}, "info.weightedValue.1": {"$gte": 0.2},
             "info.sourceID": {"$regex": "^B.+", "$options": "m"}},
            {"info.countSpatialPOS.0": {"$gte": 2}, "info.weightedValue.1": {"$gte": 0.6},
             "info.sourceID": {"$regex": "^F.+", "$options": "m"}},
            {"info.countSpatialPOS.0": {"$gte": 1}, "info.weightedValue.1": {"$gte": 0.2},
             "info.sourceID": {"$regex": "^E.+", "$options": "m"}},
            {"info.countSpatialPOS.0": {"$gte": 1}, "info.weightedValue.1": {"$gte": 0.2},
             "info.sourceID": {"$regex": "^H.+", "$options": "m"}},
            {"info.countSpatialPOS.0": {"$gte": 1}, "info.weightedValue.1": {"$gte": 0.2},
             "info.sourceID": {"$regex": "^G.+", "$options": "m"}}
        ]},
        'topic': '清洗'
    })
    pass

