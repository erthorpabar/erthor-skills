# ——————————当前文件夹路径加入搜索路径——————————
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ——————————加载环境变量——————————
from dotenv import load_dotenv
load_dotenv()

from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    # 🐰 RabbitMQ配置
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"
        case_sensitive = True

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
import aio_pika

class RabbitMQQueue(metaclass=SingletonMeta):
    """
    🐰 RabbitMQ Queue 模式 - 生产者消费者模式
    
    特点：
    - 一条消息只被一个消费者处理（负载均衡）
    - 持久化消息，不会丢失
    - 支持消息确认机制（ACK）
    - 适合可靠的任务分发场景
    """

    def __init__(self, host, port, user, password):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.connection = None
        self.channel = None

    async def connect(self):
        """建立连接"""
        # 如果还没有连接对象，则建立与 RabbitMQ 的稳健连接（断线可自动恢复）
        if not self.connection:
            self.connection = await aio_pika.connect_robust(
                host=self.host,          # 主机地址
                port=self.port,          # 端口
                login=self.user,         # 用户名
                password=self.password   # 密码
            )
            # 创建一个通道（Channel），用于后续声明队列、发布/消费消息
            self.channel = await self.connection.channel()
            # 设置消费端的预取数量为 1，确保一个消费者同一时间只处理一条消息，实现“公平分发”
            await self.channel.set_qos(prefetch_count=1)
            print("✅ RabbitMQ 连接成功")

    async def declare_queue(self, queue_name: str):
        """
        声明队列

        Args:
            queue_name: 队列名称
        """
        # 确保已建立连接和通道
        await self.connect()
        # 声明（创建或复用）一个持久化队列，服务重启后队列仍存在
        queue = await self.channel.declare_queue(
            queue_name,
            durable=True  # 队列持久化
        )
        return queue

    async def send_task(self, queue_name: str, task_data: dict):
        """
        📤 生产者：发送任务到队列

        Args:
            queue_name: 队列名称
            task_data: 任务数据（字典格式）
        """
        # 确保连接就绪
        await self.connect()
        # 将任务数据序列化为 JSON 字符串（ensure_ascii=False 保留中文）
        task_json = json.dumps(task_data, ensure_ascii=False)

        # 通过默认交换机，使用 routing_key 指定目标队列进行投递
        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=task_json.encode(),                         # 消息主体（字节串）
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT  # 消息持久化，Broker 重启不丢
            ),
            routing_key=queue_name
        )
        print(f"✅ 生产者发送任务到队列 [{queue_name}]: {task_data}")

    async def consume_task(self, queue_name: str, callback, consumer_name: str):
        """
        📥 消费者：从队列中消费任务

        Args:
            queue_name: 队列名称
            callback: 处理任务的回调函数，签名形如: async def cb(task_data, consumer_name): ...
            consumer_name: 消费者名称（用于日志标识）
        """
        # 确保队列已声明（不存在则创建，存在则复用）
        queue = await self.declare_queue(queue_name)

        # 定义消息处理函数：自动确认（message.process() 上下文）并调用业务回调
        async def process_message(message: aio_pika.IncomingMessage):
            # 使用自动处理上下文：正常完成即 ack，异常会 nack/requeue（取决于配置）
            async with message.process():
                # 解码消息体并反序列化为字典
                task_data = json.loads(message.body.decode())
                print(f"📬 [{consumer_name}] 收到任务: {task_data}")
                # 调用外部传入的异步回调执行业务逻辑
                await callback(task_data, consumer_name)

        # 订阅队列，注册处理函数，开始持续消费
        await queue.consume(process_message)
        print(f"👂 [{consumer_name}] 开始消费队列: {queue_name}")

    async def close(self):
        """关闭连接"""
        # 如果连接存在，主动关闭（会同时关闭其下的通道）
        if self.connection:
            await self.connection.close()
            print("🔌 RabbitMQ 连接已关闭")
    

    
# ——————————测试代码——————————
async def test_rabbitmq_queue():
    """测试 RabbitMQ Queue 生产者-消费者模式"""
    
    # 创建生产者连接
    rabbitmq = RabbitMQQueue(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        user=settings.RABBITMQ_USER,
        password=settings.RABBITMQ_PASSWORD
    )
    
    queue_name = "email_tasks"  # 队列名称：邮件任务队列
    
    # 🎯 场景说明：模拟邮件发送任务，由多个消费者并发处理
    print("\n" + "="*50)
    print("🐰 RabbitMQ Queue 模式 - 生产者消费者模式测试")
    print("="*50 + "\n")
    
    # 定义任务处理函数（消费者回调）
    async def process_email_task(task_data: dict, consumer_name: str):
        """处理邮件任务"""
        print(f"📧 [{consumer_name}] 开始发送邮件...")
        await asyncio.sleep(1)  # 模拟发送邮件耗时
        print(f"✅ [{consumer_name}] 邮件发送完成: {task_data['email']}")
    
    # 启动 2 个消费者（模拟两个邮件服务器）
    print("【消费者】启动中...\n")
    consumer1 = RabbitMQQueue(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        user=settings.RABBITMQ_USER,
        password=settings.RABBITMQ_PASSWORD
    )
    consumer2 = RabbitMQQueue(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        user=settings.RABBITMQ_USER,
        password=settings.RABBITMQ_PASSWORD
    )
    
    # 两个消费者开始消费同一队列，实现任务的竞争消费（公平分发依赖 prefetch_count=1）
    await consumer1.consume_task(queue_name, process_email_task, "邮件服务器-1")
    await consumer2.consume_task(queue_name, process_email_task, "邮件服务器-2")
    
    # 等待消费者完成订阅准备
    await asyncio.sleep(1)
    
    # 生产者：发送 4 个邮件任务
    print("\n【生产者】开始发送任务...\n")
    for i in range(1, 5):
        await rabbitmq.send_task(queue_name, {
            "email_id": f"EMAIL_{i:03d}",
            "email": f"user{i}@example.com",
            "subject": f"测试邮件 {i}",
            "content": f"这是第 {i} 封邮件"
        })
        await asyncio.sleep(0.3)  # 模拟任务间隔
    
    # 等待所有任务被处理完成
    await asyncio.sleep(5)
    
    # 关闭连接（生产者与两个消费者）
    await rabbitmq.close()
    await consumer1.close()
    await consumer2.close()
    
    print("\n✅ 测试完成！")


if __name__ == "__main__":
    # 在脚本直接运行时，启动异步测试入口
    asyncio.run(test_rabbitmq_queue())