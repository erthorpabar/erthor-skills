# ——————————当前文件夹路径加入搜索路径——————————
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ——————————加载环境变量——————————
from dotenv import load_dotenv
load_dotenv()


# ——————————读取环境变量——————————
api_url = os.getenv("LLM_URL")
api_key = os.getenv("LLM_API_KEY")
model = os.getenv("LLM_MODEL")


# ——————————打印——————————
print(api_url)
print(api_key)
print(model)