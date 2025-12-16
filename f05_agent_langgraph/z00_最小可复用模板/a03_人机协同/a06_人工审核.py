'''一次性llm对话 '''

# 将当前目录加入搜索路径
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入环境变量
from dotenv import load_dotenv
load_dotenv()

api_url = os.getenv("LLM_URL")
api_key = os.getenv("LLM_API_KEY")
model = os.getenv("LLM_MODEL")

# 导入包
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END, MessagesState
from langchain_openai import ChatOpenAI

from langchain_core.messages import BaseMessage
from typing import List

# —————————公共变量—————————
llm = ChatOpenAI(model=model, api_key=api_key, base_url=api_url)  

# —————————定义函数—————————
# MessagesState 内部结构（简化版）
class MessagesState(TypedDict):
    messages: List[BaseMessage]  # 消息列表
    # messages 有特殊的追加合并策略

def chat(state: MessagesState):
    messages = llm.invoke(state["messages"])
    return {"messages": messages}



