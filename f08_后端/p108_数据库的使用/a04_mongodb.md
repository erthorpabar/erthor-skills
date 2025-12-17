# 进入docker容器并连接MongoDB
docker exec -it mongodb mongosh -u admin -p admin123 --authenticationDatabase admin

# 连接本地MongoDB
# mongosh -u admin -p admin123 --authenticationDatabase admin
mongosh "mongodb://admin:admin123@localhost:27017/?authSource=admin"

# 退出重新登陆
exit

# ——————————————数据库——————————————————
# 查看有哪些数据库
show dbs

# 创建数据库（使用use切换，插入数据时自动创建）
use test_data

# 进入库（切换数据库）
use test_data

# 查看当前数据库
db

# 删除数据库（需先切换到该数据库）
use test_data
db.dropDatabase()

# ——————————————集合（表）————————————————
# 查看有哪些集合（表）
show collections

# 创建集合（表）
db.createCollection("user")

创建集合 名为user
如果集合不存在，插入数据时会自动创建

# 查看集合结构（MongoDB是文档数据库，没有固定结构）
db.user.findOne()
或
db.user.find().limit(1)

# 查看集合统计信息
db.user.stats()

# 删除集合
db.user.drop()

# ——————————————数据操作————————————————
# 插入数据（单条）
db.user.insertOne(
    {name: "user1",password: "e10adc3949ba59abbe56e057f20f883e",create_time: new Date()}
)

# 插入数据（多条）
db.user.insertMany([
    {name: "user1", password: "e10adc3949ba59abbe56e057f20f883e", create_time: new Date()},
    {name: "user2", password: "e10adc3949ba59abbe56e057f20f883e", create_time: new Date()}
])

# 查询数据（所有）
db.user.find()

# 查询数据（条件查询）
db.user.find({name: "user1"})

# 查询数据（条件查询 - 不等于）
db.user.find({name: {$ne: ""}})

# 查询数据（条件查询 - 多条件）
db.user.find({name: {$ne: ""}, password: {$ne: ""}})

# 查询数据（排序）
db.user.find().sort({create_time: 1})  # 1升序 -1降序

# 查询数据（限制数量）
db.user.find().limit(5)

# 查询数据（跳过和限制 - 分页）
db.user.find().skip(0).limit(10)

# 查询数据（只返回指定字段）
db.user.find({}, {name: 1, password: 1, _id: 0})

# 更新数据（单条）
db.user.updateOne(
    {name: "user1"},
    {$set: {name: "zcy", update_time: new Date()}}
)

# 更新数据（多条）
db.user.updateMany(
    {create_time: {$lt: new Date("2025-01-16")}},
    {$set: {update_time: new Date()}}
)

# 更新或插入（不存在则插入）
db.user.updateOne(
    {name: "user1"},
    {$set: {name: "zcy", update_time: new Date()}},
    {upsert: true}
)

# 删除数据（单条）
db.user.deleteOne({name: "user1"})

# 删除数据（多条）
db.user.deleteMany({create_time: {$lt: new Date("2025-01-01")}})

# ——————————————索引————————————————
# 创建索引（单字段）
db.user.createIndex({name: 1})  # 1升序 -1降序

# 创建唯一索引
db.user.createIndex({name: 1}, {unique: true})

# 查看索引
db.user.getIndexes()

# 删除索引
db.user.dropIndex({name: 1})
或
db.user.dropIndex("name_1")

# 删除所有索引（除了_id）
db.user.dropIndexes()

# ——————————————权限———————————————
# 创建新用户
use admin
db.createUser({
    user: "testuser",
    pwd: "testpass",
    roles: [{role: "readWrite", db: "test_data"}]
})

# 查看用户
use admin
db.getUsers()

# 删除用户
use admin
db.dropUser("testuser")

# 修改用户密码
use admin
db.changeUserPassword("testuser", "newpassword")

# 给用户添加权限
use admin
db.grantRolesToUser("testuser", [{role: "read", db: "test_data"}])

# 撤销用户权限
use admin
db.revokeRolesFromUser("testuser", [{role: "read", db: "test_data"}]) 