from datetime import timedelta

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token
from app.main import app


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


def make_token(username: str, expired: bool = False) -> str:
    if expired:
        return create_access_token(username, expires_delta=timedelta(seconds=-1))
    return create_access_token(username)


@pytest.fixture
def alice_token() -> str:
    return make_token("alice")


@pytest.fixture
def bob_token() -> str:
    return make_token("bob")


@pytest.fixture
def expired_token() -> str:
    return make_token("alice", expired=True)
