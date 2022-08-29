# coding=utf-8
from app import *

if __name__ == '__main__':
    build_tasks({
        'filter': {
            'id': {'$exists': True},
        },
        'topic': 'task1',
        'batchName': 'task1-01',
    })
    pass
