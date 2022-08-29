# coding=utf-8
# X=2 每条语料⾄少分配给⼏名⽤户
# STACK_SIZE=100 每个⽤户的默认任务量【可以去掉这个设置】
# CURRENT_TASK_TOPIC="第1期" 当前任务的主题，⽤于区分不同阶段的标注任务
# 第0期：检查和修正原句
# 第1期：中文空间语义正误判断 0
# 第2期：中文空间语义异常归因与异常文本识别 A搭配不当 B语义冲突 C 不符合常识或背景信息


class Parameter:
    X = 2
    STACK_SIZE = 30
    CURRENT_TASK_TOPIC = 1
    TOPIC = "第1期"


DB_SECRET = "♑️ec332b5c🆒0463⚛️4460☮️ade8❇️7b1018d85a2e🤖"
# API_BASE_DEV = "http://192.168.124.5:8888"
API_BASE_DEV = "10.1.115.146"
API_BASE_PROD = "http://101.43.244.203"

# DEVELOPING = False
DEVELOPING = True

API_BASE = API_BASE_DEV if DEVELOPING else API_BASE_PROD
