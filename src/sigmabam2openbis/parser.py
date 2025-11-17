import re
import pandas as pd

from bam_masterdata.datamodel.object_types import Chemical
from bam_masterdata.parsing import AbstractParser
from bam_masterdata.utils.users import get_bam_username


from sigmabam2openbis.maps import ALLOWED_PC_CODES, MAPPING_COLUMNS
from sigmabam2openbis.utils import build_notes


class SigmaBAM2OpenBISParser(AbstractParser):
    def __init__(self):
        super().__init__()

        # Choose the responsible person source from SigmaBAM either "AntragstellerIn" or "Gefahrstoffkoordinator*in"
        # ? how is this set by the user? I think it should be a static variable and not decided by the user
        # ? maybe the default should be "AntragstellerIn" and a fallback to "Gefahrstoffkoordinator*in" if empty?
        self.RESPONSIBLE_SOURCE = "AntragstellerIn"  # or "Gefahrstoffkoordinator*in"

    def get_value_as_str(self, value) -> str:
        """
        Gets the value as a stripped string, or an empty string if the value is NaN or empty.

        Args:
            value: The value to convert.

        Returns:
            str: The stripped string value or an empty string if `value` is NaN or empty.
        """
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
                umgang_id = umgang_id.zfill(4)

                # Create our new Chemical object
                chemical = Chemical()

                # Code establishes if the object Chemical exists or not in the database and either creates or updates it
                entity = self.get_value_as_str(chemical_row.get("Organisationseinheit"))
                if entity:
                    code = f"CHEM-{entity}-{umgang_id}"
                    chemical.code = code

                # All columns mapped directly
                # TODO check Konzentration and Dichte
                for source_col, final_col in MAPPING_COLUMNS.items():
                    val = self.get_value_as_str(chemical_row.get(source_col))
                    if source_col in ["Konzentration [%]", "Dichte [g/cm\u00b3]"]:
                        try:
                            val = float(val)
                        except ValueError:  # not a float number
                            continue
                        if source_col == "Konzentration [%]":
                            if val < 0.0 or val > 100.0:
                                logger.warning(
                                    f"Concentration value '{val}' out of range (0-100)% in row with Umgang-Id {umgang_id}. Please, check the excel."
                                )
                    setattr(chemical, final_col, val)

                # Responsible person is an OBJECT (PERSON.BAM) reference
                if self.RESPONSIBLE_SOURCE in chemical_row:
                    val = self.get_value_as_str(
                        chemical_row.get(self.RESPONSIBLE_SOURCE)
                    )
                    lastname, firstname = val.strip().split(",")
                    userid = get_bam_username(
                        firstname=firstname, lastname=lastname
                    ).upper()
                    chemical.responsible_person = f"/BAM_GLOBAL/BAM_DATA/{userid}"

                # OE (Organisationseinheit) is a CONTROLLEDVOCABULARY (DIVISIONS)
                if entity:
                    chemical.bam_oe = f"OE_{entity}"

                # Checks if any column related to hazardous substances (H-Sätze, EUH-Sätze, P-Sätze, CMR) is non-empty
                hazardous_substance = False
                for col in ["H-Sätze", "EUH-Sätze", "P-Sätze", "CMR"]:
                    val = self.get_value_as_str(chemical_row.get(col))
                    if val:
                        hazardous_substance = True
                        break
                chemical.hazardous_substance = hazardous_substance

                # Notes
                chemical.notes = build_notes(chemical_row)

                # Product category
                raw_pc = self.get_value_as_str(chemical_row.get("Produktkategorie", ""))

                # Extract tokens like PC0, PC21, PC9A, PC32, etc.
                matches = re.findall(r"\bPC\d+[A-Z]?\b", raw_pc, flags=re.IGNORECASE)
                matches = [m.upper() for m in matches]

                # First allowed match
                pc_code = next((m for m in matches if m in ALLOWED_PC_CODES), None)

                if pc_code:
                    chemical.product_category = pc_code
                    if len(matches) > 1:
                        logger.info(f"Multiple PC codes found in row with Umgang-Id {umgang_id}, using '{pc_code}'")
                else:
                    if raw_pc:  # non-empty but unusable
                        logger.warning(f"Unable to map Produktkategorie '{raw_pc}' to an allowed PC code in row with Umgang-Id {umgang_id}"
        )


                # Complete BAM location
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
