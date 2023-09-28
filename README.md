# asgi_etags
Simple etags middleware for asgi apps.

## Installation

The library is available on PyPI:

```shell
pip install asgi_etags
```

Or in the `Releases` tab, both in `sdist` format as well as `wheels`.

## Supported Python versions

Currently the library supports Python 3.11 only.

## Example usage:

### With FastAPI
```python
from fastapi import FastAPI
from hashlib import md5
from asgi_etags import ETagMiddleware

app = FastAPI()
app.add_middleware(ETagMiddleware, etag_generator=lambda body: md5(body).hexdigest())

@app.get("/")
def hello_world():
    return {"hello": "world"}
```

### With Litestar

```python
from litestar import Litestar
from hashlib import md5
from asgi_etags import ETagMiddlewareFactory

@get(path="/", media_type="application/json", sync_to_thread=False)
def hello_world() -> dict[str, str]:
    return {"hello": "world"}


app = Litestar(
    route_handlers=[hello_world],
    middleware=[ETagMiddlewareFactory(lambda body: md5(body).hexdigest())],
)
```
