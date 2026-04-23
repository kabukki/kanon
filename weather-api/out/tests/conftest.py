import fakeredis.aioredis
import httpx
import pytest
from fastapi.testclient import TestClient

from app import cache as cache_mod
from app.main import app


@pytest.fixture(autouse=True)
def fake_cache(monkeypatch):
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    cache_mod.cache._client = fake
    yield
    cache_mod.cache._client = None


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
