
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


# 图节点
from langgraph.graph import StateGraph, START, END

# 聊天
from langchain_openai import ChatOpenAI

# state演进
from langgraph.graph import MessagesState

# checkpoint记忆
# from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
# from langgraph.checkpoint.postgres import PostgresSaver


''' 
checkpoint 会把每次的StateSnapshot 保存下来
下一次invoke加载回来
记载了下一根要执行的节点 执行到的步骤编号

'''


# ————————公共变量—————————
llm = ChatOpenAI(model=model, api_key=api_key, base_url=api_url)  

user_id = "user_001"
session_id = "session_001"

# —————————定义函数—————————
def chat(state: MessagesState):
    messages = llm.invoke(state["messages"])
    return {"messages": messages}


# —————————定义运行流程—————————
# 创建图
graph = StateGraph(MessagesState)


# 注册节点
graph.add_node("chat", chat)

# 入口边
graph.add_edge(START, "chat")

# 出口边
graph.add_edge("chat", END)

# —————————运行—————————

# ================ checkpoint =================
# 用于存放聊天记录
'''
内存
sqlite -> 自动创建数据库 自动创建表结构
postgres -> 需手动创建数据库 自动创建表结构
创建语句
CREATE DATABASE langchain_db;
'''
# 实例化记忆
# memory = MemorySaver()
memory = SqliteSaver.from_conn_string("checkpoints.db")
# memory = PostgresSaver.from_conn_string(
#     "postgresql://user:pass@localhost/langchain_db"
# )


''' 
thread_id -> langgraph 用来区分不同对话窗口的 标识
-> 用户只有一个对话框 thread_id = user_id
-> 用户可开启多个对话框 thread_id = user_id + session_id 
此时需要创建额外表 用于记录对话框权限(确保用户只能看到自己的历史对话)
'''
config = {"configurable": {"thread_id": f"{user_id}_{session_id}"}}

'''
其他
checkpoint_id -> 区分同一对话窗口的历史记录

'''


# ===========================================
print("👋 欢迎使用AI对话助手 输入 'quit' 退出对话。\n")
# 加载历史记录
with memory as memory:
    # 编译图
    app = graph.compile(checkpointer=memory)

    # # 把store合并到system prompt
    # system_prompt = f"你是一个助手，用户信息: {store.get(namespace=('users', user_id), key='profile').value}"

    # 打印历史记录
    state = app.get_state(config) # 按照thread_id加载历史记录
    if state.values:
        for msg in state.values["messages"]:
            role = "用户" if msg.type == "human" else "助手"
            print(f"{role}: {msg.content}")


    # 对话系统
    while True:
        user_input = input("用户: ")

        # 判断是否退出
        if user_input.lower() == "quit":
            print("👋 感谢使用AI对话助手!")
            break  # 退出循环
        
        # 判断是否为空
        if not user_input.strip():
            continue  # 开启新一轮循环

        # 调用图执行对话
        result = app.invoke(
            {"messages": [{"role": "user", "content": user_input}]},
            config=config, # 根据这里的thread_id 将历史合并到state中的messages
        )
        
        # 输出助手回复
        print(f"助手: {result['messages'][-1].content}")
