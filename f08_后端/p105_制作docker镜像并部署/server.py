
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

# ——————————————启动服务——————————————
if __name__ == "__main__":
    port = int(os.getenv("PORT", 7004)) # 端口
    host = os.getenv("HOST", "0.0.0.0") # 主机

    uvicorn.run("server:app", host=host, port=port,reload=True) # 启动服务

