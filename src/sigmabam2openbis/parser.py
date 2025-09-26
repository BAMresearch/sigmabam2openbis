from bam_masterdata.datamodel.object_types import ExperimentalStep
from bam_masterdata.parsing import AbstractParser


class SigmaAtBAMParser(AbstractParser):
    def parse(self, files, collection, logger):
        synthesis = ExperimentalStep(name="Synthesis")
        synthesis_id = collection.add(synthesis)
        measurement = ExperimentalStep(name="Measurement")
        measurement_id = collection.add(measurement)
        _ = collection.add_relationship(synthesis_id, measurement_id)
        logger.info(
            "Parsing finished: Added examples synthesis and measurement experimental steps."
        )
