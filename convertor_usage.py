"""Convert matter objects into yaml"""

import asyncio

from chip.clusters.Objects import OnOff
from const import DEFAULT_SERVER_URL
from convertor import render_node, _render_cluster
from nodes import Nodes

from chip.clusters.ClusterObjects import Cluster
from typing import Dict
from dataclasses import dataclass

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
    
    # print(_render_cluster(OnOff(), node_id=0, endpoint_id=0))
    # print(render_node(Node(0, {0: Endpoint({})}), node_id=0, endpoint_id=0))


if __name__ == '__main__':
    # Execute when the module is not initialized from an import statement.
    asyncio.run(main())
