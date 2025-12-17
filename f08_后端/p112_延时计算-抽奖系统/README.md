# 限量库存抽奖系统

## 📝 功能说明

这是一个基于 FastAPI 的限量库存抽奖系统，实现了以下功能：

1. **20%概率抽奖** - 用户参与抽奖，中奖率20%
2. **库存管理** - 使用Redis分布式锁防止超卖
3. **临时订单** - 中奖后生成临时订单，设置支付超时
4. **延时消息** - 使用RabbitMQ实现超时自动归还库存
5. **订单持久化** - 支付成功后订单保存到MongoDB

## 🛠️ 技术栈

- **FastAPI** - Web框架
- **Redis** - 库存管理 + 临时订单缓存
- **MongoDB** - 正式订单持久化
- **RabbitMQ** - 延时消息队列（替代RocketMQ，支持Windows）

## 📦 安装步骤

### 1. 启动中间件

#### Redis
```powershell
# PowerShell (Windows)
docker run -d `
  --name redis `
  -p 6379:6379 `
  -e REDIS_PASSWORD=redis123 `
  -v redis_data:/data `
  redis:7 redis-server --requirepass redis123
```

#### MongoDB
```powershell
# PowerShell (Windows)
docker run -d `
  --name mongodb `
  -p 27017:27017 `
  -e MONGO_INITDB_ROOT_USERNAME=admin `
  -e MONGO_INITDB_ROOT_PASSWORD=admin123 `
  -e MONGO_INITDB_DATABASE=lottery_db `
  -v mongodb_data:/data/db `
  mongo:7
```

#### RabbitMQ
```powershell
# PowerShell (Windows)
docker run -d `
  --name rabbitmq `
  -p 5672:5672 `
  -p 15672:15672 `
  -e RABBITMQ_DEFAULT_USER=guest `
  -e RABBITMQ_DEFAULT_PASS=guest `
  -v rabbitmq_data:/var/lib/rabbitmq `
  rabbitmq:3-management
```

访问 RabbitMQ 管理界面: http://localhost:15672
- 用户名: guest
- 密码: guest

### 2. 安装Python依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量（可选）

创建 `.env` 文件：

```env
# 服务器配置
HOST=0.0.0.0
PORT=8001

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=redis123

# MongoDB配置
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_USER=admin
MONGODB_PASSWORD=admin123
MONGODB_DATABASE=lottery_db

# RabbitMQ配置
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_QUEUE=lottery_timeout

# 业务配置
INITIAL_STOCK=100
WIN_RATE=0.2
PAYMENT_TIMEOUT_SECONDS=300
```

## 🚀 启动服务

```bash
python server.py
```

服务将在 http://localhost:8001 启动

API文档: http://localhost:8001/docs

## 🧪 测试

运行测试脚本：

```bash
python test.py
```

## 📡 API接口

### 1. 健康检查
```
GET /
```

### 2. 查询库存
```
GET /stock
```

### 3. 抽奖
```
POST /lottery
{
  "user_id": "user_1",
  "username": "测试用户"
}
```

### 4. 查询订单
```
GET /order/{order_id}
```

### 5. 完成支付
```
POST /order/{order_id}/pay
```

### 6. 放弃支付
```
POST /order/{order_id}/cancel
```

### 7. 查询所有订单
```
GET /orders?limit=100
```

### 8. 重置系统（测试用）
```
POST /reset
```

## 🔧 RabbitMQ 延时消息实现

本系统使用 RabbitMQ 的 **Dead Letter Exchange (DLX) + TTL** 机制实现延时消息：

1. **延时队列** (`lottery_timeout_delay`) - 接收带TTL的消息
2. **正式队列** (`lottery_timeout`) - 接收过期后的消息
3. **消费者** - 监听正式队列，处理超时订单

### 工作流程

```
发送延时消息 → 延时队列(TTL) → 消息过期 → DLX → 正式队列 → 消费者处理
```

## ⚙️ 核心机制

### 1. 分布式锁（防止超卖）
使用 Redis Lua 脚本保证库存扣减的原子性：

```lua
local stock = redis.call('GET', KEYS[1])
if tonumber(stock) > 0 then
    redis.call('DECR', KEYS[1])
    return 1
else
    return 0
end
```

### 2. 临时订单管理
- 中奖后在 Redis 创建临时订单（带过期时间）
- 支付成功：删除临时订单 → 保存到 MongoDB
- 放弃支付：删除临时订单 → 归还库存
- 超时未支付：自动归还库存

### 3. 单例模式
所有客户端（Redis、MongoDB、RabbitMQ）都使用单例模式，确保全局唯一实例

### 4. 连接池
- Redis: ConnectionPool（最大50个连接）
- MongoDB: AsyncIOMotorClient（最大50个连接）
- RabbitMQ: aio_pika 连接池

## 🐛 故障排查

### RabbitMQ连接失败
- 确保 Docker 容器已启动: `docker ps --filter name=rabbitmq`
- 检查端口是否被占用: 5672, 15672
- 查看容器日志: `docker logs rabbitmq`

### Redis连接失败
- 确认密码配置正确
- 检查端口 6379 是否开放

### MongoDB连接失败
- 确认用户名密码正确
- 检查端口 27017 是否开放

## 📊 监控

### RabbitMQ管理界面
访问 http://localhost:15672 查看：
- 队列状态
- 消息数量
- 消费者状态

### 日志输出
服务运行时会输出详细日志：
- ✅ 成功操作
- ❌ 错误信息
- 📨 消息发送
- 📬 消息接收
- 🎉 用户中奖
- 💰 支付成功
- ⏰ 订单超时

## 🔒 生产环境建议

1. **修改默认密码** - Redis、MongoDB、RabbitMQ
2. **启用SSL/TLS** - 所有服务间通信
3. **配置防火墙** - 限制端口访问
4. **监控告警** - 配置监控和日志系统
5. **备份数据** - 定期备份 MongoDB 和 Redis
6. **负载均衡** - 使用 Nginx 或其他负载均衡器
7. **关闭调试模式** - `reload=False`, `echo=False`

## 📄 License

MIT License












