""" 
===================== nodes.py =====================
contain Nodes class for API-EXPOSER
"""
import logging
from asyncio import Event, create_task, Task

from typing import Dict, Optional, Any

from aiohttp import ClientSession
from chip.clusters.ClusterObjects import ClusterCommand
from matter_server.common.models import EventType
from matter_server.client.client import MatterClient
from matter_server.client.models.node import MatterNode


class Nodes:
    """ 
    =============== class nodes ===============
    class to create a client, connect to Matter
    Fabric and get all nodes
    """

    def __init__(self, url: str):
        self.url: str = url
        self.nodes: Dict[int, MatterNode] = {}
        self._client_global: Optional[MatterClient] = None
        self._wait_listening: Event = Event()
        self._task: Optional[Task] = None

    def _handle_node_added(self, node: MatterNode):
        self.nodes[node.node_id] = node
        logging.debug("node %d added %s", node.node_id, node)

    def _handle_node_updated(self, node: MatterNode):
        logging.debug("node %d updated %s", node.node_id, node)
        self.nodes[node.node_id] = node

    def _handle_node_removed(self, node_id: int):
        removed = self.nodes.pop(node_id)
        logging.debug("node %d added %s", node_id, removed)

    def _handle_event(self, event: EventType, *args):
        """Passes all arguments after event to the specific event handler"""
        match event:
            case EventType.NODE_ADDED:
                self._handle_node_added(*args)
            case EventType.NODE_UPDATED:
                self._handle_node_updated(*args)
            case EventType.NODE_REMOVED:
                self._handle_node_removed(*args)
            case _:
                pass

    async def _run_client(self):
        async with ClientSession() as session:
            async with MatterClient(self.url, session) as client:
                self._client_global = client
                self._client_global.subscribe_events(self._handle_event)

                # start listening
                await self._client_global.start_listening(self._wait_listening)

    async def _get_nodes(self):
        await self._wait_listening.wait()
        self.nodes.update({
            node.node_id: node
            for node in self._client_global.get_nodes()
        })
        logging.debug(self.nodes)

    async def start(self):
        """connect to Serveur and get matter nodes list"""
        if self._task is not None:
            logging.error("client already started")
            return
        self._task = create_task(self._run_client())
        await self._get_nodes()

    async def wait_stop(self):
        """connect to Serveur and get matter nodes list"""
        if self._task is None:
            logging.error("client not started")
            return
        await self._task

    async def send_cluster_command(self, node_id: int, endpoint_id: int, command: ClusterCommand):
        """Sends a cluster command to an endpoint of a matter node"""
        return await self._client_global.send_device_command(
            node_id,
            endpoint_id,
            command,
        )

    async def read_cluster_attribute(self, node_id: int, endpoint_id: int, cluster_id: int, attribute_id: int) -> Any:
        """TODO"""
        return await self._client_global.read_attribute(
            node_id,
            f'{endpoint_id}/{cluster_id}/{attribute_id}'
        )

    async def write_cluster_attribute(self, node_id: int, endpoint_id: int, cluster_id: int, attribute_id: int, value: Any) -> Any:
        """TODO"""
        return await self._client_global.write_attribute(
            node_id,
            f'{endpoint_id}/{cluster_id}/{attribute_id}',
            value
        )
