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
from typing import Literal

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

# 反思
from langchain_community.tools.tavily_search import TavilySearchResults

# 中断
from langgraph.types import interrupt

# —————————公共变量—————————
llm = ChatOpenAI(model=model, api_key=api_key, base_url=api_url)  

# 自带类
# class MessagesState(TypedDict):
#     messages: Annotated[list[BaseMessage], add_messages]
class State(MessagesState):
    summary:str   # 总结
    confirmed:bool # 


# 用户会话信息
user_id = "123"
session_id = "456"
config = {"configurable": {"thread_id": f"{user_id}_{session_id}"}}

# —————————定义函数—————————
def chat(state: State):
    res = llm.invoke(state["messagess"])
    return {"messages": res}

# 这里使用了interrupt
# 询问是否暂停 然后返回bool值
def ask_confirmation(state: State):
    print('节点1')
    print(f"收到消息: {state['messages']}")
    user_response = interrupt("\n执行前暂停 是否继续执行? (y/n): ")
    confirmed_bool = user_response.lower() == 'y'
    return {"confirmed":confirmed_bool}

# 
def process_result(state: State):
    print('节点2')
    if state["confirmed"]:
        print("用户已确认，继续执行...")
        return {"message": "操作已完成！"}
    else:
        print("用户取消，停止执行...")
        return {"message": "操作已取消"}

# —————————定义运行流程—————————
# 创建图
graph = StateGraph(State)

# 注册节点
graph.add_node("ask", ask_confirmation)
graph.add_node("process", process_result)

# 边
graph.add_edge(START, "ask")
graph.add_edge("ask", "process")
graph.add_edge("process", END)

# —————————运行—————————
memory = InMemorySaver()

# 编译图
app = graph.compile(
    checkpointer=memory,
)

# 执行

for event in app.stream({"message": "Hello World"}, config):
    print(event)
# 模拟用户输入 "yes"，使用 Command 恢复执行
from langgraph.types import Command
# 获取用户输入并恢复
user_response = input("请输入 y 继续或 n 取消: ")
for event in app.stream(Command(resume=user_response.lower()), config):
    print(event)