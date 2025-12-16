''' 
对话系统 = NLU + NER + DST + policy + NLG
nlu = 意图理解
ner = 实体抽取(生成请求参数)
dst = 管理切换到哪个对话流程
policy = 当前对话流程走向
nlg = 生成回复

'''

# 将当前目录加入搜索路径
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入环境变量
from dotenv import load_dotenv
load_dotenv()

# 导入环境变量
api_url = os.getenv("LLM_URL")
api_key = os.getenv("LLM_API_KEY")
model = os.getenv("LLM_MODEL")

# 导入包


# 聊天
from langchain_openai import ChatOpenAI

# —————————公共变量—————————
llm = ChatOpenAI(model=model, api_key=api_key, base_url=api_url)  

class State(TypedDict):
    messages: List[BaseMessage]