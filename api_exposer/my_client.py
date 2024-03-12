""" 
Contains the Nodes class for API-EXPOSER.
"""
import logging
from asyncio import Event, create_task, Task, iscoroutinefunction
from typing import Callable, Dict, Optional, Any, Set

from aiohttp import ClientSession
from chip.clusters.ClusterObjects import ClusterCommand
from matter_server.common.models import EventType, MatterNodeEvent
from matter_server.client.client import MatterClient
from matter_server.client.models.node import MatterNode


class MyClient:
    """ 
    A class regrouping the needs for communicating between the REST API and the Cluster API.
    It depends on python-matter-server to communicate to a Matter Server.
    Matter Server is an implementation of a matter controller developed by Home Assistant.
    """

    def __init__(self, url: str):
        self.nodes: Dict[int, MatterNode] = {}
        self._url: str = url
        self._client: Optional[MatterClient] = None
        self._wait_listening: Event = Event()
        self._task: Optional[Task] = None
        self._tasks: Set[Task] = set()

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
            async with MatterClient(self._url, session) as client:
                self._client = client
                self._client.subscribe_events(self._handle_event)

                # start listening
                await self._client.start_listening(self._wait_listening)

    async def _get_nodes(self):
        await self._wait_listening.wait()
        self.nodes.update({
            node.node_id: node
            for node in self._client.get_nodes()
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
        return await self._client.send_device_command(
            node_id,
            endpoint_id,
            command,
        )

    async def read_cluster_attribute(
            self,
            node_id: int,
            endpoint_id: int,
            cluster_id: int,
            attribute_id: int) -> Any:
        """TODO"""
        path = f'{endpoint_id}/{cluster_id}/{attribute_id}'
        value = await self._client.read_attribute(node_id, path)
        logging.debug('READING CLUSTER ATTRIBUTE')
        logging.debug('node : %d', node_id)
        logging.debug('path : %s', path)
        logging.debug('value : %s', value)
        return value

    async def write_cluster_attribute(
            self,
            node_id: int,
            endpoint_id: int,
            cluster_id: int,
            attribute_id: int,
            value: Any) -> Any:
        """TODO"""
        path = f'{endpoint_id}/{cluster_id}/{attribute_id}'
        logging.debug('READING CLUSTER ATTRIBUTE')
        logging.debug('node : %d', node_id)
        logging.debug('path : %s', path)
        logging.debug('value : %s', value)
        return await self._client.write_attribute(
            node_id,
            path,
            value)

    def subscribe_to_event(
            self,
            node_id: int,
            endpoint_id: int,
            cluster_id: int,
            event_id: int,
            callback: Callable[[MatterNodeEvent], None]) -> Callable[[], None]:
        """Subscribes to an event. Returns an unsubscribe handler. The callback can be a coroutine."""
        path = f'{endpoint_id}/{cluster_id}/{event_id}'
        logging.debug('READING CLUSTER ATTRIBUTE')
        logging.debug('node : %d', node_id)
        logging.debug('path : %s', path)
        logging.debug('callback : %s', callback)

        if iscoroutinefunction(callback):
            def handle(_, data: MatterNodeEvent):
                if data.endpoint_id != endpoint_id:
                    return
                if data.cluster_id != cluster_id:
                    return
                if data.event_id != event_id:
                    return
                task = create_task(callback(data))
                self._tasks.add(task)
                task.add_done_callback(self._tasks.discard)
        else:
            def handle(_, data: MatterNodeEvent):
                if data.endpoint_id != endpoint_id:
                    return
                if data.cluster_id != cluster_id:
                    return
                if data.event_id != event_id:
                    return
                callback(data)

        return self._client.subscribe_events(handle, EventType.NODE_EVENT, node_id)

    # def subscribe_to_attribute(
    #         self,
    #         node_id: int,
    #         endpoint_id: int,
    #         cluster_id: int,
    #         attribute_id: int,
    #         callback: Callable[[EventType, Any], None]) -> Callable[[], None]:
    #     """Subscribes to an attribute. Returns an unsubscribe handler. The callback can be a coroutine."""
    #     path = f'{endpoint_id}/{cluster_id}/{attribute_id}'
    #     logging.debug('READING CLUSTER ATTRIBUTE')
    #     logging.debug('node : %d', node_id)
    #     logging.debug('path : %s', path)
    #     logging.debug('callback : %s', callback)
    #     return self._client.subscribe_events(callback, EventType.ATTRIBUTE_UPDATED, node_id, path)
