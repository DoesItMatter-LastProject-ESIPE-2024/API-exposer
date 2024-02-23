"""Convert matter objects into yaml"""

from dataclasses import dataclass
import logging
from threading import Thread
from time import sleep
from typing import Dict

from chip.clusters.ClusterObjects import Cluster
from chip.clusters.Objects import OnOff
from convertor import node_to_template_names, _render_cluster
from const import DEFAULT_SERVER_URL
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


if __name__ == '__main__':
    # Execute when the module is not initialized from an import statement.
    # templateNames = node_to_template_names(
    #     Node(0, {0: Endpoint({0: OnOff()})}))
    # print(templateNames)
    # print(_render_cluster(OnOff(), **{'node_id':0,'endpoint_id':0}))

    nodes = Nodes(DEFAULT_SERVER_URL)
    Thread(target=nodes.run).start()

    # wait for nodes to be avaible
    # nodes._get_nodes()
    sleep(5)

    print("hello")

    nodes_dict = nodes.nodes

    print(nodes_dict)

    for id, node in nodes_dict:
        print(id)
        print(node_to_template_names(node))
