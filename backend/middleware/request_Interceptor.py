#!/usr/bin/env python
# coding:utf-8
# __time__: 2021/3/23 14:33
# __author__ = 'ren_mcc'

import typing

from starlette.datastructures import URL, Headers
from starlette.responses import PlainTextResponse, RedirectResponse, Response
from starlette.types import ASGIApp, Receive, Scope, Send

ENFORCE_DOMAIN_WILDCARD = "Domain wildcard patterns must be like '*.example.com'."


class DocMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        allowed_hosts: typing.List[str] = None,
    ) -> None:
        if allowed_hosts is None:
            allowed_hosts = ["*"]
        self.app = app
        self.allowed_hosts = list(allowed_hosts)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        headers = Headers(scope=scope)
        host = headers.get("host", "").split(":")[0]
        if "*" in self.allowed_hosts:
            await self.app(scope, receive, send)
        elif host in self.allowed_hosts:
            await self.app(scope, receive, send)
        else:
            response = PlainTextResponse("访问拒绝", status_code=400)
            await response(scope, receive, send)

