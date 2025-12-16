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
    
    async def publish(self, channel: str, message: dict):
        """
        📤 发布者：发布消息到频道
        
        Args:
            channel: 频道名称
            message: 消息数据（字典格式）
        
        Returns:
            接收到消息的订阅者数量
        """
        message_json = json.dumps(message, ensure_ascii=False) # 转化为json 保留中文字符
        subscriber_count = await self.client.publish(channel, message_json) # redis自己的发布订阅模式
        print(f"📢 发布消息到频道 [{channel}]: {message} (订阅者数量: {subscriber_count})")
        return subscriber_count
    
    
    async def subscribe(self, channel: str, subscriber_name: str):
        """
        📥 订阅者：订阅频道并接收消息
        
        Args:
            channel: 频道名称
            subscriber_name: 订阅者名称（用于标识）
        """
        pubsub = self.client.pubsub() # 创建一个长连接 Pub/Sub 对象
        await pubsub.subscribe(channel) # 服务器会自动将新消息推送到订阅频道
        print(f"👂 [{subscriber_name}] 开始订阅频道: {channel}")
        
        # 推送消息后
        try:
            # 这是一个长期阻塞的监听循环，不主动取消就不会结束，程序会一直挂着。
            async for message in pubsub.listen():
                if message['type'] == 'message': # Redis Pub/Sub 消息包含多种类型（如 subscribe、message 等），这里只处理真正的消息类型
                    message_data = json.loads(message['data']) # 取出数据
                    print(f"📬 [{subscriber_name}] 收到消息: {message_data}")
        except asyncio.CancelledError:
            print(f"🛑 [{subscriber_name}] 停止订阅")
            await pubsub.unsubscribe(channel) # 主动取消订阅指定频道，避免服务器端仍然保留订阅关系
            await pubsub.close() # 关闭 pubsub 连接，释放资源；否则可能导致连接泄漏
    
    async def close(self):
        """关闭连接"""
        await self.client.aclose()

# ——————————测试代码——————————
async def test_redis_pubsub():

    # ————————————创建发布者————————————
    redis_pubsub = RedisTaskQueue(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD
    )
    
    channel_name = "price_updates"


    # ————————————创建订阅者————————————
    async def create_subscriber(name: str):
        """创建订阅者"""
        subscriber = RedisTaskQueue(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD
        )
        await subscriber.subscribe(channel=channel_name, subscriber_name=name)
        await subscriber.aclose()

    # 创建三个订阅者
    # 启动了
    subscriber_tasks = [
        asyncio.create_task(create_subscriber("手机APP用户")),
        asyncio.create_task(create_subscriber("网页端用户")),
        asyncio.create_task(create_subscriber("管理后台"))
    ]
    await asyncio.sleep(1)

    # 发消息 同时 订阅者收到消息
    for i in range(1, 4):
        await redis_pubsub.publish(channel=channel_name, message={
            "product_id": f"PROD_{i:03d}",
            "product_name": f"商品{i}",
            "old_price": 100 + i * 10,
            "new_price": 90 + i * 10,
            "discount": "限时优惠"
        })
        await asyncio.sleep(1)

    # 取消订阅者任务
    for task in subscriber_tasks:
        task.cancel()

    # 等待彻底执行完成
    await asyncio.gather(*subscriber_tasks, return_exceptions=True) 
    await redis_pubsub.close()
    print("\n✅ 测试完成！")

if __name__ == "__main__":
    asyncio.run(test_redis_pubsub())