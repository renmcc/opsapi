#!/usr/bin/env python
# coding:utf-8
# __time__: 2021/2/24 13:14
# __author__ = 'ren_mcc'


str = "缁甸槼璞櫉鐢垫皵鏈夐檺鍏徃"
aaa = str.encode()

print(aaa)


unicod = "\u7f01\u7538\u69fc\u749e\ue045\u6ac9\u9422\u57ab\u76b5\u93c8\u5910\u6aba\u934f\ue100\u5f83"

print(unicod.encode("utf8").decode())