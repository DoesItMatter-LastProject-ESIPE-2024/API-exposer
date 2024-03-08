"""TODO"""

from json import dump
from pdf_parser.argument_parser import parse_args
from pdf_parser.pdf_parser import extract_from_pdf

if __name__ == '__main__':
    args = parse_args()

    with open(args.output_path, 'w', encoding='utf-8') as file:
        features = extract_from_pdf(args.specification_path, 'all')
        features = {
            id: feature.__to_json__()
            for id, feature in features.items()
        }
        dump(features, file, indent=2)
