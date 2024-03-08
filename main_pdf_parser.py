"""TODO"""
import logging

from json import dump
from pdf_parser.pdf_parser import extract_from_pdf

LOG_FILE = 'pdf_parser/out/log.txt'
OUTPUT_FILE = 'pdf_parser/out/features.json'
SPECIFICATION_FILE = './res/Matter-1.2-Application-Cluster-Specification.pdf'

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename=LOG_FILE,
        filemode='w')

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as file:
        features = extract_from_pdf(SPECIFICATION_FILE, 'all')
        features = {
            id: feature.__to_json__()
            for id, feature in features.items()
        }
        dump(features, file, indent=2)
