import json
import logging
import ssl
from collections.abc import Callable
from logging import Logger
from ssl import SSLContext

import nats
from nats.aio.client import Client
from nats.js import JetStreamContext

LOG: Logger = logging.getLogger(__name__)


class EventListener:
    def __init__(self, server: str, ca_cert_path: str):
        self.server = server
        self.ca_cert_path = ca_cert_path
        self._handlers: dict[str, Callable] = {}

    def register(self, subject: str, handler: Callable) -> None:
        self._handlers[subject] = handler

    def _tls_context(self) -> SSLContext:
        ctx: SSLContext = ssl.create_default_context()
        ctx.load_verify_locations(self.ca_cert_path)
        return ctx

    async def listen(self) -> None:
        nc: Client = await nats.connect(servers=self.server, tls=self._tls_context())
        js: JetStreamContext = nc.jetstream()
        sub: JetStreamContext.PushSubscription = await js.subscribe("cg.>", durable="cg-consumer")
        LOG.info("Listening for events")
        async for msg in sub.messages:
            handler = self._handlers.get(msg.subject)
            if handler:
                try:
                    handler(json.loads(msg.data))
                    await msg.ack()
                except Exception:
                    LOG.exception(f"Failed to handle {msg.subject}")
                    await msg.nak()
            else:
                LOG.warning(f"No handler registered for {msg.subject}")
                await msg.ack()
