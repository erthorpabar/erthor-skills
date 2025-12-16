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

# —————————定义函数—————————
def chat(state: MessagesState):
    res = llm.invoke(state["messages"])
    return {"messages": res}

# 带summary的聊天
def call_model(state:State,config:RunnableConfig):
    summary = state.get("summary","")

    if summary:
        system_prompt = f"之前对话的总结: {summary}"
        messages = [SystemMessage(content=system_prompt)] + state["messages"]
    else:
        messages = state["messages"]
    
    res = llm.invoke(messages,config)
    return {"messages": res}

# 进行总结
def summarize_conversation(state:State):
    summary = state.get("summary","")


    if summary:
        summary_message = (
            f"这是到目前为止的对话总结：{summary}\n\n"
            "请根据上述新消息扩展这个总结："
        )
    else:
        summary_message = "请创建上述对话的总结："

    # llm总结
    messages = state["messages"] + [HumanMessage(content=summary_message)]
    res = llm.invoke(messages)

    # 删除最后两条之外的所有消息
    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]

    # 
    return {
        "summary": res.content, 
        "messages": delete_messages
    }


# route
def should_continue(state:State):
    messages = state["messages"]

    # 如果超过6条 进行总结
    if len(messages) > 6:
        return "summarize_conversation"
    
    # 否则结束本轮
    return "end"


# —————————定义运行流程—————————
# 创建图
graph = StateGraph(State)

# 注册节点
graph.add_node("conversation", call_model)
graph.add_node("summarize_conversation",summarize_conversation)


# 边
graph.add_edge(START, "conversation")
graph.add_conditional_edges(
    "conversation", 
    should_continue,
    {
        "summarize_conversation":"summarize_conversation",
        "end": END
    }
)
graph.add_edge("summarize_conversation", END)

# —————————运行—————————
# 编译图
memory = MemorySaver()
app = graph.compile(checkpointer=memory)


# 一次性执行
user_input = '你是谁训练的ai 是什么型号的'
res = app.invoke({"messages": [("user", user_input)]},config=config)

# 所有历史对话
print("=" * 50 + " 完整对话历史 " + "=" * 50)
for i, msg in enumerate(res["messages"],1):
    print(i,msg.type)
    print(msg)










