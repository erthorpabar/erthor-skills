''' 
帖子发布系统 
'''

# ——————————当前文件夹路径加入搜索路径——————————
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ——————————加载环境变量——————————
from dotenv import load_dotenv
load_dotenv()

from pydantic_settings import BaseSettings # 优先系统环境变量，然后是.env文件，最后是默认值
class Settings(BaseSettings):
    
    # 🌐 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 🗄️ 数据库配置
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "123"
    MYSQL_DATABASE: str = "testdb"
    DROP_TABLES_ON_START: bool = True  # 启动时是否删除旧表重建(生产环境设为False)

    # 📦 Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = "redis123"

    # 🔐 JWT配置
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24
    
    class Config:
        # 指定从.env文件加载环境变量
        env_file = ".env" # 允许从.env文件加载配置
        env_file_encoding = "utf-8" # 指定编码
        extra = "allow" # 允许额外的没用到的配置
        case_sensitive = True  # 环境变量大小写敏感


# 创建Settings的实例
# 在其他文件中，你可以通过导入settings来访问这些配置
settings = Settings()

# ———————————————————单例模式————————————————————
'''单例'''
from threading import Lock
class SingletonMeta(type):
    _instances = {}
    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]

# ———————————————————redis连接——————————————————
import redis.asyncio as redis
from typing import Optional  # 提前导入 Optional 类型

class RedisClient(metaclass=SingletonMeta):
    def __init__(self, host, port, db, password=None):
        self.host = host
        self.port = port
        self.db = db
        self.password = password

        # ————————a简单连接
        # self.client = Redis(host=host, port=port, db=db, password=password)

        # ————————b池连接
        # 有密码和无密码的连接url不同
        if password:
            redis_url = f"redis://:{password}@{host}:{port}/{db}"
        else:
            redis_url = f"redis://{host}:{port}/{db}"

        self.pool = redis.ConnectionPool.from_url(
            redis_url,
            max_connections=20,
            retry_on_timeout=True,
            health_check_interval=0,        # 禁用健康检查
            socket_connect_timeout=5,       # 连接超时5秒
            socket_timeout=None,            # 修改：无限超时，允许brpop长时间阻塞
            retry_on_error=[redis.ConnectionError, redis.TimeoutError]
        )
        self.client = redis.Redis(connection_pool=self.pool)

    # ————————测试连接成功
    async def ping(self):
        try:
            await self.client.ping()
            print('✅ Redis连接成功')
        except Exception as e:
            print(f'❌ Redis连接失败: {e}')
            raise
    
    # ————————关闭连接
    async def close(self):
        await self.client.close()  
        await self.pool.disconnect() 
        print('✅ Redis连接已关闭')

    # ————————缓存登陆状态
    async def cache_login_status(self, token: str, user_id: int, expire_hours: int = 24):
        """
        缓存用户登录状态到Redis
        
        Args:
            token: JWT token
            user_id: 用户ID
            expire_hours: 过期时间（小时），默认24小时
        """
        await self.client.setex(
            f"token:{token}", # Redis key
            expire_hours * 3600, # 过期时间（秒）
            str(user_id) # 存储用户ID
        )

    # ————————删除登陆状态
    async def delete_login_status(self, token: str):
        """
        删除用户登录状态（登出）
        
        Args:
            token: JWT token
        """
        await self.client.delete(f"token:{token}")
    
    # ————————验证登陆状态
    async def verify_login_status(self, token: str) -> Optional[int]:
        """
        验证用户登录状态
        
        Args:
            token: JWT token
            
        Returns:
            用户ID（如果已登录）或 None（如果未登录）
        """
        user_id = await self.client.get(f"token:{token}")
        if user_id:
            return int(user_id)
        return None
        

# 
redis_client = RedisClient(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD
        )

# ————————————————————数据库——————————————————————
# 连接 异步qsl str
mysql_async = f"mysql+asyncmy://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}?charset=utf8mb4"
# 连接 同步sql str
mysql_sync = f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}?charset=utf8mb4"

