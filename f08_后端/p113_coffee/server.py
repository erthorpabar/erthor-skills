'''架构逻辑
coffee异步任务队列系统
http -> 主动发起任务 -> 待执行队列+task状态跟踪 -> 
ws -> 被动接受状态更新 -> 每次 task 状态改变 -> 发送消息


1 对于io任务 -> 多协程
2 对于cpu任务 -> 多进程



当前使用多协程


用户A(提交AI任务) ──┐                               ┌──> 异步1 ──┐
用户B(提交AI任务) ──┼──> 任务队列(并返回任务id) ──> ──┼──> 异步2 ──┼──> 返回结果
用户C(提交AI任务) ──┘                               └──> 异步3 ──┘

                        ws返回pending状态         ws返回running状态   ws返回finished状态

'''


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
    # TASK_TIMEOUT: int = 300
    
    # 📡 WebSocket配置
    # WS_PING_INTERVAL: int = 20
    # WS_PING_TIMEOUT: int = 10
    
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
import time
import random
# 数据格式
from typing import Dict, Any, Optional, Set, List
from pydantic import BaseModel
import json

# 队列
from asyncio import Queue as AsyncQueue  # 改为异步队列
import uuid

# 事件广播
import asyncio
from fastapi import WebSocket

# 全局变量
# —————————— 待执行队列 + task状态跟踪 ————————————
pending_queue = AsyncQueue()  # 改为异步队列
running_tasks = {} # 正在执行的任务
finished_tasks = {} # 已完成的任务

# ——————————————建立ws并监听广播——————————————
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
            "queue_length": pending_queue.qsize(),
            "prompt_id": prompt_id,
        }
    }
    await broadcast_ws(m)

# 当 任务 开始执行时候 向所有ws广播
async def publish_running(task: Dict[str, Any]):
    m = {
        "type": "running",
        "data": {
            "queue_length": pending_queue.qsize(),
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

    # ————————————————多协程处理任务————————————————
    async def process_task():
        """单个协程工作器"""
        while True:
            try:
                # 1
                # pending队列 -> 获取一个任务
                task = await pending_queue.get()  # 异步获取任务
                # 即便是空队列 也不会因为轮询去高频率拉去请求 因为这个协程是阻塞式的
                
                # 添加到running队列
                running_tasks[task["prompt_id"]] = task
                print(f"🚀 任务开始执行: {task['prompt_id']}")
                
                # @ 广播 任务 进入 待执行队列
                await publish_running(task)  # 直接调用，无需线程间通信

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
                        "status": "failed", 
                        "result": str(e),
                    }
                    # @ 广播 任务 失败
                    await publish_finished_failed(result)  # 直接调用

                # 3
                # running状态 -> finished状态
                # 从running中删除
                if result["prompt_id"] in running_tasks:
                    del running_tasks[result["prompt_id"]]
                # 添加到finished
                finished_tasks[result["prompt_id"]] = result 
                # 从 pending队列 中 删除 get到的任务
                pending_queue.task_done()
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
    await pending_queue.put(task)  # 改为异步放入队列
    # 2 @ 发布 pending 事件
    await publish_pending(prompt_id)
    # 3 返回 
    return {"task":  task["prompt_id"],}


@app.get("/queue",summary="查询队列长度")
async def queue_length():
    # 1 查询队列长度
    return {
        # 在running中是不算长度的
        "queue_length": pending_queue.qsize(),
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
    print("📋")
    print(f"健康检查: GET  http://{host}:{port}/")
    print(f"提交任务: POST http://{host}:{port}/prompt")
    print(f"查询队列: GET  http://{host}:{port}/queue")
    print(f"WebSocket: ws://{host}:{port}/ws")
    print(f"API文档: http://{host}:{port}/docs")
    print("-" * 60)

    uvicorn.run("server:app", host=host, port=port,reload=False) # 启动服务