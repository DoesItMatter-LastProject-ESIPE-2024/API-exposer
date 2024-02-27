"""Convert matter objects into yaml"""

import asyncio

from typing import Dict
from dataclasses import dataclass
from chip.clusters.ClusterObjects import Cluster

from const import DEFAULT_SERVER_URL
from convertor import render_node
from nodes import Nodes


@dataclass
class Endpoint:
    """pass"""
    clusters: Dict[int, Cluster]


@dataclass
class Node:
    """pass"""
    node_id: int
    endpoints: Dict[int, Endpoint]


async def main():
    """TODO"""
    nodes = Nodes(DEFAULT_SERVER_URL)
    await nodes.start()

    nodes_dict = nodes.nodes

    for node in nodes_dict.values():
        print(render_node(node))


if __name__ == '__main__':
    # Execute when the module is not initialized from an import statement.
    asyncio.run(main())
