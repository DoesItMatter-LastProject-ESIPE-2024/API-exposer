"""Contains the arguments parser of the API Exposer"""

from argparse import ArgumentParser
import logging

from api_exposer.const import DEFAULT_SERVER_URL, DEFAULT_PORT, FEATURES_JSON_FOLDER


def get_argument_parser() -> ArgumentParser:
    """Returns an instance of arguments parser ready-to-use with all arguments already added"""
    parser = ArgumentParser()

    parser.add_argument(
        '--server-url',
        type=str,
        dest='url',
        default=DEFAULT_SERVER_URL,
        help=f'the url of the matter server hosted by home-assistant, defaults to {
            DEFAULT_SERVER_URL}',
    )
    parser.add_argument(
        '--features-file',
        type=str,
        default=FEATURES_JSON_FOLDER,
        help=f'the path to the features.json file used for filtering the api, defaults to {
            FEATURES_JSON_FOLDER}',
    )
    parser.add_argument(
        '--port',
        type=int,
        dest='port',
        default=DEFAULT_PORT,
        help=f'the listening port for this server, defaults to {DEFAULT_PORT}',
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
