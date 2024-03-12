"""Convert matter objects into yaml"""

from dataclasses import dataclass
from inspect import getmembers, isclass
import logging
from asyncio import gather
from typing import Any, Dict, Iterable, Optional, Type
from jinja2 import Environment, FileSystemLoader, select_autoescape
from matter_server.client.models.node import MatterNode, MatterEndpoint
from chip.clusters.ClusterObjects import Cluster, ClusterObjectFieldDescriptor
from chip.clusters.CHIPClusters import ChipClusters
from chip.clusters.ClusterObjects import ClusterEvent

from api_exposer.utils import filter_not_none, flat_map
from api_exposer.const import SWAGGER_PATHS_TEMPLATE_FOLDER
from api_exposer.my_client import MyClient


env = Environment(
    loader=FileSystemLoader(SWAGGER_PATHS_TEMPLATE_FOLDER),
    autoescape=select_autoescape()
)


@dataclass
class Renderer:
    """TODO"""
    client: MyClient
    cluster_infos: ChipClusters
    attribute_list_id: int
    accepted_command_list_id: int

    # def _convert_type(self, class_type: type) -> str:
    #     match class_type:
    #         case _GenericAlias() | list() | set() | dict():
    #             # FIXME
    #             return 'null'
    #         case integer if issubclass(integer, int): return 'integer'
    #         case string if issubclass(string, str): return 'string'
    #         case _: return 'null'

    def _convert_type(self, class_name: str) -> str:
        match class_name:
            case 'int': return 'integer'
            case 'float': return 'number'
            case 'string': return 'string'
            case _: return 'null'

    def _render_attribute(
            self,
            node_id: int,
            endpoint_id: int,
            endpoint_name: str,
            cluster: Cluster,
            attribute: ClusterObjectFieldDescriptor) -> Optional[str]:
        """Renders an attribute path into its OpenAPI yaml format"""
        jinja_template = env.get_template("attribute.yml.j2")
        if jinja_template is None:
            return None

        return jinja_template.render(
            node_id=node_id,
            endpoint_id=endpoint_id,
            endpoint_name_list=endpoint_name,
            cluster_name=cluster.__class__.__name__,
            attribute_name=attribute.get('attributeName', 'NameNotFound'),
            attribute_type=self._convert_type(
                attribute.get('type', 'TypeNotFound')),
            is_readable=True,
            is_writable=attribute.get('writable', False))

    def _render_event(
            self,
            node_id: int,
            endpoint_id: int,
            endpoint_name: str,
            cluster: Cluster,
            event: Type[ClusterEvent]) -> Optional[str]:
        jinja_template = env.get_template("event.yml.j2")
        if jinja_template is None:
            return None

        return jinja_template.render(
            node_id=node_id,
            endpoint_id=endpoint_id,
            endpoint_name_list=endpoint_name,
            cluster_name=cluster.__class__.__name__,
            event_name=event.__name__)

    def _render_command(
            self,
            node_id: int,
            endpoint_id: int,
            endpoint_name: str,
            cluster: Cluster,
            command: Dict[str, Any]) -> Optional[str]:
        """Renders a command into its OpenAPI yaml format"""
        jinja_template = env.get_template("command.yml.j2")
        if jinja_template is None:
            return None

        return jinja_template.render(
            node_id=node_id,
            endpoint_id=endpoint_id,
            endpoint_name_list=endpoint_name,
            cluster_name=cluster.__class__.__name__,
            command_name=command.get('commandName', 'NameNotFound'),
            has_body=command.get('args', False),
            parameters={
                k: self._convert_type(v)
                for k, v in command.get('args', {}).items()})

    async def _render_attributes(
            self,
            node_id: int,
            endpoint_id: int,
            endpoint_name: str,
            cluster: Cluster) -> Iterable[str]:
        """Renders the readable attributes of a cluster into its OpenAPI yaml format"""
        attribute_ids = await self.client.read_cluster_attribute(
            node_id,
            endpoint_id,
            cluster.id,
            self.attribute_list_id)
        if len(attribute_ids) == 0:
            return []
        cluster_info = self.cluster_infos.GetClusterInfoById(cluster.id)
        attributes = cluster_info.get('attributes', None)
        if attributes is None:
            return []

        result = (
            self._render_attribute(
                node_id,
                endpoint_id,
                endpoint_name,
                cluster,
                attributes[attribute_id])
            for attribute_id in attribute_ids)

        return filter_not_none(result)

    async def _render_events(
            self,
            node_id: int,
            endpoint_id: int,
            endpoint_name: str,
            cluster: Cluster) -> Iterable[str]:
        events = self._get_events(cluster)
        result = (
            self._render_event(
                node_id,
                endpoint_id,
                endpoint_name,
                cluster,
                event)
            for event in events)
        return filter_not_none(result)

    async def _render_commands(
            self,
            node_id: int,
            endpoint_id: int,
            endpoint_name: str,
            cluster: Cluster) -> Iterable[str]:
        """Renders the commands of a cluster into its OpenAPI yaml format"""
        command_ids = await self.client.read_cluster_attribute(
            node_id,
            endpoint_id,
            cluster.id,
            self.accepted_command_list_id)
        if len(command_ids) == 0:
            return []
        cluster_info = self.cluster_infos.GetClusterInfoById(cluster.id)
        commands = cluster_info.get('commands', None)
        if commands is None:
            return []

        result = (
            self._render_command(
                node_id,
                endpoint_id,
                endpoint_name,
                cluster,
                commands[command_id])
            for command_id in command_ids)

        return filter_not_none(result)

    async def _render_cluster(
            self,
            node_id: int,
            endpoint_id: int,
            endpoint_name: str,
            cluster: Cluster) -> Iterable[str]:
        """Renders a cluster into its OpenAPI yaml format"""
        if not hasattr(cluster, 'id') or self.cluster_infos.GetClusterInfoById(cluster.id) is None:
            logging.info(
                'The cluster %s has no id',
                cluster.__class__.__name__)
            return []

        attributes = self._render_attributes(
            node_id,
            endpoint_id,
            endpoint_name,
            cluster)
        events = self._render_events(
            node_id,
            endpoint_id,
            endpoint_name,
            cluster)
        commands = self._render_commands(
            node_id,
            endpoint_id,
            endpoint_name,
            cluster)

        logging.debug('await cluster')
        result = flat_map(await gather(attributes, commands, events))
        logging.debug('finished waiting cluster')
        return result

    def _get_endpoint_names(self, endpoint: MatterEndpoint) -> str:
        return ", ".join(
            device_type.__name__
            for device_type in endpoint.device_types)

    async def _render_endpoint(self, endpoint: MatterEndpoint) -> Iterable[str]:
        """Renders an endpoint into its OpenAPI yaml format"""
        clusters = (
            self._render_cluster(
                node_id=endpoint.node.node_id,
                endpoint_id=endpoint.endpoint_id,
                endpoint_name=self._get_endpoint_names(endpoint),
                cluster=cluster)
            for cluster in endpoint.clusters.values())

        logging.debug('await endpoint')
        clusters = await gather(*clusters)
        logging.debug('finished waiting endpoint')
        return flat_map(clusters)

    async def render_node(self, node: MatterNode) -> Optional[str]:
        """Renders a node into its OpenAPI yaml format"""
        endpoints = (
            self._render_endpoint(endpoint)
            for endpoint in node.endpoints.values())

        logging.debug('await node')
        endpoints = await gather(*endpoints)
        logging.debug('finished waiting node')
        endpoints = flat_map(endpoints)
        endpoints = filter_not_none(endpoints)

        result = '\n\n'.join(endpoints)
        if result == '':
            return None
        return result

    def _get_events(
            self,
            cluster: Cluster) -> Iterable[Type[ClusterEvent]]:
        if not hasattr(cluster, 'Events'):
            return []
        return (v for _, v in getmembers(cluster.Events, lambda attr: isclass(attr) and issubclass(attr, ClusterEvent)))
