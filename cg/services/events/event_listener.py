import json
import logging
import ssl
from collections.abc import Callable
from logging import Logger
from pathlib import Path
from ssl import Purpose, SSLContext, TLSVersion

import nats
from nats.aio.client import Client
from nats.aio.msg import Msg
from nats.js import JetStreamContext

from cg.models.cg_config import NatsConfig

LOG: Logger = logging.getLogger(__name__)


class EventListener:
    def __init__(self, config: NatsConfig):
        self.ca_cert_path: Path = config.listener.ca_cert_path
        self.client_cert: Path = config.listener.client_cert_path
        self.client_key: Path = config.listener.client_key_path
        self.server: str = config.server
        self.stream = config.stream
        self.token: str = config.listener.token_path.read_text().strip()

        self._handlers: dict[str, Callable] = {}

    def register(self, subject: str, handler: Callable) -> None:
        self._handlers[subject] = handler

    async def listen(self) -> None:
        nc: Client = await nats.connect(
            servers=self.server, tls=self._tls_context(), token=self.token
        )
        js: JetStreamContext = nc.jetstream()
        sub: JetStreamContext.PushSubscription = await js.subscribe(
            f"{self.stream}.>", durable="cg-consumer"
        )
        LOG.info("Listening for events")
        async for msg in sub.messages:
            LOG.info(f"Received message on subject: {msg.subject}, data: {msg.data.decode()}")
            handler = self._handlers.get(msg.subject)
            if handler:
                try:
                    handler(json.loads(msg.data))
                    await msg.ack()
                except Exception:
                    delay: int = _exponential_backoff_delay(msg)
                    LOG.exception(
                        f"Failed to handle {msg.subject}, will retry in: {delay} seconds."
                    )
                    await msg.nak(delay=delay)
            else:
                LOG.warning(f"No handler registered for {msg.subject}")
                await msg.ack()

    def _tls_context(self) -> SSLContext:
        ctx: SSLContext = ssl.create_default_context(Purpose.SERVER_AUTH)
        ctx.minimum_version = TLSVersion.TLSv1_2
        ctx.load_verify_locations(self.ca_cert_path)
        ctx.load_cert_chain(certfile=self.client_cert, keyfile=self.client_key)
        return ctx


def _exponential_backoff_delay(msg: Msg) -> int:
    """
    Increase the delay for each attempt:
    30s, 60s, 120s etc. until a maximum of 1hr
    """
    max_backoff_seconds: int = 3600
    base_delay: int = 30
    previous_attempts: int = msg.metadata.num_delivered - 1
    return min(base_delay * (2**previous_attempts), max_backoff_seconds)
