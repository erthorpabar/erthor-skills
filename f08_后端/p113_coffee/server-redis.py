# ——————————当前文件夹路径加入搜索路径——————————
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ——————————加载环境变量——————————
from dotenv import load_dotenv
load_dotenv()

from pydantic_settings import BaseSettings # 优先系统环境变量，然后是.env文件，最后是默认值
class Settings(BaseSettings):
    
    # 🌐 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8188

    # 🔧 任务处理配置  
    MAX_WORKERS: int = 2

    # 🔴 Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = "redis123"  
    
    class Config:
        # 指定从.env文件加载环境变量
        env_file = ".env" # 允许从.env文件加载配置
        env_file_encoding = "utf-8" # 指定编码
        extra = "allow" # 允许额外的没用到的配置
        case_sensitive = True  # 环境变量大小写敏感

# 创建Settings的实例
# 在其他文件中，你可以通过导入settings来访问这些配置
settings = Settings()

# ——————————————导入包———————————————
# 测试用
import random

# 数据格式
from typing import Dict, Any, Optional, Set, List
from pydantic import BaseModel
import json


# 任务队列
import uuid

# 事件广播
import asyncio
from fastapi import WebSocket

# —————————————单例——————————————
'''单例 确保只创建一次 '''
from threading import Lock
class SingletonMeta(type):
    _instances = {}
    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


# —————————————redis——————————————
import redis.asyncio as redis
class RedisTaskQueue(metaclass=SingletonMeta):
    def __init__(self, host, port, db, password=None):

        # ————————————a简单连接
        # self.client = redis.Redis(host=host, port=port, db=db)

        # ————————————b连接池连接
        self.host = host
        self.port = port
        self.db = db
        self.password = password

        # 有密码和无密码的连接url不同
        if password:
            redis_url = f"redis://:{password}@{host}:{port}/{db}"
        else:
            redis_url = f"redis://{host}:{port}/{db}"

        self.pool = redis.ConnectionPool.from_url(
            redis_url,
            max_connections=20,
            retry_on_timeout=True,
            health_check_interval=0,        # 禁用健康检查
            socket_connect_timeout=5,       # 连接超时5秒
            socket_timeout=None,            # 修改：无限超时，允许brpop长时间阻塞
            retry_on_error=[redis.ConnectionError, redis.TimeoutError]
        )
        self.client = redis.Redis(connection_pool=self.pool)

        # —————————————全局变量—————————————
        # 三种队列(列表)
        self.pending_key = "tasks:pending"
        self.running_key = "tasks:running"
        self.finished_key = "tasks:finished"

    # ————pending队列操作——————
    async def put(self, task: dict):
        """添加任务到pending队列"""
        task_json = json.dumps(task)
        await self.client.lpush(self.pending_key, task_json) # lpush 从左端添加
    
    async def get(self):
        """从pending队列获取任务（阻塞式，保证不重复）"""
        # brpop 取出任务 并且删除任务 同时保证不会重复分配 在队列为空时候阻塞
        result = await self.client.brpop(self.pending_key, timeout=0) # 队列为空时等待
        # 返回result 为 (队列名, 任务)
        if result:
            _, task_json = result # 解包
            return json.loads(task_json) # 反序列化
        return None # 没有任务 返回None
    
    async def get_pending_count(self):
        """获取pending队列任务数量"""
        return await self.client.llen(self.pending_key)

    # ————running队列操作——————
    async def add_running(self, task_id: str, task: dict):
        """添加任务到running队列"""
        await self.client.hset(self.running_key, task_id, json.dumps(task))
    
    async def remove_running(self, task_id: str):
        """从running队列移除任务"""
        await self.client.hdel(self.running_key, task_id)
    
    async def get_running_count(self):
        """获取running队列长度"""
        return await self.client.hlen(self.running_key)

    # ————finished队列操作——————
    async def add_finished(self, task_id: str, result: dict):
        """添加任务结果到finished队列"""
        await self.client.hset(self.finished_key, task_id, json.dumps(result))
    
    async def get_finished_count(self):
        """获取finished队列长度"""
        return await self.client.hlen(self.finished_key)

    # ————其他————
    async def close(self):
        """关闭连接"""
        await self.client.aclose()
    
# ——————————————建立ws并监听广播——————————————
task_queue = None
clients : Set[WebSocket] = set() # 存放建立的ws连接

# 这个函数用来把收到的消息广播到所有ws连接的客户端
async def broadcast_ws(message: Dict[str, Any]):
    # 声明使用全局变量中的clients
    global clients

    # 如果 没有 连接 则 返回
    if not clients:
        return

    # json化message字典 ws只能发送文本和二进制
    message_str = json.dumps(message)

    # 初始化一个集合 用来记录 发送请求失败的客户 即断开的连接
    disconnected_clients = set() 

    # 尝试向每个客户端发送消息
    for client in clients: # 遍历集合
        try:
            await client.send_text(message_str) # 发送消息
        except Exception:
            # 如果 发送失败 则 添加到集合
            disconnected_clients.add(client)
    
    # 清理断开的连接
    clients -= disconnected_clients

    if disconnected_clients:
        print(f"🧹 清理了 {len(disconnected_clients)} 个断开的连接")

# 当 任务 进入 待执行队列时候 向所有ws广播
async def publish_pending(prompt_id: str):
    m = {
        "type": "pending",
        "data": {
            "queue_length": await task_queue.get_pending_count(),
            "prompt_id": prompt_id,
        }
    }
    await broadcast_ws(m)

# 当 任务 开始执行时候 向所有ws广播
async def publish_running(task: Dict[str, Any]):
    m = {
        "type": "running",
        "data": {
            "queue_length": await task_queue.get_pending_count(),
            "prompt_id": task["prompt_id"],
        }
    }
    await broadcast_ws(m)

