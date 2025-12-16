'''反思和推理 '''


# 将当前目录加入搜索路径
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入环境变量
from dotenv import load_dotenv
load_dotenv()

# 导入包
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END, MessagesState
from langchain_openai import ChatOpenAI

# 记忆
from langgraph.checkpoint.memory import MemorySaver

# 工具
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode

# 反思
from langchain_community.tools.tavily_search import TavilySearchResults

# 导入环境变量
api_url = os.getenv("LLM_URL")
api_key = os.getenv("LLM_API_KEY")
model = os.getenv("LLM_MODEL")

# —————————公共变量—————————
llm = ChatOpenAI(model=model, api_key=api_key, base_url=api_url)  


# ——————————定义函数——————————

# ===tool 函数
# 1 工具函数
from langchain_community.tools import DuckDuckGoSearchResults
search = DuckDuckGoSearchResults(max_results=2)

# 2 判断是否调用工具
def should_continue(state: MessagesState):
    last_message = state["messages"][-1] # 获取最后一条信息
    # 1 检查是否有tool_calls属性 2 检查工具列表存在工具
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        
        # 打印工具调用信息
        tool_names = [tc["name"] for tc in last_message.tool_calls]
        print(f"🔧 正在调用工具: {', '.join(tool_names)}")

        return "tools"
    
    print("🔧 不需要调用工具")
    return END # 特殊常量 代表本次执行结果结束 需要用户再次输入开启下一轮执行

# 3 绑定工具
tools = [search]
llm_with_tools = llm.bind_tools(tools) 

# ===聊天 函数
def agent(state: MessagesState):
    system_prompt = '''你是一个 ReAct (Reasoning + Acting) Agent。
处理用户问题时，请遵循以下步骤：
1. Thought(思考):分析问题需要什么信息
2. Action(行动):决定调用哪个工具
3. Observation(观察):分析工具返回的结果
4. Answer(回答):基于观察给出最终答案

始终展示你的推理过程。 '''
    messages = [{"role": "system", "content": system_prompt}] + state["messages"]
    return {"messages": [llm_with_tools.invoke(messages)]}

# —————————定义运行流程—————————
# 创建图
graph = StateGraph(MessagesState)

# 注册节点
graph.add_node("agent", agent)
graph.add_node("tools", ToolNode(tools))

# 入口边
graph.add_edge(START, "agent")

# 中间边
graph.add_edge("tools", "agent")

# 出口边
graph.add_conditional_edges(
    "agent", # 从这个节点开始
    should_continue,  # 决定走向
    {
        "tools": "tools", # 如果返回 "tools"，走向 tools 节点
        END: END # 如果返回 "END"，走向 END 节点
    }
)


# —————————运行—————————
# 编译图
app = graph.compile()

# 一次性执行
user_input = '2024年诺贝尔物理学奖获得者是谁？他们的主要贡献是什么？'
res = app.invoke({"messages": [("user", user_input)]})
print("=" * 50 + " 对话结果 " + "=" * 50)
print(res["messages"][-1].content)

# 所有历史对话
print("=" * 50 + " 完整对话历史 " + "=" * 50)
for i, msg in enumerate(res["messages"],1):
    print(i,msg.type)
    print(msg)