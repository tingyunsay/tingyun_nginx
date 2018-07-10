#!/usr/bin/env python
# -*- coding:utf-8 -*-
import sys

reload(sys)
sys.setdefaultencoding('utf8')

#添加测试用例的headers
#目标站点为：key，其相关配置为value。程序会使用同一个代理ip，不间断地去访问以下配置中的所有站点，任何一个返回不死200，即认为此代理不可用
TARGET_CONFIG = {
    "163":{
        "url":"http://music.163.com/artist/album?id=6452",
        "headers":{
            "User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36",
            "Referer":"http://music.163.com/"
        }
    }
}

