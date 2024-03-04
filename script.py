"""TODO"""
from __future__ import annotations
from dataclasses import dataclass, field
import logging
import os
from typing import Dict, Iterable, List, Optional, Callable, Tuple, TypeVar

from tabula import read_pdf as read_pdf_tables
from pandas import DataFrame
from feature import Features

from script_const import INFO_HEADER, FEATURE_HEADER, COMMAND_HEADER, ATTRIBUTE_HEADER, CLEANING_MAPPING

T = TypeVar('T')


@dataclass
class _AttributeExtractionModel:
    id: int
    name: str
    conformance: str


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
    info: List[_InfoExtractionModel] = field(default_factory=list)
    features: List[_FeatureExtractionModel] = field(default_factory=list)
    attributes: List[_AttributeExtractionModel] = field(default_factory=list)
    commands: List[_AttributeExtractionModel] = field(default_factory=list)


def extract_from_pdf(pdf_path: str) -> Dict[int, Features]:
    """Extracts features' information about clusters from the matter cluster specification pdf"""
    return _convert_to_features(_process(
        _clean_header(_clean_string(table, regex=True))
        for table in read_pdf_tables(pdf_path, pages='all', lattice=True)
        if not table.empty
    ))


def _convert_to_features(clusters: List[_ClusterExtractionModel]) -> Dict[int, Features]:
    print(*clusters, '\n---------------------------\n')
    return {}


def _process_infos(df: DataFrame) -> List[_InfoExtractionModel]:
    return [
        _InfoExtractionModel(int(row.ID, 0), row.Name)
        for row in df.itertuples()
        if not row.ID == 'n/a'  # means the cluster is provisional
    ]


def _process_features(df: DataFrame) -> List[_FeatureExtractionModel]:
    return [
        _FeatureExtractionModel(
            int(row.Bit),
            row.Code,
            row.Feature)
        for row in df.itertuples()
    ]


def _process_attributes(df: DataFrame) -> List[_AttributeExtractionModel]:
    return [
        _AttributeExtractionModel(
            int(row.ID, 0),
            row.Name,
            row.Conformance)
        for row in df.itertuples()
    ]


def _process_commands(df: DataFrame) -> List[_AttributeExtractionModel]:
    # m = re.match(const.ATTRIBUTE_PATTERN, line)
    # return None if m is None else _FeatureExtractionModel(int(m.group(1), 0), m.group(2), m.group(3))
    return []


def _find_next_info_table(
        tables: Iterable[DataFrame],
        table_visitor: Optional[Callable[[DataFrame], None]] = None) -> DataFrame:
    if table_visitor is None:
        for table in tables:
            if table.columns.equals(INFO_HEADER):
                return table
    else:
        for table in tables:
            if table.columns.equals(INFO_HEADER):
                return table
            table_visitor(table)
    return None


def _process_cluster_content(table: DataFrame, result: _ClusterExtractionModel):
    try:
        if any('\u00ad' in col for col in table.columns if isinstance(col, str)):
            logging.warning(
                'table (%s) has soft hyphens in headers, skipping it', table.columns.to_list())
        # Sadly python match case cannot support this.
        # We concatenate the lists because the tables may be on split into multiple tables
        elif table.columns.equals(FEATURE_HEADER):
            logging.info('found FEATURES for %s', result.info)
            result.features = result.features + _process_features(table)
        elif table.columns.equals(ATTRIBUTE_HEADER):
            logging.info('found ATTRIBUTES for %s', result.info)
            result.attributes = result.attributes + _process_attributes(table)
        elif table.columns.equals(COMMAND_HEADER):
            logging.info('found ATTRIBUTES for %s', result.info)
            result.commands = result.commands + _process_commands(table)
        else:
            logging.debug('skipping table : %s', table.columns)
    except Exception as e:
        print(table)
        raise e


def _process_cluster(
        info_table: DataFrame,
        tables: Iterable[DataFrame]) -> Tuple[
            Optional[_ClusterExtractionModel],
            Optional[DataFrame]]:
    """Process a cluster and return the next info table to process or None if tables empty"""
    result = _ClusterExtractionModel()
    result.info = _process_infos(info_table)
    if len(result.info) == 0:
        return (None, _find_next_info_table(tables))

    return (
        result,
        _find_next_info_table(
            tables,
            lambda t: _process_cluster_content(t, result)
        )
    )


def _process(tables: Iterable[DataFrame]) -> List[_ClusterExtractionModel]:
    result = []

    # find first table, info
    table_info = _find_next_info_table(tables)

    # for each table info process cluster
    while table_info is not None:
        cluster, table_info = _process_cluster(table_info, tables)
        if cluster is not None:
            result.append(cluster)
    return result


def _clean_string(text: str, **options) -> str:
    result = text
    for p, r in CLEANING_MAPPING:
        result = result.replace(p, r, **options)
    return result


def _clean_header(df: DataFrame) -> DataFrame:
    if any('Unnamed' in col for col in df.columns):
        new_headers = df.iloc[0].to_list()
        df = df[1:]
        df.columns = new_headers

    # removes soft hyphens in headers
    df = df.rename(columns=_clean_string)
    return df


if __name__ == '__main__':
    pdf_path = './spec.pdf'
    logging.basicConfig(level=logging.DEBUG)
    print(extract_from_pdf(pdf_path))

    # dfs = read_pdf_tables(
    #     pdf_path,
    #     lattice=True,
    #     pages='10-50',)
    # print()
    # print()
    # print()
    # dfs = [_clean_header(_clean_string(df, regex=True)) for df in dfs]
    # print(
    #     *dfs,
    #     sep="\n----------------------------\n"
    # )
