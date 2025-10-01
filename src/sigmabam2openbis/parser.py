import pandas as pd
from bam_masterdata.datamodel.object_types import Chemical
from bam_masterdata.parsing import AbstractParser

from sigmabam2openbis.maps import ALLOWED_PC_CODES, MAPPING_COLUMNS
from sigmabam2openbis.utils import build_notes, get_bam_username


class SigmaBAM2OpenBISParser(AbstractParser):
    def __init__(self):
        super().__init__()

        # Choose the responsible person source from SigmaBAM either "AntragstellerIn" or "Gefahrstoffkoordinator*in"
        # ? how is this set by the user? I think it should be a static variable and not decided by the user
        # ? maybe the default should be "AntragstellerIn" and a fallback to "Gefahrstoffkoordinator*in" if empty?
        self.RESPONSIBLE_SOURCE = "AntragstellerIn"  # or "Gefahrstoffkoordinator*in"

    def get_value_as_str(self, value) -> str:
        if pd.isna(value) or not value:
            return ""
        return str(value).strip()

    def parse(self, files, collection, logger):
        for file in files:
            if not file.endswith(".xlsx"):
                logger.error(f"SigmaBAM2OpenBISParser: Unsupported file type {file}")
                continue

            df_source = pd.read_excel(file, header=0, engine="openpyxl", dtype=str)
            for i, chemical_row in df_source.iterrows():
                # If Umgang-Id does not exist, log an error and skip this row
                umgang_id = self.get_value_as_str(chemical_row.get("Umgang-Id"))
                if not umgang_id:
                    logger.error(f"Missing or empty 'Umgang-Id' in row {i + 2}")
                    continue
                # ! ask if zfill(4) is enough or we should increase this --> it might conflict with other chemicals in the database!!!!
                umgang_id = umgang_id.zfill(4)

                # Code establishes if the object Chemical exists or not in the database and either creates or updates it
                # ! deleted `generate_code()`
                entity = self.get_value_as_str(chemical_row.get("Organisationseinheit"))
                if entity:
                    # ! one can overwrite code
                    code = f"CHEM-{entity}-{umgang_id}"
                    # chemical.code = code
                    # ? check this, as we need `space.code` and `project.code`; something like /X.1_MATERIALS/CONSUMABLES/CHEM-<entity>-<umgang_id>
                    # ! this is assigned by openBIS as indeed /space.code/project.code/code, so no need to assign
                    # identifier_prefix =f"/{space.code}/{project.code}/{code}"

                # Create our new Chemical object
                chemical = Chemical()

                # All columns mapped directly
                # TODO check Konzentration and Dichte
                for source_col, final_col in MAPPING_COLUMNS.items():
                    val = self.get_value_as_str(chemical_row.get(source_col))
                    setattr(chemical, final_col, val)

                # Responsible person is an OBJECT (PERSON.BAM)
                # ! changed get_bam_path() for get_bam_username()
                if self.RESPONSIBLE_SOURCE in chemical_row:
                    val = self.get_value_as_str(
                        chemical_row.get(self.RESPONSIBLE_SOURCE)
                    )
                    username = get_bam_username(name=val, uppercase=True)
                    responsible_person = f"/BAM_GLOBAL/BAM_DATA/{username}"
                    # chemical.responsible_person = responsible_person

                # OE (Organisationseinheit) is a VOCABULARY (DIVISIONS)
                # ! deleted get_division_name()
                division_code = self.get_value_as_str(
                    chemical_row.get("Organisationseinheit")
                )
                if division_code:
                    chemical.bam_oe = f"OE_{division_code}"

                # Checks if any column related to hazardous substances (H-Sätze, EUH-Sätze, P-Sätze, CMR) is non-empty
                for col in ["H-Sätze", "EUH-Sätze", "P-Sätze", "CMR"]:
                    val = self.get_value_as_str(chemical_row.get(col))
                    if val:
                        chemical.hazardous_substance = True
                        break

                # Notes
                chemical.notes = build_notes(chemical_row)

                # Product category
                # ! deleted `extract_pc_code()`
                pc_code = self.get_value_as_str(
                    chemical_row.get("Produktkategorie", "")
                ).split()[0]
                if pc_code in ALLOWED_PC_CODES:
                    chemical.product_category = pc_code

                # Complete BAM location
                # ! deleted `concat_location()`
                bam_location_complete = []
                for col in ["Liegenschaft", "Haus", "Etage", "Raum-Nr"]:
                    val = self.get_value_as_str(chemical_row.get(col))
                    if not val:
                        logger.warning(
                            f"Missing value for BAM location column '{col}' in row with Umgang-Id {umgang_id}"
                        )
                        continue
                    bam_location_complete.append(val)
                if bam_location_complete:
                    chemical.bam_location_complete = "_".join(bam_location_complete)

                # Adding chemicals to the collection
                collection.add(chemical)
