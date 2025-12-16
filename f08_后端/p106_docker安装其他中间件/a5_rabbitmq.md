# 拉取官方RabbitMQ镜像（包含管理界面）
docker pull rabbitmq:3-management

# 创建容器并启动(第一次)
# 创建数据卷并启动
# PowerShell(win)命令
docker run -d `
  --name rabbitmq `
  -p 5672:5672 `
  -p 15672:15672 `
  -e RABBITMQ_DEFAULT_USER=guest `
  -e RABBITMQ_DEFAULT_PASS=guest `
  -v rabbitmq_data:/var/lib/rabbitmq `
  rabbitmq:3-management

# Bash Shell(linux)命令
docker run -d \
  --name rabbitmq \ 
  -p 5672:5672 \
  -p 15672:15672 \
  -e RABBITMQ_DEFAULT_USER=guest \
  -e RABBITMQ_DEFAULT_PASS=guest \
  -v rabbitmq_data:/var/lib/rabbitmq \
  rabbitmq:3-management

解释
5672 用于连接程序
15672 用于连接网页
USER 用户名
PASS 密码
数据卷名称 rabbitmq_data 
容器内存储目录 /var/lib/rabbitmq

# 查看是否成功启动容器
docker ps --filter name=rabbitmq

# 启动容器(对于已经存在的容器)
docker start rabbitmq

# 关闭容器
docker stop rabbitmq

# 删除容器
docker rm rabbitmq
