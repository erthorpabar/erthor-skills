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
    


    # ————————————生产者：推送任务到队列————————————
    async def push_task(self, queue_name: str, task_data: dict):
        """
        📤 生产者：推送任务到队列
        
        Args:
            queue_name: 队列名称
            task_data: 任务数据（字典格式）
        """
        task_json = json.dumps(task_data, ensure_ascii=False)
        await self.client.lpush(queue_name, task_json)
        print(f"✅ 生产者推送任务到队列 [{queue_name}]: {task_data}")
        
    # ————————————消费者：从队列中获取任务（阻塞式）————————————
    async def consume_task(self, queue_name: str, timeout: int = 0):
        """
        📥 消费者：从队列中获取任务（阻塞式）
        
        Args:
            queue_name: 队列名称
            timeout: 超时时间（秒），0表示永久等待
            
        Returns:
            任务数据字典，如果超时返回None
        """
        result = await self.client.brpop(queue_name, timeout=timeout)
        if result:
            queue, task_json = result
            task_data = json.loads(task_json)
            print(f"✅ 消费者从队列 [{queue.decode()}] 获取任务: {task_data}")
            return task_data
        return None
    
    async def close(self):
        """关闭连接"""
        await self.client.aclose()
    
    

# ——————————测试代码——————————
async def test_redis_list_queue():
    redis_queue = RedisTaskQueue(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD
    )

    queue_name = "order_tasks"

    # 生产者：推送3个订单任务
    for i in range(1, 50):
        await redis_queue.push_task(queue_name, {
            "order_id": f"ORDER_{i:03d}",
            "user_id": f"USER_{i}",
            "amount": 100 * i
        })
        await asyncio.sleep(0.5)
    
    # 消费者：多线程异步模拟多个消费者
    async def worker(worker_id: int):
        """工作线程"""
        worker_queue = RedisTaskQueue(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD
        )

        while True:
            task = await worker_queue.consume_task(queue_name, timeout=2) # 阻塞式获取任务
            if task:
                print(f"🔨 工作者-{worker_id} 正在处理: {task}")
                await asyncio.sleep(1) # 模拟处理时间
                print(f"✅ 工作者-{worker_id} 完成任务")
            else:
                print(f"⏰ 工作者-{worker_id} 等待超时，退出")
                break
        await worker_queue.close()
    
    # 启动2个消费者工作线程
    await asyncio.gather(
        worker(1),
        worker(2)
    )
    
    await redis_queue.close()
    print("\n✅ 测试完成！")

if __name__ == "__main__":
    asyncio.run(test_redis_list_queue())

''' 
查看队列中的所有任务
LRANGE order_tasks 0 -1

'''
