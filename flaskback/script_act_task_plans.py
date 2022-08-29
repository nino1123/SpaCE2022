# coding=utf-8
from app import *

if __name__ == '__main':
    with open('files/plans(2).json', 'r') as ft:
        plans = json.load(ft)
        print(['len(plans) : ', len(plans)])
    #
    cc = 0
    for plan in plans:
        if '_id' in plan:
            plan.pop('_id')
        db_Task.find_one_and_replace({'id': plan['id']}, plan)
        cc += 1
    print(cc)
