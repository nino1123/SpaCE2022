import json
from typing import List, Dict, Tuple

labels_to_int = {
    'fine': 0,
    'someFine': 0,
    'someBad': 1,
    'bad': 1,
    'other': 2,
}

def convert_to_dict_according_to_id(list_data: List[Dict]) -> Dict[str, Dict]:
    ret = {}
    for instance in list_data:
        ret[instance['id']] = instance
    return ret

class Calculator:
    def __init__(self,
                 _entries: List[Dict],
                 _tasks: List[Dict],
                 _users: List[Dict],
                 _annos: List[Dict],
                 _batch_name: str,
                ):
        self.entries: Dict[str, Dict] = convert_to_dict_according_to_id(_entries)
        self.tasks: Dict[str, Dict] = convert_to_dict_according_to_id(_tasks)
        self.users: Dict[str, Dict] = convert_to_dict_according_to_id(_users)
        self.annos: Dict[str, Dict] = convert_to_dict_according_to_id(_annos)
        self.batch_name = _batch_name

    def run(self):
        ret = []
        for user_id in self.users:
            user = self.users[user_id]
            group = user['currTaskGroup']
            if group == 'zwdGroup':
                continue
            result, consistancy = self.calculate_single_consistancy(user)
            ret.append([user['id'],
                        user['name'],
                        self.users[user['manager']]['name'] if 'manager' in user else None,
                        consistancy,
                        result]
                      )
        return ret

    def calculate_single_consistancy(self, user: Dict):
        tasks = self._get_tasks_of_single_user(user)
        if len(tasks) == 0:
            return [], 0
        result, consistancy = self._calculate_consistancy_of_tasks(tasks)
        return result, consistancy

    def _get_tasks_of_single_user(self, user: Dict) -> List[Dict]:
        ret = []
        done_tasks = user['doneTasks']
        for task_id in done_tasks:
            task = self.tasks[task_id]
            if task['batchName'] != self.batch_name:
                continue
            if 'polygraph' in task:
                continue
            ret.append(task)
        return ret

    def _calculate_consistancy_of_tasks(self, tasks: Dict) -> Dict[int, str]:
        ret = []
        count = 0
        for task in tasks:
            result = self._check_annotation_of_single_task(task)
            ret.append(result)
            if result != 'distinct':
                count += 1
        return ret, count / len(ret)

    def _check_annotation_of_single_task(self, task: Dict):
        users = task['to']
        results = []
        for user_id in users:
            anno = self._get_annotation_of_user(user_id, task['id'])
            label = anno['content']['annotations'][0]['label']
            results.append(labels_to_int[label])
        if len(set(results)) != 1:
            return 'distinct'
        elif results[0] == 0:
            return 'fine'
        elif results[0] == 1:
            return 'bad'
        elif results[0] == 2:
            return 'drop'

    def _get_annotation_of_user(self, user_id: str, task_id: str):
        user = self.users[user_id]
        all_annos = user['allAnnos']
        for anno_id in all_annos:
            anno = self.annos[anno_id]
            if anno['task'] == task_id:
                return anno
        raise Exception


def calculate_consistance(entries: List[Dict],
                          tasks: List[Dict],
                          users: List[Dict],
                          annos: List[Dict],
                          batch_name: str = 'test',
                         ):
    calculator = Calculator(entries, tasks, users, annos, batch_name)
    results = calculator.run()
    return sorted(results, key=lambda x: x[3], reverse=True)

if __name__ == '__main__':
    inputs = json.load(open('db.json', 'r'))
    users = inputs['users']
    tasks = inputs['tasks']
    annos = inputs['annos']
    entries = inputs['entries']
    ret = calculate_consistance(entries, tasks, users, annos, 'task1-01')
    for rr in ret:
        print(rr)
