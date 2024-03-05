from __future__ import annotations
import logging
from math import isnan
from typing import Dict, Iterable, List, Optional, Callable, Tuple
# from camelot import read_pdf
from tabula import read_pdf
from pandas import DataFrame

from pdf_parser.cluster_model import AttributeExtractionModel, FeatureExtractionModel, InfoExtractionModel, ClusterExtractionModel
from pdf_parser.cluster_header import INFO_HEADER, FEATURE_HEADER, COMMAND_HEADER, ATTRIBUTE_HEADER, CLEANING_MAPPING
from feature import Feature, Features

def _is_conform(conformance: str, feature: FeatureExtractionModel) -> bool:
    # TODO : Lionia travail un peu stp
    return True

def _is_writable(attribute: AttributeExtractionModel) -> bool:
    # TODO : Lionia travail un peu stp
    return True

def _is_readable(attribute: AttributeExtractionModel) -> bool:
    # TODO : Lionia travail un peu stp
    return True

def _cluster_to_features(cluster: ClusterExtractionModel) -> List[Feature]:
    return [
        Feature(
            set(
                att.name for att in cluster.attributes
                if _is_writable(att) and _is_conform(att.conformance, feature)),
            set(
                att.name for att in cluster.attributes
                if _is_readable(att) and _is_conform(att.conformance, feature)),
            set(
                com.name for com in cluster.commands
                if _is_conform(com.conformance, feature)),
            feature.name
        )
        for feature in cluster.features
    ]


def _convert_to_features(clusters: List[ClusterExtractionModel]) -> Dict[int, Features]:
    return {
        info.id: Features(_cluster_to_features(cluster))
        for cluster in clusters
        for info in cluster.info
    }


def _process_infos(df: DataFrame) -> List[InfoExtractionModel]:
    return [
        InfoExtractionModel(int(row.ID, 0), row.Name)
        for row in df.itertuples()
        if not row.ID == 'n/a'  # means the cluster is provisional
    ]


def _process_features(df: DataFrame) -> List[FeatureExtractionModel]:
    return [
        FeatureExtractionModel(
            int(row.Bit),
            row.Code,
            row.Feature)
        for row in df.itertuples()
    ]


def _process_attributes(df: DataFrame) -> List[AttributeExtractionModel]:
    return [
        AttributeExtractionModel(
            int(row.ID, 0),
            row.Name,
            row.Conformance)
        for row in df.itertuples()
        if isinstance(row.ID, str)  # MAY not be a string if not an attribute
    ]


def _process_commands(df: DataFrame) -> List[AttributeExtractionModel]:
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


def _process_cluster_content(table: DataFrame, result: ClusterExtractionModel):
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
            Optional[ClusterExtractionModel],
            Optional[DataFrame]]:
    """Process a cluster and return the next info table to process or None if tables empty"""
    result = ClusterExtractionModel()
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


def _process(tables: Iterable[DataFrame]) -> List[ClusterExtractionModel]:
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
    try:
        for p, r in CLEANING_MAPPING:
            result = result.replace(p, r, **options)
    except Exception as e:
        logging.error('error converting %s -> %s', repr(text), repr(result))
        raise e
    return result

def _reset_header(df: DataFrame) -> DataFrame:
    if any('Unnamed' in col for col in df.columns):
        new_headers = df.iloc[0].to_list()
        df = df[1:]
        df.columns = new_headers
    return df
    

def _clean_header(df: DataFrame) -> DataFrame:
    # removes soft hyphens in headers
    df = df.rename(columns=_clean_string)
    return df


def _read_pdf_tables(pdf_path: str, pages: str) -> List[DataFrame]:
    return (table for table in read_pdf(
        pdf_path,
        pages=pages,
        lattice=True
    ))


def extract_from_pdf(pdf_path: str, pages: str) -> Dict[int, Features]:
    """Extracts feature's informations about clusters from the matter cluster specification pdf"""
    tables = _read_pdf_tables(pdf_path, pages)
    tables = (_reset_header(table) for table in tables if not table.empty)
    return _convert_to_features(_process(
        _clean_header(_clean_string(table, regex=True))
        for table in tables
        if all(isinstance(col, str) for col in table.columns)
    ))
