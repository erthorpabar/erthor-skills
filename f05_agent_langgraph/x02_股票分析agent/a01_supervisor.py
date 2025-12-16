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
from typing import TypedDict, Dict, Any, List, Literal, Optional, List, Annotated
from pydantic import BaseModel, Field
from langgraph.types import Command
from datetime import datetime, timedelta

# 图节点管理
from langgraph.graph import StateGraph, START, END

# 聊天
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langchain_core.messages import BaseMessage

# 记忆
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.memory import InMemorySaver

# 工具
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode

# 格式化输出
from langchain_core.output_parsers import JsonOutputParser

# prompt模板
from langchain_core.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# 反思
from langchain_community.tools.tavily_search import TavilySearchResults

# 中断
from langgraph.types import interrupt

# 加载路径
import pathlib

# —————————公共变量—————————
llm = ChatOpenAI(model=model, api_key=api_key, base_url=api_url)  

# 用户会话信息
user_id = "123"
session_id = "456"
config = {"configurable": {"thread_id": f"{user_id}_{session_id}"}}



# —————————state
''' 
{
    # 1 股票代码
    "stock_symbol": "TSLA", 

    # 2 数据获取状态
    "fetch_data": {  
        "stock_data": None,  # 行情数据
        "analyst_recommendations": None,  # 分析师推荐
        "news_sentiment": None  # 新闻情绪
    },

    # 3 分析
    "analysis": { 
        "technical": None,  # 技术分析
        "recommendations": None,  # 投资建议
        "sentiment": None  # 情绪分析
    },

    # 4 报告状态
    "report": {
        "market_summary": None,  # 市场摘要
        "technical_section": None,  # 技术分析部分
        "recommendation_section": None,  # 投资建议部分
        "news_section": None,  # 新闻情绪部分
        "final_section": None,  # 最终建议部分
        "full_report": None  # 完整报告
    },

    # 5 supervisor 状态管理者
    "error": None,  # 错误信息
    "next_agent": None,  # 决定下一根要执行的agent

    "messages": [HumanMessage(content="请分析股票 TSLA 并生成完整报告。")]
}
'''
# 数据抓取
class DataFetchState(BaseModel):
    stock_data: Optional[dict] = None # 行情数据
    analyst_recommendations: Optional[dict] = None # 分析师评级
    news_sentiment: Optional[dict] = None  #公司新闻情绪数据

# 分析
class AnalysisState(BaseModel):
    technical: Optional[dict] = None # 技术指标分析结果
    recommendations: Optional[dict] = None # 分析师评级结果
    sentiment: Optional[dict] = None # 新闻情绪分析结果

# 报告生成
class ReportState(BaseModel): 
    market_summary: Optional[str] = None # 市场摘要
    technical_section: Optional[str] = None # 技术分析
    recommendation_section: Optional[str] = None # 投资建议
    news_section: Optional[str] = None # 新闻情绪
    final_section: Optional[str] = None # 最终建议
    full_report: Optional[str] = None # 拼接完整报告

# 调度和控制 所有节点都返回到这个节点 来决定下一个要执行的节点
class SupervisorState(BaseModel):
    stock_symbol: Optional[str] = None
    fetch_data: DataFetchState = Field(default_factory=DataFetchState)
    analysis: AnalysisState = Field(default_factory=AnalysisState)
    report: ReportState = Field(default_factory=ReportState)

    error: Optional[str] = None # 错误信息 若有值则流程中断
    next_agent: Optional[str] = None # 决定下一个agent

    messages: List[BaseMessage]

# ———————————————data_fetch 节点 —————————————————————
# pip install finnhub-python
import finnhub
FINNHUB_API_KEY = 'd2619t1r01qhge4eu7igd2619t1r01qhge4eu7j0'
client = finnhub.Client(api_key=FINNHUB_API_KEY)


