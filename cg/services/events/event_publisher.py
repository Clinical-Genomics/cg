import json

from cg.models.cg_config import NatsConfig


def publish_command(nats_config: NatsConfig, subject: str, data: dict) -> str:
    config = nats_config.publisher
    command = f"{config.nats_binary_path} pub --server {nats_config.server} --tlsca {config.ca_cert_path} --tlscert {config.client_cert_path} --tlskey {config.client_key_path} --token $(cat {config.token_path}) {subject} '{json.dumps(data)}'"
    return command
