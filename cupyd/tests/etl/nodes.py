from typing import Any, Iterator, List, Optional

from cupyd import Transformer, Loader, Extractor, Filter


class ListExtractor(Extractor):

    def __init__(self, items: List[Any]):
        super().__init__()
        self.configuration.run_in_main_process = True
        self.items = items

    def extract(self) -> Iterator[Any]:
        for item in self.items:
            yield item


class AdderToStr(Transformer):

    def transform(self, item: int) -> str:
        item += 5
        return str(item)


class CustomFilter(Filter):

    def filter(self, item: str) -> Optional[str]:
        if int(item) % 5 == 0:
            return None
        else:
            return item


class ListLoader(Loader):
    def __init__(self):
        super().__init__()
        self.configuration.run_in_main_process = True
        self.items = []

    def start(self):
        self.items = []

    def load(self, item: Any):
        self.items.append(item)
