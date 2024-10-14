"""In this example we will compute the factorial of 20.000 integers, using multiprocessing,
while storing the results into 2 separate lists, one for even values and another for odd values."""

import math
import logging
from time import time
from typing import Any, Iterator, Optional

from cupyd import ETL, Extractor, Transformer, Loader, Filter

logger = logging.getLogger("readme_etl")


class IntegerExtractor(Extractor):

    def __init__(self, total_items: int):
        super().__init__()
        self.total_items = total_items

        # generated integers will be passed onto each worker in buckets of size 10
        self.configuration.bucket_size = 10

    def extract(self) -> Iterator[int]:
        for item in range(self.total_items):
            yield item


class Factorial(Transformer):

    def transform(self, item: int) -> int:
        return math.factorial(item)


class EvenOnly(Filter):

    def filter(self, item: int) -> Optional[int]:
        return item if item & 1 else None


class OddOnly(Filter):

    def filter(self, item: int) -> Optional[int]:
        return None if item & 1 else item


class ListLoader(Loader):

    def __init__(self):
        super().__init__()
        self.configuration.run_in_main_process = True
        self.items = []

    def start(self):
        self.items = []

    def load(self, item: Any):
        self.items.append(item)


def compute_with_single_process():
    start_time = time()

    even_results = []
    odd_results = []

    logger.info("Running README script without cupyd...")

    for value in range(20_000):
        result = math.factorial(value)
        if result & 1:
            even_results.append(factorial)
        else:
            odd_results.append(factorial)

    logger.info(f"Finished! Elapsed time: {time() - start_time} seconds")


if __name__ == "__main__":
    # 1. Instantiate the ETL Nodes
    ext = IntegerExtractor(total_items=20_000)
    factorial = Factorial()
    even_only = EvenOnly()
    odd_only = OddOnly()
    even_ldr = ListLoader()
    odd_ldr = ListLoader()

    # 2. Connect the Nodes to determine the data flow. Notice the two ETL branches after the
    # factorial is computed
    ext >> factorial >> [even_only >> even_ldr, odd_only >> odd_ldr]

    # 3. Run the ETL with 8 workers (multiprocessing Processes)
    etl = ETL(extractor=ext)
    etl.run(workers=8, show_progress=True, monitor_performance=True)

    # 4. You can access the results stored in both Loaders after the ETL is finished
    even_factorials = even_ldr.items
    odd_factorials = odd_ldr.items

    # Let's compare the performance with a single core, although without the cupyd overhead
    compute_with_single_process()
