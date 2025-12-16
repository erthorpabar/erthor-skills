
# docker介绍
等价于配置好的linux环境

# 下载docker
docker desktop

# (linux系统中)权限
sudo usermod -aG docker $USER
newgrp docker

# 查看当前存在的镜像
docker image ls

# 拉取镜像
docker pull python:latest

# 构建当前文件夹的镜像(cd到当前文件夹)
docker build -t aaa:v1.0.0 .

# 启动镜像
docker run -d -p 80:7005 aaa:v1.0.0
-d 容器后台运行
-p 内部到外部的映射端口号

# 启动镜像 - 命令行
docker run -it python:latest

# 关闭镜像
docker stop 5f74ab2b2f24


# 开启多个镜像实例
docker run -d -P aaa:v1.0.0
# 查看映射情况
docker ps


# ——————————————下载kafka(kraft模式无需zookeeper)———————————————
# 下载镜像
docker pull confluentinc/cp-kafka:latest

# 创建数据卷 可以被多个容器共享 独立于容器存在
docker volume create kafka-data

# 删除现有容器（如果存在）
docker rm -f kafka

# 启动Kafka镜像 (KRaft模式，无需Zookeeper)
''' 
-d 后台运行
--name 创建的容器名称
KAFKA_NODE_ID 节点ID
KAFKA_PROCESS_ROLES controller,broker 角色设置
KAFKA_CONTROLLER_QUORUM_VOTERS 控制器选举配置
KAFKA_LISTENERS 监听地址
KAFKA_ADVERTISED_LISTENERS 客户端连接地址
KAFKA_CONTROLLER_LISTENER_NAMES 控制器监听器名称
KAFKA_LISTENER_SECURITY_PROTOCOL_MAP 协议映射
KAFKA_LOG_DIRS 日志目录
外：内 端口号映射
数据卷名称：默认存储数据目录
指定要运行的镜像
'''
docker run -d `
  --name kafka `
  -p 9092:9092 `
  -p 9093:9093 `
  -e KAFKA_NODE_ID=1 `
  -e KAFKA_PROCESS_ROLES=controller,broker `
  -e KAFKA_CONTROLLER_QUORUM_VOTERS=1@kafka:9093 `
  -e KAFKA_LISTENERS=PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093 `
  -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 `
  -e KAFKA_CONTROLLER_LISTENER_NAMES=CONTROLLER `
  -e KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT `
  -e KAFKA_LOG_DIRS=/var/lib/kafka/data `
  -v kafka-data:/var/lib/kafka/data `
  apache/kafka:latest

docker run -d `
  --name kafka `
  -p 9092:9092 `
  -e KAFKA_BROKER_ID=1 `
  -e KAFKA_ZOOKEEPER_CONNECT=localhost:2181 `
  -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 `
  -e KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 `
  -e KAFKA_AUTO_CREATE_TOPICS_ENABLE=true `
  confluentinc/cp-kafka:latest

8a26cde55d3f2d002333d0a7d64dfc97208ef57069c67f0636a01b7000cc2243

# 容器内部操作
# 创建topic
docker exec -it kafka /opt/kafka/bin/kafka-topics.sh --create --topic ttt --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

# 删除topic
docker exec -it kafka /opt/kafka/bin/kafka-topics.sh --delete --topic ttt --bootstrap-server localhost:9092

# 查看topic列表
docker exec -it kafka /opt/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092

# 查看topic详细信息
docker exec -it kafka /opt/kafka/bin/kafka-topics.sh --describe --topic ttt --bootstrap-server localhost:9092

# 进入 生产者发送消息 模式
docker exec -it kafka /opt/kafka/bin/kafka-console-producer.sh --topic ttt --bootstrap-server localhost:9092

# 消费者接收消息
docker exec -it kafka /opt/kafka/bin/kafka-console-consumer.sh --topic ttt --from-beginning --bootstrap-server localhost:9092

# 查看Kafka容器日志（排查问题时使用）
docker logs kafka

# 查看容器状态
docker ps -a


# ——————————————下载timescale数据库————————————————————
# 下载镜像
docker pull timescale/timescaledb:latest-pg17
# 创建数据卷 可以被多个容器共享 独立于容器存在
docker volume create timescale-data
# 启动数据库镜像
''' 
-d 后台运行
name 创建的容器名称
POSTGRES_USER 用户名
POSTGRES_PASSWORD 密码
POSTGRES_DB 数据库名称
外：内 端口号映射
数据卷名称：默认存储数据目录
指定要运行的镜像
'''
docker run -d --name ccc -e POSTGRES_USER=aaa -e POSTGRES_PASSWORD=1234 -e POSTGRES_DB=ddd -p 5432:5432 -v ttt-data:/var/lib/postgresql/data timescale/timescaledb:latest-pg17

docker run -d \
  --name ccc \
  -e POSTGRES_USER=aaa \
  -e POSTGRES_PASSWORD=1234 \
  -e POSTGRES_DB=ddd \
  -p 5432:5432 \
  -v timescale-data:/var/lib/postgresql/data \
  timescale/timescaledb:latest-pg17
# 容器内部连接
docker exec -it ccc psql -U aaa -d ddd
# 外部连接
psql -h localhost -p 5432 -U aaa -d ddd