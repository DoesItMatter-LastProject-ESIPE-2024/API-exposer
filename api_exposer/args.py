"""Contains the arguments parser of the API Exposer"""

from argparse import ArgumentParser

from api_exposer.const import DEFAULT_SERVER_URL


def get_args_parser() -> ArgumentParser:
    """Returns an instance of arguments parser ready-to-use with all arguments already added"""
    parser = ArgumentParser()

    parser.add_argument(
        '--server-url',
        type=str,
        dest='url',
        default=DEFAULT_SERVER_URL,
        help=f'Vendor ID for the Fabric, defaults to {DEFAULT_SERVER_URL}',
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
