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


# —————————公共变量—————————
llm = ChatOpenAI(model=model, api_key=api_key, base_url=api_url)  

# —————————定义函数—————————
# MessagesState 内部结构（简化版）
# class MessagesState(TypedDict):
#     messages: List[BaseMessage]  # 消息列表
#     # messages 有特殊的追加合并策略

def chatbot(state: MessagesState):
    return {"messages": [llm.invoke(state["messages"])]}


# —————————定义运行流程—————————
# 创建图
graph = StateGraph(MessagesState)

# 注册节点
graph.add_node("chatbot", chatbot)

# 入口边
graph.add_edge(START, "chatbot")

# 出口边
graph.add_edge("chatbot", END)

# —————————运行—————————
# 编译图
app = graph.compile()

# 一次性执行
user_input = '你是哪家的模型 什么版本型号'
res = app.invoke({"messages": [("user", user_input)]})
print(res["messages"][-1].content)




