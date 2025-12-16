# 拉取官方MySQL镜像
docker pull mysql:8.0

# 创建容器并启动(第一次)
# 创建数据卷并启动
# PowerShell(win)命令
docker run -d `
  --name mysql `
  -p 3306:3306 `
  -e MYSQL_ROOT_PASSWORD=123 `
  -e MYSQL_DATABASE=testdb `
  -e MYSQL_USER=testuser `
  -e MYSQL_PASSWORD=testpass `
  -v mysql_data:/var/lib/mysql `
  mysql:8.0

# Bash Shell(linux)命令
docker run -d \
  --name mysql \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=123 \
  -e MYSQL_DATABASE=testdb \
  -e MYSQL_USER=testuser \
  -e MYSQL_PASSWORD=testpass \
  -v mysql_data:/var/lib/mysql \
  mysql:8.0

解释
3306 MySQL默认端口
MYSQL_ROOT_PASSWORD root用户密码
MYSQL_DATABASE 创建默认数据库
MYSQL_USER 创建普通用户
MYSQL_PASSWORD 普通用户密码
数据卷名称 mysql_data
容器内存储目录 /var/lib/mysql

# 查看是否成功启动容器
docker ps --filter name=mysql

# 启动容器(对于已经存在的容器)
docker start mysql

# 关闭容器
docker stop mysql

# 删除容器
docker rm mysql