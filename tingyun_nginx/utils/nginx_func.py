#!/usr/bin/env python2
# -*- coding:utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import re
import config
import commands
import datetime
import logging


# 传入的result_ips是一个list：[ip1:port1 , ip2:port2 , ....]
def generate_nginx_content(result_ips):
    update_content = ""
    for proxy in result_ips:
        if proxy:
            ip_port = proxy.split(",")[0]
            update_content += "server {ip}:{port} weight=1 max_fails=2 fail_timeout=500s;\n".format(
                ip=ip_port.split(":")[0],
                port=ip_port.split(":")[1]
            )

    return update_content

def update_nginx_conf(result_ips, path):
    proxy_path = path
    with open(proxy_path) as f:
        content = f.read()
        f.close()
    new_ip = generate_nginx_content(result_ips)
    content = "upstream  proxy_upstream {\n" + new_ip + "}"
    with open(proxy_path, "wb") as f:
        f.write(content)
        f.close()

#写入配置文件并重启nginx
def reload_nginx(result_ips):
    nginx_proxy_upstream_file_path = config.nginx_proxy_upstream_file_path
    # 像在/etc下的路径还需要root的权限去执行，应先调整好相关的权限
    update_nginx_conf(result_ips, nginx_proxy_upstream_file_path)

    # reload nginx
    # 注：odp的nginx在reload之前必须要start
    cmd = "/home/company_gitlab/odp/webserver/loadnginx.sh reload"
    #cmd = "/usr/sbin/nginx -s reload"
    res = commands.getstatusoutput(cmd)
    Date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if res[0] == 0:
        # logging.info("odp nginx重启成功.")
        logging.info("%s:tingyun nginx重启成功." % Date)
    else:
        # logging.warning("odp nginx重启失败.")
        logging.info("%s:tingyun nginx重启失败." % Date)
