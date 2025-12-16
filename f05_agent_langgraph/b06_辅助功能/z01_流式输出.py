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

import asyncio

# 图节点管理
from langgraph.graph import StateGraph, START, END

# 聊天
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState

# 记忆
from langgraph.checkpoint.memory import MemorySaver

# —————————公共变量—————————
llm = ChatOpenAI(model=model, api_key=api_key, base_url=api_url)  

# —————————定义函数—————————
def chat(state: MessagesState):
    return {"messages": [llm.invoke(state["messages"])]}

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
# 记忆
memory = MemorySaver()

# 编译图
app = graph.compile()

# 配置
config = {"configurable": {"thread_id": "user_001"}}

# —————————多轮对话流式输出—————————
async def chat_with_streaming():
    print("👋 欢迎使用AI对话助手（流式输出）输入 'quit' 退出对话。\n")
    
    while True:
        user_input = input("用户: ")
        
        # 判断是否退出
        if user_input.lower() == "quit":
            print("👋 感谢使用AI对话助手!")
            break
        
        # 判断是否为空
        if not user_input.strip():
            continue
        
        # 流式输出
        print("助手: ", end="", flush=True)
        
        async for event in app.astream_events(
            {"messages": [{"role": "user", "content": user_input}]},
            config=config,
            version="v2"
        ):
            kind = event.get("event")
            
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    print(content, end="", flush=True)
        
        print("\n")  # 换行

# 运行
if __name__ == "__main__":
    asyncio.run(chat_with_streaming())