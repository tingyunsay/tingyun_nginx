#!/usr/bin/env python2
# -*- coding:utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import requests
import logging
from config import *

#快代理相关方法


# anonymous_level  默认为高匿名度的代理:ha -- high 高匿 , an -- 匿名 , tr -- 透明 , 可以重叠，按照；切分，如：an_ha;an_an
# protocol  默认为https(同时支持http)的代理，支持后续改造，两者分类取
# area      默认不限制，我们一般不需要国外的暂时，中国
# method    默认为支持post(同时也支持get)，后续改造，分成两类，按需取
# sep       取得结果中的分割符号，1-\r\n, 2-\n, 3-空格, 4-|
# 支持的浏览器有： chrom/IE/360/Firefox
# 由于本地还需要做一次验证，就不取对方接口中按照速度返回的了，这个速度不是实时的速度，而是他们扫描时候获取的速度，无参考价值
def get_kuaiurl(orderid, num, anonymous_level="an_ha", protocol=2, area="中国", method=2, sep=2, quality=1):
    base_url = "http://dev.kdlapi.com/api/getproxy?"
    anonymous = ""
    for i in [x for x in anonymous_level.split(";")]:
        if i:
            anonymous += (i + "=1&")
    url = base_url + "orderid={orderid}&num={num}&protocol={protocol}&area={area}&method={method}&{anonymous}&quality={quality}".format(
        orderid=orderid,
        num=num,
        protocol=protocol,
        area=area,
        method=method,
        anonymous=anonymous,
        quality=quality,
    )
    return url


#获取未验证的ip
def get_notverify_ip(url):
    try:
        content = requests.get(url).content
    except Exception, e:
        logging.warning("快代理接口获取失败，请检查服务")
        exit()
    kuaidaili_ip = set(content.split("\n"))
    res = []
    for i in kuaidaili_ip:
        temp = {}
        temp['from'] = API_CONFIG['kuaidaili']['from']
        temp['ip'] = i
        res.append(temp)
    return res

