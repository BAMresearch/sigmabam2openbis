from bam_masterdata.logger import logger
from bam_masterdata.metadata.entities import CollectionType


class TestSigmaBAM2OpenBISParser:
    def test_parse(self, parser):
        collection = CollectionType()
        parser.parse([], collection, logger)

        assert len(collection.attached_objects) == 2
        objects = list(collection.attached_objects.values())
        assert objects[0].name == "Synthesis"
        assert objects[1].name == "Measurement"
        assert len(collection.relationships) == 1
