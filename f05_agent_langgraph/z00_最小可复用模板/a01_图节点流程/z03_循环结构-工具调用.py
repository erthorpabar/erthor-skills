
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
from typing import Literal

# 图节点
from langgraph.graph import StateGraph, START, END

# 聊天
from langchain_openai import ChatOpenAI

# state演进
from langgraph.graph import MessagesState

# tool
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode

# ————————公共变量—————————
llm = ChatOpenAI(model=model, api_key=api_key, base_url=api_url)  


# —————————定义函数—————————
# 1 定义tool
@tool
def calculator(expression: str) -> str:
    """执行数学计算。

    Args:
        expression: str (数学表达式 数字1 运算符 数字2 如 '25 * 4')


    Returns:
        str (计算结果 如 '100')
    """
    try:
        parts = expression.strip().split()
        if len(parts) != 3:
            return "格式错误，请使用: 数字1 运算符 数字2"
        num1, op, num2 = parts
        num1, num2 = float(num1), float(num2)
        if op == '+': return str(num1 + num2)
        elif op == '-': return str(num1 - num2)
        elif op == '*': return str(num1 * num2)
        elif op == '/': return str(num1 / num2) if num2 != 0 else "除数不能为零"
        else: return f"不支持的运算符: {op}"
    except:
        return "计算错误"

@tool
def get_weather(city: str) -> str:
    """查询城市天气。

    Args:
        city: str (城市名称 如 '北京')

    Returns:
        str (天气信息 如 '晴天,15°C')
    """
    # 模拟天气查询
    # 模拟数据库
    weather_db = {
        "北京": "晴天,15°C",
        "上海": "多云,18°C",
        "深圳": "阴天,22°C"
    }
    # 
    try:
        return weather_db.get(city, "未知城市")
    # except requests.Timeout:
    #     return "ERROR: API 超时，请稍后重试"
    # except requests.HTTPError as e:
    #     return f"ERROR: API 返回错误 {e.response.status_code}"
    except Exception as e:
        return f"ERROR: 未知错误 {str(e)}"

# 2 绑定tool
tools = [calculator, get_weather]
llm_with_tools = llm.bind_tools(tools) 

# 3 定义chat
def chat(state: MessagesState):
    messages = llm_with_tools.invoke(state["messages"])
    return {"messages": messages}

# 4 定义route
def route(state: MessagesState) -> Literal["tools","end"]:
    # 获取最后一条信息
    last = state["messages"][-1]
    # 1 检查是否有tool_calls属性 2 检查工具列表存在工具
    if hasattr(last, "tool_calls") and last.tool_calls:

        # 打印工具调用信息
        for t in last.tool_calls:
            print(f"  - 调用工具：{t['name']}")
            print(f"    参数：{t['args']}")

        return "tools"

    return "end"

# —————————定义运行流程—————————
''' 
运行流程
chat -> route -> ( tools | end )
        ↑____________↓         
'''
# 创建图
graph = StateGraph(MessagesState)

# 注册节点
graph.add_node("chat", chat)
graph.add_node("tools", ToolNode(tools))


# 入口边
graph.add_edge(START, "chat")

# 返回边
graph.add_edge("tools", "chat")

# route边
graph.add_conditional_edges(
    "chat",                    # 从这个节点开始
    route,                     # 决定走向
    {
        "tools": "tools",       # 如果返回 "tools"，走向 tools 节点
        "end": END              # 如果返回 "end"，走向 END 节点
    }
)


# —————————运行—————————
# 编译图
app = graph.compile()

# 一次性执行
user_input = '北京和上海天气怎么样？'
res = app.invoke({"messages": [("user", user_input)]})

# 打印对话结果
print("=" * 50 + " 对话结果 " + "=" * 50)
print(res["messages"][-1].content)

# 所有历史对话
print("=" * 50 + " 完整对话历史 " + "=" * 50)
for i, msg in enumerate(res["messages"],1):
    print(i,msg.type)
    print(msg)


''' 
函数调用具体流程
《不断查询是否需要调用工具直到不需要为止》

1 human 用户输入
user_input = '北京和上海天气怎么样？'

2 ai 模型判断是否需要工具
{
"role": "assistant",
"content": "", # 用于储存结果
"tool_calls": [{
    "name": "get_weather", # 工具函数名称
    "args": {'city': '北京'} # 工具函数参数
    "id": "abcd-1234", # 唯一标识符号 用于追踪这次调用
    }]
} 

3 tool 工具执行后 返回结果
{
    "tool_call_id": "abcd-1234",  # 对应上面的 id
    "name": "get_weather",
    "content": "晴天,15°C"       # 结果
}

4 ai 模型返回
{"role": "assistant", "content": "晴天,15°C"}

'''