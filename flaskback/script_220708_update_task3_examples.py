# coding=utf-8
from app import *

if __name__ == '__main__':
    with open("task3示例-annos.json", "r") as ff:
        annos = json.load(ff)
        for anno in annos:
            result = db['Anno'].replace_one({'id': anno.get('id')}, anno, upsert=False)
            print([result.matched_count, result.modified_count])
