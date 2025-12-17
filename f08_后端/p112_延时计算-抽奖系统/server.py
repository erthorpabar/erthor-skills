''' 
限量库存抽奖系统
功能：
1. 20%概率抽奖
2. 中奖后生成临时订单，库存-1
3. 可以放弃支付或完成支付
4. 超时未支付自动归还库存
'''

# ——————————当前文件夹路径加入搜索路径——————————
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ——————————加载环境变量——————————
from dotenv import load_dotenv
load_dotenv()

from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    
    # 🌐 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    
    # 📦 Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = "redis123"
    
    # 🗄️ MongoDB配置
    MONGODB_HOST: str = "localhost"
    MONGODB_PORT: int = 27017
    MONGODB_USER: str = "admin"
    MONGODB_PASSWORD: str = "admin123"
    MONGODB_DATABASE: str = "lottery_db"
    
    # 📨 RabbitMQ配置
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_QUEUE: str = "lottery_timeout"
    
    # 🎰 业务配置
    INITIAL_STOCK: int = 100  # 初始库存
    WIN_RATE: float = 0.2  # 中奖概率 20%
    PAYMENT_TIMEOUT_SECONDS: int = 300  # 支付超时时间(秒) 5分钟
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"
        case_sensitive = True

# 创建Settings的实例
settings = Settings()

# ———————————————————单例模式————————————————————
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

# ———————————————————Redis连接——————————————————
import redis.asyncio as redis
from typing import Optional
import json

class RedisClient(metaclass=SingletonMeta):
    def __init__(self, host, port, db, password=None):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        
        # Redis Key 常量
        self.STOCK_KEY = "lottery:stock"  # 库存key
        self.TEMP_ORDER_PREFIX = "lottery:temp_order:"  # 临时订单前缀
        self.LOCK_KEY = "lottery:lock"  # 分布式锁key

        # 池连接
        if password:
            redis_url = f"redis://:{password}@{host}:{port}/{db}"
        else:
            redis_url = f"redis://{host}:{port}/{db}"

        self.pool = redis.ConnectionPool.from_url(
            redis_url,
            max_connections=50,
            retry_on_timeout=True,
            health_check_interval=0,
            socket_connect_timeout=5,
            socket_timeout=None,
            retry_on_error=[redis.ConnectionError, redis.TimeoutError]
        )
        self.client = redis.Redis(connection_pool=self.pool)

    # ————————测试连接成功
    async def ping(self):
        try:
            await self.client.ping()
            print('✅ Redis连接成功')
        except Exception as e:
            print(f'❌ Redis连接失败: {e}')
            raise
    
    # ————————关闭连接
    async def close(self):
        await self.client.close()  
        await self.pool.disconnect() 
        print('✅ Redis连接已关闭')

    # ————————初始化库存
    async def init_stock(self, stock: int):
        """初始化库存数量"""
        await self.client.set(self.STOCK_KEY, stock)
        print(f'✅ 初始化库存: {stock}')

    # ————————获取当前库存
    async def get_stock(self) -> int:
        """获取当前库存"""
        stock = await self.client.get(self.STOCK_KEY)
        return int(stock) if stock else 0

    # ————————减少库存(带分布式锁)
    async def decrease_stock(self) -> bool:
        """
        减少库存（使用Lua脚本保证原子性）
        返回: True表示成功，False表示库存不足
        """
        lua_script = """
        local stock = redis.call('GET', KEYS[1])
        if tonumber(stock) > 0 then
            redis.call('DECR', KEYS[1])
            return 1
        else
            return 0
        end
        """
        result = await self.client.eval(lua_script, 1, self.STOCK_KEY)
        return bool(result)

    # ————————增加库存
    async def increase_stock(self):
        """归还库存"""
        await self.client.incr(self.STOCK_KEY)

    # ————————保存临时订单
    async def save_temp_order(self, order_id: str, order_data: dict, expire_seconds: int):
        """
        保存临时订单到Redis（设置过期时间）
        Args:
            order_id: 订单ID
            order_data: 订单数据
            expire_seconds: 过期时间（秒）
        """
        key = f"{self.TEMP_ORDER_PREFIX}{order_id}"
        await self.client.setex(key, expire_seconds, json.dumps(order_data))

    # ————————获取临时订单
    async def get_temp_order(self, order_id: str) -> Optional[dict]:
        """获取临时订单"""
        key = f"{self.TEMP_ORDER_PREFIX}{order_id}"
        data = await self.client.get(key)
        return json.loads(data) if data else None

    # ————————删除临时订单
    async def delete_temp_order(self, order_id: str):
        """删除临时订单"""
        key = f"{self.TEMP_ORDER_PREFIX}{order_id}"
        await self.client.delete(key)

