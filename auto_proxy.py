#!/usr/bin/env python
# -*- coding:utf-8 -*-
import sys

reload(sys)
sys.setdefaultencoding('utf8')
import requests
import re
import commands
import time, signal
import signal, functools
import sys, threading
from multiprocessing import Pool
import datetime
from threading import Thread
from Queue import Queue
import logging
import requests
import socket

# author  tingyun  2017-12-07

file_name = __file__.split('/')[-1].replace(".py", "")
# 运行过程中的日志文件在执行目录下的lyric_test.log中
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s [line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='%s.log' % file_name,
                    filemode='a')

# 将日志打印到标准输出（设定在某个级别之上的错误）
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

RESULT = []

# 这个锁加的貌似有点瑕疵
m = threading.Lock()


# 获取未验证的ip
def get_notverify_ip(url):
    try:
        content = requests.get(url).content
    except Exception, e:
        logging.warning("快代理接口获取失败，请检查服务")
    kuaidaili_ip = content.split("\n")
    return kuaidaili_ip


# 获取验证过的res
def get_res_ip(res_file_path):
    with open("%s"%res_file_dir, "rb") as f:
        kuaidaili_ip = f.read()
        f.close()
    res = []
    kuaidaili_ip = filter(lambda x: x, kuaidaili_ip.split("\n"))
    return kuaidaili_ip


# 时间合适的写入到文件中 proxy:speed , 后续可更改策略到缓存中或者其他地方
def test_is_goof(ip):
    proxy = ip
    # command = "curl -o /dev/null -s -w '%{time_total}' 'http://baidu.com' --connect-timeout 1.5 -m 1.5 -x {proxy}".format(proxy=proxy,time_total="{time_total}")
    command = "curl -A \"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36\" -I -s \"http://www.happyjuzi.com\" -x%s -m1 | awk '(NR==1){if($2==200)print 1}' | wc -l" % proxy
    res = commands.getstatusoutput(command)
    if proxy and len(proxy) <= 21:
        # 片段二
        # 上面返回1的，直接认为可用，后续可以添加其他网站：如xiami，163music，douban等等
        # 不再去验证了（老的策略还需要验证响应时间）
        # 测试时间命令为：curl -o /dev/null -s -w '%{time_total}' 'www.baidu.com' -x ip:port
        if res[1] == '1':
            return proxy
        else:
            return None


# 传入的kuaidaili_ip是一个list：[ip1:port1 , ip2:port2 , ....]
def generate_squid_content(kuaidaili_ip):
    update_content = ""
    for i, proxy in enumerate(kuaidaili_ip):
        if proxy:
            ip_port = proxy.split(",")[0]
            update_content += "cache_peer {ip} parent {port} 0 no-query weighted-round-robin weight=1 connect-fail-limit=2 allow-miss max-conn=5 name={ip}{name}\n".format(
                ip=ip_port.split(":")[0],
                port=ip_port.split(":")[1],
                name=i,
            )

    return update_content


# 更新squid conf文件的内容，即ip
def update_squid_conf(kuaidaili_ip):
    squid_content = ""
    with open("/etc/squid/squid.conf", "rb") as f:
        squid_content = f.read()
        f.close()
    proxy_group = re.findall("cache_peer \d+[\W|\w]+(?=never_direct)", squid_content)[0]

    update_content = generate_squid_content(kuaidaili_ip)
    # 将旧的内容换成新的内容，重新写入到suqid conf中
    res = re.sub(proxy_group, update_content, squid_content)
    with open("/etc/squid/squid.conf", "wb") as f:
        f.write(res)
        f.close()


# 传入的kuaidaili_ip是一个list：[ip1:port1 , ip2:port2 , ....]
def generate_nginx_content(kuaidaili_ip):
    update_content = ""
    for proxy in kuaidaili_ip:
        if proxy:
            ip_port = proxy.split(",")[0]
            update_content += "server {ip}:{port} weight=1 max_fails=2 fail_timeout=500s;\n".format(
                ip=ip_port.split(":")[0],
                port=ip_port.split(":")[1]
            )

    return update_content