@tool(description="获取日度股票行情数据。参数为symbol，例如 'AAPL'")
def fetch_stock_quote(symbol: str) -> dict:
    """获取指定股票的行情数据。

    Args:
        symbol: str (股票代码 如 'AAPL')

    Returns:
        dict (股票行情数据 如 {'c': 150.75, 'd': 0.25, 'dp': 0.165, 'h': 151.25, 'l': 149.5, 'o': 150.5, 't': 1717171200, 'v': 1000000})
    """
    try:
        quote = client.quote(symbol)
        if not quote or "c" not in quote:
            raise RuntimeError("行情数据不完整")
        datat = {
            "open": quote["o"], "high": quote["h"], "low": quote["l"],
            "close": quote["c"], "previous_close": quote["pc"],
            "change": quote["d"], "change_percent": quote["dp"],
        }
        return datat
    except Exception as e:
        raise RuntimeError(f"fetch_stock_quote 失败: {e}")

@tool(description="获取分析师推荐数据。参数为symbol，例如 'AAPL'")
def fetch_analyst_recommendations(symbol: str) -> dict:
    """获取分析师评级数据。

    Args:
        symbol: str (股票代码 如 'AAPL')

    Returns:
        dict (分析师推荐数据 如 {'strong_buy': 10, 'buy': 20, 'hold': 30, 'sell': 40, 'strong_sell': 50})
    """
    try:
        recs = client.recommendation_trends(symbol) or []
        if not recs:
            raise ValueError("空的 recommendation_trends 数据")

        latest = recs[-1]
        total = sum(latest.get(k, 0)
                    for k in ["strongBuy", "buy", "hold", "sell", "strongSell"]) or 1

        return {
            "strong_buy": latest.get("strongBuy", 0),
            "buy": latest.get("buy", 0),
            "hold": latest.get("hold", 0),
            "sell": latest.get("sell", 0),
            "strong_sell": latest.get("strongSell", 0),
            "consensus": latest.get("consensus", ""),
            "period": latest.get("period", ""),
            "buy_percentage": round((latest.get("strongBuy", 0)
                                 + latest.get("buy", 0)) / total * 100, 2),
            "sell_percentage": round((latest.get("sell", 0)
                                  + latest.get("strongSell", 0)) / total * 100, 2),
        }
    except Exception as e:
        raise RuntimeError(f"fetch_analyst_recommendations 失败: {e}")

@tool(description="获取新闻情绪数据。参数为symbol，例如 'AAPL'")
def fetch_news_sentiment(symbol: str) -> dict:
    """获取新闻情绪数据。
    
    Args:
        symbol: str (股票代码 如 'AAPL')

    Returns:
        dict (新闻情绪数据 如 {'positive_news_count': 10, 'negative_news_count': 20, 'neutral_news_count': 30, 'overall_sentiment': '中性', 'recent_news': [{'headline': '苹果公司发布新款iPhone', 'summary': '苹果公司发布新款iPhone，市场反响热烈', 'datetime': 1717171200, 'url': 'https://www.apple.com/news/iphone'}]})
    """
    print(f"fetch_news_sentiment for {symbol}")
    try:

        today = datetime.now().strftime("%Y-%m-%d")
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        news_list = client.company_news(symbol, _from=week_ago, to=today) or []

        pos = neg = neu = 0
        recent = []
        pos_kws = ["positive", "growth", "up", "success", "profit", "gain", "win", "strong", "excellent", "outperform"]
        neg_kws = ["negative", "loss", "down", "fail", "decline", "weak", "poor", "underperform", "risk", "trouble"]

        for item in news_list[:5]:
            headline = (item.get("headline") or "").lower()
            if any(k in headline for k in pos_kws):
                pos += 1
            elif any(k in headline for k in neg_kws):
                neg += 1
            else:
                neu += 1

            recent.append({
                "headline": item.get("headline", ""),
                "summary": item.get("summary", ""),
                "datetime": item.get("datetime", 0),
                "url": item.get("url", "")
            })

        total = pos + neg + neu
        overall = (
            "无数据" if total == 0
            else "正面" if pos > neg * 1.5
            else "负面" if neg > pos * 1.5
            else "中性"
        )
        return {
            "positive_news_count": pos,
            "negative_news_count": neg,
            "neutral_news_count": neu,
            "overall_sentiment": overall,
            "recent_news": recent
        }
    except Exception as e:
        raise RuntimeError(f"fetch_news_sentiment 失败: {e}")


