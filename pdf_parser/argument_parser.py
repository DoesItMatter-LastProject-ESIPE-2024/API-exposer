"""Contains the arguments parser of the API Exposer"""

from argparse import ArgumentParser
import logging

from pdf_parser.cluster_header import OUTPUT_FILE, SPECIFICATION_FILE


def get_argument_parser() -> ArgumentParser:
    """Returns an instance of arguments parser ready-to-use with all arguments already added"""
    parser = ArgumentParser()

    parser.add_argument(
        '--output-path',
        type=str,
        default=OUTPUT_FILE,
        help=f'the file path for the json output, default={OUTPUT_FILE}',
    )
    parser.add_argument(
        '--specification-path',
        type=str,
        default=SPECIFICATION_FILE,
        # pylint: disable=line-too-long
        help=f'the specification pdf file path, default={SPECIFICATION_FILE}',
    )
    parser.add_argument(
        '--log-level',
        type=str,
        default='info',
        # pylint: disable=line-too-long
        help='Provide logging level. Example --log-level debug, default=info, possible=(critical, error, warning, info, debug)',
    )
    parser.add_argument(
        '--log-file',
        type=str,
        default=None,
        help='Log file to write to (optional).',
    )

    return parser


def parse_args() -> any:
    """Parse all arguments"""
    args = get_argument_parser().parse_args()

    handlers = [logging.FileHandler(args.log_file)] if args.log_file else None
    logging.basicConfig(handlers=handlers, level=args.log_level.upper())

    return args
