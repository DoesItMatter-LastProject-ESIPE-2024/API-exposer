"""Convert matter objects into yaml"""

import asyncio

from api_exposer.const import DEFAULT_SERVER_URL
from api_exposer.renderer import render_node
from api_exposer.my_client import MyClient


async def main():
    """
    This is an example on how to use the convertor
    to render on the console all the paths
    proposed by all the nodes on a matter fabric.
    """
    nodes = MyClient(DEFAULT_SERVER_URL)
    await nodes.start()

    nodes_dict = nodes.nodes

    for node in nodes_dict.values():
        print(render_node(node))


if __name__ == '__main__':
    # Execute when the module is not initialized from an import statement.
    asyncio.run(main())
