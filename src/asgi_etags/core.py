from collections.abc import Sequence
from http import HTTPStatus
from enum import Enum, auto
from asgi_etags.types import ASGIApp, ETagGenerator, Receive, Scope, Send, Method, Path


class ConditionalETagHeader(Enum):
    IF_MATCH = auto()
    IF_NONE_MATCH = auto()


class ETagMiddleware:
    __slots__: tuple[str, ...] = (
        "app",
        "etag_generator",
        "ignore_paths",
    )

    def __init__(
        self,
        app: ASGIApp,
        etag_generator: ETagGenerator,
        ignore_paths: Sequence[tuple[Method, Path]] | None = None,
    ) -> None:
        self.app = app
        self.etag_generator = etag_generator
        self.ignore_paths = ignore_paths or []

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        assert "type" in scope, "ASGI scope must contain a 'type' key"

        if not scope["type"] == "http" or (scope["method"], scope["path"]) in self.ignore_paths:
            await self.app(scope, receive, send)
        else:
            for header, value in scope["headers"]:
                match header, value:
                    case (b"if-match", client_etag):
                        conditional_header = ConditionalETagHeader.IF_MATCH
                        client_etag = value.decode()
                        break
                    case (b"if-none-match", client_etag):
                        conditional_header = ConditionalETagHeader.IF_NONE_MATCH
                        client_etag = value.decode()
                        break
                    case _:
                        continue
            else:
                client_etag = None
                conditional_header = None

            await self.app(
                scope,
                receive,
                ETagSendWrapper(send, client_etag, conditional_header, self.etag_generator),
            )


class ETagMiddlewareFactory:
    __slots__: tuple[str, ...] = ("etag_generator", "ignore_paths")

    def __init__(self, etag_generator: ETagGenerator, ignore_paths: Sequence[tuple[Method, Path]]) -> None:
        self.etag_generator = etag_generator
        self.ignore_paths = ignore_paths

    def __call__(self, app: ASGIApp) -> ETagMiddleware:
        return ETagMiddleware(app, self.etag_generator, self.ignore_paths)


class ETagSendWrapper:
    __slots__: tuple[str, ...] = (
        "send",
        "client_etag",
        "conditional_header",
        "etag_generator",
        "original_scope",
    )

    def __init__(
        self,
        send: Send,
        client_etag: str | None,
        conditional_header: ConditionalETagHeader | None,
        etag_generator: ETagGenerator,
    ) -> None:
        self.send = send
        self.client_etag = client_etag
        self.conditional_header = conditional_header
        self.etag_generator = etag_generator

        self.original_scope: dict | None = None

    def _is_modified(self, server_etag: str, client_etag: str | None) -> bool:
        return server_etag != client_etag

    async def __call__(self, scope: dict) -> None:
        if scope["type"] == "http.response.start":
            self.original_scope = scope.copy()
            return

        if scope["type"] == "http.response.body":
            if self.original_scope is None:
                raise RuntimeError("_ETagSendWrapper called before http.response.start")

            server_etag = self.etag_generator(scope["body"])

            match self.conditional_header:
                case ConditionalETagHeader.IF_MATCH:
                    if self._is_modified(server_etag, self.client_etag):
                        await self.send(
                            {
                                "type": "http.response.start",
                                "status": HTTPStatus.PRECONDITION_FAILED,
                                "headers": self.original_scope["headers"],
                            }
                        )
                        await self.send({"type": "http.response.body", "body": b"", "more_body": False})
                        return
                case ConditionalETagHeader.IF_NONE_MATCH:
                    if not self._is_modified(server_etag, self.client_etag):
                        await self.send(
                            {
                                "type": "http.response.start",
                                "status": HTTPStatus.NOT_MODIFIED,
                                "headers": self.original_scope["headers"],
                            }
                        )
                        await self.send({"type": "http.response.body", "body": b"", "more_body": False})
                        return

            self.original_scope["headers"].append(("ETag".encode(), server_etag.encode()))
            await self.send(self.original_scope)

            await self.send(scope)
            return
