import httpx
import pytest

from teler import AsyncClient, Client, exceptions
from teler.resources.calls import AsyncCallResourceManager, CallResourceManager

TEST_API_KEY = "TEST_API_KEY"


# Sync client
def test_client_init_sets_api_key_and_client_and_managers():
    client = Client(api_key=TEST_API_KEY)

    assert client.api_key == TEST_API_KEY
    assert isinstance(client.httpx_client, httpx.Client)
    assert isinstance(client.calls, CallResourceManager)


def test_client_init_missing_api_key_raises():
    with pytest.raises(exceptions.BadParametersException):
        Client()


def test_client_context_manager():
    with Client(api_key=TEST_API_KEY) as client:
        assert client.api_key == TEST_API_KEY
        assert isinstance(client.httpx_client, httpx.Client)
        assert isinstance(client.calls, CallResourceManager)
    # After context, the client should be closed
    assert client.httpx_client.is_closed


# Async client
@pytest.mark.asyncio
async def test_async_client_init_sets_api_key_and_client_and_managers():
    client = AsyncClient(api_key=TEST_API_KEY)

    assert client.api_key == TEST_API_KEY
    assert isinstance(client.httpx_client, httpx.AsyncClient)
    assert isinstance(client.calls, AsyncCallResourceManager)

    await client.httpx_client.aclose()


@pytest.mark.asyncio
async def test_async_client_init_missing_api_key_raises():
    with pytest.raises(exceptions.BadParametersException):
        AsyncClient()


@pytest.mark.asyncio
async def test_async_client_context_manager():
    async with AsyncClient(api_key=TEST_API_KEY) as client:
        assert client.api_key == TEST_API_KEY
        assert isinstance(client.httpx_client, httpx.AsyncClient)
        assert isinstance(client.calls, AsyncCallResourceManager)
    # After context, the client should be closed
    assert client.httpx_client.is_closed