# 当 任务 成功时候 向所有ws广播
async def publish_finished_success(result):
    m = {
        "type": "finished-success",
        "data": result,
    }
    await broadcast_ws(m)

# 当 任务 失败时候 向所有ws广播
async def publish_finished_failed(result):
    m = {
        "type": "finished-failed",
        "data": result,
    }
    await broadcast_ws(m)


# ——————————————创建app——————————————
import uvicorn
from fastapi import FastAPI

# 生命周期函数
from contextlib import asynccontextmanager
@asynccontextmanager

async def lifespan(app: FastAPI):

    # 启动阶段
    print("🚀 服务器启动")

    # ——————————————初始化Redis连接——————————————
    global task_queue
    task_queue = RedisTaskQueue(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD
    )
    
    # 测试Redis连接
    try:
        await task_queue.client.ping()
        print("✅ Redis连接成功")
    except Exception as e:
        print(f"❌ Redis连接失败: {e}")
        raise

    # ————————————————多协程处理任务————————————————
    async def process_task():
        """单个协程工作器"""
        while True:
            try:
                # 1
                # pending队列 -> 获取一个任务
                task = await task_queue.get()  # 异步获取任务
                # 即便是空队列 也不会因为轮询去高频率拉去请求 因为这个协程是阻塞式的


                if task is None:
                    continue

                # 添加到running队列
                await task_queue.add_running(task["prompt_id"], task)

                # @ 广播 任务 进入 待执行队列
                await publish_running(task)  # 直接调用，无需线程间通信
                print(f"🚀 任务开始执行: {task['prompt_id']}")
                # 2
                # pending状态 -> running状态 + 生成result
                # 执行任务
                try: # 成功执行
                    await asyncio.sleep(20)  # 改为异步等待
                    '''ai生图时间'''
                    result_data =  f"x{random.randint(1, 100)}.png"

                    # 生成最终结果
                    result = {
                        "prompt_id": task["prompt_id"],
                        "result": result_data,
                        "status": "success", 
                    }
                    # @ 广播 任务 成功
                    await publish_finished_success(result)  # 直接调用

                except Exception as e: # 失败执行
                    # 生成最终结果
                    result = {
                        "prompt_id": task["prompt_id"],
                        "result": str(e),
                        "status": "failed", 
                    }
                    # @ 广播 任务 失败
                    await publish_finished_failed(result)  # 直接调用

                # 3
                # running状态 -> finished状态
                # 从running中删除
                await task_queue.remove_running(result["prompt_id"])
                # 添加到finished
                await task_queue.add_finished(result["prompt_id"], result)
                print(f"🚀 任务完成: {result['prompt_id']}")
                
            except Exception as e:
                print(f"❌ 任务处理异常: {e}")

    # 启动 max_workers 个 协程工作器
    workers = []
    for i in range(settings.MAX_WORKERS):
        worker = asyncio.create_task(process_task())
        workers.append(worker)
        print(f"🔄 启动协程工作器 {i+1}")
    
    yield # 分割点 以上是启动阶段 以下是关闭阶段
    
    # 关闭阶段
    print("🛑 服务器关闭")
    # 取消所有协程工作器
    for worker in workers:
        worker.cancel()
    # 等待所有工作器结束
    await asyncio.gather(*workers, return_exceptions=True)

    # 关闭Redis连接
    if task_queue:
        await task_queue.close()
        print("🔴 Redis连接已关闭")

# 实例化app
app = FastAPI(lifespan=lifespan)



# ——————————————路由——————————————
@app.get("/",summary="健康检查")
async def online():
    return {"message": "ok"}


class prompt_input(BaseModel):
    prompt_data: str
@app.post("/prompt",summary="提交任务")
async def submit(request: prompt_input): 
    x = request.prompt_data
    # 1 生成 task 放入带生成队列
    # 生成task
    prompt_id = str(uuid.uuid4())
    task = {
        "prompt_id": prompt_id,
        "prompt_data": x,
    }
    await task_queue.put(task)  # 改为异步放入队列
    # 2 @ 发布 pending 事件
    await publish_pending(prompt_id)
    # 3 返回 
    return {"task":  task["prompt_id"],}


@app.get("/queue",summary="查询队列长度")
async def queue_length():
    # 1 查询队列长度
    return {
        # 在running中是不算长度的
        "queue_length": await task_queue.get_pending_count(),
    }


@app.websocket("/ws") # 建立ws连接
async def ws_client_connect(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            # 保持连接 并 接收消息
            data = await websocket.receive_text() 
            try:
                message = json.loads(data)
                print(f"收到消息: {message}")
            except json.JSONDecodeError:
                print(f"⚠️ 无效的JSON消息: {data}")
    except Exception as e:
        print(f"❌ WebSocket错误: {e}")
        clients.discard(websocket)


# ——————————————中间件————————————————
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ——————————————启动服务——————————————
if __name__ == "__main__":
    port = settings.PORT
    host = settings.HOST

    print("-" * 60)
    print("🌐")
    print(f"服务器启动在 http://{host}:{port}")
    print(f"Redis配置: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    print(f"并行处理数量: {settings.MAX_WORKERS}")
    print("📋")
    print(f"健康检查: GET  http://{host}:{port}/")
    print(f"提交任务: POST http://{host}:{port}/prompt")
    print(f"查询队列: GET  http://{host}:{port}/queue")
    print(f"WebSocket: ws://{host}:{port}/ws")
    print(f"API文档: http://{host}:{port}/docs")
    print("-" * 60)

    uvicorn.run("server-redis:app", host=host, port=port,reload=False) # 启动服务