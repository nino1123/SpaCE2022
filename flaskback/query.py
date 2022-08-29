import os 
import sys 
import json 
import time 
import pymongo


def insert_text_corpus(
    db, 
    collection_name,
    data_path,
):
    collection = db[collection_name]
    collection.delete_many({})
    with open(data_path, 'r', encoding='utf-8') as fin:
        js_list = json.load(fin)
        collection.insert_many(js_list)


def get_collection(db_port, database_name, collection_name, data_path=None):
    client = pymongo.MongoClient("mongodb://localhost:%d/" %db_port)
    db = client[database_name]
    if (collection_name not in db.list_collection_names()) and (data_path is not None):
        insert_text_corpus(db, collection_name, data_path)
    collection = db[collection_name]

    return collection


def query_text_corpus(collection, params):
    start_time = time.time()
    # results = db.find(params)
    results = collection.aggregate([
    {
        "$unwind": {
            "path": "$content.material.tokenList"
        }, 
    },
    {
        "$match": {
            "content.material.tokenList.word": params['word'],
            "content.material.tokenList.to.word": params['to'],
        },
    }])
    elapsed = time.time() - start_time
    return results, elapsed


if __name__ == "__main__":
    db_port = 27017
    database_name = 'SpaCE'
    collection_name = 'entry'

    collection = get_collection(
        db_port=db_port,
        database_name=database_name,
        collection_name=collection_name,
        # data_path='/data/zfw/SpaCE/data/database/Entry.json'
        data_path=''
    )
    
    params = {
        'word': '内',
        'to': '里',
    }
    results, elapsed = query_text_corpus(collection, params)
    print(list(results))
    print('Time Elapsed: %f' %elapsed)