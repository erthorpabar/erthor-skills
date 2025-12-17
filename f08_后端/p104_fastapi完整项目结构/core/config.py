from pydantic_settings import BaseSettings # 优先环境变量，然后是.env文件，最后是默认值

class Settings(BaseSettings):
    
    # openai 配置
    OPENAI_API_URL: str
    OPENAI_API_KEY: str
    OPENAI_API_MODEL: str

    # comfyu 配置
    COMFYUI_API_URL: str
    
    class Config:
        # 指定从.env文件加载环境变量
        env_file = ".env" # 允许从.env文件加载配置
        extra = "allow" # 允许额外的没用到的配置

# 创建Settings的实例
# 在其他文件中，你可以通过导入settings来访问这些配置
settings = Settings()

