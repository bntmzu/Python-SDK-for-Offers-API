from .httpx import HttpxTransport
from .aiohttp import AiohttpTransport
from .requests import RequestsTransport


def get_transport(name: str, timeout: float = 10.0):
    name = name.lower()
    if name == "httpx":
        return HttpxTransport(timeout)
    elif name == "aiohttp":
        return AiohttpTransport(timeout)
    elif name == "requests":
        return RequestsTransport(timeout)
    else:
        raise ValueError(f"Unknown transport: {name}")
