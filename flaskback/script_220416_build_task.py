# coding=utf-8
from app import *

if __name__ == '__main__':
    build_tasks({
        'filter': {
            '$where': 'function(){return +this.id>=3048}',
        },
        'topic': '第1期',
        'batchName': 'task1-02',
    })
    pass
