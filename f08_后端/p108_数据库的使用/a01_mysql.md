# 进入docker容器并连接MySQL
docker exec -it mysql mysql -u root -p

# 连接本地MySQL
# 先启动
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p
mysql -h localhost -P 3306 -u root -p

# 退出重新登陆
EXIT;

# ——————————————数据库——————————————————
# 查看有哪些库
SHOW DATABASES;

# 创建数据库
CREATE DATABASE test_data;

# 进入库
use test_data;

# ——————————————表————————————————
# 查看有哪些表
show tables;

# 创建表
create table if not exists user(
	id int auto_increment comment '用户id 无需输入 自增',
	name varchar(20) not null comment '用户名',
	password char(32) not null comment '密码 -> md5进行hash -> 128bit -> 32位',
    create_time datetime default current_timestamp comment '用户注册时间',
    update_time datetime default current_timestamp on update current_timestamp comment '最后修改时间',
	primary key (id), -- 主键
	unique key idx_name (name) -- 对某列创建唯一索引 确保不重复
)default charset=utf8mb4 comment '此表用来存储用户信息'; -- 设置编码方式位utf-8


创建表 如果有则跳过 表名称为user
(
id列 可变字符串 不允许为空 
name列 固定字符串 不允许为空 
password列 固定字符串 不允许为空
create_time列 datatime类型 默认为当前时间戳
update_time列 datatime类型 默认为更新时候的时间戳
主键为(id列)
唯一索引确保不重复(name列)
)
设置解码方式 


# 查看表头
desc user;
或
show create table user;

# 查看前几行
SELECT * FROM user LIMIT 5;
# 查询
select name,password from user where name!='' and password !='' order by create_time ;

# 添加列
alter table user add phonenumber char(11) not null default '' comment '手机号';
# 修改列名称
alter table user change phonenumber phone char(11) not null default '' comment '手机号';
# 删除列
alter table user drop phone;

# 写入数据
insert into user (name,password) values 
    ("user1","e10adc3949ba59abbe56e057f20f883e"),
    ("user2","e10adc3949ba59abbe56e057f20f883e");

# 修改整行
update user set name='zcy' where create_time>20250116;
# 删除整行
delete from user where create_time<20250101;

# 删除表
drop table user;




# ——————————————权限———————————————
# 创建新账号
CREATE USER 'aaa' IDENTIFIED BY '12345';

# 给某账号某个库的权限
GRANT ALL PRIVILEGES ON ddd.* to aaa;

# 赋予所有权限
GRANT ALL PRIVILEGES ON *;


