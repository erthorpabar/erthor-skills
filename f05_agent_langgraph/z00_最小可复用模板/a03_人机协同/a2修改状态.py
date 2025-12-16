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


from langchain_core.messages import HumanMessage

from langchain_core.messages import RemoveMessage

# —————————公共变量—————————
llm = ChatOpenAI(model=model, api_key=api_key, base_url=api_url)  

# —————————定义函数—————————
# MessagesState 内部结构（简化版）
# class MessagesState(TypedDict):
#     messages: List[BaseMessage]  # 消息列表
#     # messages 有特殊的追加合并策略

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

# 记忆
from langgraph.checkpoint.memory import MemorySaver
memory = MemorySaver()

# # 用户会话信息
user_id = "123"
session_id = "456"
config = {"configurable": {"thread_id": f"{user_id}_{session_id}"}}

# 编译图
app = graph.compile(
    interrupt_before=["chat"],  # 第一次执行到这里保存历史状态暂停 第二次出发后继续执行
    # interrupt_after=["chat"],  # 
    checkpointer=memory,
)

# 一次性执行

user_input = '你是哪家的模型 什么版本型号'
# 第一次执行到这里保存历史状态暂停
res = app.invoke(
    {"messages": [("user", user_input)]}, 
    config = config,
)


# ========== 第一次暂停：执行前审查 ==========
# 这个暂停就相当于 yeild
print("=== 第一次暂停：执行前审查 ===")
# =========== 修改状态 ============
state = app.get_state(config) # 检查状态
new_input = '学猫叫 '
current_messages = state.values.get('messages',[])
print('1',current_messages)
last_message = current_messages[-1]
app.update_state(config,{"messages":[
    # RemoveMessage(id = last_message.id), # 通过id删除最后一条
    HumanMessage(content = new_input,id = last_message.id) # 增加一个相同id的输入 如果有会直接覆盖
]}
)

# ================================
state = app.get_state(config) # 获取更新状态
print('2',state.values.get('messages',[]))
if state.next: # 如果有下一个节点（说明在断点处）
    # 当前状态检查
    print(f"下一个要执行的节点: {state.next}")
    print(f"当前输入: {state.values.get('messages', [])[-1].content}")
    # print(f"当前状态: {state.values}")
    # print(f"当前任务: {state.tasks}")

    
    
    # 人工审查
    user_input = input("\n执行前暂停 是否继续执行? (y/n): ")
    if user_input.lower() != "y":
        print("执行已取消")
        exit()
    
    # 继续执行 chat 节点
    res = app.invoke(None, config)  # None 表示继续执行
    print(f"助手回复: {res['messages'][-1].content}")
