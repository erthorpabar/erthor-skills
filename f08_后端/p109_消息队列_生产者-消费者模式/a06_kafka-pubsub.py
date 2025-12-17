# ——————————当前文件夹路径加入搜索路径——————————
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ——————————加载环境变量——————————
from dotenv import load_dotenv
load_dotenv()

from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    # 📊 Kafka配置
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    
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
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

class KafkaMultipleGroups(metaclass=SingletonMeta):
    """
    📊 Kafka 多个 Consumer Group 模式 - 发布订阅模式
    
    特点：
    - 不同Consumer Group，每个组都会收到所有消息（广播）
    - 消息持久化，可重复消费
    - 支持海量数据
    - 适合需要持久化和高吞吐的广播场景
    """
    
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        self.consumers = []
    
    async def create_producer(self):
        """创建生产者"""
        if not self.producer:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8')
            )
            await self.producer.start()
            print("✅ Kafka Producer 创建成功")
    
    async def publish_event(self, topic: str, event_data: dict):
        """
        📤 发布者：发布事件到Topic
        
        Args:
            topic: 主题名称
            event_data: 事件数据（字典格式）
        """
        await self.create_producer()
        await self.producer.send_and_wait(topic, event_data)
        print(f"📢 发布事件到Topic [{topic}]: {event_data}")
    
    async def subscribe_events(self, topic: str, group_id: str, subscriber_name: str, callback):
        """
        📥 订阅者：订阅Topic事件（不同的Consumer Group）
        
        Args:
            topic: 主题名称
            group_id: 消费者组ID（不同组都会收到消息）
            subscriber_name: 订阅者名称
            callback: 处理事件的回调函数
        """
        consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=group_id,  # 不同的group_id，每个组都会收到所有消息
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=True
        )
        
        await consumer.start()
        self.consumers.append(consumer)
        print(f"👂 [{subscriber_name}] 订阅Topic: {topic} (Group: {group_id})")
        
        try:
            async for message in consumer:
                event_data = message.value
                print(f"📬 [{subscriber_name}] 收到事件: {event_data}")
                await callback(event_data, subscriber_name)
        finally:
            await consumer.stop()
    
    async def close(self):
        """关闭所有连接"""
        if self.producer:
            await self.producer.stop()
        for consumer in self.consumers:
            await consumer.stop()
        print("🔌 Kafka 连接已关闭")


# ——————————测试代码——————————
async def test_kafka_multiple_groups():
    """测试 Kafka 多个 Consumer Group 发布-订阅模式"""
    
    kafka = KafkaMultipleGroups(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS
    )
    
    topic_name = "user_register_events"
    
    # 🎯 场景：用户注册事件，多个服务都要接收并处理
    print("\n" + "="*50)
    print("📊 Kafka 多个 Consumer Group 模式 - 发布订阅模式测试")
    print("="*50 + "\n")
    
    # 消息处理函数
    async def process_email_service(event_data: dict, subscriber_name: str):
        """邮件服务处理"""
        print(f"📧 [{subscriber_name}] 发送欢迎邮件...")
        await asyncio.sleep(0.5)
        print(f"✅ [{subscriber_name}] 欢迎邮件已发送: {event_data['email']}")
    
    async def process_coupon_service(event_data: dict, subscriber_name: str):
        """优惠券服务处理"""
        print(f"🎟️ [{subscriber_name}] 发放新人优惠券...")
        await asyncio.sleep(0.5)
        print(f"✅ [{subscriber_name}] 优惠券已发放: {event_data['user_id']}")
    
    async def process_analytics_service(event_data: dict, subscriber_name: str):
        """数据分析服务处理"""
        print(f"📊 [{subscriber_name}] 记录用户行为...")
        await asyncio.sleep(0.5)
        print(f"✅ [{subscriber_name}] 数据已记录: {event_data['user_id']}")
    
    # 启动3个订阅者（不同的Consumer Group）
    print("【订阅者】启动中...\n")
    subscriber_task1 = asyncio.create_task(
        kafka.subscribe_events(topic_name, "email_service_group", "邮件服务", process_email_service)
    )
    subscriber_task2 = asyncio.create_task(
        kafka.subscribe_events(topic_name, "coupon_service_group", "优惠券服务", process_coupon_service)
    )
    subscriber_task3 = asyncio.create_task(
        kafka.subscribe_events(topic_name, "analytics_service_group", "数据分析服务", process_analytics_service)
    )
    
    # 等待订阅者准备好
    await asyncio.sleep(2)
    
    # 发布者：发布3个用户注册事件
    print("\n【发布者】开始发布事件...\n")
    for i in range(1, 4):
        await kafka.publish_event(topic_name, {
            "event_id": f"EVENT_{i:03d}",
            "user_id": f"USER_{i:06d}",
            "username": f"user{i}",
            "email": f"user{i}@example.com",
            "register_time": "2025-10-30 10:00:00",
            "source": "mobile_app"
        })
        await asyncio.sleep(1)
    
    # 等待事件处理完成
    await asyncio.sleep(5)
    
    # 取消订阅者任务
    subscriber_task1.cancel()
    subscriber_task2.cancel()
    subscriber_task3.cancel()
    
    await asyncio.gather(subscriber_task1, subscriber_task2, subscriber_task3, return_exceptions=True)
    await kafka.close()
    
    print("\n✅ 测试完成！")


if __name__ == "__main__":
    asyncio.run(test_kafka_multiple_groups())


"""
💡 运行结果说明：
- 每条消息会被所有3个Consumer Group接收（广播）
- 每个服务都有独立的Consumer Group
- 消息持久化，支持重复消费
- 适合：用户行为追踪、多服务协同、数据同步等大数据广播场景

📦 安装依赖：
pip install aiokafka

💡 核心区别：
- Consumer Group模式：同一组内负载均衡，一条消息只被一个消费者处理
- 多Consumer Group模式：不同组都接收，实现发布-订阅
"""