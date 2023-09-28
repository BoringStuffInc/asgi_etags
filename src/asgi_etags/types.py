from collections.abc import Awaitable, Callable
from typing import TypeAlias

Scope: TypeAlias = dict
Receive: TypeAlias = Callable[[None], Awaitable[dict]]
Send: TypeAlias = Callable[[dict], Awaitable[None]]
ASGIApp: TypeAlias = Callable[[Scope, Receive, Send], Awaitable[None]]

ETagGenerator: TypeAlias = Callable[[bytes], str]

Method: TypeAlias = str
Path: TypeAlias = str
