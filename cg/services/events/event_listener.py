import json
import logging
import ssl
from collections.abc import Callable
from logging import Logger
from pathlib import Path
from ssl import Purpose, SSLContext, TLSVersion

import nats
from nats.aio.client import Client
from nats.js import JetStreamContext

from cg.models.cg_config import NatsConfig

LOG: Logger = logging.getLogger(__name__)


class EventListener:
    def __init__(self, config: NatsConfig):
        self.server: str = config.server
        self.ca_cert_path: Path = config.listener.ca_cert_path
        self.client_cert: Path = config.listener.client_cert_path
        self.client_key: Path = config.listener.client_key_path
        self.token: str = config.listener.token_path.read_text().strip()

        self._handlers: dict[str, Callable] = {}

    def register(self, subject: str, handler: Callable) -> None:
        self._handlers[subject] = handler

    async def listen(self) -> None:
        nc: Client = await nats.connect(
            servers=self.server, tls=self._tls_context(), token=self.token
        )
        js: JetStreamContext = nc.jetstream()
        sub: JetStreamContext.PushSubscription = await js.subscribe("cg.>", durable="cg-consumer")
        LOG.info("Listening for events")
        async for msg in sub.messages:
            LOG.info(f"Received message on subject: {msg.subject}, data: {msg.data.decode()}")
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

    def _tls_context(self) -> SSLContext:
        ctx: SSLContext = ssl.create_default_context(Purpose.SERVER_AUTH)
        ctx.minimum_version = TLSVersion.TLSv1_2
        ctx.load_verify_locations(self.ca_cert_path)
        ctx.load_cert_chain(certfile=self.client_cert, keyfile=self.client_key)
        return ctx
