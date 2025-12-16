# 拉取官方PostgreSQL镜像
docker pull postgres:15

# 创建容器并启动(第一次)
# 创建数据卷并启动
# PowerShell(win)命令
docker run -d `
  --name postgres `
  -p 5432:5432 `
  -e POSTGRES_DB=testdb `
  -e POSTGRES_USER=testuser `
  -e POSTGRES_PASSWORD=testpass `
  -v postgres_data:/var/lib/postgresql/data `
  postgres:15

# Bash Shell(linux)命令
docker run -d \
  --name postgres \
  -p 5432:5432 \
  -e POSTGRES_DB=testdb \
  -e POSTGRES_USER=testuser \
  -e POSTGRES_PASSWORD=testpass \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:15

解释
5432 PostgreSQL默认端口
POSTGRES_DB 创建默认数据库
POSTGRES_USER 数据库用户名
POSTGRES_PASSWORD 数据库密码
数据卷名称 postgres_data
容器内存储目录 /var/lib/postgresql/data

# 查看是否成功启动容器
docker ps --filter name=postgres

# 启动容器(对于已经存在的容器)
docker start postgres

# 关闭容器
docker stop postgres

# 删除容器
docker rm postgres