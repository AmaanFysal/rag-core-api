import io

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_search_passes_jwt_sub_as_owner_id(
    client: AsyncClient, alice_token: str, mocker
):
    mock_search = mocker.patch(
        "app.api.routes.search.RetrievalService.search",
        return_value=[],
    )
    await client.post(
        "/search/",
        json={"query": "hello", "top_k": 3},
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    mock_search.assert_called_once()
    _, kwargs = mock_search.call_args
    assert kwargs["owner_id"] == "alice"


async def test_ask_passes_jwt_sub_as_owner_id(
    client: AsyncClient, alice_token: str, mocker
):
    mock_ask = mocker.patch(
        "app.api.routes.ask.RAGService.ask",
        return_value={"answer": "ok", "sources": []},
    )
    await client.post(
        "/ask/",
        json={"question": "what is this?", "top_k": 3},
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    mock_ask.assert_called_once()
    _, kwargs = mock_ask.call_args
    assert kwargs["owner_id"] == "alice"


async def test_owner_id_in_body_is_ignored(
    client: AsyncClient, alice_token: str, mocker
):
    """Client cannot override owner_id — field removed from schema, Pydantic ignores it."""
    mock_search = mocker.patch(
        "app.api.routes.search.RetrievalService.search",
        return_value=[],
    )
    # Pass owner_id in body (should be silently ignored by Pydantic)
    await client.post(
        "/search/",
        json={"query": "hello", "top_k": 3, "owner_id": "bob"},
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    mock_search.assert_called_once()
    _, kwargs = mock_search.call_args
    # owner_id must come from the JWT (alice), not the body (bob)
    assert kwargs["owner_id"] == "alice"


async def test_unauthenticated_upload_returns_401(client: AsyncClient):
    response = await client.post(
        "/documents/upload",
        files={"file": ("test.txt", io.BytesIO(b"hello world"), "text/plain")},
    )
    assert response.status_code == 401


async def test_upload_passes_jwt_sub_as_owner_id(
    client: AsyncClient, alice_token: str, mocker
):
    mocker.patch(
        "app.api.routes.document.DocumentService.get_by_owner_and_hash",
        return_value=None,
    )
    mock_stub = mocker.patch(
        "app.api.routes.document.DocumentService.create_document_stub",
    )

    class FakeDoc:
        id = 1
        status = "processed"
        owner_id = "alice"

    mock_stub.return_value = FakeDoc()
    mocker.patch("app.api.routes.document.DocumentService.save_file", return_value=None)
    mocker.patch(
        "app.api.routes.document.ProcessingService.process_document", return_value=None
    )

    await client.post(
        "/documents/upload",
        files={"file": ("test.txt", io.BytesIO(b"hello world"), "text/plain")},
        headers={"Authorization": f"Bearer {alice_token}"},
    )

    mock_stub.assert_called_once()
    _, kwargs = mock_stub.call_args
    assert kwargs["owner_id"] == "alice"
