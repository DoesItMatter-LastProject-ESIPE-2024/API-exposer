"""TODO"""
import logging

from pdf_parser.pdf_parser import extract_from_pdf

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    print(extract_from_pdf(
        './res/Matter-1.2-Application-Cluster-Specification.pdf',
        '1-end'
    ))
