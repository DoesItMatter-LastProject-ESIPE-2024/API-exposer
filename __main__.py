"""Script entry point to run the POC."""
import argparse
import logging

from matter_server.common.models import EventType
from matter_server.client.client import MatterClient
from matter_server.client.models.node import MatterNode


from threading import Thread
from aiohttp import ClientSession
from asyncio import sleep
import asyncio
from aiorun import run

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

    devices = {}

    def _handle_event(event: EventType, node: MatterNode, *args):
        if event == EventType.NODE_ADDED:
            devices[node.node_id] = node
            print(f"node {node.node_id} added {node}")
            print(devices)

        elif event == EventType.NODE_UPDATED:
            print(f"node {node.node_id} updated {node}")
            devices[node.node_id] = node
            print(devices)

        elif event == EventType.NODE_REMOVED:
            removed = devices.pop(node)
            print(f"node {node} added {removed}")
            print(devices)

    global client_global
    client_global = None

    async def run_client():
        async with ClientSession() as session:
            async with MatterClient(args.url, session) as client:
                global client_global
                client_global = client
                client.subscribe_events(_handle_event)

                # start listening
                await client.start_listening()

    Thread(target=asyncio.run, args=[run_client()]).start()

    while (client_global is None):
        pass

    Thread(target=asyncio.run, args=[sleep(2)]).run()

    devices.update(
        {node.node_id: node for node in client_global.get_nodes()})
    print(devices)


if __name__ == "__main__":
    main()