'''  
操作数据库的orm框架
sqlalchemy[asyncio]

异步驱动
asyncmy

Microsoft C++ Build 工具
https://visualstudio.microsoft.com/visual-cpp-build-tools/
'''
# 异步连接mysql数据库
from sqlalchemy.ext.asyncio import create_async_engine

# 1 创建engine对象 负责 连接数据库 (不操作数据库)
sql_engine_async = create_async_engine(
    mysql_async,
    echo = False, # 打印sql语句
    pool_size = 10, # 连接池大小
    max_overflow = 20, # 最大连接数
    pool_timeout = 10, # 连接超时时间
    pool_recycle = 3600, # 回收时间
    pool_pre_ping = True, # 连接前测试是否可用
    )

# 2 创建session对象 负责 操作数据库
from sqlalchemy.ext.asyncio import AsyncSession,async_sessionmaker

AsyncSessionFactory = async_sessionmaker(
    sql_engine_async,  # 第一个位置参数直接传 engine
    class_ = AsyncSession,  # 异步session类
    autoflush = True,  # 查找之前自动刷新session以查找最新数据
    expire_on_commit = False,  # 提交后是否过期
)

# 3 定义base类 -> 对应一张表
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, Text, select, func

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'user'  
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment='用户id 自增')
    name: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, comment='用户名')
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, comment='用户邮箱')
    password: Mapped[str] = mapped_column(String(32), nullable=False, comment='密码的md5')
    create_time: Mapped[datetime] = mapped_column(DateTime, default=func.now(), comment='用户注册时间')
    update_time: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), comment='最后修改时间')



class News(Base):
    __tablename__ = 'post'  
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment='新闻id')
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, comment='发布者id')
    title: Mapped[str] = mapped_column(String(100), nullable=False, comment='新闻标题')
    article: Mapped[str] = mapped_column(Text, nullable=False, comment='正文')
    create_time: Mapped[datetime] = mapped_column(DateTime, default=func.now(), comment='发布时间')
    update_time: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), comment='最后修改时间')
    delete_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, default=None, comment='删除时间')

# 4 同步创建所有表
# sqlalchemy自动追踪 数据库表结构 自动创建表
if settings.DROP_TABLES_ON_START: # 如果需要删除旧表重建
    print('⚠️ 开发模式 删除旧表并重建')
    
    from sqlalchemy import create_engine
    sql_engine_sync = create_engine(mysql_sync)
    
    # 先删除所有表（如果存在）
    Base.metadata.drop_all(bind=sql_engine_sync)
    print('✅ 已删除所有旧表')
    
    # 再创建所有表
    Base.metadata.create_all(bind=sql_engine_sync)
    print('✅ 已创建所有新表')
    
    # 关闭同步引擎连接
    sql_engine_sync.dispose()


# ——————————————创建app——————————————
import uvicorn
from fastapi import FastAPI

# 生命周期函数
from contextlib import asynccontextmanager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 测试 sql连接
    global sql_engine_async, AsyncSessionFactory
    try:
        async with sql_engine_async.begin() as conn:
            await conn.run_sync(lambda _: None)
        print('✅ SQL连接成功')
    except Exception as e:
        print(f'❌ SQL连接失败: {e}')
        raise

    # 测试 redis连接
    global redis_client
    try:
        await redis_client.ping()
        print('✅ Redis连接成功')
    except Exception as e:
        print(f'❌ Redis连接失败: {e}')
        raise

    yield # 应用运行期间

    # 关闭阶段
    print('🛑 服务器关闭')
    if sql_engine_async:
        await sql_engine_async.dispose()
        print('✅ SQL连接已关闭')
    if redis_client:
        await redis_client.close()
        print('✅ Redis连接已关闭')


# 实例化app
app = FastAPI(lifespan=lifespan, title="帖子发布系统")

# ——————————————路由——————————————
@app.get("/", summary="健康检查")
async def online():
    """健康检查端点"""
    return {"message": "ok", "service": "帖子发布系统"}

# ————————————路由 写入数据库——————————————
from pydantic import BaseModel

