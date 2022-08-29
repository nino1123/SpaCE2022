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
    collection_names = ["Entry"]
    for name in collection_names:
        collection_path = os.path.join(dir_path, f"{name}.jsonlines")
        collection = db.get_collection(name)
        found_items = collection.find({}, {"_id": 0})
        with open(collection_path, 'w') as ff:
            for item in found_items:
                ff.write(json.dumps(item, ensure_ascii=False))
                ff.write("\n")
            pass
        pass
    pass