# 创建Redis客户端实例
redis_client = RedisClient(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    password=settings.REDIS_PASSWORD
)

# ———————————————————MongoDB连接——————————————————
from motor.motor_asyncio import AsyncIOMotorClient

class MongoDBClient(metaclass=SingletonMeta):
    def __init__(self, host, port, username, password, database):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database_name = database
        
        # 构建连接URL
        if username and password:
            connection_url = f"mongodb://{username}:{password}@{host}:{port}/"
        else:
            connection_url = f"mongodb://{host}:{port}/"
        
        # 创建异步客户端
        self.client = AsyncIOMotorClient(
            connection_url,
            maxPoolSize=50,
            minPoolSize=10,
            serverSelectionTimeoutMS=5000
        )
        
        # 获取数据库
        self.db = self.client[database]
        
        # 集合
        self.orders_collection = self.db['orders']  # 正式订单集合

    # ————————测试连接
    async def ping(self):
        try:
            await self.client.admin.command('ping')
            print('✅ MongoDB连接成功')
        except Exception as e:
            print(f'❌ MongoDB连接失败: {e}')
            raise

    # ————————关闭连接
    async def close(self):
        self.client.close()
        print('✅ MongoDB连接已关闭')

    # ————————保存正式订单
    async def save_order(self, order_data: dict):
        """保存正式订单到MongoDB"""
        result = await self.orders_collection.insert_one(order_data)
        return str(result.inserted_id)

    # ————————查询订单
    async def get_order(self, order_id: str):
        """根据订单ID查询订单"""
        return await self.orders_collection.find_one({"order_id": order_id})

    # ————————查询所有订单
    async def get_all_orders(self, limit: int = 100):
        """查询所有正式订单"""
        cursor = self.orders_collection.find().sort("create_time", -1).limit(limit)
        return await cursor.to_list(length=limit)

# 创建MongoDB客户端实例
mongodb_client = MongoDBClient(
    host=settings.MONGODB_HOST,
    port=settings.MONGODB_PORT,
    username=settings.MONGODB_USER,
    password=settings.MONGODB_PASSWORD,
    database=settings.MONGODB_DATABASE
)

# ———————————————————RabbitMQ连接——————————————————
import asyncio
import aio_pika
from aio_pika import Message, DeliveryMode, ExchangeType

