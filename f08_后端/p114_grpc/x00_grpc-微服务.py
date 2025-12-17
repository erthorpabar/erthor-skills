''' 
# 微服务
grpc (google remote process call)

# 官网
https://grpc.io/

# 源码
https://github.com/grpc/grpc

# grpc 异步api
https://grpc.github.io/grpc/python/grpc_asyncio.html


# 
pip install grpcio
pip install grpcio-tools

# proto -> py 代码
-I. 表示proto文件在当前文件夹
--python_out=. 仅包含数据结构py代码
--grpc_python_out=. 包含grpc服务

# 生成配置文件
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. x01.proto

x01.proto -> x01_pb2.py 和 x01_pb2_grpc.py -> 定义 输入 输出
x02_server.py -> 定义 异步 和 数据处理逻辑
x03_test.ipynb -> 测试 异步发起请求
'''