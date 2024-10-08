from unittest import TestCase

from cupyd import ETL
from cupyd.tests.etl.nodes import ListExtractor, AdderToStr, ListLoader, CustomFilter


def test__etl_01():
    test_case = TestCase()

    items = [0, 1, 2, 3, 4, 5]
    expected_items = ["5", "6", "7", "8", "9", "10"]

    ext = ListExtractor(items)
    tf = AdderToStr()
    ldr = ListLoader()

    ext >> tf >> ldr
    ETL(ext).run()

    test_case.assertListEqual(ldr.items, expected_items)


def test__etl_02():
    test_case = TestCase()

    items = [0, 1, 2, 3, 4, 5]
    expected_items = ["5", "6", "7", "8", "9", "10"]

    ext = ListExtractor(items)
    tf = AdderToStr()
    ldr_1 = ListLoader()
    ldr_2 = ListLoader()

    ext >> tf >> [ldr_1, ldr_2]
    ETL(ext).run()

    test_case.assertListEqual(ldr_1.items, expected_items)
    test_case.assertListEqual(ldr_2.items, expected_items)


def test__etl_03():
    test_case = TestCase()

    items = [0, 1, 2, 3, 4, 5]
    expected_items = ["5", "6", "7", "8", "9", "10"]

    ext = ListExtractor(items=items)
    tf = AdderToStr()
    ldr_1 = ListLoader()
    ldr_2 = ListLoader()

    ext >> tf >> [ldr_1, ldr_2]
    ETL(ext).run()

    test_case.assertCountEqual(ldr_1.items, expected_items)
    test_case.assertCountEqual(ldr_2.items, expected_items)


def test__etl_04():
    test_case = TestCase()

    items = [0, 1, 2, 3, 4, 5]
    expected_items_1 = ["5", "6", "7", "8", "9", "10"]
    expected_items_2 = ["6", "7", "8", "9"]

    ext = ListExtractor(items=items)
    tf = AdderToStr()
    filter_1 = CustomFilter()
    ldr_1 = ListLoader()
    ldr_2 = ListLoader()

    ext >> tf >> [ldr_1, filter_1 >> ldr_2]
    ETL(ext).run()

    test_case.assertCountEqual(ldr_1.items, expected_items_1)
    test_case.assertCountEqual(ldr_2.items, expected_items_2)
