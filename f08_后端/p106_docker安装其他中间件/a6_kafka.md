# 拉取Zookeeper镜像(先启动Zookeeper)
docker pull confluentinc/cp-zookeeper:latest

# 拉取Kafka镜像
docker pull confluentinc/cp-kafka:latest

# 启动Zookeeper
# PowerShell(win)命令
docker run -d `
  --name zookeeper `
  -p 2181:2181 `
  -e ZOOKEEPER_CLIENT_PORT=2181 `
  -e ZOOKEEPER_TICK_TIME=2000 `
  -v zookeeper_data:/var/lib/zookeeper/data `
  confluentinc/cp-zookeeper:latest

# Bash Shell(linux)命令
docker run -d \
  --name zookeeper \
  -p 2181:2181 \
  -e ZOOKEEPER_CLIENT_PORT=2181 \
  -e ZOOKEEPER_TICK_TIME=2000 \
  -v zookeeper_data:/var/lib/zookeeper/data \
  confluentinc/cp-zookeeper:latest

# 启动Kafka
# PowerShell(win)命令
docker run -d `
  --name kafka `
  -p 9092:9092 `
  -e KAFKA_BROKER_ID=1 `
  -e KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181 `
  -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 `
  -e KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 `
  -v kafka_data:/var/lib/kafka/data `
  --link zookeeper `
  confluentinc/cp-kafka:latest

# Bash Shell(linux)命令
docker run -d \
  --name kafka \
  -p 9092:9092 \
  -e KAFKA_BROKER_ID=1 \
  -e KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181 \
  -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 \
  -e KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 \
  -v kafka_data:/var/lib/kafka/data \
  --link zookeeper \
  confluentinc/cp-kafka:latest

解释
2181 Zookeeper端口
9092 Kafka端口
KAFKA_BROKER_ID Kafka代理ID
KAFKA_ZOOKEEPER_CONNECT Zookeeper连接地址
KAFKA_ADVERTISED_LISTENERS Kafka监听地址
KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR 副本因子
数据卷名称 zookeeper_data, kafka_data
容器内存储目录 /var/lib/zookeeper/data, /var/lib/kafka/data

# 查看是否成功启动容器
docker ps --filter name=kafka
docker ps --filter name=zookeeper

# 启动容器(对于已经存在的容器)
docker start zookeeper
docker start kafka

# 关闭容器
docker stop kafka
docker stop zookeeper

# 删除容器
docker rm kafka
docker rm zookeeper