import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from hashlib import md5
from asgi_etags import ETagMiddleware


def md5_hash(body: bytes) -> str:
    return md5(body).hexdigest()


@pytest.fixture
def app():
    app = FastAPI()
    app.add_middleware(ETagMiddleware, etag_generator=md5_hash)

    @app.get("/")
    def root():
        return {"hello": "world"}

    return app


def test_etag_middleware(app):
    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["ETag"] == md5_hash(b'{"hello":"world"}')


def test_etag_middleware_if_none_match(app):
    client = TestClient(app)
    etag = md5_hash(b'{"hello":"world"}')

    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["ETag"] == etag

    response = client.get("/", headers={"If-None-Match": etag})
    assert response.status_code == 304


def test_etag_middleware_if_match(app):
    client = TestClient(app)
    etag = md5_hash(b'{"hello":"world"}')

    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["ETag"] == etag

    response = client.get("/", headers={"If-Match": etag})
    assert response.status_code == 200

    response = client.get("/", headers={"If-Match": "invalid"})
    assert response.status_code == 412
