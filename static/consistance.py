# only for task1

import json
import argparse
from typing import List, Dict, Tuple

from data_manager import DataManager

label_to_int = {
    'fine': 1,
    'someFine': 2,
    'someBad': 3,
    'bad': 4,
    'other': -1,
}

int_to_label = {
    1: 'fine',
    2: 'someFine',
    3: 'someBad',
    4: 'bad',
    -1: 'drop',
    5: 'undetermined',
}

binary_label = {
    1: 1,
    2: 1,
    3: 4,
    4: 4,
    -1: -1,
}

class Calculator:
    all_levels = {
        'strict': 0,
        'binary': 1,
        'loose': 2,
    }

    def __init__(self,
                 data_manager: DataManager,
                 level: str = 'strict',
                ):
        self.data_manager: DataManager = data_manager
        self.level = self.all_levels[level]

    def get_info_of_entries(self):
        ret = []
        total_consistant = 0
        total_num = 0
        tasks_from_different_corpus = {}
        for task in self.data_manager.get_done_tasks():
            entry = self.data_manager.get_entry(task['entry'])
            corpus_type = entry['originId'][0:3]
            if corpus_type not in tasks_from_different_corpus:
                tasks_from_different_corpus[corpus_type] = []
            tasks_from_different_corpus[corpus_type].append(task)

        results_of_different_corpus = {}
        for corpus_type in tasks_from_different_corpus:
            tasks = tasks_from_different_corpus[corpus_type]
            result, num_of_consistant_labels = self._calculate_consistancy_of_tasks(tasks)
            total_consistant += num_of_consistant_labels
            total_num += len(result)
            results_of_different_corpus[corpus_type] = {
                'total_num': len(result),
                'consistant_num': num_of_consistant_labels,
                'consistancy_rate': num_of_consistant_labels / len(result) \
                if len(result) != 0 else 0
            }
        return results_of_different_corpus, total_consistant / total_num

    def get_info_of_users(self):
        ret = []
        total_consistant = 0
        total_num = 0
        for user_id in self.data_manager.annotators:
            user = self.data_manager.get_user(user_id)
            result, num_of_consistant_labels = self._calculate_consistancy_of_single_user(user)
            manager = self.data_manager.get_manager_of_user(user_id)
            total_consistant += num_of_consistant_labels
            total_num += len(result)
            ret.append([user['id'],
                        user['name'],
                        manager,
                        num_of_consistant_labels,
                        num_of_consistant_labels / len(result) \
                        if len(result) != 0 else 0,     # consistancy
                        result]
                      )
        return ret, total_consistant / total_num

    def _calculate_consistancy_of_single_user(self, user: Dict):
        tasks = self.data_manager.get_done_tasks_of_single_user(user)
        if len(tasks) == 0:
            return [], 0
        result, count = self._calculate_consistancy_of_tasks(tasks)
        return result, count

    def _calculate_consistancy_of_tasks(self,
                                        tasks: Dict,
                                       ) -> Tuple[int, int]:
        ret = []
        count = 0
        for task in tasks:
            result = self._check_annotation_of_single_task(task)
            ret.append(result)
            if result != 'distinct':
                count += 1
        return ret, count

    def _check_annotation_of_single_task(self, task: Dict):
        users = task['to']
        labels = []
        for user_id in users:
            anno = self.data_manager.get_annotation_of_user(user_id, task['id'])
            if anno is None:
                continue
            label = anno['content']['annotations'][0]['label']
            labels.append(label_to_int[label])
        return self._determine_label(labels)

    def _determine_label(self, labels: List[int]) -> str:
        func = {
            0: self._determine_label_strict,
            1: self._determine_label_binary,
            2: self._determine_label_loose,
        }
        return func[self.level](labels)

    def _determine_label_strict(self, labels: List[int]) -> str:
        if len(set(labels)) != 1:
            return 'distinct'
        return int_to_label[labels[0]]

    def _determine_label_binary(self, labels: List[int]) -> str:
        binary_labels = [binary_label[label] for label in labels]
        if len(set(binary_labels)) != 1:
            return 'distinct'
        return int_to_label[binary_labels[0]]

    def _determine_label_loose(self, labels: List[int]) -> str:
        if len(set(labels)) == 1:
            return int_to_label[labels[0]]

        for label in labels:
            if label == -1:
                return 'distinct'

        if max(labels) - min(labels) > 1:
            return 'distinct'

        if min(labels) == 2:
            return int_to_label[5]
        else:
            return int_to_label[binary_label[min(labels)]]


def calculate_consistance_of_users(entries: List[Dict],
                                   tasks: List[Dict],
                                   users: List[Dict],
                                   annos: List[Dict],
                                   prefix_of_batch_name: str = 'test',
                                   level: str = 'strict',
                                  ):
    data_manager = DataManager(entries, tasks, users, annos, prefix_of_batch_name)
    calculator = Calculator(data_manager, level=level)
    results, total_consistancy = calculator.get_info_of_users()
    return sorted(results, key=lambda x: x[3], reverse=True), total_consistancy

def calculate_consistance_of_entries(entries: List[Dict],
                                     tasks: List[Dict],
                                     users: List[Dict],
                                     annos: List[Dict],
                                     prefix_of_batch_name: str = 'test',
                                     level: str = 'strict',
                                    ):
    data_manager = DataManager(entries, tasks, users, annos, prefix_of_batch_name)
    calculator = Calculator(data_manager, level=level)
    results, total_consistancy = calculator.get_info_of_entries()
    return results, total_consistancy

def main(args):
    inputs = json.load(open('db.json', 'r'))
    users = inputs['users']
    tasks = inputs['tasks']
    annos = inputs['annos']
    entries = inputs['entries']
    if args.goal == 'user':
        func = calculate_consistance_of_users
    elif args.goal == 'entry':
        func = calculate_consistance_of_entries
    else:
        raise KeyError
    print(func(entries, tasks, users, annos, prefix_of_batch_name=args.prefix, level=args.level))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--goal', type=str, default='user', help='user or entry')
    parser.add_argument('--prefix', type=str, default='task1', help='prefix of batch name')
    parser.add_argument('--level', type=str, default='strict', help='level of consistancy')
    args = parser.parse_args()
    main(args)
