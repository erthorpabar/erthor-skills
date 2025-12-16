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

    # 🐰 RabbitMQ配置
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_VHOST: str = "/"
    
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
import aio_pika
from aio_pika import ExchangeType


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
    def __init__(self, host, port, db):

        # ————————————a简单连接
        # self.client = redis.Redis(host=host, port=port, db=db)

        # ————————————b连接池连接
        self.host = host
        self.port = port
        self.db = db

        self.pool = redis.ConnectionPool.from_url(
            f"redis://{host}:{port}/{db}",
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
    
# —————————————rabbitmq广播——————————————
class RabbitMQ(metaclass=SingletonMeta):
    def __init__(self, host, port, user, password, vhost):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.vhost = vhost
        self.connection = None
        self.channel = None
        