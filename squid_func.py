#!/usr/bin/env python
# -*- coding:utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import re
import config
import commands
import datetime
import logging

# 传入的kuaidaili_ip是一个list：[ip1:port1 , ip2:port2 , ....]
def generate_squid_content(result_ips):
    update_content = ""
    for i, proxy in enumerate(result_ips):
        if proxy:
            ip_port = proxy.split(",")[0]
            update_content += "cache_peer {ip} parent {port} 0 no-query weighted-round-robin weight=1 connect-fail-limit=2 allow-miss max-conn=5 name={ip}{name}\n".format(
                ip=ip_port.split(":")[0],
                port=ip_port.split(":")[1],
                name=i,
            )
    return update_content


# 更新squid conf文件的内容，即ip
def update_squid_conf(result_ips,path):
    squid_content = ""
    with open(path, "rb") as f:
        squid_content = f.read()
        f.close()
    proxy_group = re.findall("cache_peer \d+[\W|\w]+(?=never_direct)", squid_content)[0]
    update_content = generate_squid_content(result_ips)
    # 将旧的内容换成新的内容，重新写入到suqid conf中
    res = re.sub(proxy_group, update_content, squid_content)
    with open(path, "wb") as f:
        f.write(res)
        f.close()

def reload_squid(result_ips):
    squid_proxy_file_path = config.squid_proxy_file_path
    # 像在/etc下的路径还需要root的权限去执行，应先调整好相关的权限
    update_squid_conf(result_ips, squid_proxy_file_path)

    # reload squid
    cmd = "/etc/init.d/squid restart"
    res = commands.getstatusoutput(cmd)
    Date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if res[0] == 0:
        logging.info("%s:tingyun squid重启成功." % Date)
    else:
        logging.info("%s:tingyun squid重启失败." % Date)