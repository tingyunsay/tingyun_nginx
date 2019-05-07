#!/usr/bin/env python2
# -*- coding:utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')
sys.path.append('../../')
import requests
import logging
from tingyun_nginx.config import *

#迅代理相关方法

def get_url(orderid, spiderid):
    base_url = "http://api.xdaili.cn/xdaili-api//greatRecharge/getGreatIp?spiderId={spiderid}&orderno={orderid}&returnType=2&count=5".format(
        spiderid=spiderid,
        orderid=orderid
    )
    return base_url


#获取未验证的ip
def get_notverify_ip(url):
    try:
        res_json = requests.get(url).json()
    except Exception, e:
        logging.warning("讯代理接口获取失败，请检查服务，错误信息为:%s"%e)
        exit()
    kuaidaili_ip = res_json['RESULT']
    res = []
    for i in kuaidaili_ip:
        temp = {}
        temp['from'] = API_CONFIG['xundaili']['from']
        temp['ip'] = "%s:%s"%(i['ip'],i['port'])
        res.append(temp)
    return res

if __name__ == '__main__':
    url = get_url(API_CONFIG['xundaili']['order_id'], API_CONFIG['xundaili']['spiderid'])
    get_notverify_ip(url)
