"""TODO"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import StrEnum, auto
import logging
import re
from typing import Iterator, List, Optional, Set, Callable, Tuple, TypeVar

from pypdf import PdfReader

import script_const as const

T = TypeVar('T')


class _ExtractionState(StrEnum):
    SEARCH_INFO = auto()
    SEARCH_FEATURES = auto()
    SEARCH_ATTRIBUTES = auto()
    SEARCH_COMMANDS = auto()


@dataclass
class _AttributeExtractionModel:
    id: int
    name: str
    features: Set[str]


@dataclass
class _FeatureExtractionModel:
    id: int
    code: str
    name: str


@dataclass
class _InfoExtractionModel:
    id: int
    name: str


@dataclass
class _ClusterExtractionModel:
    info: Optional[_InfoExtractionModel] = None
    features: List[_FeatureExtractionModel] = field(default_factory=list)
    attributes: List[_AttributeExtractionModel] = field(default_factory=list)
    commands: List[_AttributeExtractionModel] = field(default_factory=list)


def extract_from_pdf(pdf_path: str):
    """Extracts features' information about clusters from the matter cluster specification pdf"""
    with open(pdf_path, 'rb') as file:
        reader = PdfReader(file)
        lines = (
            line
            for page in reader.pages
            for line in page.extract_text().splitlines()
        )
        return _process(lines)


def _title(line: str) -> Optional[str]:
    m = re.match(const.PATTERN_TITLE, line)
    return None if m is None else m.groups()[-1]


def _state(line: str) -> Optional[_ExtractionState]:
    title = _title(line)
    match title:
        case None:
            return None
        case const.INFO_TITLE:
            return _ExtractionState.SEARCH_INFO
        case const.FEATURE_TITLE:
            return _ExtractionState.SEARCH_FEATURES
        case const.ATTRIBUTE_TITLE:
            return _ExtractionState.SEARCH_ATTRIBUTES
        case const.COMMAND_TITLE:
            return _ExtractionState.SEARCH_COMMANDS


def _process_table(
        header: str,
        process_table_value: Callable[[str], Optional[T]],
        lines: Iterator[str]) -> List[T]:
    # consume until header
    found_header = False
    processed: List[T] = []
    for line in lines:
        # no title inside a table
        if _title(line) is not None:
            return processed
        if found_header or header == line:
            found_header = True
        value = process_table_value(line)
        if value is None:
            continue
        processed.append(value)
    return processed


def _process_info(line: str) -> Optional[_InfoExtractionModel]:
    m = re.match(const.INFO_PATTERN, line)
    return None if m is None else _InfoExtractionModel(int(m.group(1), 0), m.group(2))


def _process_feature(line: str) -> Optional[_FeatureExtractionModel]:
    m = re.match(const.FEATURE_PATTERN, line)
    return None if m is None else _FeatureExtractionModel(int(m.group(1)), m.group(2), m.group(3))


def _process_attribute(line: str) -> Optional[_AttributeExtractionModel]:
    m = re.match(const.ATTRIBUTE_PATTERN, line)
    return None if m is None else _FeatureExtractionModel(int(m.group(1), 0), m.group(2), m.group(3))


def _process_command(line: str) -> Optional[_AttributeExtractionModel]:
    m = re.match(const.ATTRIBUTE_PATTERN, line)
    return None if m is None else _FeatureExtractionModel(int(m.group(1), 0), m.group(2), m.group(3))


def _process_state(
        state: _ExtractionState,
        model: List[_ClusterExtractionModel],
        current: _ClusterExtractionModel,
        lines: Iterator[str]) -> Tuple[
            _ExtractionState,
            List[_ClusterExtractionModel],
            _ClusterExtractionModel]:
    logging.debug('processing state : %s', state)
    match state:
        case _ExtractionState.SEARCH_INFO:
            infos = _process_table(
                const.INFO_HEADER, _process_info, lines)

            if len(infos) == 0:
                logging.info('could not found cluster id and name')
                return (state, model, current)
            info = infos[0]

            new_model = model
            if current.info is not None:
                new_model = [*model, current]

            return (_ExtractionState.SEARCH_FEATURES, new_model, _ClusterExtractionModel(
                info,
                current.features,
                current.attributes,
                current.commands))

        case _ExtractionState.SEARCH_FEATURES:
            features = _process_table(
                const.FEATURE_HEADER, _process_feature, lines)

            if len(features) == 0:
                logging.info(
                    'could not found any features for cluster %d %s',
                    current.info.id,
                    current.info.name)
                return (state, model, current)

            return (_ExtractionState.SEARCH_ATTRIBUTES, model, _ClusterExtractionModel(
                current.info,
                features,
                current.attributes,
                current.commands))

        case _ExtractionState.SEARCH_ATTRIBUTES:
            attributes = _process_table(
                const.ATTRIBUTE_HEADER, _process_attribute, lines)

            if len(attributes) == 0:
                logging.info(
                    'could not found any attribute for cluster %d %s',
                    current.info.id,
                    current.info.name)
                return (state, model, current)

            return (_ExtractionState.SEARCH_COMMANDS, model, _ClusterExtractionModel(
                current.info,
                current.features,
                attributes,
                current.commands))

        case _ExtractionState.SEARCH_COMMANDS:
            commands = _process_table(
                const.COMMAND_HEADER, _process_command, lines)

            if len(commands) == 0:
                logging.info(
                    'could not found any command for cluster %d %s',
                    current.info.id,
                    current.info.name)
                return (state, model, current)

            return (_ExtractionState.SEARCH_INFO, model, _ClusterExtractionModel(
                current.info,
                current.features,
                current.attributes,
                commands))


def _process(lines: Iterator[str]):
    state = None
    model: List[_ClusterExtractionModel] = []
    current = _ClusterExtractionModel()
    for line in lines:
        if state is None:
            state = _state(line)
            continue

        new_state = _state(line)
        if new_state is not None:
            state = new_state
            continue

        state, model, current = _process_state(state, model, current, lines)
    if current.info is not None:
        model.append(current)
    print(*model, sep='\n')


if __name__ == '__main__':
    pdf_path = './spec.pdf'
    # logging.basicConfig(level=logging.INFO)
    # extract_from_pdf(pdf_path)
    import tabula

    # dfs = tabula.read_pdf(pdf_path, pages='all', lattice=True, multiple_tables=True)
    # print('---------------')
    # print(*dfs, sep='\n---------------\n')
    # print('---------------')
    dfs = tabula.read_pdf(pdf_path, pages=66, lattice=True)
    df = dfs[-1].replace(r' \\r', '', regex=True)
    print(df)
    print()

    # with open(pdf_path, 'rb') as file:
    #     reader = PdfReader(file)
    #     print(reader.pages[65].extract_text(extraction_mode='layout'))
