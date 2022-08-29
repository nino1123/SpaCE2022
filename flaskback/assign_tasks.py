from typing import List, Dict, Tuple
import math
import random
from queue import PriorityQueue
from dataclasses import dataclass, field

import json


@dataclass
class Task:
    id_: str
    topic: str
    entry: str
    users_per_task: int
    to: List[str] = field(default_factory=list)
    submitters: List[str] = field(default_factory=list)

    @property
    def rest(self):
        return self.users_per_task - len(self.to)

    def __lt__(self, other):
        if self.rest == 0:
            return False
        elif other.rest == 0:
            return True
        elif self.rest < other.rest:
            return True
        elif self.rest > other.rest:
            return False
        else:
            return self.id_ < other.id_

    def to_dict(self):
        return {
            'id': self.id_,
            'topic': self.topic,
            'entry': self.entry,
            'to': self.to,
            'submitters': self.submitters,
        }


@dataclass
class TaskAssigner:
    entries: List[Dict] = field(default_factory=list)
    users: List[Dict] = field(default_factory=list)
    tasks: List[Dict] = field(default_factory=list)
    incomplete_tasks: List[Dict] = field(default_factory=list)
    incomplete_tasks_num: int = 0
    topic: str = None
    users_per_task: int = 2
    tasks_per_user: int = 10
    polygraphs_per_user: Dict[str, int] = field(default_factory=dict)
    total_polygraphs_per_user: int = 0
    polygraphs: List[Dict] = field(default_factory=list)

    @classmethod
    def build(cls,
              entries: List[Dict],
              users: List[Dict],
              tasks: List[Dict] = [],
              topic: str = None,
              exclusion: List[str] = [],
              users_per_task: int = 2,
              tasks_per_user: int = 10,
              polygraphs_per_user: Dict[str, int] = {},
             ):
        tasks = cls._get_tasks_by_topic(tasks, topic)
        incomplete_tasks, incomplete_tasks_num \
                = cls._get_incomplete_tasks(tasks, users_per_task)
        unassigned_entries \
                = cls._get_unassigned_entries(entries, tasks, exclusion)
        polygraphs, total_polygraphs_per_user \
                = cls._get_polygraphs(entries, polygraphs_per_user)
        print(total_polygraphs_per_user)
        return cls(unassigned_entries,
                   users, tasks,
                   incomplete_tasks,
                   incomplete_tasks_num,
                   topic,
                   users_per_task,
                   tasks_per_user,
                   polygraphs_per_user,
                   total_polygraphs_per_user,
                   polygraphs)

    @classmethod
    def _get_tasks_by_topic(cls,
                            tasks: List[Dict],
                            topic: str,
                           ) -> List[Dict]:
        tasks_with_certain_topic = []
        for task in tasks:
            if task['topic'] == topic:
                tasks_with_certain_topic.append(task)
        return tasks_with_certain_topic

    @classmethod
    def _get_incomplete_tasks(cls,
                              tasks: List[Dict],
                              users_per_task: int,
                             ) -> Tuple[List[Dict], int]:
        incomplete_tasks = []
        incomplete_tasks_num = 0

        def _remove_incomplete_user(task: Dict):
            if len(task['submitters']) != len(task['to']):
                removals = []
                for user in task['to']:
                    if user not in task['submitters']:
                        removals.append(user)
                for user in removals:
                    task['to'].remove(user)

        for task in tasks:
            _remove_incomplete_user(task)
            if len(task['submitters']) < users_per_task:
                incomplete_tasks.append(task)
                incomplete_tasks_num += users_per_task - len(task['submitters'])
        return incomplete_tasks, incomplete_tasks_num

    @classmethod
    def _get_unassigned_entries(cls,
                                entries: List[Dict],
                                tasks: List[Dict],
                                exclusion: List[str],
                               ):
        unassigned_entries = []
        assigned_entries = set([task['entry'] for task in tasks])
        for entry in entries:
            # this entry is a polygraph
            if 'polygraph' in entry:
                continue
            # this entry is exclusive
            if entry['info']['rpId'] in exclusion:
                continue
            # this entry is assigned
            if entry['id'] in assigned_entries:
                continue
            unassigned_entries.append(entry)
        return unassigned_entries

    @classmethod
    def _get_polygraphs(cls,
                        entries: List[Dict],
                        polygraphs_per_user: Dict[str, int],
                       ) -> Tuple[List[Dict], int]:
        polygraphs = {}
        total_polygraphs_per_user = 0
        for polygraph_type in polygraphs_per_user:
            polygraphs[polygraph_type] = []
            total_polygraphs_per_user \
                    += polygraphs_per_user[polygraph_type]

        for entry in entries:
            if 'polygraph' in entry:
                polygraph_type = entry['polygraph']
                assert entry['polygraph'] in polygraphs
                polygraphs[polygraph_type].append(entry)

        for polygraph_type in polygraphs:
            assert len(polygraphs[polygraph_type]) != 0

        return polygraphs, total_polygraphs_per_user

    def assign(self) -> List[Dict]:
        candidate_entries = self._get_candidate_entries()
        candidate_tasks, task_index = self._create_candidate_tasks(candidate_entries)
        tasks = self._assign_tasks(candidate_tasks)
        polygraph_tasks = self._assign_polygraphs(task_index)
        total_tasks = self._merge_tasks_and_polygraphs(tasks, polygraph_tasks)
        return total_tasks

    def _get_candidate_entries(self) -> List[Dict]:
        self.real_tasks_per_user = self.tasks_per_user - self.total_polygraphs_per_user
        total_tasks_num = self.real_tasks_per_user * len(self.users)
        needed_tasks_num = max(0, total_tasks_num - self.incomplete_tasks_num)
        needed_entries_num = \
                math.ceil(needed_tasks_num / self.users_per_task)
        if needed_entries_num > len(self.entries):
            self._update_tasks_per_user()
            candidate_entries = self.entries
        else:
            random.shuffle(self.entries)
            candidate_entries = self.entries[0:needed_entries_num]
        return candidate_entries

    def _update_tasks_per_user(self):
        print('WARNING: number of unassigned entries are smaller than needed entries')
        provided_tasks_num = len(self.entries) * self.users_per_task
        total_tasks_num = provided_tasks_num + self.incomplete_tasks_num
        self.real_tasks_per_user = math.ceil(total_tasks_num / len(self.users))
        self.tasks_per_user = self.real_tasks_per_user + self.total_polygraphs_per_user

    def _create_candidate_tasks(self,
                                candidate_entries: List[Dict],
                               ) -> PriorityQueue:
        task_ids = [task['id'] for task in self.tasks]
        task_index = len(task_ids)

        def next_index(task_index: int):
            task_index += 1
            while str(task_index) in task_ids:
                task_index += 1
            return task_index

        queue = PriorityQueue()
        for task in self.incomplete_tasks:
            queue.put(Task(task['id'], task['topic'], task['entry'],
                           self.users_per_task, task['to'], task['submitters']))
        for entry in candidate_entries:
            task_index = next_index(task_index)
            queue.put(Task(str(task_index), self.topic, entry['id'],
                           self.users_per_task, [], []))
        return queue, task_index

    def _assign_tasks(self,
                      candidate_tasks: PriorityQueue,
                     ) -> List[Dict]:
        for i in range(self.real_tasks_per_user):
            if not self._assign_tasks_to_each_user(candidate_tasks):
                break
        return self._queue_to_list(candidate_tasks)

    def _assign_tasks_to_each_user(self,
                                   candidate_tasks: PriorityQueue
                                  ) -> bool:
        random.shuffle(self.users)
        for user in self.users:
            user_id = user['id']

            # if all tasks are assigned to enough users
            task = candidate_tasks.get()
            if len(task.to) == self.users_per_task:
                return False
            else:
                candidate_tasks.put(task)

            self._assign_task_to_user(user_id, candidate_tasks)
        return True

    def _assign_task_to_user(self,
                             user: str,
                             tasks: PriorityQueue,
                            ):
        temp_list = []
        while not tasks.empty():
            task = tasks.get()
            temp_list.append(task)
            if len(task.to) == self.users_per_task:
                break
            if user not in task.to:
                task.to.append(user)
                break
        for task in temp_list:
            tasks.put(task)

    def _queue_to_list(self,
                       candidate_tasks: PriorityQueue,
                      ) -> List[Dict]:
        tasks = []
        while not candidate_tasks.empty():
            task = candidate_tasks.get()
            tasks.append(task.to_dict())
        return tasks

    def _assign_polygraphs(self,
                           task_index: int,
                          ) -> Dict[str, List[Dict]]:
        polygraph_tasks = self._create_polygraph_tasks(task_index)
        self._assign_polygraph_tasks_to_users(polygraph_tasks)
        return polygraph_tasks

    def _create_polygraph_tasks(self,
                                task_index: int
                               ) -> Dict[str, List[Dict]]:
        task_ids = [task['id'] for task in self.tasks]

        def next_index(task_index: int):
            task_index += 1
            while str(task_index) in task_ids:
                task_index += 1
            return task_index

        polygraph_tasks = {}
        for polygraph_type in self.polygraphs:
            polygraph_tasks[polygraph_type] = []
            polygraphs = self.polygraphs[polygraph_type]
            for entry in polygraphs:
                task_index = next_index(task_index)
                polygraph_tasks[polygraph_type].append({
                    'id': str(task_index),
                    'topic': self.topic,
                    'entry': entry['id'],
                    'to': [],
                })
        return polygraph_tasks

    def _assign_polygraph_tasks_to_users(self,
                                         polygraph_tasks: Dict[str, List[Dict]]
                                        ) -> Dict[str, List[Dict]]:
        for user in self.users:
            user_id = user['id']
            for polygraph_type in polygraph_tasks:
                polygraphs = polygraph_tasks[polygraph_type]
                polygraphs_num = self.polygraphs_per_user[polygraph_type]
                assert polygraphs_num <= len(polygraphs)
                tasks = random.sample(polygraphs, polygraphs_num)
                for task in tasks:
                    assert user_id not in task['to']
                    task['to'].append(user_id)

    def _merge_tasks_and_polygraphs(self,
                                    tasks: List[Dict],
                                    polygraphs: Dict[str, List[Dict]],
                                    shuffle: bool = True,
                                   ) -> List[Dict]:
        for polygraph_type in polygraphs:
            polygraph_tasks = polygraphs[polygraph_type]
            for task in polygraph_tasks:
                tasks.append(task)
        if shuffle:
            random.shuffle(tasks)
        return tasks


