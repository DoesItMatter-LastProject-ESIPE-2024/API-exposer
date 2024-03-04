"""Convert matter objects into yaml"""

import asyncio

from const import DEFAULT_SERVER_URL
from convertor import render_node
from nodes import Nodes


async def main():
    """
    This is an example on how to use the convertor
    to render on the console all the paths
    proposed by all the nodes on a matter fabric.
    """
    nodes = Nodes(DEFAULT_SERVER_URL)
    await nodes.start()

    nodes_dict = nodes.nodes

    for node in nodes_dict.values():
        print(render_node(node))


if __name__ == '__main__':
    # Execute when the module is not initialized from an import statement.
    asyncio.run(main())
