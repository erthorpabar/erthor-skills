# ——————————当前文件夹路径加入搜索路径——————————
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))  # 将当前文件夹路径加入到 Python 搜索路径，便于本地模块导入

# ——————————加载环境变量——————————
from dotenv import load_dotenv
load_dotenv()  # 从 .env 文件加载环境变量

from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    # 🐰 RabbitMQ配置（支持从环境变量覆盖）
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "admin"
    RABBITMQ_PASSWORD: str = "admin123"
    
    class Config:
        env_file = ".env"           # 指定环境变量文件
        env_file_encoding = "utf-8" # 文件编码
        extra = "allow"             # 允许额外未定义的字段
        case_sensitive = True       # 环境变量大小写敏感

settings = Settings()  # 实例化配置对象

'''单例'''
from threading import Lock
class SingletonMeta(type):
    _instances = {}          # 保存各类的单例实例
    _lock: Lock = Lock()     # 线程锁，保证并发下的单例安全

    def __call__(cls, *args, **kwargs):
        # 双检锁（这里用统一的锁）：确保只创建一个实例
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


import asyncio
import json
import aio_pika

class RabbitMQExchange(metaclass=SingletonMeta):
    """
    🐰 RabbitMQ Exchange 模式 - 发布订阅模式

    特点：
    - 一条消息被所有订阅者接收（广播）
    - 支持多种 Exchange 类型（Fanout、Topic、Direct、Headers）
    - 消息持久化，可靠性高
    - 适合需要持久化的广播场景
    """
    
    def __init__(self, host, port, user, password):
        # 基础连接配置
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        # 连接与通道句柄
        self.connection = None
        self.channel = None
    
    async def connect(self):
        """建立连接并创建通道"""
        if not self.connection:
            # 建立稳健连接：断线后可自动重连
            self.connection = await aio_pika.connect_robust(
                host=self.host,
                port=self.port,
                login=self.user,
                password=self.password
            )
            # 创建通道（Channel）：声明交换机、队列以及收发消息都在通道上完成
            self.channel = await self.connection.channel()
            print("✅ RabbitMQ 连接成功")
    
    async def declare_fanout_exchange(self, exchange_name: str):
        """
        声明 Fanout Exchange（广播交换机）
        
        Args:
            exchange_name: 交换机名称
        """
        await self.connect()  # 确保连接与通道已就绪
        # durable=True 表示交换机持久化，Broker 重启后仍存在
        exchange = await self.channel.declare_exchange(
            exchange_name,
            aio_pika.ExchangeType.FANOUT,  # Fanout：忽略 routing_key，将消息广播到所有绑定该交换机的队列
            durable=True
        )
        return exchange
    
    async def publish_message(self, exchange_name: str, message_data: dict):
        """
        📤 发布者：发布消息到交换机
        
        Args:
            exchange_name: 交换机名称
            message_data: 消息数据（字典格式）
        """
        # 确保交换机已声明（不存在则创建）
        exchange = await self.declare_fanout_exchange(exchange_name)
        # 将字典转为 JSON 字符串（ensure_ascii=False 以支持中文）
        message_json = json.dumps(message_data, ensure_ascii=False)
        
        # 发布消息到交换机；Fanout 模式下 routing_key 通常留空
        await exchange.publish(
            aio_pika.Message(
                body=message_json.encode(),                        # 二进制消息体
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT    # 消息持久化（写入磁盘队列）
            ),
            routing_key=""  # Fanout 模式不需要 routing_key
        )
        print(f"📢 发布消息到交换机 [{exchange_name}]: {message_data}")
    
    async def subscribe_message(self, exchange_name: str, callback, subscriber_name: str):
        """
        📥 订阅者：订阅交换机消息
        
        Args:
            exchange_name: 交换机名称
            callback: 处理消息的回调函数（async），签名形如：async def cb(message_data, subscriber_name)
            subscriber_name: 订阅者名称（用于日志标识）
        """
        # 确保交换机存在
        exchange = await self.declare_fanout_exchange(exchange_name)
        
        # 为订阅者声明一个临时独占队列：
        # - name="" 由服务器随机生成队列名
        # - exclusive=True 只允许当前连接使用，连接关闭后队列自动删除
        queue = await self.channel.declare_queue("", exclusive=True)
        # 将队列绑定到交换机（Fanout：忽略 routing_key，收到所有该交换机的消息）
        await queue.bind(exchange)
        
        # 定义消息处理协程：自动 ack，并调用业务回调
        async def process_message(message: aio_pika.IncomingMessage):
            # message.process() 上下文：正常执行完成后自动 ack；异常可触发 nack/requeue（按配置）
            async with message.process():
                # 解码并反序列化消息体
                message_data = json.loads(message.body.decode())
                print(f"📬 [{subscriber_name}] 收到消息: {message_data}")
                # 执行业务回调
                await callback(message_data, subscriber_name)
        
        # 开始消费该临时队列，注册处理函数
        await queue.consume(process_message)
        print(f"👂 [{subscriber_name}] 订阅交换机: {exchange_name}")
    
    async def close(self):
        """关闭连接（会连带关闭通道）"""
        if self.connection:
            await self.connection.close()
            print("🔌 RabbitMQ 连接已关闭")


