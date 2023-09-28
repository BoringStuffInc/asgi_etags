# asgi_etags
Simple etags middleware for asgi apps.

## Installation

The library is available on PyPI:

```shell
pip install asgi_etags
```

Or in the `Releases` tab, both in `sdist` format as well as `wheels`.

## Example usage:

### With FastAPI
```python
from fastapi import FastAPI
from hashlib import md5
from asgi_etags import ETagMiddlewareFactory

app = FastAPI()
app.add_middleware(ETagMiddlewareFactory(lambda body: md5(body).hexdigest()))

@app.get("/")
def hello_world():
    return {"hello": "world"}
```

### With Litestar

```python
from litestar import Litestar

@get(path="/", media_type="application/json", sync_to_thread=False)
def hello_world() -> dict[str, str]:
    return {"hello": "world"}


app = Litestar(
    route_handlers=[hello_world],
    middleware=[ETagMiddlewareFactory(lambda body: md5(body).hexdigest())],
)
```
