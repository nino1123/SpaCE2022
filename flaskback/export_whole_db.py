# coding=utf-8
from app import *

if __name__ == '__main__':
    cwd = os.getcwd()
    backups_path = os.path.join(cwd, "backups")
    if not os.path.exists(backups_path):
        os.mkdir(backups_path)
    db_name = f"DB-{time_string()}"
    dir_path = os.path.join(backups_path, db_name)
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)
    meta = {}
    collection_names = db.list_collection_names()
    for name in collection_names:
        collection_path = os.path.join(dir_path, f"{name}.json")
        collection = db.get_collection(name)
        found_items = collection.find({}, {"_id": 0})
        items = [item for item in found_items]
        with open(collection_path, 'w') as ff:
            ff.write(json.dumps(items, ensure_ascii=False))
            pass
    pass