#  写入数据
from sqlalchemy.exc import IntegrityError
from pydantic import field_validator, EmailStr
from fastapi import HTTPException, status

# ————————注册用户
class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str

    @field_validator('password')  # 新的装饰器
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码至少6位')
        return v

import hashlib
def hash_password(password: str) -> str:
    """使用MD5加密密码"""
    return hashlib.md5(password.encode('utf-8')).hexdigest()


@app.post("/register", summary="用户注册")
async def register(request: UserRegister): 
     # 对密码进行MD5加密
    hashed_password = hash_password(request.password)
    
    # 异步上下文管理器
    async with AsyncSessionFactory() as session: # 异步session
        try:
            async with session.begin(): # 开启异步事务 事务结束自动commit
                # 获取写入值
                new_user = User(
                    email=request.email.lower(),  # 邮箱转小写
                    name=request.username,         # 用户名
                    password=hashed_password       # 加密后的密码
                )

                # 写入
                session.add(new_user)

                # 刷新获取自增ID
                await session.flush()

         # 出错自动回滚
        except IntegrityError:
            raise HTTPException(status_code=400, detail="邮箱或用户名已存在")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"写入失败: {str(e)}")

    return {
                "message": "注册成功",
                "user_id": new_user.id,
                "username": new_user.name
            }


# ————————登录用户
import jwt
# 添加JWT生成函数（放在hash_password函数下面）
def create_jwt_token(user_id: int) -> str:
    """生成JWT token"""
    from datetime import timezone
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token

class UserLogin(BaseModel):
    email: EmailStr
    password: str

@app.post("/login", summary="用户登录")
async def login(request: UserLogin):
    # 对密码进行MD5加密
    hashed_password = hash_password(request.password)
    
    # 异步上下文管理器
    async with AsyncSessionFactory() as session:
        try:
            # 查询用户
            stmt = select(User).where(
                User.email == request.email.lower(),
                User.password == hashed_password
            )
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            # 验证用户
            if not user:
                raise HTTPException(status_code=401, detail="邮箱或密码错误")
            
            # 生成JWT token
            token = create_jwt_token(user.id)

            # 将token存入Redis，设置过期时间
            await redis_client.cache_login_status(token, user.id)

            
            return {
                "message": "登录成功",
                "token": token,
                "user_id": user.id,
                "username": user.name,
                "email": user.email
            }
            
        except HTTPException:
            raise
        except Exception as e:
            print(f"❌ 登录失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="登录失败"
            )

# ————————用户登出
from fastapi import Header

# 添加JWT验证函数（放在create_jwt_token函数下面）
async def verify_jwt_token(token: str) -> dict:
    """验证JWT token并检查Redis登录状态"""
    try:
        # 1. 验证JWT token本身
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        
        # 2. 检查Redis中的登录状态
        user_id = await redis_client.verify_login_status(token)
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token已失效，请重新登录")
        
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的Token")
    except HTTPException:
        raise

