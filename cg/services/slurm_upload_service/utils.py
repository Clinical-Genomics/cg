from cg.constants.priority import SlurmAccount, SlurmQos


def get_quality_of_service(account: SlurmAccount) -> SlurmQos:
    return SlurmQos.HIGH if account == SlurmAccount.PRODUCTION else SlurmQos.LOW
