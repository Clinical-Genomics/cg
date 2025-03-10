from pydantic import BaseModel
from typing import List


class RealmAccess(BaseModel):
    roles: List[str]


class IntrospectionResponse(BaseModel):
    exp: int
    iat: int
    auth_time: int
    jti: str
    iss: str
    sub: str
    typ: str
    azp: str
    sid: str
    acr: str
    allowed_origins: List[str] | None = None
    realm_access: RealmAccess
    scope: str
    email_verified: bool
    name: str
    preferred_username: str
    given_name: str
    family_name: str
    email: str
    client_id: str
    username: str
    token_type: str
    active: bool


class TokenResponseModel(BaseModel):
    access_token: str
    expires_in: int
    id_token: str
    not_before_policy: int | None = None
    refresh_expires_in: int
    refresh_token: str
    scope: str
    session_state: str
    token_type: str


class DecodingResponse(BaseModel):
    exp: int
    iat: int
    auth_time: int
    jti: str
    iss: str
    sub: str
    typ: str
    azp: str
    sid: str
    acr: str
    allowed_origins: List[str] | None = None
    realm_access: RealmAccess
    scope: str
    email_verified: bool
    name: str
    preferred_username: str
    given_name: str
    family_name: str
    email: str


class UserInfo(BaseModel):
    sub: str
    email_verified: bool
    name: str
    preferred_username: str
    given_name: str
    family_name: str
    email: str
