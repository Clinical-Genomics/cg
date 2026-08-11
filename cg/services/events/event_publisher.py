import json


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
