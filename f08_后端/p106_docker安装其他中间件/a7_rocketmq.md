# 拉取RocketMQ镜像
docker pull apache/rocketmq:5.1.4

# 启动NameServer(先启动NameServer)
# PowerShell(win)命令
docker run -d `
  --name rocketmq-nameserver `
  -p 9876:9876 `
  -v rocketmq_nameserver_logs:/home/rocketmq/logs `
  -v rocketmq_nameserver_store:/home/rocketmq/store `
  -e JAVA_OPT_EXT="-server -Xms256m -Xmx256m" `
  apache/rocketmq:5.1.4 sh mqnamesrv

# Bash Shell(linux)命令
docker run -d \
  --name rocketmq-nameserver \
  -p 9876:9876 \
  -v rocketmq_nameserver_logs:/home/rocketmq/logs \
  -v rocketmq_nameserver_store:/home/rocketmq/store \
  -e JAVA_OPT_EXT="-server -Xms256m -Xmx256m" \
  apache/rocketmq:5.1.4 sh mqnamesrv

# 启动Broker
# PowerShell(win)命令
docker run -d `
  --name rocketmq-broker `
  -p 10909:10909 `
  -p 10911:10911 `
  -p 10912:10912 `
  -e NAMESRV_ADDR=rocketmq-nameserver:9876 `
  -e JAVA_OPT_EXT="-server -Xms256m -Xmx256m" `
  -v rocketmq_broker_logs:/home/rocketmq/logs `
  -v rocketmq_broker_store:/home/rocketmq/store `
  --link rocketmq-nameserver `
  apache/rocketmq:5.1.4 sh mqbroker -n rocketmq-nameserver:9876

# Bash Shell(linux)命令
docker run -d \
  --name rocketmq-broker \
  -p 10909:10909 \
  -p 10911:10911 \
  -p 10912:10912 \
  -e NAMESRV_ADDR=rocketmq-nameserver:9876 \
  -e JAVA_OPT_EXT="-server -Xms256m -Xmx256m" \
  -v rocketmq_broker_logs:/home/rocketmq/logs \
  -v rocketmq_broker_store:/home/rocketmq/store \
  --link rocketmq-nameserver \
  apache/rocketmq:5.1.4 sh mqbroker -n rocketmq-nameserver:9876

解释
9876 NameServer端口(客户端连接NameServer查询路由信息)
10909 Broker VIP通道端口(高优先级消息通道)
10911 Broker普通通道端口(客户端发送和接收消息)
10912 Broker HA通道端口(主从同步端口)
NAMESRV_ADDR NameServer连接地址(Broker注册到NameServer)
JAVA_OPT_EXT JVM启动参数(设置堆内存大小)
数据卷名称 rocketmq_nameserver_logs (NameServer运行日志)
数据卷名称 rocketmq_nameserver_store (NameServer元数据存储)
数据卷名称 rocketmq_broker_logs (Broker运行日志)
数据卷名称 rocketmq_broker_store (Broker消息存储、索引文件、消费进度等)
容器内存储目录 /home/rocketmq/logs (统一存储 日志文件目录)
容器内存储目录 /home/rocketmq/store (统一存储 数据存储目录)

# 查看是否成功启动容器
docker ps --filter name=rocketmq-nameserver
docker ps --filter name=rocketmq-broker

# 启动容器(对于已经存在的容器)
docker start rocketmq-nameserver
docker start rocketmq-broker

# 关闭容器
docker stop rocketmq-broker
docker stop rocketmq-nameserver

# 删除容器
docker rm rocketmq-broker
docker rm rocketmq-nameserver

# 依赖关系说明
RocketMQ需要启动两个组件:
1. NameServer - 服务注册中心,管理Broker路由信息
2. Broker - 消息存储和转发服务器

启动顺序: 必须先启动NameServer,再启动Broker
原因: Broker启动时需要向NameServer注册,如果NameServer未启动则Broker无法正常运行