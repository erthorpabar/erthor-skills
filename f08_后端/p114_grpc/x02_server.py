import x01_pb2_grpc
import asyncio
class sss(x01_pb2_grpc.xyzServicer): # 继承定义的服务 然后实现接口
    async def Search(self, request, context):
        # 获取输入
        v = request.x

        # 处理逻辑
        v = v + "123"
        # 模拟阻塞
        await asyncio.sleep(1)

        # 构造返回数据
        import x01_pb2
        response = x01_pb2.out_message()

        response.var = v
        response.list.extend(["1", "2", "3"])
        response.dict.update({"a": "1", "b": "2", "c": "3"})

        # 返回
        return response
    
from concurrent.futures import ThreadPoolExecutor
import grpc
async def main():
    server = grpc.aio.server(ThreadPoolExecutor(max_workers=10))
    x01_pb2_grpc.add_xyzServicer_to_server(sss(), server)
    server.add_insecure_port('0.0.0.0:50051')
    await server.start()
    print("grpc Server started on port 50051")
    await server.wait_for_termination() # 循环并开始等待

if __name__ == "__main__":
    asyncio.run(main())