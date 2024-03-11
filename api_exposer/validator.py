"""Validates arguments"""

import logging
from typing import Optional, Dict, Any

from fastapi.exceptions import HTTPException
from fastapi.requests import Request

from chip.clusters.CHIPClusters import ChipClusters
from chip.clusters.ClusterObjects import Cluster, ClusterCommand
from chip.clusters import Objects
from matter_server.client.models.node import MatterNode, MatterEndpoint

from api_exposer.my_client import MyClient


ClusterInfo = Dict[str, Any]
CommandInfo = Dict[str, Any]
AttributeInfo = Dict[str, Any]
EventInfo = Dict[str, Any]


def not_found(msg: str) -> None:
    """Logs a message ``msg`` and raises an HTTPException
    with error code 404 and ``msg`` as the description"""
    logging.warning(msg)
    raise HTTPException(404, msg)


def validate_node_id(client: MyClient, node_id: int) -> MatterNode:
    """Returns the node if found otherwise raise HTTPException"""
    if node_id not in client.nodes:
        not_found(f'node {node_id} not found')
    return client.nodes[node_id]


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


def validate_event_name(cluster: Cluster, event_name: str) -> int:
    """Returns the event if found otherwise raise HTTPException"""
    if not hasattr(cluster, 'Events'):
        not_found('cluster does not have events')
    if not hasattr(cluster.Events, event_name):
        not_found(f'command {event_name} not found')
    return getattr(cluster.Events, event_name)


def validate_attribute_name(cluster_infos: ChipClusters, cluster: Cluster, attribute_name: str) -> AttributeInfo:
    """Returns the attribute if found otherwise raise HTTPException"""
    # field = cluster.descriptor.GetFieldByLabel(attribute_name)
    # if field is None:
    #     not_found(f'cluster does not have {attribute_name}')

    cluster_info: ClusterInfo = cluster_infos.ListClusterAttributes().get(
        cluster.__class__.__name__, {})
    attribute_info: Optional[AttributeInfo] = cluster_info.get(
        attribute_name, None)

    if attribute_info is None:
        not_found(f'cluster does not have {attribute_name}')
    return attribute_info


async def validate_json_body(request: Request) -> Dict[str, Any]:
    """Returns the json body as a dict or raise HTTPException"""
    if (await request.body()) == b'':
        raise HTTPException(400, "missing POST body")
    json_value: Dict[str, any] = await request.json()
    if not isinstance(json_value, dict):
        raise HTTPException(400, "malformed json")
    return json_value


def validate_json_attribute(json_object: Dict[str, Any], attribute_name: str) -> Any:
    """Returns the attribute value if present or else raise HTTPException"""
    result = json_object.get(attribute_name, None)
    if result is None:
        raise HTTPException(400, "malformed json")

    return result
