"""Constants specific for encryption"""

from enum import StrEnum

from cg.utils.enums import ListEnum


class CipherAlgorithm(StrEnum):
    TRIPLE_DES: str = "3DES"
    AES: str = "AES"
    AES192: str = "AES192"
    AES256: str = "AES256"
    BLOWFISH: str = "BLOWFISH"
    CAMELLIA128: str = "CAMELLIA128"
    CAMELLIA192: str = "CAMELLIA192"
    CAMELLIA256: str = "CAMELLIA256"
    CAST5: str = "CAST5"
    IDEA: str = "IDEA"
    TWOFISH: str = "TWOFISH"


class EncryptionUserID(StrEnum):
    HASTA_USER_ID: str = '"Clinical Genomics"'


class GPGParameters(ListEnum):
    ASYMMETRIC_ENCRYPTION: list[str] = [
        "--encrypt",
        "--yes",
        "--recipient",
        EncryptionUserID.HASTA_USER_ID,
    ]
    ASYMMETRIC_DECRYPTION: list = [
        "--decrypt",
        "--yes",
        "--batch",
        "--cipher-algo",
        CipherAlgorithm.AES256,
        "--passphrase",
        EncryptionUserID.HASTA_USER_ID,
    ]
    SYMMETRIC_ENCRYPTION: list[str] = [
        "--symmetric",
        "--yes",
        "--cipher-algo",
        CipherAlgorithm.AES256,
        "--batch",
        "--compress-algo",
        "None",
        "--passphrase-file",
    ]
    SYMMETRIC_DECRYPTION: list[str] = [
        "--decrypt",
        "--yes",
        "--cipher-algo",
        CipherAlgorithm.AES256,
        "--batch",
        "--passphrase-file",
    ]
    OUTPUT_PARAMETER: list[str] = [
        "-o",
    ]