@app.post("/logout", summary="用户登出")
async def logout(authorization: str = Header(None)):
    """
    用户登出（从Redis删除登录状态）
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供Token")
    
    # 提取token（格式: "Bearer <token>"）
    try:
        token = authorization.split(" ")[1]
    except IndexError:
        raise HTTPException(status_code=401, detail="Token格式错误")
    
    # 只验证JWT格式，不检查Redis（因为可能已经过期）
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("user_id")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的Token")
    
    # 从Redis删除登录状态（如果存在的话）
    await redis_client.delete_login_status(token)
    
    return {
        "message": "登出成功",
        "user_id": user_id
    }

# ————————获取当前用户信息
@app.get("/me", summary="获取当前用户信息")
async def get_current_user_info(authorization: str = Header(None)):
    """
    获取当前登录用户的信息
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供Token")
    
    # 提取token
    try:
        token = authorization.split(" ")[1]
    except IndexError:
        raise HTTPException(status_code=401, detail="Token格式错误")
    
    # 验证JWT token
    payload = await verify_jwt_token(token)
    user_id = payload.get("user_id")
    
    # 查询用户信息
    async with AsyncSessionFactory() as session:
        try:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(status_code=404, detail="用户不存在")
            
            return {
                "user_id": user.id,
                "username": user.name,
                "email": user.email,
                "create_time": user.create_time.isoformat(),
                "update_time": user.update_time.isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


# ————————发布帖子
class NewsCreate(BaseModel):
    title: str
    article: str
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if len(v) < 1 or len(v) > 100:
            raise ValueError('标题长度必须在1-100字符之间')
        return v
    
    @field_validator('article')
    @classmethod
    def validate_article(cls, v):
        if len(v) < 1:
            raise ValueError('正文不能为空')
        return v

@app.post("/news", summary="发布帖子")
async def create_news(request: NewsCreate, authorization: str = Header(None)):
    """
    发布新帖子
    步骤：
    1. 验证token获取用户ID
    2. 创建News记录
    3. 返回创建的帖子信息
    """
    # 1️⃣ 验证token
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供Token")
    
    try:
        token = authorization.split(" ")[1]
    except IndexError:
        raise HTTPException(status_code=401, detail="Token格式错误")
    
    # 验证JWT token并获取用户ID
    payload = await verify_jwt_token(token)
    user_id = payload.get("user_id")
    
    # 2️⃣ 创建帖子
    async with AsyncSessionFactory() as session:
        try:
            async with session.begin():
                # 创建新帖子
                new_news = News(
                    user_id=user_id,
                    title=request.title,
                    article=request.article
                )
                
                # 写入数据库
                session.add(new_news)
                await session.flush()  # 刷新获取自增ID
                
                # 刷新对象以确保所有属性都已加载
                await session.refresh(new_news)
                
                # 在事务块内获取所有需要的值并格式化
                news_id = new_news.id
                news_title = new_news.title
                news_create_time_str = new_news.create_time.isoformat()
                
            # 3️⃣ 返回结果（事务已提交）
            return {
                "message": "发布成功",
                "news_id": news_id,
                "title": news_title,
                "create_time": news_create_time_str
            }
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"发布失败: {str(e)}"
            )

# ————————获取帖子统计列表
@app.get("/news", summary="获取帖子列表")
async def get_news_list(
    page: int = 1,
    page_size: int = 10
):
    """
    获取帖子列表（分页，仅未删除的帖子）
    步骤：
    1. 计算分页参数
    2. 查询未删除的帖子（delete_time为None）
    3. 获取帖子总数
    4. 返回列表和统计信息
    """
    # 1️⃣ 验证分页参数
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 10
    
    # 计算偏移量
    offset = (page - 1) * page_size
    
    async with AsyncSessionFactory() as session:
        try:
            # 2️⃣ 查询未删除的帖子列表（按创建时间倒序）
            stmt = (
                select(News, User.name.label('username'))
                .join(User, News.user_id == User.id)
                .where(News.delete_time.is_(None))
                .order_by(News.create_time.desc())
                .offset(offset)
                .limit(page_size)
            )
            result = await session.execute(stmt)
            news_list = result.all()
            
            # 3️⃣ 查询总数
            count_stmt = select(func.count(News.id)).where(News.delete_time.is_(None))
            count_result = await session.execute(count_stmt)
            total = count_result.scalar()
            
            # 4️⃣ 组装返回数据
            news_data = [
                {
                    "id": news.id,
                    "title": news.title,
                    "user_id": news.user_id,
                    "username": username,
                    "create_time": news.create_time.isoformat(),
                    "update_time": news.update_time.isoformat()
                }
                for news, username in news_list
            ]
            
            return {
                "message": "查询成功",
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
                "data": news_data
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"查询失败: {str(e)}"
            )

