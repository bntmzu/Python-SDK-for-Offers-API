from http import HTTPStatus
from typing import Any, Dict, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.register_product_request import RegisterProductRequest
from ...models.register_product_response import RegisterProductResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: RegisterProductRequest,
    bearer: Union[Unset, str] = UNSET,
) -> Dict[str, Any]:
    headers: Dict[str, Any] = {}
    if not isinstance(bearer, Unset):
        headers["Bearer"] = bearer

    _kwargs: Dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/products/register",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, RegisterProductResponse]]:
    if response.status_code == HTTPStatus.CREATED:
        response_201 = RegisterProductResponse.from_dict(response.json())

        return response_201
    if response.status_code == HTTPStatus.UNAUTHORIZED:
        response_401 = cast(Any, None)
        return response_401
    if response.status_code == HTTPStatus.CONFLICT:
        response_409 = cast(Any, None)
        return response_409
    if response.status_code == HTTPStatus.UNPROCESSABLE_CONTENT:
        response_422 = cast(Any, None)
        return response_422
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Any, RegisterProductResponse]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: RegisterProductRequest,
    bearer: Union[Unset, str] = UNSET,
) -> Response[Union[Any, RegisterProductResponse]]:
    """Register Product

     Register a new product.

    Args:
        bearer (Union[Unset, str]): Access token from the auth endpoint.
        body (RegisterProductRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, RegisterProductResponse]]
    """

    kwargs = _get_kwargs(
        body=body,
        bearer=bearer,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    body: RegisterProductRequest,
    bearer: Union[Unset, str] = UNSET,
) -> Optional[Union[Any, RegisterProductResponse]]:
    """Register Product

     Register a new product.

    Args:
        bearer (Union[Unset, str]): Access token from the auth endpoint.
        body (RegisterProductRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, RegisterProductResponse]
    """

    return sync_detailed(
        client=client,
        body=body,
        bearer=bearer,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: RegisterProductRequest,
    bearer: Union[Unset, str] = UNSET,
) -> Response[Union[Any, RegisterProductResponse]]:
    """Register Product

     Register a new product.

    Args:
        bearer (Union[Unset, str]): Access token from the auth endpoint.
        body (RegisterProductRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, RegisterProductResponse]]
    """

    kwargs = _get_kwargs(
        body=body,
        bearer=bearer,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: RegisterProductRequest,
    bearer: Union[Unset, str] = UNSET,
) -> Optional[Union[Any, RegisterProductResponse]]:
    """Register Product

     Register a new product.

    Args:
        bearer (Union[Unset, str]): Access token from the auth endpoint.
        body (RegisterProductRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, RegisterProductResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            bearer=bearer,
        )
    ).parsed
