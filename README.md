# cupyd

[![PyPI - Version](https://img.shields.io/pypi/v/cupyd)](https://pypi.org/project/cupyd/)
![Python Version from PEP 621 TOML](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fjalorub%2Fcupyd%2Frefs%2Fheads%2Fmain%2Fpyproject.toml&style=flat-square)
[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/jalorub/cupyd/ci.yaml?style=flat-square)](https://github.com/jalorub/cupyd/actions/workflows/ci.yaml?query=branch%3Amain++)
[![Coverage Status](https://coveralls.io/repos/github/jalorub/cupyd/badge.svg)](https://coveralls.io/github/jalorub/cupyd)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/cupyd?style=flat-square)](https://pypistats.org/packages/cupyd)

                                                      __     
                                                     /\ \    
      ___       __  __      _____       __  __       \_\ \   
     /'___\    /\ \/\ \    /\ '__`\    /\ \/\ \      /'_` \  
    /\ \__/    \ \ \_\ \   \ \ \L\ \   \ \ \_\ \    /\ \L\ \ 
    \ \____\    \ \____/    \ \ ,__/    \/`____ \   \ \___,_\
     \/____/     \/___/      \ \ \/      `/___/> \   \/__,_ /
                              \ \_\         /\___/           
                               \/_/         \/__/

Python framework to create your own ETLs.

## Features

- Simple but powerful syntax.
- Modular approach that encourages re-using components across different ETLs.
- Parallelism out-of-the-box without the need of writing multiprocessing code.
- Very compatible:
    - Runs on Unix, Windows & MacOS.
    - Python >= 3.9
- Lightweight:
    - No dependencies for its core version.
    - [WIP] API version will require [Falcon](https://falcon.readthedocs.io/en/stable/index.html),
      which is a minimalist ASGI/WSGI framework that doesn't require other packages to work.
    - [WIP] The Dashboard (full) version will require Falcon and [Dash](https://dash.plotly.com/).

## Usage

In this example we will compute the factorial of 20.000 integers, using multiprocessing,
while storing the results into 2 separate lists, one for even values and another for odd values.

``` py title="basic_etl.py"
import math
from typing import Any, Iterator

from cupyd import ETL, Extractor, Transformer, Loader, Filter


class IntegerExtractor(Extractor):

    def __init__(self, total_items: int):
        super().__init__()
        self.total_items = total_items

        # generated integers will be passed to the workers in buckets of size 10
        self.configuration.bucket_size = 10

    def extract(self) -> Iterator[int]:
        for item in range(self.total_items):
            yield item


class Factorial(Transformer):

    def transform(self, item: int) -> int:
        return math.factorial(item)


class EvenOnly(Filter):

    def filter(self, item: int) -> int | None:
        return item if item & 1 else None


class OddOnly(Filter):

    def filter(self, item: int) -> int | None:
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


if __name__ == "__main__":
    # 1. Define the ETL Nodes
    ext = IntegerExtractor(total_items=20_000)
    factorial = Factorial()
    even_only = EvenOnly()
    odd_only = OddOnly()
    even_ldr = ListLoader()
    odd_ldr = ListLoader()

    # 2. Connect the Nodes to determine the data flow. Notice the ETL branches after the
    # factorial is computed
    ext >> factorial >> [even_only >> even_ldr, odd_only >> odd_ldr]

    # 3. Run the ETL with 8 workers (multiprocessing Processes)
    etl = ETL(extractor=ext)
    etl.run(workers=8, show_progress=True, monitor_performance=True)

    # 4. You can access the results stored in both Loaders after the ETL is finished
    even_factorials = even_ldr.items
    odd_factorials = odd_ldr.items
```

For more information, go the [examples](cupyd/examples) directory
- - -

💘 (_**Project under construction**_)
