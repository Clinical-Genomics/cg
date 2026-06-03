import json


def publish_command(nats_config, subject: str, data: dict) -> str:
    config = nats_config.publisher
    json_str: str = json.dumps(data).replace('"', '\\"')
    command: str = (
        f"{nats_config.nats_binary_path} pub "
        f"--server {nats_config.server} "
        f"--tlsca {config.ca_cert_path} "
        f"--tlscert {config.client_cert_path} "
        f"--tlskey {config.client_key_path} "
        f"--token $(cat {config.token_path}) "
        f'{subject} "{json_str}"'  # double quotes around json to allow bash expansion
    )
    return command
