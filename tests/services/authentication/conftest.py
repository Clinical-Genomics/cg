import pytest
from cg.services.authentication.models import (
    DecodingResponse,
    IntrospectionResponse,
    RealmAccess,
    TokenResponseModel,
    UserInfo,
)


@pytest.fixture
def realm_access() -> RealmAccess:
    return RealmAccess(roles=["cg-employee"])


@pytest.fixture
def introspection_response(realm_access) -> IntrospectionResponse:
    return IntrospectionResponse(
        exp=1672531199,
        iat=1672531199,
        auth_time=1672531199,
        jti="unique-jti",
        iss="https://issuer.example.com",
        sub="subject-id",
        typ="Bearer",
        azp="client-id",
        sid="session-id",
        acr="1",
        allowed_origins=["https://allowed.example.com"],
        realm_access=realm_access,
        scope="email profile",
        email_verified=True,
        name="John Doe",
        preferred_username="johndoe",
        given_name="John",
        family_name="Doe",
        email="johndoe@example.com",
        client_id="client-id",
        username="johndoe",
        token_type="Bearer",
        active=True,
    )


@pytest.fixture
def token_response() -> TokenResponseModel:
    return TokenResponseModel(
        access_token="access_token",
        expires_in=3600,
        id_token="id_token",
        not_before_policy=0,
        refresh_expires_in=3600,
        refresh_token="refresh_token",
        scope="email profile",
        session_state="session-state",
        token_type="Bearer",
    )


@pytest.fixture
def decode_token_response(realm_access) -> DecodingResponse:
    return DecodingResponse(
        exp=1672531199,
        iat=1672531199,
        auth_time=1672531199,
        jti="unique-jti",
        iss="https://issuer.example.com",
        sub="subject-id",
        typ="Bearer",
        azp="client-id",
        sid="session-id",
        acr="1",
        allowed_origins=["https://allowed.example.com"],
        realm_access=realm_access,
        scope="email profile",
        email_verified=True,
        name="John Doe",
        preferred_username="johndoe",
        given_name="John",
        family_name="Doe",
        email="johndoe@example.com",
    )


@pytest.fixture
def user_info() -> UserInfo:
    return UserInfo(
        sub="subject-id",
        email_verified=True,
        name="John Doe",
        preferred_username="johndoe",
        given_name="John",
        family_name="Doe",
        email="johndoe@example.com",
    )
