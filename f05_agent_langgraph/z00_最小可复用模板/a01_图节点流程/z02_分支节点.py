'''多agent 分支判断对话 '''

# 将当前目录加入搜索路径
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入环境变量
from dotenv import load_dotenv
load_dotenv()

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
# ===聊天 函数
def researcher(state: MessagesState):
    """研究员：负责信息收集"""
    system_prompt = '''你是资深研究员，擅长收集和分析行业信息。请提供数据和趋势分析。 '''
    messages = [{"role": "system", "content": system_prompt}] + state["messages"]
    print('🔍 研究员：正在收集信息...')
    return {"messages": [llm.invoke(messages)]}

def chart_analyst(state: MessagesState):
    """图表分析师：负责数据可视化建议"""
    system_prompt = '''你是数据可视化专家，擅长将数据转化为图表建议。请推荐合适的图表类型和关键指标。 '''
    messages = [{"role": "system", "content": system_prompt}] + state["messages"]
    print('🔍 图表分析师：正在分析数据...')
    return {"messages": [llm.invoke(messages)]}

def report_writer(state: MessagesState):
    """报告撰写员：整合信息并生成最终报告"""
    system_prompt = '''你是专业报告撰写员，擅长将研究结果和图表建议整合成结构清晰的报告。 '''
    messages = [{"role": "system", "content": system_prompt}] + state["messages"]
    print('🔍 报告撰写员：正在撰写报告...')
    return {"messages": [llm.invoke(messages)]}


# 判断方向函数
# Literal 类型提示 限制返回值只能返回特定的数值
def supervisor(state: MessagesState) -> Literal["researcher", "chart_analyst", "report_writer", "end"]:
    """管理者：协调各个 Agent 的工作流程"""
    messages = state["messages"]

    # 简单的状态机逻辑
    # 根据当前对话中ai已经相应的次数 决定下一步执行哪个agent
    response_count = len([m for m in messages if m.type == "ai"])  # 只计算 AI 消息

    if response_count == 0:
        return "researcher"  # 第一步：研究
    elif response_count == 1:
        return "chart_analyst"  # 第二步：图表分析
    elif response_count == 2:
        return "report_writer"  # 第三步：报告撰写
    else:
        return "end"  # 完成



# —————————定义运行流程—————————
# 创建图
graph = StateGraph(MessagesState)

# 注册节点
graph.add_node("researcher", researcher)
graph.add_node("chart_analyst", chart_analyst)
graph.add_node("report_writer", report_writer)

# 入口边
graph.add_conditional_edges(
    START, 
    supervisor,
    
    {
        "researcher": "researcher", 
        "chart_analyst": "chart_analyst", 
        "report_writer": "report_writer", 
        "end": END
    }
)

# 出口边
# 条件边 - 所有节点都由 supervisor 决定下一步
graph.add_conditional_edges(
    "researcher", 
    supervisor,
    {"researcher": "researcher", 
    "chart_analyst": "chart_analyst", 
    "report_writer": "report_writer", 
    "end": END
    }
)
graph.add_conditional_edges(
    "chart_analyst", 
    supervisor,
    {"researcher": "researcher", 
    "chart_analyst": "chart_analyst", 
    "report_writer": "report_writer", 
    "end": END
    }
)
graph.add_conditional_edges(
    "report_writer", 
    supervisor,
    {"researcher": "researcher", 
    "chart_analyst": "chart_analyst", 
    "report_writer": "report_writer", 
    "end": END
    }
)


# —————————运行—————————
# 编译图
app = graph.compile()

# 一次性执行
user_input = '请帮我分析一下 2024 年生成式 AI 市场的发展趋势，并给出报告'
res = app.invoke({"messages": [("user", user_input)]})

# 所有历史对话
print("=" * 50 + " 完整对话历史 " + "=" * 50)
for i, msg in enumerate(res["messages"],1):
    print(i,msg.type)
    print(msg)