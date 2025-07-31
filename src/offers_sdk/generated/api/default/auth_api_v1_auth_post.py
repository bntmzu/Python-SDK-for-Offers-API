from http import HTTPStatus
from typing import Any, Dict, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.auth_response import AuthResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    *,
    bearer: str,
) -> Dict[str, Any]:
    headers: Dict[str, Any] = {}
    headers["Bearer"] = bearer

    _kwargs: Dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/auth",
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, AuthResponse, HTTPValidationError]]:
    if response.status_code == HTTPStatus.CREATED:
        response_201 = AuthResponse.from_dict(response.json())

        return response_201
    if response.status_code == HTTPStatus.UNAUTHORIZED:
        response_401 = cast(Any, None)
        return response_401
    if response.status_code == HTTPStatus.BAD_REQUEST:
        response_400 = cast(Any, None)
        return response_400
    if response.status_code == HTTPStatus.UNPROCESSABLE_CONTENT:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Any, AuthResponse, HTTPValidationError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    bearer: str,
) -> Response[Union[Any, AuthResponse, HTTPValidationError]]:
    """Auth

     Generates new JWT access token. Expiration of token is 5 minutes.

    Another access token can only be requested once the previous token expires.

    Authenticate requests by including a header: `Bearer: <access-token>`.

    Args:
        bearer (str): Refresh token obtained during access request

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, AuthResponse, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        bearer=bearer,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    bearer: str,
) -> Optional[Union[Any, AuthResponse, HTTPValidationError]]:
    """Auth

     Generates new JWT access token. Expiration of token is 5 minutes.

    Another access token can only be requested once the previous token expires.

    Authenticate requests by including a header: `Bearer: <access-token>`.

    Args:
        bearer (str): Refresh token obtained during access request

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, AuthResponse, HTTPValidationError]
    """

    return sync_detailed(
        client=client,
        bearer=bearer,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    bearer: str,
) -> Response[Union[Any, AuthResponse, HTTPValidationError]]:
    """Auth

     Generates new JWT access token. Expiration of token is 5 minutes.

    Another access token can only be requested once the previous token expires.

    Authenticate requests by including a header: `Bearer: <access-token>`.

    Args:
        bearer (str): Refresh token obtained during access request

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, AuthResponse, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        bearer=bearer,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    bearer: str,
) -> Optional[Union[Any, AuthResponse, HTTPValidationError]]:
    """Auth

     Generates new JWT access token. Expiration of token is 5 minutes.

    Another access token can only be requested once the previous token expires.

    Authenticate requests by including a header: `Bearer: <access-token>`.

    Args:
        bearer (str): Refresh token obtained during access request

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, AuthResponse, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            client=client,
            bearer=bearer,
        )
    ).parsed
