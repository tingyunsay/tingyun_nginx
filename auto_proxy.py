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
from config import *
import kuaidaili_func
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



# 获取已经验证过的res，格式为：ip值 from
def get_res_ip(res_file_path):
    with open("%s"%res_file_dir, "rb") as f:
        kuaidaili_ip = f.read()
        f.close()
    res = []
    exists_ips = kuaidaili_ip.split("\n")
    exists_ips.remove('')
    if exists_ips != ['']:
        map(lambda x: res.append({
            "ip":x.split("\t")[0],
            "from":x.split("\t")[1]
        }), exists_ips)
        return res
    else:
        return []

# 时间合适的写入到文件中 proxy\tfrom , 后续可更改策略到缓存中或者其他地方
def test_is_good(item):
    proxy = item['ip']
    From = item['from']
    # command = "curl -o /dev/null -s -w '%{time_total}' 'http://baidu.com' --connect-timeout 1.5 -m 1.5 -x {proxy}".format(proxy=proxy,time_total="{time_total}")
    
    #弃用这种curl的方法，因为很多代理即便是失效的，也会返回200
    #command = "curl -A \"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36\" -I -s \"http://www.happyjuzi.com\" -x%s -m1 | awk '(NR==1){if($2==200)print 1}' | wc -l" % proxy
    #res = commands.getstatusoutput(command)
    
    #读取配置文件中相关配置，并进行访问测试
    res = False
    for k, v in TARGET_CONFIG.items():
        try:
            logging.info("当前测试站点为:%s"%k)
            res = requests.get(v['url'],headers=v['headers'],proxies={"http":"http://%s"%proxy},timeout=6)
        except Exception,e:
            #一旦其中某个站点失败，置换res成False，且break
            logging.info("站点:%s访问失败，失败原因如下:%s，此ip:%s不可用，跳出..."%(k,e,proxy))
            res = False
            break

    if proxy and len(proxy) <= 21:
        # 片段二
        # 上面返回1的，直接认为可用，后续可以添加其他网站：如xiami，163music，douban等等
        # 不再去验证了（老的策略还需要验证响应时间）
        # 测试时间命令为：curl -o /dev/null -s -w '%{time_total}' 'www.baidu.com' -x ip:port
        if res and res.status_code==200:
            logging.info("ip:%s可用，加入结果集中."%proxy)
            return "%s\t%s"%(proxy,From)
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




def update_nginx_conf(kuaidaili_ip, path):
    proxy_path = path
    with open(proxy_path) as f:
        content = f.read()
        f.close()
    new_ip = kuaidaili_func.generate_nginx_content(kuaidaili_ip)
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
            RESULT.append(test_is_good(item))
            self.queue.task_done()



def main(url):
    update_squid_conf()


if __name__ == '__main__':
    #结果文件路径
    if commands.getstatusoutput("touch %s" % res_file_dir)[0] != 0:
        logging.error("结果文件touch失败，请检查路径是否存在!")
        exit()
    for k,v in API_CONFIG.items():
        if k == "kuaidaili" and v['use']:
            url = kuaidaili_func.get_kuaiurl(v['order_id'],num=20, protocol=1, area="", method=1, quality=0)
            # 直接用url得到的ip和现有的ip得到一个去重的结果，再统一丢去认证
            all_ip = kuaidaili_func.get_notverify_ip(url) + get_res_ip(res_file_dir)
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
            with open("%s"%res_file_dir, "wb") as f:
                content = ""
                for i in result:
                    if i is not None and i is not '':
                        content += i + "\n"
                f.write(content)
                f.close()

            str1 = "代理来源为：1，总共验证了 %d , 其中有效代理为 %s 个." % (len(all_ip), len(get_res_ip(res_file_dir)))
            logging.info(str1)
            str2 = "耗时 %s s" % (str(now - pre))
            logging.info(str2)
        elif k == "xundaili" and v['use']:
            pass

        nginx_proxy_upstream_file_path = nginx_proxy_upstream_file_path
        # 像在/etc下的路径还需要root的权限去执行，应先调整好相关的权限
        result_ips = list(set([x['ip'] for x in get_res_ip(res_file_dir)]))
        update_nginx_conf(result_ips, nginx_proxy_upstream_file_path)

        # reload nginx
        # cmd = "/home/work/liaohong/odp/webserver/loadnginx.sh reload"
        cmd = "/usr/sbin/nginx -s reload"
        res = commands.getstatusoutput(cmd)
        Date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if res[0] == 0:
            # logging.info("odp nginx重启成功.")
            logging.info("%s:tingyun nginx重启成功."%Date)
        else:
            # logging.warning("odp nginx重启失败.")
            logging.info("%s:tingyun nginx重启失败."%Date)