# ————————按id获取帖子详情
@app.get("/news/{news_id}", summary="获取帖子详情")
async def get_news_detail(news_id: int):
    """
    根据ID获取帖子详情
    步骤：
    1. 根据ID查询帖子
    2. 检查帖子是否存在且未删除
    3. 关联查询发布者信息
    4. 返回完整信息
    """
    async with AsyncSessionFactory() as session:
        try:
            # 1️⃣ 查询帖子及发布者信息
            stmt = (
                select(News, User.name.label('username'), User.email.label('user_email'))
                .join(User, News.user_id == User.id)
                .where(News.id == news_id)
            )
            result = await session.execute(stmt)
            data = result.one_or_none()
            
            # 2️⃣ 检查帖子是否存在
            if not data:
                raise HTTPException(status_code=404, detail="帖子不存在")
            
            news, username, user_email = data
            
            # 3️⃣ 检查是否已删除
            if news.delete_time is not None:
                raise HTTPException(status_code=404, detail="帖子已删除")
            
            # 4️⃣ 返回详细信息
            return {
                "message": "查询成功",
                "data": {
                    "id": news.id,
                    "title": news.title,
                    "article": news.article,
                    "user_id": news.user_id,
                    "username": username,
                    "user_email": user_email,
                    "create_time": news.create_time.isoformat(),
                    "update_time": news.update_time.isoformat()
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"查询失败: {str(e)}"
            )

# ————————按id删除帖子
@app.delete("/news/{news_id}", summary="删除帖子")
async def delete_news(news_id: int, authorization: str = Header(None)):
    """
    删除帖子（软删除）
    步骤：
    1. 验证token获取用户ID
    2. 查询帖子是否存在
    3. 验证是否为帖子所有者
    4. 设置delete_time（软删除）
    """
    # 1️⃣ 验证token
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供Token")
    
    try:
        token = authorization.split(" ")[1]
    except IndexError:
        raise HTTPException(status_code=401, detail="Token格式错误")
    
    # 验证JWT token并获取用户ID
    payload = await verify_jwt_token(token)
    user_id = payload.get("user_id")
    
    # 2️⃣ 删除帖子
    async with AsyncSessionFactory() as session:
        try:
            async with session.begin():
                # 查询帖子
                stmt = select(News).where(News.id == news_id)
                result = await session.execute(stmt)
                news = result.scalar_one_or_none()
                
                # 3️⃣ 检查帖子是否存在
                if not news:
                    raise HTTPException(status_code=404, detail="帖子不存在")
                
                # 检查是否已删除
                if news.delete_time is not None:
                    raise HTTPException(status_code=400, detail="帖子已删除")
                
                # 4️⃣ 验证权限（只能删除自己的帖子）
                if news.user_id != user_id:
                    raise HTTPException(status_code=403, detail="无权删除此帖子")
                
                # 5️⃣ 软删除：设置删除时间
                news.delete_time = datetime.now()
                
                return {
                    "message": "删除成功",
                    "news_id": news_id
                }
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"删除失败: {str(e)}"
            )

# ——————————————中间件————————————————
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 允许所有来源（生产环境应设置为具体域名列表）
    allow_credentials=True, # 允许携带凭证（如Cookie）
    allow_methods=["*"], # 允许所有HTTP方法
    allow_headers=["*"], # 允许所有请求头
)
# ——————————————启动服务——————————————
if __name__ == "__main__":
    port = settings.PORT # 端口
    host = settings.HOST # 主机

    print("-" * 60)
    print("🌐")
    print(f"服务器启动在 http://{host}:{port}")
    print("📋")
    print(f"健康检查:   GET    http://{host}:{port}/")

    print(f"用户注册:   POST   http://{host}:{port}/register")
    print(f"用户登录:   POST   http://{host}:{port}/login")
    print(f"用户登出:   POST   http://{host}:{port}/logout")

    print(f"发布帖子:   POST   http://{host}:{port}/news")
    print(f"帖子列表:   GET    http://{host}:{port}/news")

    print(f"帖子详情:   GET    http://{host}:{port}/news/{{id}}")
    print(f"删除帖子:   DELETE http://{host}:{port}/news/{{id}}")

    print(f"当前用户:   GET    http://{host}:{port}/me")
    print(f"API文档:    http://{host}:{port}/docs")
    print("-" * 60)

    uvicorn.run("server:app", host=host, port=port, reload=False) # 启动服务