class RabbitMQClient(metaclass=SingletonMeta):
    def __init__(self, host, port, username, password, queue_name):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.queue_name = queue_name
        
        # 延时队列名称
        self.delay_queue_name = f"{queue_name}_delay"
        self.delay_exchange_name = f"{queue_name}_delay_exchange"
        
        # 连接对象（启动时创建）
        self.connection = None
        self.channel = None
        self.consumer_task = None
        
    # ————————启动连接
    async def start(self):
        """启动RabbitMQ连接并创建队列"""
        try:
            # 创建连接
            self.connection = await aio_pika.connect_robust(
                host=self.host,
                port=self.port,
                login=self.username,
                password=self.password,
            )
            
            # 创建通道
            self.channel = await self.connection.channel()
            
            # 设置QoS（每次只处理1条消息）
            await self.channel.set_qos(prefetch_count=1)
            
            # ——————————创建延时队列结构——————————
            # 1. 声明正式队列（用于接收延时后的消息）
            self.queue = await self.channel.declare_queue(
                self.queue_name,
                durable=True
            )
            
            # 2. 声明延时队列（带有TTL和DLX配置）
            delay_queue = await self.channel.declare_queue(
                self.delay_queue_name,
                durable=True,
                arguments={
                    'x-dead-letter-exchange': '',  # 死信交换机（默认交换机）
                    'x-dead-letter-routing-key': self.queue_name,  # 死信路由键（指向正式队列）
                }
            )
            
            # 3. 启动消费者监听正式队列
            self.consumer_task = asyncio.create_task(self._start_consumer())
            
            print('✅ RabbitMQ连接成功')
            
        except Exception as e:
            print(f'❌ RabbitMQ连接失败: {e}')
            raise

    # ————————关闭连接
    async def close(self):
        """关闭RabbitMQ连接"""
        try:
            # 取消消费者任务
            if self.consumer_task:
                self.consumer_task.cancel()
                try:
                    await self.consumer_task
                except asyncio.CancelledError:
                    pass
            
            # 关闭通道和连接
            if self.channel:
                await self.channel.close()
            if self.connection:
                await self.connection.close()
            
            print('✅ RabbitMQ连接已关闭')
        except Exception as e:
            print(f'⚠️ RabbitMQ关闭时出错: {e}')

    # ————————发送延时消息
    async def send_delay_message(self, order_id: str, delay_seconds: int):
        """
        发送延时消息（使用TTL + Dead Letter实现）
        消息先发送到延时队列，TTL过期后自动路由到正式队列
        """
        try:
            message_body = json.dumps({"order_id": order_id})
            
            # 创建消息（设置TTL）
            message = Message(
                body=message_body.encode(),
                delivery_mode=DeliveryMode.PERSISTENT,  # 持久化
                expiration=delay_seconds * 1000  # 过期时间（毫秒）
            )
            
            # 发送到延时队列
            await self.channel.default_exchange.publish(
                message,
                routing_key=self.delay_queue_name
            )
            
            print(f'📨 发送延时消息: order_id={order_id}, delay={delay_seconds}s')
            
        except Exception as e:
            print(f'❌ 发送延时消息失败: {e}')
            raise

    # ————————启动消费者
    async def _start_consumer(self):
        """启动消费者监听正式队列"""
        try:
            print(f'👂 开始监听队列: {self.queue_name}')
            
            # 消费消息
            async with self.queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        await self._handle_message(message)
                        
        except asyncio.CancelledError:
            print('🛑 消费者任务已取消')
        except Exception as e:
            print(f'❌ 消费者出错: {e}')

    # ————————处理消息
    async def _handle_message(self, message: aio_pika.IncomingMessage):
        """处理接收到的延时消息"""
        try:
            # 解析消息体
            message_body = message.body.decode('utf-8')
            data = json.loads(message_body)
            order_id = data.get('order_id')
            
            print(f'📬 收到延时消息: order_id={order_id}')
            
            # 处理超时订单
            await self._handle_timeout_order(order_id)
            
        except Exception as e:
            print(f'❌ 处理消息失败: {e}')

    # ————————处理超时订单
    async def _handle_timeout_order(self, order_id: str):
        """
        处理超时未支付的订单
        1. 检查Redis中是否还有临时订单
        2. 如果有，说明超时未支付，归还库存并删除临时订单
        """
        try:
            # 检查临时订单是否还存在
            temp_order = await redis_client.get_temp_order(order_id)
            
            if temp_order:
                # 订单超时未支付，归还库存
                await redis_client.increase_stock()
                
                # 删除临时订单
                await redis_client.delete_temp_order(order_id)
                
                print(f'⏰ 订单超时处理完成: order_id={order_id}, 已归还库存')
            else:
                print(f'✅ 订单已处理: order_id={order_id}, 无需归还库存')
                
        except Exception as e:
            print(f'❌ 处理超时订单失败: order_id={order_id}, error={e}')

# 创建RabbitMQ客户端实例
rabbitmq_client = RabbitMQClient(
    host=settings.RABBITMQ_HOST,
    port=settings.RABBITMQ_PORT,
    username=settings.RABBITMQ_USER,
    password=settings.RABBITMQ_PASSWORD,
    queue_name=settings.RABBITMQ_QUEUE
)

# ——————————————创建FastAPI应用——————————————
import uvicorn
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from contextlib import asynccontextmanager
from datetime import datetime
import uuid
import random

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    
    # ————————启动阶段————————
    print('🚀 服务启动中...')
    
    # 1. 测试Redis连接
    try:
        await redis_client.ping()
    except Exception as e:
        print(f'❌ Redis连接失败: {e}')
        raise
    
    # 2. 初始化库存
    await redis_client.init_stock(settings.INITIAL_STOCK)
    
    # 3. 测试MongoDB连接
    try:
        await mongodb_client.ping()
    except Exception as e:
        print(f'❌ MongoDB连接失败: {e}')
        raise
    
    # 4. 启动RabbitMQ
    try:
        await rabbitmq_client.start()
    except Exception as e:
        print(f'❌ RabbitMQ连接失败: {e}')
        raise
    
    print('✅ 所有服务启动成功')
    
    yield  # 应用运行期间
    
    # ————————关闭阶段————————
    print('🛑 服务关闭中...')
    
    if redis_client:
        await redis_client.close()
    
    if mongodb_client:
        await mongodb_client.close()
    
    if rabbitmq_client:
        await rabbitmq_client.close()
    
    print('✅ 所有服务已关闭')

