import logging
from time import time
from typing import NoReturn, Optional

from fastapi import HTTPException, Request
from httpx import AsyncClient
from httpx_oauth.clients.openid import OpenID
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import PlainTextResponse

from app.helpers.interfaces.middleware import MiddlewareAbc


class KeycloakMiddleware(MiddlewareAbc):
    def __init__(
        self,
        middleware_class: type[BaseHTTPMiddleware],
        server_url: str,
        realm_name: str,
        configuration_endpoint: str,
        client_id: str,
        client_secret_key: str,
        logger: logging.Logger = None,
    ) -> NoReturn:
        super().__init__(middleware_class, logger)
        self.server_url = server_url
        self.configuration_endpoint = configuration_endpoint
        self.realm_name = realm_name
        self.client_id = client_id
        self.client_secret_key = client_secret_key

    def get_keycloak_openid_oauth(self) -> OpenID:
        configuration_endpoint = self.configuration_endpoint.format(
            real_name=self.realm_name,
        )
        return OpenID(
            client_id=self.client_id,
            client_secret=self.client_secret_key,
            openid_configuration_endpoint=f"{self.server_url}{configuration_endpoint}",
        )

    async def fetch_userinfo(self, token: str) -> dict:
        openid_data = self.get_keycloak_openid_oauth()
        async with AsyncClient() as client:
            response = await client.get(
                openid_data.openid_configuration["userinfo_endpoint"],
                headers={"Authorization": f"Bearer {token}"},
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 403:
                raise HTTPException(status_code=403, detail={"Forbidden"})
            response.raise_for_status()

    async def __call__(self, request: Request, call_next):
        start = time()
        token = request.cookies.get("access_token")
        if not token:
            return PlainTextResponse(status_code=401, content="Authorization token missing")
        try:
            user_info = await self.fetch_userinfo(token)
            token_info = await self.get_token_info(token)
            roles = token_info.get("scope", "").split()
        except Exception as e:
            return PlainTextResponse(status_code=403, content=f"Forbidden, error{e}")

        request.scope["user_roles"] = roles
        request.scope["user_info"] = user_info
        response = await call_next(request)
        self.logger.info(f"Request took {time() - start:.2f} seconds")
        return response

    async def get_token_info(self, token: str) -> Optional[dict]:
        openid_data = self.get_keycloak_openid_oauth()
        async with AsyncClient() as client:
            response = await client.post(
                openid_data.openid_configuration["introspection_endpoint"],
                data={
                    "token": token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret_key,
                },
            )

            if response.status_code == 200:
                token_info = response.json()
                if token_info.get("active"):
                    return token_info
                else:
                    return None
            else:
                self.logger.error(f"Error validating token: {response.text}")
                return None
