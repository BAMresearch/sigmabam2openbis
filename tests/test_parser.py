import os

from bam_masterdata.logger import logger
from bam_masterdata.metadata.entities import CollectionType


def test_dummy():
    assert True


# ! We need to do testing for proper application of this parser
# def test_parse_example_1(self, parser):
#     collection = CollectionType()
#     # ! ask if these examples can be added openly to the repo under `tests/data/`
#     file = os.path.join("tmp", "example_01.xlsx")
#     parser.parse([file], collection, logger)
#     assert True

# def test_parse_example_2(self, parser):
#     collection = CollectionType()
#     file = os.path.join("tmp", "example_02.xlsx")
#     parser.parse([file], collection, logger)
#     assert True