# ——————————测试代码——————————
async def test_rabbitmq_exchange():
    """测试 RabbitMQ Exchange 发布-订阅模式"""
    
    # 创建发布者（也可复用为订阅者，因实现为单例，参数相同返回同一实例）
    rabbitmq = RabbitMQExchange(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        user=settings.RABBITMQ_USER,
        password=settings.RABBITMQ_PASSWORD
    )
    
    exchange_name = "system_notifications"  # 交换机名称：系统通知
    
    # 🎯 测试场景：系统通知，所有订阅的服务都需要接收（广播）
    print("\n" + "="*50)
    print("🐰 RabbitMQ Exchange 模式 - 发布订阅模式测试")
    print("="*50 + "\n")
    
    # 定义订阅者的消息处理函数
    async def process_notification(message_data: dict, subscriber_name: str):
        """处理系统通知（模拟业务耗时 0.5s）"""
        print(f"🔔 [{subscriber_name}] 处理通知: {message_data['title']}")
        await asyncio.sleep(0.5)
        print(f"✅ [{subscriber_name}] 通知处理完成")
    
    # 启动 3 个订阅者（分别代表不同的下游服务）
    print("【订阅者】启动中...\n")
    subscriber1 = RabbitMQExchange(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        user=settings.RABBITMQ_USER,
        password=settings.RABBITMQ_PASSWORD
    )
    subscriber2 = RabbitMQExchange(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        user=settings.RABBITMQ_USER,
        password=settings.RABBITMQ_PASSWORD
    )
    subscriber3 = RabbitMQExchange(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        user=settings.RABBITMQ_USER,
        password=settings.RABBITMQ_PASSWORD
    )
    
    # 三个订阅者订阅同一交换机，每条消息会广播给三者各自的队列
    await subscriber1.subscribe_message(exchange_name, process_notification, "用户服务")
    await subscriber2.subscribe_message(exchange_name, process_notification, "订单服务")
    await subscriber3.subscribe_message(exchange_name, process_notification, "通知服务")
    
    # 等待订阅者完成绑定，确保不会错过后续发布的消息
    await asyncio.sleep(1)
    
    # 发布 3 条系统通知消息（每条会广播给 3 个订阅者）
    print("\n【发布者】开始发布消息...\n")
    for i in range(1, 4):
        await rabbitmq.publish_message(exchange_name, {
            "notify_id": f"NOTIFY_{i:03d}",
            "title": f"系统通知 {i}",
            "content": f"这是第 {i} 条系统通知",
            "level": "info"
        })
        await asyncio.sleep(1)  # 控制发布节奏，便于观察输出
    
    # 等待所有消息处理完成
    await asyncio.sleep(3)
    
    # 依次关闭连接（发布者与三个订阅者）
    await rabbitmq.close()
    await subscriber1.close()
    await subscriber2.close()
    await subscriber3.close()
    
    print("\n✅ 测试完成！")


if __name__ == "__main__":
    # 脚本入口：运行异步测试用例
    asyncio.run(test_rabbitmq_exchange())


"""
💡 运行结果说明：
- 每条消息会被所有 3 个订阅者接收（广播）
- 每个订阅者都有独立的临时独占队列
- 消息与交换机均设置为持久化，可靠性高
- 适用场景：系统通知、配置更新、数据同步等需要持久化的广播场景

📦 安装依赖：
pip install aio-pika python-dotenv pydantic-settings
"""