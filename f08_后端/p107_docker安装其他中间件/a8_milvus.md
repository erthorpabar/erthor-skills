# 
milvus 有三个版本
lite - 轻量版
standalone - 单机版
distributed - 分布式版

# 
standalone需要同时运行三个容器
etcd 存储元数据
minlo 存储向量数据和索引
milvus 主服务

# Docker Compose 一条命令启动所有服务(自动拉取缺失镜像)
docker-compose up -d

# 停止服务
docker-compose stop 

# 删除容器
docker-compose down

# 删除容器 和 数据卷
docker-compose down -v

# 默认端口号
19530