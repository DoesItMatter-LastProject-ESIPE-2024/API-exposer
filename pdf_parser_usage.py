"""TODO"""
import logging

from json import dump
from pdf_parser.pdf_parser import extract_from_pdf

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    with open("pdf_parser/out/tmp.txt", "w", encoding='utf-8') as file:
        features = extract_from_pdf(
            './res/Matter-1.2-Application-Cluster-Specification.pdf', 'all')
        features = {
            id: feature.__json__()
            for id, feature in features.items()
        }
        dump(features, file, indent=2)

