import pytest
from asgi_etags import ETagMiddlewareFactory
from hashlib import md5
from litestar import Litestar, get
from litestar.testing import TestClient


def md5_hash(body: bytes) -> str:
    return md5(body).hexdigest()


@pytest.fixture
def app():
    @get(path="/", media_type="application/json", sync_to_thread=False)
    def root() -> dict[str, str]:
        return {"hello": "world"}

    @get(path="/health", media_type="application/json", sync_to_thread=False)
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app = Litestar(
        route_handlers=[root, health],
        middleware=[ETagMiddlewareFactory(etag_generator=md5_hash, ignore_paths=[("GET", "/health")])],
    )

    return app


def test_etag_middleware(app):
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.headers["ETag"] == md5_hash(b'{"hello":"world"}')


def test_etag_middleware_if_none_match(app):
    with TestClient(app) as client:
        etag = md5_hash(b'{"hello":"world"}')

        response = client.get("/")
        assert response.status_code == 200
        assert response.headers["ETag"] == etag

        response = client.get("/", headers={"If-None-Match": etag})
        assert response.status_code == 304


def test_etag_middleware_if_match(app):
    with TestClient(app) as client:
        etag = md5_hash(b'{"hello":"world"}')

        response = client.get("/")
        assert response.status_code == 200
        assert response.headers["ETag"] == etag

        response = client.get("/", headers={"If-Match": etag})
        assert response.status_code == 200

        response = client.get("/", headers={"If-Match": "invalid"})
        assert response.status_code == 412


def test_etag_middleware_ignore_paths(app):
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert "ETag" not in response.headers
