
# ——————————当前文件夹路径加入搜索路径——————————
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ——————————加载环境变量——————————
from dotenv import load_dotenv
load_dotenv()

from pydantic_settings import BaseSettings # 优先系统环境变量，然后是.env文件，最后是默认值
class Settings(BaseSettings):
    
    # LLM 配置
    LLM_URL: str = " "
    LLM_API_KEY: str = " "
    LLM_MODEL: str = " "

    # comfyui 配置
    COMFYUI_API_URL: str = " "

    # 数据库配置
    MYSQL1: str = " "
    MYSQL2: str = " "
    
    class Config:
        # 指定从.env文件加载环境变量
        env_file = ".env" # 允许从.env文件加载配置
        env_file_encoding = "utf-8" # 指定编码
        extra = "allow" # 允许额外的没用到的配置
        case_sensitive = True  # 环境变量大小写敏感

# 创建Settings的实例
# 在其他文件中，你可以通过导入settings来访问这些配置
settings = Settings()



# ——————————————创建app——————————————
import uvicorn
from fastapi import FastAPI
app = FastAPI()

# ——————————————get——————————————
@app.get("/aaa")
async def root():
    return {"message": "这是GET接口"}


# ——————————————post——————————————
# 1 Request 接收请求体数据
from fastapi import Request
@app.post("/bbb")
async def root(request: Request): 
    data = await request.json()
    return {"message": "这是POST接口", "data": data}


# 2 BaseModel 接收请求体数据
from pydantic import BaseModel
class Input(BaseModel):
    name: str
    age: int
@app.post("/ccc")
async def root(request: Input): 
    data = {"name": request.name, "age": request.age}
    return {"message": "这是POST接口", "data": data}


# ——————————————注入依赖——————————————
''' 
1 注入依赖自动触发
post路由函数(request,a=depends(函数)
自动触发

2 手写触发
post路由函数(request)
手写触发 a = 函数

明显手写触发更直观
'''
from fastapi import Depends

class Input2(BaseModel):
    name: str
    age: int

async def get_keys(request: Input2):  
    return list(request.model_dump().keys()) 

@app.post("/ddd")
async def root(request: Input2, keys: list = Depends(get_keys)):  # 函数会自动触发
    data = {"keys": keys}
    return {"message": "这是POST接口", "data": data}


# —————————include_router引入其他文件路由——————————————
''' 
from api.a import router as a
app.include_router(a, prefix="/a", tags=["a"])
'''


# ——————————————数据库————————————————
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
MYSQL1 = "mysql+asyncmy://root:123@127.0.0.1:3306/testdb?charset=utf8mb4" # 异步连接数据库字符串
MYSQL1 = settings.MYSQL1
engine = create_async_engine(
    MYSQL1,
    echo = False, # 打印sql语句
    pool_size = 10, # 连接池大小
    max_overflow = 20, # 最大连接数
    pool_timeout = 10, # 连接超时时间
    pool_recycle = 3600, # 回收时间
    pool_pre_ping = True, # 连接前测试是否可用
    )

# 2 创建session对象 负责 操作数据库
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

AsyncSessionFactory = sessionmaker(
    bind = engine,
    class_ = AsyncSession, # 异步session类
    autoflush = True, # 查找之前自动刷新session以查找最新数据
    expire_on_commit = False, # 提交后是否过期
)

# 3 定义base类 -> 对应一张表
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

Base = declarative_base() # 创建基类
class User(Base):
    __tablename__ = "user"
    
    id = Column(Integer, primary_key=True, index=True) # 主键约束primary_key
    email = Column(String(100), unique=True, index=True) # 唯一约束unique
    username = Column(String(100), unique=True,)
    password = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.now) # 创建时间


# 4 同步创建所有表
from sqlalchemy import create_engine
MYSQL2 = "mysql+pymysql://root:123@127.0.0.1:3306/testdb?charset=utf8mb4" # 同步连接数据库字符串
MYSQL2 = settings.MYSQL2
t_engine = create_engine(MYSQL2) # 替换+asyncmy为+pymysql
User.metadata.create_all(bind=t_engine)


# 5 写入数据
from sqlalchemy.exc import IntegrityError
from pydantic import field_validator, EmailStr
from fastapi import HTTPException

class Input3(BaseModel):
    email: EmailStr
    username: str
    password: str

    @field_validator('password')  # 新的装饰器
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码至少6位')
        return v
    
@app.post("/eee")
async def root(request: Input3): 
    # 异步上下文管理器
    async with AsyncSessionFactory() as session: # 异步session
        try:
            async with session.begin(): # 开启异步事务 事务结束自动commit
                x = User(email=request.email, username=request.username, password=request.password) 
                session.add(x) # 写入数据
        # 出错自动回滚
        except IntegrityError:
            raise HTTPException(status_code=400, detail="邮箱或用户名已存在")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"写入失败: {str(e)}")
    return {"message": "新用户注册成功"}
    
# ——————————————中间件———————————————
import time
from fastapi import Request
from typing import Callable

# 打印监控中间件
async def m03_log(request: Request, call_next: Callable):
    print("-" * 50)

    start = time.time()

    print(f"🚀 收到请求: {request.method} {request.url}")
    print(f"📍 客户端IP: {request.client.host if request.client else 'Unknown'}")
    # 打印POST请求的参数
    if request.method == "POST":
        try:
            body = await request.body()
            if body:
                print(f"📦 POST参数: {body.decode('utf-8')}")
        except:
            print("📦 POST参数: 无法读取")
    
    response = await call_next(request)
    
    end = time.time()
    time_cost = end-start

    response.headers["X-Process-Time"] = str(time_cost)
    response.headers["X-Server"] = "FastAPI-Custom"
    
    print(f"✅ 响应状态: {response.status_code}, 处理时间: {time_cost:.4f}秒")

    return response

# 防xss攻击中间件
async def m02_xxs(request: Request, call_next: Callable):
    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff" # 防止XSS攻击
    response.headers["X-Frame-Options"] = "DENY" # 防止点击劫持
    response.headers["X-XSS-Protection"] = "1; mode=block" # 防止XSS攻击
    return response

# 允许跨域中间件
async def m01_cors(request: Request, call_next: Callable):
    response = await call_next(request)
    
    response.headers["Access-Control-Allow-Origin"] = "*" # 允许所有源
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS" # 允许所有方法
    response.headers["Access-Control-Allow-Headers"] = "*" # 允许所有请求头
    return response

# 注意：中间件的注册顺序很重要，后注册的先执行
app.middleware("http")(m03_log) # 日志记录
app.middleware("http")(m02_xxs) # 防止XSS攻击
app.middleware("http")(m01_cors) # 允许跨域

# ——————————————启动服务——————————————
if __name__ == "__main__":
    port = int(os.getenv("PORT", 7004)) # 端口
    host = os.getenv("HOST", "0.0.0.0") # 主机

    uvicorn.run("server:app", host=host, port=port,reload=True) # 启动服务

