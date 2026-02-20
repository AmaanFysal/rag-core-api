import pytest
from httpx import AsyncClient

from app.core.security import create_access_token

pytestmark = pytest.mark.asyncio


async def test_missing_token_returns_401(client: AsyncClient):
    response = await client.post("/search/", json={"query": "hello", "top_k": 3})
    assert response.status_code == 401


async def test_garbage_token_returns_401(client: AsyncClient):
    response = await client.post(
        "/search/",
        json={"query": "hello", "top_k": 3},
        headers={"Authorization": "Bearer not.a.valid.token"},
    )
    assert response.status_code == 401


async def test_wrong_signature_returns_401(client: AsyncClient):
    # Sign a token with a different secret
    from jose import jwt
    bad_token = jwt.encode({"sub": "alice"}, "wrong-secret", algorithm="HS256")
    response = await client.post(
        "/search/",
        json={"query": "hello", "top_k": 3},
        headers={"Authorization": f"Bearer {bad_token}"},
    )
    assert response.status_code == 401


async def test_expired_token_returns_401(client: AsyncClient, expired_token: str):
    response = await client.post(
        "/search/",
        json={"query": "hello", "top_k": 3},
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401


async def test_valid_token_reaches_route(client: AsyncClient, alice_token: str, mocker):
    mocker.patch(
        "app.api.routes.search.RetrievalService.search",
        return_value=[],
    )
    response = await client.post(
        "/search/",
        json={"query": "hello", "top_k": 3},
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert response.status_code == 200


async def test_login_returns_token(client: AsyncClient):
    response = await client.post(
        "/auth/token",
        data={"username": "alice", "password": "alice_password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


async def test_wrong_password_returns_401(client: AsyncClient):
    response = await client.post(
        "/auth/token",
        data={"username": "alice", "password": "wrongpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 401
