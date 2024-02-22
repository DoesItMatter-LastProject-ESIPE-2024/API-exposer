"""Script entry point to run the POC."""

import logging
import argparse

from devices import Devices

from const import DEFAULT_SERVER_URL

# Get parsed passed in arguments.
parser = argparse.ArgumentParser(
    description="POC - get a list of connected matter node"
)


parser.add_argument(
    "--server-url",
    type=str,
    dest="url",
    default=DEFAULT_SERVER_URL,
    help=f"Vendor ID for the Fabric, defaults to {DEFAULT_SERVER_URL}",
)
parser.add_argument(
    "--log-level",
    type=str,
    default="info",
    # pylint: disable=line-too-long
    help="Provide logging level. Example --log-level debug, default=info, possible=(critical, error, warning, info, debug)",
)
parser.add_argument(
    "--log-file",
    type=str,
    default=None,
    help="Log file to write to (optional).",
)


def main():
    """Run main execution."""
    args = parser.parse_args()

    # configure logging
    handlers = [logging.FileHandler(args.log_file)] if args.log_file else None
    logging.basicConfig(handlers=handlers, level=args.log_level.upper())

    Devices(args.url).run()

if __name__ == "__main__":
    main()
