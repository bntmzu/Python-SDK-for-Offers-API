import requests
from typing import Any, Dict, Optional

from .base import BaseTransport


class RequestsTransport(BaseTransport):
    """
    Sync transport implementation using requests.Session.
    """

    def __init__(self, timeout: float = 10.0):
        self._timeout = timeout
        self._session = requests.Session()

    def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Any = None,
        data: Any = None,
        timeout: Optional[float] = None,
    ) -> requests.Response:
        response = self._session.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json,
            data=data,
            timeout=timeout or self._timeout,
        )
        return response

    def close(self):
        self._session.close()
