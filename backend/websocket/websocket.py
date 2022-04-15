#!/usr/bin/env python
# coding:utf-8
# __time__: 2021/3/23 13:11
# __author__ = 'ren_mcc'


from starlette.endpoints import WebSocketEndpoint


class Echo(WebSocketEndpoint):
    encoding = "text"

    # 连接
    async def on_connect(self, web_socket):
        await web_socket.accept()

    # 消息
    async def on_receive(self, web_socket, data):
        print(data)
        await web_socket.send_text(f"Message text was: {data}")

    # 断开
    async def on_disconnect(self, web_socket, close_code):
        pass
