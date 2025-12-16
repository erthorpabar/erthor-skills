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



'''单例'''
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


import asyncio
import json
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
    

    # —————————————————写入读取———————————————————
    async def set(self, key,value):
        '''写入'''
        await self.client.set(key,value)
    
    async def get(self, key):
        '''读取'''
        value = await self.client.get(key)
        if type(value) == bytes:
            return value.decode('utf-8')
        return value

    # —————————————————写入读取字典———————————————————
    async def set_dict(self, key,value):
        '''写入字典 value为字典类型'''
        await self.client.set(key,json.dumps(value))

    async def get_dict(self, key):
        '''读取字典'''
        value = await self.get(key)
        return json.loads(value)

    # —————————————————删除———————————————————
    async def delete(self, key):
        '''删除'''
        await self.client.delete(key)

    # —————————————————关闭连接———————————————————
    async def close(self):
        '''关闭连接'''
        await self.client.aclose()

    # —————————————————锁———————————————————

    # 非原子性操作
    async def add_counter(self, key,amount=1):
        '''增加计数器'''
        await self.client.incrby(key,amount)
    
    async def sub_counter(self, key,amount=1):
        '''减少计数器'''
        await self.client.decrby(key,amount)
    
    # 原子性操作
    async def add_counter_atomic(self, key,amount=1):
        '''安全增加计数器'''
        async with self.client.lock(f"lock:{key}"):
            await self.client.incrby(key,amount)




# 测试
async def test_redis():
    redis_client = RedisTaskQueue(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB, password=settings.REDIS_PASSWORD)

    # 测试写入读取
    await redis_client.set('name', 'ccc')
    name = await redis_client.get('name')
    print(f"姓名: {name}")

    # 测试写入读取字典
    await redis_client.set_dict('user', {'name': 'ccc', 'age': 18})
    user = await redis_client.get_dict('user')
    print(f"用户: {user}")

    # 测试删除
    await redis_client.delete('name')
    name = await redis_client.get('name')
    print(f"姓名: {name}")

    # 测试锁
    await redis_client.set('counter', 0)
    await redis_client.add_counter_atomic('counter', 10)
    counter = await redis_client.get('counter')
    print(f"计数器: {counter}")

    # 测试关闭连接
    await redis_client.close()

if __name__ == "__main__":
    asyncio.run(test_redis())


''' 
命令行
# 启动本地redis服务
redis-cli

# 连接到docker容器中的redis服务
docker exec -it redis redis-cli -a redis123

# 写入
set name ccc

# 读取
get name

# 退出
exit

'''