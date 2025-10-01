from .parser import SigmaBAM2OpenBISParser

# Add more metadata if needed
sigmabam2openbis_parser_entry_point = {
    "name": "SigmaBAM2OpenBISParser",
    "description": "Mapper script to convert SigmaBAM chemical inventory exports into openBIS-compatible format.",
    "parser_class": SigmaBAM2OpenBISParser,
}
