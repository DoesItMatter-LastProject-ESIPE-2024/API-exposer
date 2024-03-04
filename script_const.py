"""TODO"""
import re

PATTERN_TITLE = re.compile(r'^(\d+\.)+ (.+)$')

INFO_TITLE = 'Cluster ID'
INFO_HEADER = 'ID Name'
INFO_PATTERN = re.compile(r'(0x\d+) (.+)')

FEATURE_TITLE = 'Features'
FEATURE_HEADER = 'Bit Code Feature Summary'
FEATURE_PATTERN = re.compile(r'(\d+) (\w+) (\w+)  (.+)')

ATTRIBUTE_TITLE = 'Attributes'
ATTRIBUTE_HEADER = 'ID Name Type Constraint Quality  Default Access Confor'
ATTRIBUTE_PATTERN = re.compile(r'(0x\d+) (.+) (.+) (.+) (.+) (.+) (.+) (.+)')

COMMAND_TITLE = 'Commands'
COMMAND_HEADER = ''
COMMAND_PATTERN = re.compile(r'(0x\d+) (.+)')