# 创建FastAPI应用
app = FastAPI(lifespan=lifespan, title="限量库存抽奖系统")

# ——————————————路由定义——————————————

# ————————健康检查
@app.get("/", summary="健康检查")
async def health_check():
    """健康检查端点"""
    stock = await redis_client.get_stock()
    return {
        "message": "ok",
        "service": "限量库存抽奖系统",
        "current_stock": stock
    }

# ————————获取当前库存
@app.get("/stock", summary="查询当前库存")
async def get_stock():
    """查询当前剩余库存"""
    stock = await redis_client.get_stock()
    return {
        "message": "查询成功",
        "stock": stock,
        "total": settings.INITIAL_STOCK,
        "sold": settings.INITIAL_STOCK - stock
    }

# ————————抽奖接口
class LotteryRequest(BaseModel):
    user_id: str  # 用户ID
    username: str  # 用户名

class LotteryResponse(BaseModel):
    success: bool  # 是否中奖
    message: str  # 提示信息
    order_id: Optional[str] = None  # 订单ID（中奖时返回）
    expire_time: Optional[str] = None  # 支付过期时间

@app.post("/lottery", response_model=LotteryResponse, summary="抽奖")
async def lottery(request: LotteryRequest):
    """
    抽奖接口
    流程：
    1. 检查库存是否充足
    2. 随机判断是否中奖（20%概率）
    3. 中奖：减少库存 -> 生成临时订单 -> 发送延时消息
    4. 未中奖：返回未中奖信息
    """
    
    # 1️⃣ 检查库存
    current_stock = await redis_client.get_stock()
    if current_stock <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="库存不足，抽奖已结束"
        )
    
    # 2️⃣ 随机判断是否中奖（20%概率）
    is_win = random.random() < settings.WIN_RATE
    
    if not is_win:
        return LotteryResponse(
            success=False,
            message="很遗憾，未中奖！再试试吧~"
        )
    
    # 3️⃣ 中奖流程
    # 3.1 减少库存（使用Lua脚本保证原子性）
    success = await redis_client.decrease_stock()
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="库存不足，抽奖已结束"
        )
    
    # 3.2 生成临时订单
    order_id = f"ORDER_{uuid.uuid4().hex[:16].upper()}"
    create_time = datetime.now()
    expire_time = create_time.timestamp() + settings.PAYMENT_TIMEOUT_SECONDS
    
    temp_order = {
        "order_id": order_id,
        "user_id": request.user_id,
        "username": request.username,
        "status": "pending",  # pending: 待支付
        "create_time": create_time.isoformat(),
        "expire_time": datetime.fromtimestamp(expire_time).isoformat()
    }
    
    # 3.3 保存临时订单到Redis（设置过期时间）
    await redis_client.save_temp_order(
        order_id=order_id,
        order_data=temp_order,
        expire_seconds=settings.PAYMENT_TIMEOUT_SECONDS
    )
    
    # 3.4 发送延时消息到RabbitMQ（超时检查）
    await rabbitmq_client.send_delay_message(
        order_id=order_id,
        delay_seconds=settings.PAYMENT_TIMEOUT_SECONDS
    )
    
    print(f'🎉 用户中奖: user_id={request.user_id}, order_id={order_id}')
    
    return LotteryResponse(
        success=True,
        message="恭喜中奖！请在5分钟内完成支付",
        order_id=order_id,
        expire_time=temp_order["expire_time"]
    )

# ————————查询临时订单
@app.get("/order/{order_id}", summary="查询临时订单")
async def get_temp_order(order_id: str):
    """查询临时订单状态"""
    order = await redis_client.get_temp_order(order_id)
    
    if not order:
        # 检查是否在MongoDB中（已支付订单）
        formal_order = await mongodb_client.get_order(order_id)
        if formal_order:
            # 转换MongoDB的ObjectId为字符串
            formal_order['_id'] = str(formal_order['_id'])
            return {
                "message": "订单已支付",
                "status": "paid",
                "order": formal_order
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="订单不存在或已超时"
            )
    
    return {
        "message": "查询成功",
        "status": "pending",
        "order": order
    }

