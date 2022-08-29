import json
from typing import List, Dict

from data_manager import DataManager


class Counter:
    def __init__(self,
                 data_manager: DataManager,
                ):
        self.data_manager = data_manager

    def run(self) -> Dict[str, int]:
        tagged_entries = self.data_manager.get_tagged_entries()
        return self._count_tagged_entries(tagged_entries)

    def _count_tagged_entries(self, tagged_entries: List[int]) -> Dict[str, int]:
        ret = {}
        for entry_id in tagged_entries:
            entry = self.data_manager.get_entry(entry_id)
            corpus_type = entry['originId'][0:3]
            if corpus_type not in ret:
                ret[corpus_type] = 0
            ret[corpus_type] += 1

        total = 0
        for key in ret:
            total += ret[key]
        ret['total'] = total
        return ret


def count_tagged_num(entries: List[Dict],
                     tasks: List[Dict],
                     users: List[Dict],
                     annos: List[Dict],
                     prefix_of_batch_name: str = 'task1',
                    ) -> Dict[str, int]:
    data_manager = DataManager(entries, tasks, users, annos, prefix_of_batch_name)
    counter = Counter(data_manager)
    return counter.run()

if __name__ == '__main__':
    inputs = json.load(open('db.json', 'r'))
    users = inputs['users']
    tasks = inputs['tasks']
    annos = inputs['annos']
    entries = inputs['entries']
    ret = count_tagged_num(
        entries,
        tasks,
        users,
        annos,
        'task1-03',
    )
    print(ret)
