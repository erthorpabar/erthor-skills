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

class KafkaConsumerGroup(metaclass=SingletonMeta):
    """
    📊 Kafka Consumer Group 模式 - 生产者消费者模式
    
    特点：
    - 同一个Consumer Group中，一条消息只被一个消费者处理
    - 分区机制，支持水平扩展
    - 消息持久化，可重复消费
    - 高吞吐量，适合大数据场景
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
    
    async def send_message(self, topic: str, message_data: dict):
        """
        📤 生产者：发送消息到Topic
        
        Args:
            topic: 主题名称
            message_data: 消息数据（字典格式）
        """
        await self.create_producer()
        await self.producer.send_and_wait(topic, message_data)
        print(f"✅ 生产者发送消息到Topic [{topic}]: {message_data}")
    
    async def consume_messages(self, topic: str, group_id: str, consumer_name: str, callback):
        """
        📥 消费者：消费Topic消息（Consumer Group模式）
        
        Args:
            topic: 主题名称
            group_id: 消费者组ID（同一组内的消费者负载均衡）
            consumer_name: 消费者名称
            callback: 处理消息的回调函数
        """
        consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=group_id,  # 同一个group_id的消费者会负载均衡
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',  # 从最早的消息开始消费
            enable_auto_commit=True
        )
        
        await consumer.start()
        self.consumers.append(consumer)
        print(f"👂 [{consumer_name}] 开始消费Topic: {topic} (Group: {group_id})")
        
        try:
            async for message in consumer:
                message_data = message.value
                print(f"📬 [{consumer_name}] 收到消息 (分区{message.partition}): {message_data}")
                await callback(message_data, consumer_name)
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
async def test_kafka_consumer_group():
    """测试 Kafka Consumer Group 生产者-消费者模式"""
    
    kafka = KafkaConsumerGroup(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS
    )
    
    topic_name = "order_events"
    group_id = "order_processing_group"
    
    # 🎯 场景：订单事件处理，同一个组内的消费者负载均衡
    print("\n" + "="*50)
    print("📊 Kafka Consumer Group 模式 - 生产者消费者模式测试")
    print("="*50 + "\n")
    
    # 消息处理函数
    async def process_order_event(message_data: dict, consumer_name: str):
        """处理订单事件"""
        print(f"🔨 [{consumer_name}] 开始处理订单...")
        await asyncio.sleep(1)  # 模拟处理时间
        print(f"✅ [{consumer_name}] 订单处理完成: {message_data['order_id']}")
    
    # 启动2个消费者（同一个Consumer Group）
    print("【消费者】启动中...\n")
    consumer_task1 = asyncio.create_task(
        kafka.consume_messages(topic_name, group_id, "订单处理器-1", process_order_event)
    )
    consumer_task2 = asyncio.create_task(
        kafka.consume_messages(topic_name, group_id, "订单处理器-2", process_order_event)
    )
    
    # 等待消费者准备好
    await asyncio.sleep(2)
    
    # 生产者：发送5个订单事件
    print("\n【生产者】开始发送消息...\n")
    for i in range(1, 6):
        await kafka.send_message(topic_name, {
            "order_id": f"ORDER_{i:03d}",
            "user_id": f"USER_{i}",
            "product": f"商品{i}",
            "amount": 100 * i,
            "status": "pending"
        })
        await asyncio.sleep(0.5)
    
    # 等待消息处理完成
    await asyncio.sleep(8)
    
    # 取消消费者任务
    consumer_task1.cancel()
    consumer_task2.cancel()
    
    await asyncio.gather(consumer_task1, consumer_task2, return_exceptions=True)
    await kafka.close()
    
    print("\n✅ 测试完成！")


if __name__ == "__main__":
    asyncio.run(test_kafka_consumer_group())


"""
💡 运行结果说明：
- 同一个Consumer Group中，每条消息只被一个消费者处理
- 5个消息会被2个消费者轮流处理（负载均衡）
- 支持分区，可水平扩展
- 适合：日志收集、事件处理、数据管道等大数据场景

📦 安装依赖：
pip install aiokafka

🐳 Docker 启动 Kafka：
# 1. 启动 Zookeeper
docker run -d --name zookeeper -p 2181:2181 zookeeper:3.7

# 2. 启动 Kafka
docker run -d --name kafka -p 9092:9092 \
  -e KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181 \
  -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 \
  -e KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 \
  --link zookeeper \
  confluentinc/cp-kafka:latest
"""