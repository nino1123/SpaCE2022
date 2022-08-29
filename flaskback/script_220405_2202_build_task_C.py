# coding=utf-8
from app import *

if __name__ == '__main':
    # 构建 Task 表
    build_tasks({
        'filter': {
            "info.countSpatialPOS.0": {"$eq": 1},
            "info.weightedValue.0": {"$gte": 20},
            "info.weightedValue.1": {"$gte": 0.35},
            "info.sourceID": {
                "$regex": "^C.+",
                "$options": "m"
            }
        },
        'topic': '清洗',
        'batchName': '清洗-第2批',
    })
    pass
