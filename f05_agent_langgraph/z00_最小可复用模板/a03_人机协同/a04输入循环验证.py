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
    name:str  
    age:int

class State(TypedDict):
    name: str
    age: int
    email: str

# 用户会话信息
user_id = "123"
session_id = "456"
config = {"configurable": {"thread_id": f"{user_id}_{session_id}"}}

# —————————定义函数—————————
def chat(state: State):
    res = llm.invoke(state["messagess"])
    return {"messages": res}

def collect_age(state: State):
    """收集并验证年龄输入"""
    prompt = "请输入您的年龄（正整数）："

    while True:
        # 每次循环都会暂停等待输入
        answer = interrupt(prompt)

        # 验证输入
        try:
            age = int(answer)
            if age > 0 and age < 150:
                print(f"年龄验证通过: {age}")
                return {"age": age}
            else:
                prompt = f"'{answer}' 不是有效年龄，请输入1-150之间的数字："
        except ValueError:
            prompt = f"'{answer}' 不是数字，请输入有效的年龄："

def collect_email(state: State):
    """收集并验证邮箱输入"""
    prompt = "请输入您的邮箱地址："

    while True:
        answer = interrupt(prompt)

        # 简单的邮箱验证
        if "@" in answer and "." in answer:
            print(f"邮箱验证通过: {answer}")
            return {"email": answer}
        else:
            prompt = f"'{answer}' 不是有效邮箱，请重新输入（需包含@和.）："
    

def show_summary(state: State):
    """显示收集结果"""
    print("\n" + "="*40)
    print("信息收集完成！")
    print(f"   姓名: {state['name']}")
    print(f"   年龄: {state['age']}")
    print(f"   邮箱: {state['email']}")
    print("="*40)
    return state

# —————————定义运行流程—————————
# 创建图
graph = StateGraph(State)
graph.add_node("collect_age", collect_age)
graph.add_node("collect_email", collect_email)
graph.add_node("show_summary", show_summary)

graph.add_edge(START, "collect_age")
graph.add_edge("collect_age", "collect_email")
graph.add_edge("collect_email", "show_summary")
graph.add_edge("show_summary", END)

# —————————运行—————————
memory = InMemorySaver()
app = graph.compile(checkpointer=memory)

# 模拟用户输入 "yes"，使用 Command 恢复执行
from langgraph.types import Command
initial = {"name": "张三", "age": 0, "email": ""}

print("=== 开始收集信息 ===\n")

# 第一次运行，会在第一个 interrupt 处暂停
for event in app.stream(initial, config, stream_mode="values"):
    if "__interrupt__" in str(event):
        print(f"系统提示: {event}")

# 模拟用户输入无效年龄
print("\n用户输入: 'abc' (无效)")
for event in app.stream(Command(resume="abc"), config, stream_mode="values"):
    if "__interrupt__" in str(event):
        print(f"系统提示: {event}")

# 再次输入无效年龄
print("\n用户输入: '-5' (无效)")
for event in app.stream(Command(resume="-5"), config, stream_mode="values"):
    if "__interrupt__" in str(event):
        print(f"系统提示: {event}")

# 输入有效年龄，进入下一步
print("\n用户输入: '25' (有效)")
for event in app.stream(Command(resume="25"), config, stream_mode="values"):
    if "__interrupt__" in str(event):
        print(f"系统提示: {event}")

# 输入无效邮箱
print("\n用户输入: 'invalid' (无效邮箱)")
for event in app.stream(Command(resume="invalid"), config, stream_mode="values"):
    if "__interrupt__" in str(event):
        print(f"系统提示: {event}")

# 输入有效邮箱
print("\n用户输入: 'zhangsan@example.com' (有效)")
for event in app.stream(Command(resume="zhangsan@example.com"), config, stream_mode="values"):
    print(f"最终状态: {event}")