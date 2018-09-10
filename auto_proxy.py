#!/usr/bin/env python
# -*- coding:utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import commands
import time
import threading
from multiprocessing import Pool
from threading import Thread
from Queue import Queue
import logging
import requests
from config import *
import config
import kuaidaili_func
import nginx_func
import squid_func
import xundaili_func

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
        if res and res.status_code==200:
            logging.info("ip:%s可用，加入结果集中."%proxy)
            return "%s\t%s"%(proxy,From)
        else:
            return None

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

if __name__ == '__main__':
    #结果文件路径
    if commands.getstatusoutput("touch %s" % res_file_dir)[0] != 0:
        logging.error("结果文件touch失败，请检查路径是否存在!")
        #exit()
    for k,v in API_CONFIG.items():
        if k == "kuaidaili" and v['use']:
            url = kuaidaili_func.get_kuaiurl(v['order_id'],num=20, protocol=1, area="", method=1, quality=0)
            all_ip = kuaidaili_func.get_notverify_ip(url) + get_res_ip(res_file_dir)
            all_ip = filter(lambda x: x, all_ip)
        elif k == "xundaili" and v['use']:
            #暂时设定为一次提取五个，计算下并发再看看需要多少
            url = xundaili_func.get_url(API_CONFIG['xundaili']['order_id'],API_CONFIG['xundaili']['spiderid'])
            all_ip = xundaili_func.get_notverify_ip(url) + get_res_ip(res_file_dir)
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

    #结果文件，供nginx或squid使用
    result_ips = list(set([x['ip'] for x in get_res_ip(res_file_dir)]))

    #重启squid，重启时间长
    #squid_func.reload_squid(result_ips)

    #重启nginx
    nginx_func.reload_nginx(result_ips)