# ————————放弃支付接口
@app.post("/order/{order_id}/cancel", summary="放弃支付")
async def cancel_order(order_id: str):
    """
    放弃支付接口
    流程：
    1. 检查临时订单是否存在
    2. 归还库存
    3. 删除临时订单
    """
    
    # 1️⃣ 检查临时订单
    order = await redis_client.get_temp_order(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在或已超时"
        )
    
    # 2️⃣ 归还库存
    await redis_client.increase_stock()
    
    # 3️⃣ 删除临时订单
    await redis_client.delete_temp_order(order_id)
    
    print(f'❌ 用户放弃支付: order_id={order_id}, 已归还库存')
    
    return {
        "message": "已取消订单，库存已归还",
        "order_id": order_id
    }

# ————————支付接口
@app.post("/order/{order_id}/pay", summary="完成支付")
async def pay_order(order_id: str):
    """
    完成支付接口
    流程：
    1. 检查临时订单是否存在
    2. 删除临时订单
    3. 生成正式订单保存到MongoDB
    """
    
    # 1️⃣ 检查临时订单
    temp_order = await redis_client.get_temp_order(order_id)
    if not temp_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在或已超时"
        )
    
    # 2️⃣ 删除临时订单
    await redis_client.delete_temp_order(order_id)
    
    # 3️⃣ 生成正式订单
    formal_order = {
        "order_id": temp_order["order_id"],
        "user_id": temp_order["user_id"],
        "username": temp_order["username"],
        "status": "paid",  # paid: 已支付
        "create_time": temp_order["create_time"],
        "pay_time": datetime.now().isoformat()
    }
    
    # 3.4 保存到MongoDB
    mongo_id = await mongodb_client.save_order(formal_order)
    
    print(f'💰 用户完成支付: order_id={order_id}, mongo_id={mongo_id}')
    
    return {
        "message": "支付成功！",
        "order_id": order_id,
        "mongo_id": mongo_id
    }

# ————————查询所有正式订单
@app.get("/orders", summary="查询所有正式订单")
async def get_all_orders(limit: int = 100):
    """查询所有已支付的正式订单"""
    orders = await mongodb_client.get_all_orders(limit=limit)
    
    # 转换MongoDB的ObjectId为字符串
    for order in orders:
        order['_id'] = str(order['_id'])
    
    return {
        "message": "查询成功",
        "total": len(orders),
        "orders": orders
    }

# ————————重置系统（仅供测试）
@app.post("/reset", summary="重置系统（测试用）")
async def reset_system():
    """
    重置系统（清空数据，恢复初始状态）
    ⚠️ 仅供测试使用
    """
    # 重置库存
    await redis_client.init_stock(settings.INITIAL_STOCK)
    
    # 清空MongoDB订单
    await mongodb_client.orders_collection.delete_many({})
    
    print('🔄 系统已重置')
    
    return {
        "message": "系统已重置",
        "stock": settings.INITIAL_STOCK
    }

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

    print("-" * 70)
    print("🎰 限量库存抽奖系统")
    print(f"🌐 服务器地址: http://{host}:{port}")
    print("-" * 70)
    print(f"健康检查:     GET    http://{host}:{port}/")
    print(f"查询库存:     GET    http://{host}:{port}/stock")
    print(f"抽奖:        POST   http://{host}:{port}/lottery")
    print(f"查询订单:     GET    http://{host}:{port}/order/{{order_id}}")
    print(f"放弃支付:     POST   http://{host}:{port}/order/{{order_id}}/cancel")
    print(f"完成支付:     POST   http://{host}:{port}/order/{{order_id}}/pay")
    print(f"查询订单列表: GET    http://{host}:{port}/orders")
    print(f"重置系统:     POST   http://{host}:{port}/reset")
    print(f"API文档:     http://{host}:{port}/docs")
    print("-" * 70)
    print(f"📦 初始库存: {settings.INITIAL_STOCK}")
    print(f"🎲 中奖概率: {settings.WIN_RATE * 100}%")
    print(f"⏰ 支付超时: {settings.PAYMENT_TIMEOUT_SECONDS}秒")
    print("-" * 70)

    uvicorn.run("server:app", host=host, port=port, reload=False)