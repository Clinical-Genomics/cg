import asyncio
import json
import ssl
from pathlib import Path
from ssl import Purpose, SSLContext, TLSVersion

import nats
from nats.aio.client import Client
from nats.js import JetStreamContext


def publish_command(nats_config, subject: str, data: dict) -> str:
    json_str: str = json.dumps(data).replace('"', '\\"')
    command: str = (
        f"{nats_config.nats_binary_path} pub "
        "--jetstream "
        f"--server {nats_config.server} "
        f"--tlsca {nats_config.ca_cert_path} "
        f"--tlscert {nats_config.client_cert_path} "
        f"--tlskey {nats_config.client_key_path} "
        f"--token $(cat {nats_config.token_path}) "
        f'{subject} "{json_str}"'  # double quotes around json to allow bash expansion
    )
    return command


def publish(nats_config, subject: str, data: dict) -> None:
    """Publish an event to NATS JetStream from synchronous code."""
    asyncio.run(publish_async(nats_config=nats_config, subject=subject, data=data))


async def publish_async(nats_config, subject: str, data: dict) -> None:
    nc: Client = await nats.connect(
        servers=nats_config.server,
        tls=_tls_context(nats_config=nats_config),
        token=Path(nats_config.token_path).read_text().strip(),
    )
    try:
        js: JetStreamContext = nc.jetstream()
        payload: bytes = json.dumps(data).encode()
        await js.publish(subject=subject, payload=payload)
    finally:
        await nc.drain()


def _tls_context(nats_config) -> SSLContext:
    ctx: SSLContext = ssl.create_default_context(Purpose.SERVER_AUTH)
    ctx.minimum_version = TLSVersion.TLSv1_2
    ctx.load_verify_locations(nats_config.ca_cert_path)
    ctx.load_cert_chain(
        certfile=nats_config.client_cert_path,
        keyfile=nats_config.client_key_path,
    )
    return ctx
