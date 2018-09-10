#!/usr/bin/env python
# -*- coding:utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')

#添加测试用例的headers
#目标站点为：key，其相关配置为value。程序会使用同一个代理ip，不间断地去访问以下配置中的所有站点，任何一个返回不是200，即认为此代理不可用
TARGET_CONFIG = {
    "163":{
        "url":"http://music.163.com/artist/album?id=6452",
        "headers":{
            "User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36",
            "Referer":"http://music.163.com/"
        }
    }
}
#保存验证结果的文件路径，可用的ip都会先被记录到这个文件中，下次作为原料继续用来测试验证
res_file_dir = "/home/cas_docking/squid_proxy/tingyun_nginx/res.txt"
#程序验证完会：生成的nginx代理的文件路径
#nginx_proxy_upstream_file_path = "/etc/nginx/proxy_upstream.conf"
nginx_proxy_upstream_file_path = "/home/company_gitlab/odp/webserver/conf/proxy_upstream.conf"


#squid需要替换的配置文件路径
squid_proxy_file_path = "/etc/squid/squid.conf"

#此处提供一致的服务商的api接口配置，只需要填入对应的参数如订单号，不需要修改主程序代码
#若需要使用某个服务商，即可在其key值中的use值置换成1，这里我们使用kuaidaili
API_CONFIG = {
    "kuaidaili":{
        "order_id":"快代理的订单号",
        "use":1,
        #ip来源
        "from":1
    },
    "xundaili":{
        "order_id":"讯代理的订单号",
        "use":0,
        "from":2,
        "spiderid":"讯代理特有的spiderid"
    }

}
