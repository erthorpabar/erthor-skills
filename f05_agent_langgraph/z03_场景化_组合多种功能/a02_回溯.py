# 将当前目录加入搜索路径
import os
import sys

from langgraph.graph.state import RunnableConfig
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

# chat
from langchain_openai import ChatOpenAI

# 消息在一次执行中传递
from langgraph.graph import MessagesState

# prompt
from langchain_core.messages import SystemMessage, HumanMessage

# 删除消息
from langchain_core.messages import RemoveMessage

# 记忆
from langgraph.checkpoint.memory import MemorySaver

# —————————公共变量—————————
llm = ChatOpenAI(model=model, api_key=api_key, base_url=api_url)  

# 自带类
# class MessagesState(TypedDict):
#     messages: Annotated[list[BaseMessage], add_messages]
class State(MessagesState):
    summary:str   # 总结


# 用户会话信息
user_id = "123"
session_id = "456"
config = {"configurable": {"thread_id": f"{user_id}_{session_id}"}}


# 系统提示词
system_prompt = ''
sys_msg = SystemMessage(content = system_prompt)
