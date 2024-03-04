"""TODO"""

from os import linesep
from typing import List, Tuple
from pandas import Index

CLEANING_MAPPING: List[Tuple[str, str]] = [
    (f'\xad{linesep}', ''),  # soft hyphens
    ('\xad\r\n', ''),  # soft hyphens
    ('\xad\r', ''),  # soft hyphens
    ('\xad\n', ''),  # soft hyphens
    (linesep, ' '),
    ('\r\n', ' '),
    ('\r', ' '),
    ('\n', ' ')
]

INFO_HEADER = Index(['ID', 'Name'])
FEATURE_HEADER = Index(['Bit', 'Code', 'Feature', 'Summary'])
ATTRIBUTE_HEADER = Index(
    ['ID', 'Name', 'Type', 'Constraint', 'Quality', 'Default', 'Access', 'Conformance'])
COMMAND_HEADER = Index(
    ['ID', 'Name', 'Direction', 'Response', 'Access', 'Conformance'])
SPECIFIC_COMMAND_HEADER = Index([])
