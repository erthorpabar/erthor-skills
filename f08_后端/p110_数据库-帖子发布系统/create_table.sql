create database post;   -- 建库
create user 'tester' identified by '123456';     -- 创建用户
grant all on post.* to tester;   -- 授予用户权限
use post;

-- 建表
create table if not exists user(
	id int auto_increment comment '用户id 自增',
	name varchar(20) not null comment '用户名',
	password char(32) not null comment '密码的md5',
    create_time datetime default current_timestamp comment '用户注册时间',
    update_time datetime default current_timestamp on update current_timestamp comment '最后修改时间',
	primary key (id),
	unique key idx_name (name)
)default charset=utf8mb4 comment '用户信息';

create table if not exists news(
	id int auto_increment comment '新闻id',
	user_id int not null comment '发布者id',
	title varchar(100) not null comment '新闻标题',
	article text not null comment '正文',
    create_time datetime default current_timestamp comment '发布时间',
    update_time datetime default current_timestamp on update current_timestamp comment '最后修改时间',
    delete_time datetime default null comment '删除时间',
	primary key (id),
	key idx_user (user_id)
)default charset=utf8mb4 comment '新闻';