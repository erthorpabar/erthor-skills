'''
1 状态演进 对一个state状态进行不断更新
2 每次都需要返回一个{} 才能让graph知道需要更新什么变量的值 并且怎么更新
3 举例子
更新前 state = {message:[]}
返回{message:['你好']}
更新后 state = {message:['你好']}
4 特殊情况 返回{} 不更新
5 state 只负责一轮执行的演进 多轮的演进需要使用memory
'''

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
from typing import Annotated
import operator
import random

# 图节点
from langgraph.graph import StateGraph, START, END

# 聊天
from langchain_openai import ChatOpenAI

# state演进
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages

# ————————公共变量—————————
llm = ChatOpenAI(model=model, api_key=api_key, base_url=api_url)  

class State(TypedDict):
    name : str # 覆盖更新
    age : Annotated[int, operator.add] # 累加更新
    event : Annotated[list, operator.add] # 列表追加更新
    messages : Annotated[list, add_messages] # 对话追加更新 对话历史记录 等价于MessagesState

# —————————定义函数—————————
# 覆盖更新
def rename(state: State):
    n = ["aaa","bbb","ccc","ddd","eeee"]
    name = random.choice(n) 
    return {"name": name}

# 累加更新
def add_age(state: State):
    return {"age": 1}

# 列表追加更新
def add_event(state: State):
    e = ["event1", "event2", "event3", "event4", "event5"]
    event = random.choice(e)
    return {"event": [event]}

# 对话追加更新
def chat(state: MessagesState):
    messages = llm.invoke(state["messages"])

    # 统计token使用量
    usage = messages.response_metadata.get("usage") or messages.response_metadata.get("token_usage", {})
    if usage:
        print(f"[输入token] prompt_tokens = {usage.get('prompt_tokens')}")
        print(f"[输出token] completion_tokens = {usage.get('completion_tokens')}")
        print(f"[总token] total_tokens = {usage.get('total_tokens')}")
    return {"messages": messages}

# 打印
def print_state(state: State):
    print(state["name"])
    print(state["age"])
    print(state["event"])
    print(state["messages"])
    return {}

# —————————定义运行流程—————————
# 创建图
graph = StateGraph(State)

# 注册节点
graph.add_node("rename", rename)
graph.add_node("add_age", add_age)
graph.add_node("add_event", add_event)
graph.add_node("chat", chat)
graph.add_node("print_state", print_state)

# 入口边
graph.add_edge(START, "rename")

# 中间边
graph.add_edge("rename", "add_age")
graph.add_edge("add_age", "add_event")
graph.add_edge("add_event", "chat")
graph.add_edge("chat", "print_state")

# # 出口边
graph.add_edge("print_state", END)


# —————————运行—————————
# 编译图
app = graph.compile()



# 一次性执行
user_input = '你是哪家的模型 什么版本型号'
res = app.invoke({
    # "name": "",  
    # "age": 0,    
    # "event": [], 
    "messages": [("user", user_input)], 
})