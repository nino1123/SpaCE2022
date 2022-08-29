# coding=utf-8
from app import *
import os

if __name__ == '__main__':
    db = make_backup()
    print(db["_meta"])

