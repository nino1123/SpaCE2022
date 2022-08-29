import json
from typing import Dict, List

# from data_manager import DataManager
from data_manager import convert_to_dict_according_to_id

class Examiner:
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

    def run(self) -> Dict[str, Dict]:
        ret = []
        for user_id in self.users:
            user = self.users[user_id]
            group = user.get('currTaskGroup')
            if group == 'zwdGroup':
                continue
            result = self.examine_single_user(user)
            ret.append([user['id'],
                        user['name'],
                        self.users[user['manager']]['name'] if 'manager' in user else None,
                        result]
                      )
        return ret

    def examine_single_user(self, user: Dict):
        polygraph_annos = self._get_polygraph_annos_of_single_user(user)
        result = self._check_annotation_of_polygraphs(polygraph_annos)
        return result

    def _get_polygraph_tasks_of_single_user(self, user: Dict) -> List[Dict]:
        ret = []
        done_tasks = user['doneTasks']
        for task_id in done_tasks:
            task = self.tasks[task_id]
            if task['batchName'] != self.batch_name:
                continue
            if 'polygraph' not in task:
                continue
            ret.append(task)
        return sorted(ret, key=lambda x: x['id'])

    def _get_polygraph_annos_of_single_user(self, user: Dict) -> List[Dict]:
        ret = []
        all_annos = user.get('allAnnos') or []
        for anno_id in all_annos:
            anno = self.annos[anno_id]
            task = self.tasks[anno['task']]
            if task['batchName'] != self.batch_name:
                continue
            if 'polygraph' not in anno:
                continue
            ret.append(anno)
        return sorted(ret, key=lambda x: x['task'])

    def _check_annotation_of_polygraphs(self, annos: List[Dict]) -> Dict:
        all_entries = []
        correct_entries = []
        count = 0
        correct = 0
        for anno in annos:
            entry_id = anno['entry']
            result = self._check_single_annotation(anno)
            if result == -1:
                continue
            if result == 1:
                correct_entries.append(entry_id)
                correct += 1
            count += 1
            all_entries.append(entry_id)
        return {
            'total_num': count,
            'correct_num': correct,
            'all_entries': all_entries,
            'correct_entries': correct_entries,
        }

    def _check_single_annotation(self, anno: Dict) -> int:
        entry = self.entries[anno['entry']]
        results = entry['results']
        if len(results) == 0:
            return -1
        count = 0
        for std_anno in results['_temp_annots']:
            for user_anno in anno['content']['annotations']:
                count += self._compare_annotation(std_anno, user_anno)
        if count != len(results['_temp_annots']):
            return 0
        return 1

    def _compare_annotation(self, std_anno: Dict, user_anno: Dict) -> int:
        # compare label
        std_label = std_anno['label']
        if std_label == 'artificicalErrorString':
            std_label = 'otherErrorString'
        user_label = user_anno['label']
        if user_label != std_label:
            return 0
        # compare range
        difference_of_range = set(std_anno['on']).difference(set(user_anno['on']))
        if len(difference_of_range) == len(std_anno['on']):
            return 0
        # compare modified text if label is 'otherErrorString'
        if std_label == 'otherErrorString':
            if 'withText' not in std_anno:
                return 1
            if 'withText' not in user_anno:
                return 0
            if std_anno['withText'].find(user_anno['withText']) == -1 \
               or user_anno['withText'].find(std_anno['withText']) == -1:
                return 0
        return 1


def examine(entries: List[Dict],
            tasks: List[Dict],
            users: List[Dict],
            annos: List[Dict],
            batch_name: str = 'test',
           ) -> Dict[str, bool]:
    examiner = Examiner(entries, tasks, users, annos, batch_name)
    results = examiner.run()
    return results

if __name__ == '__main__':
    inputs = json.load(open('db.json', 'r'))
    users = inputs['users']
    tasks = inputs['tasks']
    annos = inputs['annos']
    entries = inputs['entries']
    ret = examine(entries, tasks, users, annos, 'task0-02')
    print(ret)
