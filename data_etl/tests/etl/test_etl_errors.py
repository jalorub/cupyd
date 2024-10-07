import pytest

from data_etl import ETL
from data_etl.core.exceptions import ETLExecutionError
from data_etl.tests.etl.nodes import ListExtractor, AdderToStr, ListLoader, CustomFilter


def test__etl_error_transformer():
    items = [0, 1, 2, "3", 4, 5]

    ext = ListExtractor(items=items)
    tf = AdderToStr()
    filter_1 = CustomFilter()
    ldr_1 = ListLoader()
    ldr_2 = ListLoader()

    ext >> tf >> [ldr_1, filter_1 >> ldr_2]
    etl = ETL(ext)

    with pytest.raises(ETLExecutionError):
        etl.run()


def test__etl_error_extractor():
    items = None

    ext = ListExtractor(items=items)  # type: ignore
    tf = AdderToStr()
    filter_1 = CustomFilter()
    ldr_1 = ListLoader()
    ldr_2 = ListLoader()

    ext >> tf >> [ldr_1, filter_1 >> ldr_2]
    etl = ETL(ext)

    with pytest.raises(ETLExecutionError):
        etl.run()