def update_nginx_conf(kuaidaili_ip, path):
    proxy_path = path
    with open(proxy_path) as f:
        content = f.read()
        f.close()
    new_ip = generate_nginx_content(kuaidaili_ip)
    content = "upstream  proxy_upstream {\n" + new_ip + "}"
    with open(proxy_path, "wb") as f:
        f.write(content)
        f.close()


class ThreadWorker(Thread):
    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue
        self.result = []

    def run(self):
        while True:
            item = self.queue.get()
            if item is None:
                break
            RESULT.append(test_is_goof(item))
            self.queue.task_done()


# anonymous_level  默认为高匿名度的代理:ha -- high 高匿 , an -- 匿名 , tr -- 透明 , 可以重叠，按照；切分，如：an_ha;an_an
# protocol  默认为https(同时支持http)的代理，支持后续改造，两者分类取
# area      默认不限制，我们一般不需要国外的暂时，中国
# method    默认为支持post(同时也支持get)，后续改造，分成两类，按需取
# sep       取得结果中的分割符号，1-\r\n, 2-\n, 3-空格, 4-|
# 支持的浏览器有： chrom/IE/360/Firefox
# 由于本地还需要做一次验证，就不取对方接口中按照速度返回的了，这个速度不是实时的速度，而是他们扫描时候获取的速度，无参考价值
def get_kuaiurl(orderid, num, anonymous_level="an_ha", protocol=2, area="中国", method=2, sep=2, quality=1):
    #base_url = "http://dev.kuaidaili.com/api/getproxy?b_iphone=1&"
    base_url = "http://dev.kuaidaili.com/api/getproxy?"
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


def main(url):
    update_squid_conf()


if __name__ == '__main__':
    res_file_dir = "/home/cas_docking/squid_proxy/res.txt"
    commands.getoutput("touch %s"%res_file_dir)
    url = get_kuaiurl("快代理的订单号",num=2000, protocol=1, area="", method=1, quality=0)
    # 直接用url得到的ip和现有的ip得到一个去重的结果，再统一丢去认证
    all_ip = list(set(get_notverify_ip(url) + get_res_ip(res_file_dir)))
    all_ip = filter(lambda x: x, all_ip)
    pre = time.time()

    queue = Queue()
    good_id = []
    for x in range(20):
        worker = ThreadWorker(queue)
        worker.daemon = True
        worker.start()
    
    fuck = []
    for task in all_ip:
        queue.put(task)
    queue.join()
    now = time.time()
    result = filter(lambda x: x, RESULT)
    # print "有效代理共有 %s"%str(len(result))
    with open("%s"%res_file_dir, "wb") as f:
        content = ""
        for i in result:
            if i is not None and i is not '':
                content += i + "\n"
        f.write(content)
        f.close()

    str1 = "总共验证了 %d , 其中有效代理为 %s 个." % (len(all_ip), len(get_res_ip()))
    logging.info(str1)
    str2 = "耗时 %s s" % (str(now - pre))
    logging(str2)

    nginx_proxy_upstream_file_path = "/etc/nginx/proxy_upstream.conf"
    # 像在/etc下的路径还需要root的权限去执行，应先调整好相关的权限
    # update_nginx_conf(get_res_ip(),"/home/work/liaohong/odp/webserver/conf/proxy_upstream.conf")
    update_nginx_conf(get_res_ip(), nginx_proxy_upstream_file_path)

    # reload nginx
    # cmd = "/home/work/liaohong/odp/webserver/loadnginx.sh reload"
    cmd = "/usr/sbin/nginx -s reload"
    res = commands.getstatusoutput(cmd)
    if res[0] == 0:
        # logging.info("odp nginx重启成功.")
        print "tingyun nginx重启成功."
    else:
        # logging.warning("odp nginx重启失败.")
        print "tingyun nginx重启失败."

