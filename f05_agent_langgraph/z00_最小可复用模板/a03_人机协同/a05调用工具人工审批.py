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



# 用户会话信息
user_id = "123"
session_id = "456"
config = {"configurable": {"thread_id": f"{user_id}_{session_id}"}}

# —————————定义函数—————————
def chat(state: State):
    res = llm.invoke(state["messagess"])
    return {"messages": res}

# 定义工具
@tool
def send_email(to: str, subject: str, body: str) -> str:
    """发送邮件给指定收件人"""
    # 实际应用中这里会调用邮件服务
    return f"邮件已发送给 {to}，主题: {subject}"

@tool
def delete_file(filename: str) -> str:
    """删除指定文件（危险操作）"""
    return f"文件 {filename} 已删除"

@tool
def get_weather(city: str) -> str:
    """获取城市天气（安全操作）"""
    return f"{city}今天天气晴朗，温度25度C"

# 绑定工具
# 创建 Agent
tools = [send_email, delete_file, get_weather]
llm = ChatOpenAI(model="gpt-4").bind_tools(tools)

def agent(state: State):
    """Agent 节点：调用 LLM 决定下一步"""
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

# ————————————————————————
# 定义哪些工具需要审批
TOOLS_REQUIRING_APPROVAL = {"send_email", "delete_file"}

# 创建带审批功能的工具节点
def tool_node_with_approval(state: State):
    """执行工具调用，敏感工具需要审批"""
    last_message = state["messages"][-1]

    results = []
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        # 检查是否需要审批
        if tool_name in TOOLS_REQUIRING_APPROVAL:
            print(f"\n敏感操作需要审批: {tool_name}")
            print(f"   参数: {tool_args}")

            # 暂停等待审批
            approval = interrupt({
                "type": "tool_approval",
                "tool": tool_name,
                "args": tool_args,
                "message": f"是否允许执行 {tool_name}？(approve/reject)"
            })

            if approval.lower() != "approve":
                results.append({
                    "tool_call_id": tool_call["id"],
                    "content": f"操作被用户拒绝: {tool_name}"
                })
                continue

            print(f"用户已批准 {tool_name}")

        # 执行工具
        tool_map = {
            "send_email": send_email,
            "delete_file": delete_file,
            "get_weather": get_weather
        }

        result = tool_map[tool_name].invoke(tool_args)
        results.append({
            "tool_call_id": tool_call["id"],
            "content": result
        })

    from langchain_core.messages import ToolMessage
    return {"messages": [ToolMessage(**r) for r in results]}

# 构建图
builder = StateGraph(AgentState)
builder.add_node("agent", agent)
builder.add_node("tools", tool_node_with_approval)

builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")

memory = InMemorySaver()
graph = builder.compile(checkpointer=memory)

# 测试
config = {"configurable": {"thread_id": "agent-test"}}

print("=== 测试1：查询天气（不需要审批）===")
for event in graph.stream(
    {"messages": [("user", "北京今天天气怎么样？")]},
    config,
    stream_mode="values"
):
    if event["messages"]:
        print(event["messages"][-1])

print("\n=== 测试2：发送邮件（需要审批）===")
config2 = {"configurable": {"thread_id": "agent-test-2"}}

for event in graph.stream(
    {"messages": [("user", "帮我发一封邮件给 boss@company.com，主题是请假申请")]},
    config2,
    stream_mode="values"
):
    if "__interrupt__" in str(event):
        print(f"\n等待审批...")
        break
    if event["messages"]:
        print(event["messages"][-1])

# 用户审批
print("\n用户输入: approve")
for event in graph.stream(Command(resume="approve"), config2, stream_mode="values"):
    if event["messages"]:
        print(event["messages"][-1])