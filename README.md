# tingyun_nginx
自动代理切换脚本，nginx正向代理配置，暂时支持的平台只有快代理，如果使用到了新的服务商，再更新对应的接口服务，做成一体化.  
注：
nginx正向代理还存在一些问题：如400错误没法自动重试，使用squid则没有这个问题（但是squid也存在其他问题）

## nginx代理自动切换
### 一
使用nginx 1.5.0以上版本最为好，因为有403失败自动重试，之前的版本都是没有的
nginx版本变更说明如下：

![啦啦啦](https://github.com/tingyunsay/tingyun_nginx/raw/master/img/version_change.png)
### 二
注：二中的所有配置都在nginx的根目录下
nginx配置文件如下：
```text
#在/etc/nginx/nginx.conf中添加如下行

include proxy/*.conf;
```
执行如下命令
```text
cd /etc/nginx/

mkdir proxy
cd proxy

touch proxy.conf
touch proxy_upstream.conf
```
其中proxy.conf配置好相关的端口和日志路径，网页异常处理等
```text
server  {
    listen 0.0.0.0:9112;

    access_log  logs/proxy/access.log  main;
    error_log  logs/proxy/error.log;
    error_page  404  /static/html/404.html;

    proxy_connect_timeout 8s;
    proxy_send_timeout 8s;
    proxy_read_timeout 8s;
    location / {
        proxy_connect_timeout 10;
        proxy_buffers 256 4k;
        proxy_max_temp_file_size 0;
        proxy_set_header Host $http_host;
        
        error_page 403 /dealwith_500;
        error_page 302 /dealwith_500;

        proxy_next_upstream http_500 http_502 http_503 http_504 http_403 http_404 error timeout invalid_header;
        proxy_pass http://proxy_upstream;

        proxy_cache_valid 200 302 10m;
        proxy_cache_valid 301 1h;
        proxy_cache_valid any 1m;
    }

    location /dealwith_500 {
    return 500;
    }
}
```
proxy_upstream.conf这个文件默认为空即可，后续程序跑完了会overwrite这个文件
其中保存的格式如下：
```text
upstream  proxy_upstream {
server 115.218.219.182:9000 weight=1 max_fails=2 fail_timeout=500s;
......
｝
```
### 三
购买代理商家所提供接口的数据应该是如下格式：  
　　xxx.xxx.xxx.xxx\n  
　　xxx.xxx.xxx.xxx\n  
　　......  
如果需要自定义切分出单个的ip地址，请修改代码中这一部分：<font color="red">**get_notverify_ip()**</font>中的split("\n")成为你自己的文本格式即可
### 四
需要手动配置的相关文件  
在config.conf中：
```python
res_file_dir = "/home/cas_docking/squid_proxy/res.txt"
```
这个res.txt是用来保存上一次验证成功，可用的ip地址,其会被当成一部分原料，加入到下一次的验证过程中去，和服务商提供的新的代理ip一起被重新验证，得到的新的结果继续保存(overwrite)在其中

```python
nginx_proxy_upstream_file_path = "/etc/nginx/proxy_upstream.conf"
```
以上是你生成的nginx代理的文件路径，需要在系统的nginx配置文件：nginx.conf中引入，在二中有介绍

```python
TARGET_CONFIG = {
    "163":{
        "url":"http://music.163.com/artist/album?id=6452",
        "headers":{
            "User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36",
            "Referer":"http://music.163.com/"
        }
    }
}
```
其中配置的是：目标站点，即你希望程序验证的代理对于哪些目标站点可用。  
可以配置多个，程序会使用代理ip顺序去访问这些url,并附加上对应的haders，任何一个出错，直接认为这个代理ip不可用
### End
上面的步骤都完成之后，再挂上一个crontab任务即可，设定每隔多长时间启动一次，程序运行失败的话，相关报错可以在日志中查看
之后我们使用nginx代理即可了
```python
curl "http://www.baidu.com" -x 127.0.0.1:9112
```
