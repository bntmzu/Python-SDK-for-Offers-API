from typing import Any, Dict, Optional


class BaseTransport:
    """
    Abstract transport layer interface for Offers SDK.
    All HTTP client backends should inherit from this class.
    """

    async def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Any = None,
        data: Any = None,
        timeout: Optional[float] = None,
    ) -> Any:
        raise NotImplementedError(
            "Transport implementations must override this method."
        )
