# 将当前目录加入搜索路径
import os
from re import S
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
from typing import TypedDict, Dict, Any, List, Literal

# 图节点管理
from langgraph.graph import StateGraph, START, END

# 聊天
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState

# 记忆
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.memory import InMemorySaver

# 工具
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode

# 格式化
from langchain_core.output_parsers import JsonOutputParser

# prompt模板
from langchain_core.prompts import PromptTemplate

# 反思
from langchain_community.tools.tavily_search import TavilySearchResults

# 中断
from langgraph.types import interrupt

# 加载路径
import pathlib

# —————————公共变量—————————
llm = ChatOpenAI(model=model, api_key=api_key, base_url=api_url)  

# 自带类
# class MessagesState(TypedDict):
#     messages: Annotated[list[BaseMessage], add_messages]
class State(MessagesState):
    name:str  
    age:int

# 用户会话信息
user_id = "123"
session_id = "456"
config = {"configurable": {"thread_id": f"{user_id}_{session_id}"}}

# —————————定义函数—————————
def chat(state: State):
    res = llm.invoke(state["messagess"])
    return {"messages": res}


#  
''' 
supervisor
决定下一根要执行的agent

'''