from typing import List, Dict, Iterable, Union

def convert_to_dict_according_to_id(list_data: List[Dict]) -> Dict[str, Dict]:
    ret = {}
    for instance in list_data:
        ret[instance['id']] = instance
    return ret

class DataManager:
    def __init__(self,
                 _entries: List[Dict],
                 _tasks: List[Dict],
                 _users: List[Dict],
                 _annos: List[Dict],
                 _prefix_of_batch_name: str = 'tasks1',
                 contain_polygraph: bool = False,
                ):
        self.entries: Dict[str, Dict] = convert_to_dict_according_to_id(_entries)
        self.tasks: Dict[str, Dict] = convert_to_dict_according_to_id(_tasks)
        self.users: Dict[str, Dict] = convert_to_dict_according_to_id(_users)
        self.annos: Dict[str, Dict] = convert_to_dict_according_to_id(_annos)
        self.prefix_of_batch_name: str = _prefix_of_batch_name
        self.contain_polygraph = contain_polygraph

    def get_tagged_entries(self) -> List[int]:
        tagged_entries = []
        for anno_id in self.annos:
            anno = self.annos[anno_id]
            # not of current batch
            task_id = anno['task']
            task = self.tasks[task_id]
            if not task['batchName'].startswith(self.prefix_of_batch_name):
                continue

            # polygraph
            entry_id = anno['entry']
            entry = self.entries[entry_id]
            if 'polygraph' in entry:
                continue

            if entry_id not in tagged_entries:
                tagged_entries.append(entry_id)
        return tagged_entries

    def get_entry(self, entry_id: str) -> Dict:
        return self.entries[entry_id]

    def get_user(self, user_id: str) -> Dict:
        return self.users[user_id]

    def get_id_of_user(self, user_name: str) -> str:
        for id_, user in self.users.items():
            if user['name'] == user_name:
                return id_
        return None

    def get_manager_of_user(self, user_id: str) -> str:
        user = self.users[user_id]
        if 'manager' not in user:
            return None
        return self.users[user['manager']]['name']

    @property
    def annotators(self) -> List[str]:
        return list(self.get_annotators())

    def get_annotators(self) -> Iterable[str]:
        for user_id in self.users:
            user = self.users[user_id]
            group = user.get('currTaskGroup')
            if group == 'zwdGroup':
                continue
            yield user_id

    def get_done_tasks(self) -> List[Dict]:
        ret = []
        for task_id in self.tasks:
            task = self.tasks[task_id]
            if not task['batchName'].startswith(self.prefix_of_batch_name):
                continue
            if not self.contain_polygraph and 'polygraph' in task:
                continue
            if len(task['to']) == 0:
                continue
            if len(task['submitters']) == 0:
                continue
            if len(task['submitters']) != len(task['to']):
                continue
            ret.append(task)
        return ret

    def get_done_tasks_of_single_user(self,
                                      user: Union[Dict, str],
                                     ) -> List[Dict]:
        if isinstance(user, str):
            user = self.users[user]

        ret = []
        done_tasks = user.get('doneTasks') or []
        for task_id in done_tasks:
            task = self.tasks[task_id]
            if not task['batchName'].startswith(self.prefix_of_batch_name):
                continue
            if not self.contain_polygraph and 'polygraph' in task:
                continue
            ret.append(task)
        return ret

    def get_annotations(self):
        ret = []
        for anno_id in self.annos:
            anno = self.annos[anno_id]
            task = self.tasks[anno['task']]
            if not task['batchName'].startswith(self.prefix_of_batch_name):
                continue
            if not self.contain_polygraph and 'polygraph' in task:
                continue
            ret.append(anno)
        return ret

    def get_annotations_of_user(self, user_id: str) -> List[Dict]:
        ret = []
        all_annos = self.users[user_id]['allAnnos']
        for anno_id in all_annos:
            anno = self.annos[anno_id]
            task = self.tasks[anno['task']]
            if not task['batchName'].startswith(self.prefix_of_batch_name):
                continue
            if not self.contain_polygraph and 'polygraph' in task:
                continue
            ret.append(anno)
        return ret

    def get_annotation_of_user(self, user_id: str, task_id: str):
        user = self.users[user_id]
        all_annos = user['allAnnos']
        for anno_id in all_annos:
            anno = self.annos[anno_id]
            if anno['task'] == task_id:
                return anno
        return None