def assign_tasks(entries: List[Dict],
                 users: List[Dict],
                 tasks: List[Dict] = [],
                 topic: str = None,
                 exclusion: List[str] = [],
                 users_per_task: int = 2,
                 tasks_per_user: int = 30,
                 polygraphs_per_user: Dict[str, int] = {},
                ):
    task_assigner = TaskAssigner.build(
        entries, users, tasks,
        topic, exclusion,
        users_per_task, tasks_per_user,
        polygraphs_per_user
    )
    return task_assigner.assign()


if __name__ == '__main__':
    params = json.load(open('file.json', 'r',encoding="utf-8"))
    entries = params['entries']
    users = params['users']
    tasks = params['tasks']
    topic = params['topic']
    exclusion = params['exclusion']
    users_per_task = params['users_per_task']
    tasks_per_user = params['tasks_per_user']
    polygraphs_per_user = params['polygraphs_per_user']
    tasks = assign_tasks(
        entries,
        users,
        tasks,
        topic,
        exclusion,
        users_per_task,
        tasks_per_user,
        polygraphs_per_user,
    )
    # print(tasks)
    count = 0
    count_2 = 0
    for task in tasks:
        if len(task['to']) == 2:
            count += 1
        elif len(task['to']) == 1:
            count_2 += 1
    print(count_2)
    # print(tasks)