def data_fetch_node(state: DataFetchState) -> Command:
    print('data_fetch_node 执行')

    stock_symbol = state.stock_symbol

    #  绑定tool
    tools = [fetch_stock_quote, fetch_analyst_recommendations, fetch_news_sentiment]
    llm_with_tools = llm.bind_tools(tools) 

    prompt = ChatPromptTemplate.from_template(''' 
你是数据获取专家，负责获取股票相关数据。
用户输入的股票代码：{stock_symbol}
你的任务：
1. 依次调用上述三个工具，参数为提取的股票代码；
2. 将三个工具返回的数据整合为一个字典，包含以下键：
- stock_data: 股票行情数据
- analyst_recommendations: 分析师评级数据
- news_sentiment: 新闻情绪数据 
3. 仅返回整合后的字典，不要包含其他任何解释性文字。

''')

    workflow = prompt | llm_with_tools | JsonOutputParser()
    res = workflow.invoke({
        "stock_symbol": stock_symbol
    })
    d = res.get("data", {})

    # 返回命令，指定下一个节点为supervisor
    return Command(update=d, goto="supervisor")


# ———————————————analysis 节点 —————————————————————

# ———————————————report 节点 —————————————————————

# ———————————————supervisor 节点 —————————————————————
supervisor_prompt = ChatPromptTemplate.from_template("""
你是一个主管 Agent，负责根据整个状态调度下游三个子 Agent：
- data_fetch：获取股票行情、分析师评级和新闻情绪数据
- analysis：对已获取的数据做技术和情绪分析
- report：撰写最终报告

调度逻辑必须严格遵循以下顺序：
1. 首先，检查是否有错误。如果有错误，立即终止工作流（返回END）。
2. 如果data_fetch尚未完成，调用data_fetch Agent。
3. 如果data_fetch已完成但analysis尚未完成，调用analysis Agent。
4. 如果analysis已完成但report尚未生成，调用report Agent。
5. 如果report已生成，终止工作流（返回END）。

只需输出一个 JSON，包含字段 next_agent，其值为 data_fetch、analysis、report 或 END。

用户问题：{user_question}
当前状态：
- 股票代码: {stock_symbol}
- fetch_data 是否已完成: {has_fetch_data}
- analysis 是否已完成: {has_analysis}
- report 是否已生成: {has_report}
- 是否出错: {has_error}
""")

def supervisor_node(state: SupervisorState) -> Command:
    print('supervisor_node 执行')
    if state.error:
        # 更新error字段 并跳转到__end__节点
        return Command(update={"error": state.error}, goto="__end__")
    
    # 获取用户问题
    user_question = state.messages[-1].content

    # 定义工作流
    workflow = supervisor_prompt | llm | JsonOutputParser()
    res = workflow.invoke({
        "user_question": user_question,
        "stock_symbol": state.stock_symbol,
        "has_fetch_data": state.fetch_data.stock_data is not None,
        "has_analysis": state.analysis.technical is not None,
        "has_report": state.report.full_report is not None,
        "has_error": state.error is not None
    })

    # 解析json格式输出
    next_agent = res.get("next_agent", "END")
    if next_agent == "END" or next_agent == "__end__":
        return Command(goto=END)
    
    # 更新到下一个节点
    return Command(goto=next_agent)


def compile_workflow():
    # 创建图
    graph = StateGraph(MessagesState)
    # 注册节点
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("data_fetch", data_fetch_node)
    graph.add_node("analysis", analysis_node)
    graph.add_node("report", report_node)
    # 入口边
    graph.add_edge(START, "supervisor")
    # 中间边
    graph.add_edge("data_fetch", "supervisor")
    graph.add_edge("analysis", "supervisor")
    graph.add_edge("report", "supervisor")
    # 出口边
    graph.add_edge("supervisor", END)
    # 编译图
    app = graph.compile()
    return app


# 执行
if __name__ == "__main__":
    # 用户输入
    user_input = "TSLA"

    # 编译图
    app = compile_workflow()

    # 开始状态
    state = SupervisorState(
        messages=[HumanMessage(content=f"请分析股票 {user_input} 并生成完整报告。")]
    )

    # 执行
    res = app.invoke(state)
    print(res)

    # 打印
    if res.get('report'):
        print(res['report'])

    








