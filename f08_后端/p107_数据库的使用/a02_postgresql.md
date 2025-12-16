# 进入docker容器并连接PostgreSQL
# 必须直连数据库
docker exec -it postgres psql -U testuser -d testdb

# 查看端口号
SHOW port;

# 退出
\q

# ——————————————数据库————————————
# 查看所有数据库
\l

# 创建数据库
CREATE DATABASE test_data;

# 进入数据库
\c test_data


# ——————————————表——————————————————
# 查看数据库中所有表
\dt

# 1 先创建表
CREATE TABLE IF NOT EXISTS "user" (
    id SERIAL PRIMARY KEY,
    name VARCHAR(20) NOT NULL,
    password CHAR(32) NOT NULL,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT idx_name UNIQUE (name)
);

# 2 再添加注释
COMMENT ON TABLE users IS '此表用来存储用户信息';
COMMENT ON COLUMN users.id IS '用户id 无需输入 自增';
COMMENT ON COLUMN users.name IS '用户名';
COMMENT ON COLUMN users.password IS '原始密码 -> md5进行hash -> 128bit -> 32位';
COMMENT ON COLUMN users.create_time IS '用户注册时间';
COMMENT ON COLUMN users.update_time IS '最后修改时间';

创建表 如果有则跳过 表名称为user
(
id列 自增整数类型 主键
name列 可变字符串 不允许为空 
password列 固定字符串 不允许为空
create_time列 timestamp类型 默认为当前时间戳
update_time列 timestamp类型 默认为当前时间戳(不会自动触发)
主键为(id列)
唯一索引确保不重复(name列)
)

# 查看表
\d users

# 查看表头
\d+ users

# 查询数据
SELECT * FROM users LIMIT 5;

# 添加列
ALTER TABLE users ADD COLUMN phone CHAR(11) NOT NULL DEFAULT '';
COMMENT ON COLUMN users.phone IS '手机号';
# 修改列名称
ALTER TABLE users RENAME COLUMN phone TO phonenumber;
# 删除列
ALTER TABLE users DROP COLUMN phonenumber;

# 写入数据
INSERT INTO users (name, password) VALUES 
    ('user1', 'e10adc3949ba59abbe56e057f20f883e'),
    ('user2', 'e10adc3949ba59abbe56e057f20f883e');

# 查看索引
\di

# 查看当前用户
SELECT current_user;

# 查看当前数据库
SELECT current_database();

# ——————————————权限———————————————
# 创建新账号
CREATE USER aaa WITH PASSWORD '12345';

# 给某账号某个库的权限
GRANT ALL PRIVILEGES ON DATABASE ddd TO aaa;

# 给某账号某个库中所有表的权限
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO aaa;

# 赋予所有权限（需要谨慎使用）
GRANT ALL PRIVILEGES ON DATABASE * TO aaa;

# 撤销权限
REVOKE ALL PRIVILEGES ON DATABASE ddd FROM aaa;

# 查看当前用户
SELECT current_user;

# 查看当前数据库
SELECT current_database();