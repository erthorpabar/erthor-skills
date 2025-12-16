# 拉取官方MongoDB镜像
docker pull mongo:7

# 创建容器并启动(第一次)
# 创建数据卷并启动
# PowerShell(win)命令
docker run -d `
  --name mongodb `
  -p 27017:27017 `
  -e MONGO_INITDB_ROOT_USERNAME=admin `
  -e MONGO_INITDB_ROOT_PASSWORD=admin123 `
  -e MONGO_INITDB_DATABASE=testdb `
  -v mongodb_data:/data/db `
  -v mongodb_config:/data/configdb `
  mongo:7

# Bash Shell(linux)命令
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=admin123 \
  -e MONGO_INITDB_DATABASE=testdb \
  -v mongodb_data:/data/db \
  -v mongodb_config:/data/configdb \
  mongo:7

解释
27017 MongoDB默认端口
MONGO_INITDB_ROOT_USERNAME root用户名
MONGO_INITDB_ROOT_PASSWORD root密码
MONGO_INITDB_DATABASE 创建默认数据库
数据卷名称 mongodb_data 数据库数据存储卷
数据卷名称 mongodb_config 配置文件存储卷（可选，用于持久化自定义配置）
容器内存储目录 /data/db 数据库文件存储位置
容器内存储目录 /data/configdb 配置文件存储位置

# 查看是否成功启动容器
docker ps --filter name=mongodb

# 启动容器(对于已经存在的容器)
docker start mongodb

# 关闭容器
docker stop mongodb

# 删除容器
docker rm mongodb
# 同时删除数据库
docker rm -v mongodb