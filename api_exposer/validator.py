"""Validates arguments"""

import logging

from fastapi import HTTPException
from matter_server.client.models.node import MatterNode, MatterEndpoint
from chip.clusters.ClusterObjects import Cluster, ClusterCommand, ClusterObjectFieldDescriptor
from chip.clusters import Objects

from api_exposer.my_client import MyClient as ClientNodes


def not_found(msg: str) -> None:
    """Logs a message ``msg`` and raises an HTTPException
    with error code 404 and ``msg`` as the description"""
    logging.warning(msg)
    raise HTTPException(404, msg)


def validate_node_id(client_node: ClientNodes, node_id: int) -> MatterNode:
    """Returns the node if found otherwise raise HTTPException"""
    if node_id not in client_node.nodes:
        not_found(f'node {node_id} not found')
    return client_node.nodes[node_id]


def validate_endpoint_id(node: MatterNode, endpoint_id: int) -> MatterEndpoint:
    """Returns the endpoint if found otherwise raise HTTPException"""
    if endpoint_id not in node.endpoints:
        not_found(f'endpoint {endpoint_id} not found')
    return node.endpoints[endpoint_id]


def validate_cluster_name(endpoint: MatterEndpoint, cluster_name: str) -> Cluster:
    """Returns the cluster if found otherwise raise HTTPException"""
    if not hasattr(Objects, cluster_name):
        not_found(f'cluster {cluster_name} not found')
    cluster_class = getattr(Objects, cluster_name)

    if not hasattr(cluster_class, 'id'):
        not_found('cluster id field not found')
    cluster_id = cluster_class.id

    if cluster_id not in endpoint.clusters:
        not_found(f'cluster {cluster_id} not found in endpoint')
    return endpoint.clusters[cluster_id]


def validate_command_name(cluster: Cluster, command_name: str) -> type[ClusterCommand]:
    """Returns the command class if found otherwise raise HTTPException"""
    if not hasattr(cluster, 'Commands'):
        not_found('cluster does not have commands')
    if not hasattr(cluster.Commands, command_name):
        not_found(f'command {command_name} not found')
    return getattr(cluster.Commands, command_name)


def validate_attribute_name(cluster: Cluster, attribute_name: str) -> ClusterObjectFieldDescriptor:
    """Returns the attribute if found otherwise raise HTTPException"""
    field = cluster.descriptor.GetFieldByLabel(attribute_name)
    if field is None:
        not_found(f'cluster does not have {attribute_name}')
    return field
