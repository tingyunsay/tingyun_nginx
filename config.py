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
nginx_proxy_upstream_file_path = "/etc/nginx/proxy_upstream.conf"
