from typing import List, Dict, Tuple


class Disambiguator:
    def __call__(self, sent, tasks) -> Tuple[List[str], List[Dict[str, str]]]:
        raise NotImplementedError
