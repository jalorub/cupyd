import logging
from typing import Iterator, Any, Optional

from cupyd.core.etl import ETL
from cupyd.core.nodes import Extractor, Transformer, Filter, Loader

logger = logging.getLogger("my_logger")


class IntExtractor(Extractor):

    def __init__(self, n: int):
        super().__init__()
        self.configuration.run_in_main_process = True
        self.n = n

    def start(self):
        logger.info("Extractor started!")

    def extract(self) -> Iterator[int]:
        for value in range(self.n):
            yield value


class Adder(Transformer):

    def start(self):
        pass

    def transform(self, value: int) -> int:
        return value + 1

    def finalize(self):
        logger.info("Adder finalized!")


class Multiplier(Transformer):
    """Multiply a given value by 1."""

    def start(self):
        logger.info("Multiplier started!")

    def transform(self, value: int) -> int:
        return value * 1


class ListLoader(Loader):

    def __init__(self):
        super().__init__()
        self.configuration.run_in_main_process = True
        self.items = []

    def start(self, msg: Any = None):
        self.items = []

    def load(self, item: Any):
        self.items.append(item)


class EvenValuesFilter(Filter):

    def filter(self, item: int) -> Optional[int]:
        if item % 2 == 0:
            return None
        else:
            return item


def run_etl():
    total_items = 50_000_000

    # EXTRACTOR
    ext = IntExtractor(n=total_items)
    ext.configuration.bucket_size = 10_000
    ext.configuration.run_in_main_process = False

    tf_1 = Adder()

    tf_2 = Adder()
    tf_2.configuration.run_in_main_process = True

    tf_3 = Multiplier()

    # FILTER NODE
    flt_1 = EvenValuesFilter()
    flt_1.configuration.run_in_main_process = True

    # LOADERS
    ldr_a = ListLoader()
    ldr_b = ListLoader()

    ext >> tf_1 >> tf_2 >> tf_3 >> ldr_a
    tf_1 >> flt_1 >> ldr_b

    etl = ETL(extractor=ext)
    etl.run(
        workers=4,
        raise_exception=True,
        show_progress=True,
        monitor_performance=True,
        verbose=False,
    )

    logger.info(f"Total items in ldr_a {len(ldr_a.items)} | total items ldr_b {len(ldr_b.items)}")


if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)
    logging.info("Starting my script...")
    run_etl()
    logging.info("Exiting my script")
