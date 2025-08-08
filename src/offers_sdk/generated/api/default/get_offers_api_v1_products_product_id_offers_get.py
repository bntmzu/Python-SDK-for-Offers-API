from http import HTTPStatus
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union
from typing import cast

import httpx

from ... import errors
from ...client import AuthenticatedClient
from ...client import Client
from ...models.offer_response import OfferResponse
from ...types import UNSET
from ...types import Response
from ...types import Unset


def _get_kwargs(
    product_id: str,
    *,
    bearer: Union[Unset, str] = UNSET,
) -> Dict[str, Any]:
    headers: Dict[str, Any] = {}
    if not isinstance(bearer, Unset):
        headers["Bearer"] = bearer

    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": f"/api/v1/products/{product_id}/offers",
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, List["OfferResponse"]]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = OfferResponse.from_dict(response_200_item_data)

            response_200.append(response_200_item)

        return response_200
    if response.status_code == HTTPStatus.UNAUTHORIZED:
        response_401 = cast(Any, None)
        return response_401
    if response.status_code == HTTPStatus.NOT_FOUND:
        response_404 = cast(Any, None)
        return response_404
    if response.status_code == HTTPStatus.UNPROCESSABLE_CONTENT:
        response_422 = cast(Any, None)
        return response_422
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Any, List["OfferResponse"]]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    product_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    bearer: Union[Unset, str] = UNSET,
) -> Response[Union[Any, List["OfferResponse"]]]:
    """Get Offers

     Get offers for an existing product by ID.

    Args:
        product_id (str):
        bearer (Union[Unset, str]): Access token from the auth endpoint.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, List['OfferResponse']]]
    """

    kwargs = _get_kwargs(
        product_id=product_id,
        bearer=bearer,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    product_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    bearer: Union[Unset, str] = UNSET,
) -> Optional[Union[Any, List["OfferResponse"]]]:
    """Get Offers

     Get offers for an existing product by ID.

    Args:
        product_id (str):
        bearer (Union[Unset, str]): Access token from the auth endpoint.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, List['OfferResponse']]
    """

    return sync_detailed(
        product_id=product_id,
        client=client,
        bearer=bearer,
    ).parsed


async def asyncio_detailed(
    product_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    bearer: Union[Unset, str] = UNSET,
) -> Response[Union[Any, List["OfferResponse"]]]:
    """Get Offers

     Get offers for an existing product by ID.

    Args:
        product_id (str):
        bearer (Union[Unset, str]): Access token from the auth endpoint.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, List['OfferResponse']]]
    """

    kwargs = _get_kwargs(
        product_id=product_id,
        bearer=bearer,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    product_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    bearer: Union[Unset, str] = UNSET,
) -> Optional[Union[Any, List["OfferResponse"]]]:
    """Get Offers

     Get offers for an existing product by ID.

    Args:
        product_id (str):
        bearer (Union[Unset, str]): Access token from the auth endpoint.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, List['OfferResponse']]
    """

    return (
        await asyncio_detailed(
            product_id=product_id,
            client=client,
            bearer=bearer,
        )
    ).parsed
