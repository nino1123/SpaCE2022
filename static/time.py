import json
from dateutil.parser import parse as parse_time
from typing import List, Dict

from data_manager import DataManager

class StatusCollector:
    def __init__(self,
                 data_manager: DataManager,
                ):
        self.data_manager = data_manager

    def get_work_status_of_annotators(self) -> List[Dict]:
        ret = {}
        for user_id in self.data_manager.annotators:
            user = self.data_manager.get_user(user_id)
            user_name = user['name']
            ret[user_name] = self._get_work_status_of_single_user(user_id)
        return ret.items()

    def _get_work_status_of_single_user(self, user_id: str) -> Dict:
        annos = self.data_manager.get_annotations_of_user(user_id)
        all_time = 0
        for anno in annos:
            total_time = 0
            start_time = 0
            end_time = 0

            time_log = anno['content']['_ctrl']['timeLog']
            for time_info in time_log:
                op_type = time_info[0]
                time_str = time_info[1]
                if op_type == 'check':
                    if end_time != 0:
                        total_time += (end_time - start_time).microseconds
                    start_time = 0
                    end_time = 0
                elif op_type == 'in':
                    if end_time != 0:
                        total_time += (end_time - start_time).microseconds
                    start_time = parse_time(time_str)
                    end_time = 0
                elif op_type == 'out':
                    end_time = parse_time(time_str)
            if end_time != 0:
                total_time += (end_time - start_time).microseconds

            all_time += total_time
        return {
            'all_time': all_time,
            'average_time': all_time / len(annos) if len(annos) != 0 else 0,
            'num_of_annotations': len(annos)
        }

    def get_work_status_of_checkers(self):
        count = {}
        for anno in self.data_manager.get_annotations():
            time_log = anno['content']['_ctrl']['timeLog']
            # checker_id = []
            for time_info in time_log:
                op_type = time_info[0]
                flag = False
                if op_type == 'check':
                    flag = True
                    check_info = time_info[2]
                    if 'name' not in check_info \
                       and 'id' not in check_info:
                        raise KeyError
                    if 'id' not in check_info:
                        name = check_info['name']
                        id_ = self.data_manager.get_id_of_user(name)
                    else:
                        id_ = check_info['id']
                    if id_ is None:
                        continue
                    if id_ not in count:
                        count[id_] = 0
                    count[id_] += 1
                    break
                    # checker_id.append(id_)

            if flag is False:
                if 'review' in anno['content']:
                    if 'reviewer' in anno['content']['review']:
                        reviewer = anno['content']['review']['reviewer']
                        id_ = self.data_manager.get_id_of_user(reviewer)
                        if id_ is None:
                            continue
                        if id_ not in count:
                            count[id_] = 0
                        count[id_] += 1

        ret = []
        for id_ in count:
            ret.append((id_, self.data_manager.get_user(id_)['name'], count[id_]))
        return ret

def get_work_status_of_annotators(entries: List[Dict],
                                  tasks: List[Dict],
                                  users: List[Dict],
                                  annos: List[Dict],
                                  prefix_of_batch_name: str = 'task1',
                                  contain_polygraph: bool = True,
                                 ):
    data_manager = DataManager(
        entries, tasks, users, annos,
        prefix_of_batch_name, contain_polygraph=contain_polygraph
    )
    status_collector = StatusCollector(data_manager)
    results = status_collector.get_work_status_of_annotators()
    return sorted(results, key=lambda x: x[1]['all_time'], reverse=True)

def get_work_status_of_checkers(entries: List[Dict],
                                tasks: List[Dict],
                                users: List[Dict],
                                annos: List[Dict],
                                prefix_of_batch_name: str = 'task1',
                                contain_polygraph: bool = True,
                               ):
    data_manager = DataManager(
        entries, tasks, users, annos,
        prefix_of_batch_name, contain_polygraph=contain_polygraph
    )
    status_collector = StatusCollector(data_manager)
    results = status_collector.get_work_status_of_checkers()
    return sorted(results, key=lambda x: x[2], reverse=True)

if __name__ == '__main__':
    inputs = json.load(open('db.json', 'r'))
    users = inputs['users']
    tasks = inputs['tasks']
    annos = inputs['annos']
    entries = inputs['entries']
    '''
    print(get_work_status_of_annotators(
        entries, tasks, users, annos, 'task1-03'
    ))
    '''
    print(get_work_status_of_checkers(
        entries, tasks, users, annos, 'task1-02'
    ))
