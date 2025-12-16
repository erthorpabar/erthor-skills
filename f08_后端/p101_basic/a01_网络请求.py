''' 
ip ->  请求工具 -> 传输协议 -> 解析格式

1 ip 和 端口
- ip 
- ip = 192.168.123.123:8080 代表电脑再网络世界中的位置
- 端口号 8080 代表电脑中程序的位置
127.0.0.1:8080 代表服务只能在本机访问
0.0.0.0:8080 代表服务对所有网络开放
- 域名 = http://aaa.com
- 通过 域名 与 ip 绑定 则可通过域名访问到ip地址的服务

2 请求工具
- 浏览器 附带用户电脑信息 
- 代码 模拟浏览器行为 自动化获取数据

3 传输协议
- tcp = 先建立连接 顺序校验 (可靠)
- udp = 无需建立连接 不保证顺序 (快速 实时数据)

4 应用层 解析格式
- http-get (参数放在url中)
- http-post (参数放在请求体中)
    http请求状态码
    200 请求成功
    400 请求错误
    404 资源不存在
    500 服务器内部错误
- websocket (长连接 实时推送)
- http/2 (gRPC基于此协议实现)

''' 

# 导入包
import requests

# get请求
url = "https://jsonplaceholder.typicode.com/posts/1" # 免费测试api
response = requests.get(url)
print('测试get')
print(f"状态码: {response.status_code}")
print(f"响应内容: {response.json()}")

# post请求
url = "https://jsonplaceholder.typicode.com/posts" # 免费测试api
data = {"title": "测试标题", "body": "测试内容", "userId": 2}
response = requests.post(url, json=data)
print('测试post')
print(f"状态码: {response.status_code}")
print(f"响应内容: {response.json()}")