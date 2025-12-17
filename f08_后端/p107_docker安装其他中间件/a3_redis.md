# 拉取官方Redis镜像
docker pull redis:7

# 创建容器并启动(第一次)
# ————创建数据卷并启动
# PowerShell(win)命令
docker run -d `
  --name redis `
  -p 6379:6379 `
  -e REDIS_PASSWORD=redis123 `
  -v redis_data:/data `
  redis:7 redis-server --requirepass redis123

# Bash Shell(linux)命令
docker run -d \
  --name redis \
  -p 6379:6379 \
  -e REDIS_PASSWORD=redis123 \
  -v redis_data:/data \
  redis:7 redis-server --requirepass redis123

# ————或者使用配置文件启动(推荐)
# PowerShell(win)命令
docker run -d `
  --name redis `
  -p 6379:6379 `
  -v redis_data:/data `
  -v redis_config:/usr/local/etc/redis `
  redis:7 redis-server /usr/local/etc/redis/redis.conf

# Bash Shell(linux)命令
docker run -d \
  --name redis \
  -p 6379:6379 \
  -v redis_data:/data \
  -v redis_config:/usr/local/etc/redis \
  redis:7 redis-server /usr/local/etc/redis/redis.conf

# ————带持久化配置的启动命令
# PowerShell(win)命令
docker run -d `
  --name redis `
  -p 6379:6379 `
  -e REDIS_PASSWORD=redis123 `
  -v redis_data:/data `
  redis:7 redis-server --requirepass redis123 --appendonly yes

# Bash Shell(linux)命令
docker run -d \
  --name redis \
  -p 6379:6379 \
  -e REDIS_PASSWORD=redis123 \
  -v redis_data:/data \
  redis:7 redis-server --requirepass redis123 --appendonly yes

解释
6379 Redis默认端口
REDIS_PASSWORD Redis密码
--requirepass 设置密码
--appendonly yes 启用AOF持久化
数据卷名称 redis_data
容器内存储目录 /data
配置文件目录 /usr/local/etc/redis

# 查看是否成功启动容器
docker ps --filter name=redis

# 连接Redis客户端测试
docker exec -it redis redis-cli -a redis123

# 启动容器(对于已经存在的容器)
docker start redis

# 关闭容器
docker stop redis

# 删除容器
docker rm redis

# Redis集群模式(3主3从)
# 创建Redis集群网络
docker network create redis-cluster

# 启动6个Redis节点
for i in {1..6}; do
  docker run -d \
    --name redis-node-$i \
    --net redis-cluster \
    -p $((7000+i)):6379 \
    -v redis-node-$i:/data \
    redis:7 redis-server --port 6379 --cluster-enabled yes --cluster-config-file nodes.conf --cluster-node-timeout 5000 --appendonly yes
done

# 创建集群
docker exec -it redis-node-1 redis-cli --cluster create \
  $(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' redis-node-1):6379 \
  $(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' redis-node-2):6379 \
  $(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' redis-node-3):6379 \
  $(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' redis-node-4):6379 \
  $(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' redis-node-5):6379 \
  $(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' redis-node-6):6379 \
  --cluster-replicas 1