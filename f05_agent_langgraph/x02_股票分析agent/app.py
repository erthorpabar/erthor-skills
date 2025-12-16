# 将当前目录加入搜索路径
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入环境变量
from dotenv import load_dotenv
load_dotenv()

# 设置环境变量
os.environ["LLM_URL"] = "https://open.bigmodel.cn/api/paas/v4/"
os.environ["LLM_API_KEY"] = "bcb4b79cf63d81bb74004a7438afe404.ZWtkkACpqBa522oQ"
os.environ["LLM_MODEL"] = "GLM-4-Flash-250414"

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

# 数据处理
import json
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator

# —————————公共变量—————————
llm = ChatOpenAI(model=model, api_key=api_key, base_url=api_url)

# 用户会话信息
user_id = "123"
session_id = "456"
config = {"configurable": {"thread_id": f"{user_id}_{session_id}"}}



# —————————state

# 子图状态 - 数据获取子图
class DataFetchSubgraphState(BaseModel):
    stock_symbol: Optional[str] = None
    stock_data: Optional[dict] = None # 日周期行情数据（当前交易日的OHLC数据）
    analyst_recommendations: Optional[dict] = None # 分析师推荐
    news_sentiment: Optional[dict] = None  #公司新闻情绪数据

# 子图状态 - 分析子图
class AnalysisSubgraphState(BaseModel):
    stock_data: Optional[dict] = None # 日周期行情数据（当前交易日的OHLC数据）
    analyst_recommendations: Optional[dict] = None # 分析师推荐
    news_sentiment: Optional[dict] = None  #新闻情绪数据
    technical: Optional[dict] = None # 技术指标分析结果
    recommendations: Optional[dict] = None # 分析师评级结果
    sentiment: Optional[dict] = None # 新闻情绪分析结果

# 子图状态 - 报告生成子图
class ReportSubgraphState(BaseModel):
    stock_data: Optional[dict] = None # 日周期行情数据（当前交易日的OHLC数据）
    analyst_recommendations: Optional[dict] = None # 分析师推荐
    news_sentiment: Optional[dict] = None  #新闻情绪数据
    technical: Optional[dict] = None # 技术指标分析结果
    recommendations: Optional[dict] = None # 分析师评级结果
    sentiment: Optional[dict] = None # 新闻情绪分析结果
    summary: Optional[dict] = None # 摘要信息
    market_summary: Optional[str] = None # 市场摘要
    technical_section: Optional[str] = None # 技术分析
    recommendation_section: Optional[str] = None # 投资建议
    news_section: Optional[str] = None # 新闻情绪
    final_section: Optional[str] = None # 最终建议
    full_report: Optional[str] = None # 拼接完整报告

# 主图状态 - 调度和控制
class SupervisorState(BaseModel):
    stock_symbol: Optional[str] = None
    fetch_data: DataFetchSubgraphState = Field(default_factory=DataFetchSubgraphState)
    analysis: AnalysisSubgraphState = Field(default_factory=AnalysisSubgraphState)
    report: ReportSubgraphState = Field(default_factory=ReportSubgraphState)

    error: Optional[str] = None # 错误信息 若有值则流程中断
    next_agent: Optional[str] = None # 决定下一个agent

    messages: List[BaseMessage]


# ———————————————data_fetch 节点 —————————————————————
# pip install finnhub-python
import finnhub
FINNHUB_API_KEY = 'd2619t1r01qhge4eu7igd2619t1r01qhge4eu7j0'
client = finnhub.Client(api_key=FINNHUB_API_KEY)


def fetch_stock_quote(symbol: str) -> dict:
    """获取指定股票的日周期行情数据（当前交易日的OHLC数据）。

    Args:
        symbol: str (股票代码 如 'AAPL')

    Returns:
        dict (日周期股票行情数据 如 {'open': 150.5, 'high': 151.25, 'low': 149.5, 'close': 150.75, 'previous_close': 150.5, 'change': 0.25, 'change_percent': 0.165})
        注意：返回的是当前交易日的日周期数据，包含开盘价、最高价、最低价、收盘价等
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


# ———————————————数据获取子图节点 —————————————————————
def fetch_stock_data_node(state: DataFetchSubgraphState) -> DataFetchSubgraphState:
    """获取股票行情数据"""
    print('fetch_stock_data_node 执行')
    try:
        stock_data = fetch_stock_quote(state.stock_symbol)
        return DataFetchSubgraphState(
            stock_symbol=state.stock_symbol,
            stock_data=stock_data
        )
    except Exception as e:
        print(f"获取股票行情数据失败: {e}")
        # 返回原始状态，但带有错误信息（通过其他方式处理）
        return state

def fetch_analyst_data_node(state: DataFetchSubgraphState) -> DataFetchSubgraphState:
    """获取分析师推荐数据"""
    print('fetch_analyst_data_node 执行')
    try:
        analyst_recommendations = fetch_analyst_recommendations(state.stock_symbol)
        return DataFetchSubgraphState(
            stock_symbol=state.stock_symbol,
            stock_data=state.stock_data,
            analyst_recommendations=analyst_recommendations
        )
    except Exception as e:
        print(f"获取分析师推荐数据失败: {e}")
        return state

def fetch_news_data_node(state: DataFetchSubgraphState) -> DataFetchSubgraphState:
    """获取新闻情绪数据"""
    print('fetch_news_data_node 执行')
    try:
        news_sentiment = fetch_news_sentiment(state.stock_symbol)
        return DataFetchSubgraphState(
            stock_symbol=state.stock_symbol,
            stock_data=state.stock_data,
            analyst_recommendations=state.analyst_recommendations,
            news_sentiment=news_sentiment
        )
    except Exception as e:
        print(f"获取新闻情绪数据失败: {e}")
        return state

def create_data_fetch_subgraph():
    """创建数据获取子图"""
    from langgraph.graph import StateGraph

    subgraph = StateGraph(DataFetchSubgraphState)

    # 添加节点
    subgraph.add_node("fetch_stock", fetch_stock_data_node)
    subgraph.add_node("fetch_analyst", fetch_analyst_data_node)
    subgraph.add_node("fetch_news", fetch_news_data_node)

    # 定义执行顺序
    subgraph.add_edge("fetch_stock", "fetch_analyst")
    subgraph.add_edge("fetch_analyst", "fetch_news")

    # 设置入口和出口
    subgraph.set_entry_point("fetch_stock")
    subgraph.set_finish_point("fetch_news")

    return subgraph.compile()


# ———————————————analysis 节点 —————————————————————

def technical_analysis_tool(data: dict) -> dict:
    """对股票数据进行技术分析, 包括RSI, MACD和EMA指标计算"""
    print("start technical_analysis_tool")
    result = {}

    try:
        # 获取收盘价
        close_price = data.get('close')
        if close_price:
            # 假设我们有过去14天的收盘价（这里用随机数据模拟）
            np.random.seed(42)
            past_prices = np.random.normal(close_price, 5, 14)  # 生成14个接近当前价格的随机数
            past_prices = np.append(past_prices, close_price)  # 添加当前价格
            past_prices = sorted(past_prices)  # 排序以便模拟时间序列

            # 计算RSI
            rsi_indicator = RSIIndicator(pd.Series(past_prices), window=14)
            rsi = rsi_indicator.rsi().iloc[-1]
            result['rsi'] = round(rsi, 2)

            # RSI解读
            if rsi < 30:
                result['rsi_interpretation'] = '超卖，可能反弹'
            elif rsi > 70:
                result['rsi_interpretation'] = '超买，可能回调'
            else:
                result['rsi_interpretation'] = '中性'

            # 计算MACD
            macd_indicator = MACD(pd.Series(past_prices))
            macd = macd_indicator.macd().iloc[-1]
            signal = macd_indicator.macd_signal().iloc[-1]
            result['macd'] = round(macd, 4)
            result['macd_signal'] = round(signal, 4)

            # MACD解读
            if macd > signal:
                result['macd_interpretation'] = 'MACD金叉，看涨'
            else:
                result['macd_interpretation'] = 'MACD死叉，看跌'

            # 计算5日均线和20日均线
            ema5_indicator = EMAIndicator(pd.Series(past_prices), window=5)
            ema20_indicator = EMAIndicator(pd.Series(past_prices), window=20)
            ema5 = ema5_indicator.ema_indicator().iloc[-1]
            ema20 = ema20_indicator.ema_indicator().iloc[-1]
            result['ema5'] = round(ema5, 2)
            result['ema20'] = round(ema20, 2)

            # 均线解读
            if ema5 > ema20:
                result['ema_interpretation'] = '短期均线上穿长期均线，形成金叉，看涨'
            else:
                result['ema_interpretation'] = '短期均线下穿长期均线，形成死叉，看跌'

        return result
    except Exception as e:
        print(f'技术分析工具执行失败: {str(e)}')
        result['error'] = f'技术分析工具执行失败: {str(e)}'
        return result

def recommendation_analysis_tool(data: dict) -> dict:
    """对分析师评级数据进行分析"""
    print("start recommendation_analysis_tool")
    result = {}

    try:
        # 提取评级数据
        strong_buy = data.get('strong_buy', 0)
        buy = data.get('buy', 0)
        hold = data.get('hold', 0)
        sell = data.get('sell', 0)
        strong_sell = data.get('strong_sell', 0)
        period = data.get('period')

        result['strong_buy'] = strong_buy
        result['buy'] = buy
        result['hold'] = hold
        result['sell'] = sell
        result['strong_sell'] = strong_sell
        result['period'] = period

        # 计算总评级数和买入/卖出比例
        total = strong_buy + buy + hold + sell + strong_sell
        if total > 0:
            result['buy_percentage'] = round((strong_buy + buy) / total * 100, 2)
            result['sell_percentage'] = round((sell + strong_sell) / total * 100, 2)
            result['hold_percentage'] = round(hold / total * 100, 2)

            # 分析师共识
            if result['buy_percentage'] > 60:
                result['consensus'] = '强烈买入'
            elif result['buy_percentage'] > 30:
                result['consensus'] = '买入'
            elif result['sell_percentage'] > 60:
                result['consensus'] = '强烈卖出'
            elif result['sell_percentage'] > 30:
                result['consensus'] = '卖出'
            else:
                result['consensus'] = '持有'
        else:
            result['consensus'] = '无共识'

        return result
    except Exception as e:
        print(f'分析师评级分析工具执行失败: {str(e)}')
        result['error'] = f'分析师评级分析工具执行失败: {str(e)}'
        return result

def news_sentiment_analysis_tool(data: dict) -> dict:
    """对新闻进行情绪分析"""
    print("start news_sentiment_analysis_tool")
    result = {}

    try:
        result['news_count'] = len(data.get('recent_news', []))
        result['recent_news'] = data.get('recent_news', [])[:3]

        # 获取新闻情绪数据
        result['positive_news_count'] = data.get('positive_news_count', 0)
        result['negative_news_count'] = data.get('negative_news_count', 0)
        result['neutral_news_count'] = data.get('neutral_news_count', 0)
        result['overall_sentiment'] = data.get('overall_sentiment', '中性')

        return result
    except Exception as e:
        print(f'新闻情绪分析工具执行失败: {str(e)}')
        result['error'] = f'新闻情绪分析工具执行失败: {str(e)}'
        return result


# ———————————————分析子图节点 —————————————————————
def technical_analysis_node(state: AnalysisSubgraphState) -> AnalysisSubgraphState:
    """技术分析节点"""
    print('technical_analysis_node 执行')
    try:
        technical = technical_analysis_tool(state.stock_data or {})
        return AnalysisSubgraphState(
            stock_data=state.stock_data,
            analyst_recommendations=state.analyst_recommendations,
            news_sentiment=state.news_sentiment,
            technical=technical
        )
    except Exception as e:
        print(f"技术分析失败: {e}")
        return state

def recommendation_analysis_node(state: AnalysisSubgraphState) -> AnalysisSubgraphState:
    """分析师推荐分析节点"""
    print('recommendation_analysis_node 执行')
    try:
        recommendations = recommendation_analysis_tool(state.analyst_recommendations or {})
        return AnalysisSubgraphState(
            stock_data=state.stock_data,
            analyst_recommendations=state.analyst_recommendations,
            news_sentiment=state.news_sentiment,
            technical=state.technical,
            recommendations=recommendations
        )
    except Exception as e:
        print(f"分析师推荐分析失败: {e}")
        return state

def sentiment_analysis_node(state: AnalysisSubgraphState) -> AnalysisSubgraphState:
    """新闻情绪分析节点"""
    print('sentiment_analysis_node 执行')
    try:
        sentiment = news_sentiment_analysis_tool(state.news_sentiment or {})
        return AnalysisSubgraphState(
            stock_data=state.stock_data,
            analyst_recommendations=state.analyst_recommendations,
            news_sentiment=state.news_sentiment,
            technical=state.technical,
            recommendations=state.recommendations,
            sentiment=sentiment
        )
    except Exception as e:
        print(f"新闻情绪分析失败: {e}")
        return state

def create_analysis_subgraph():
    """创建分析子图"""
    from langgraph.graph import StateGraph

    subgraph = StateGraph(AnalysisSubgraphState)

    # 添加节点
    subgraph.add_node("technical_analysis", technical_analysis_node)
    subgraph.add_node("recommendation_analysis", recommendation_analysis_node)
    subgraph.add_node("sentiment_analysis", sentiment_analysis_node)

    # 定义执行顺序
    subgraph.add_edge("technical_analysis", "recommendation_analysis")
    subgraph.add_edge("recommendation_analysis", "sentiment_analysis")

    # 设置入口和出口
    subgraph.set_entry_point("technical_analysis")
    subgraph.set_finish_point("sentiment_analysis")

    return subgraph.compile()


# ———————————————report 节点 —————————————————————

def generate_market_summary_tool(data: dict) -> dict:
    """生成市场摘要部分（日周期数据）"""
    print('调用generate_market_summary_tool工具')
    result = {}
    try:
        stock_data = data.get('stock_data', {})
        market_summary = []

        if stock_data:
            # 日周期数据：当前交易日的OHLC数据
            market_summary.append('**日周期数据（当前交易日）**')
            market_summary.append(f'- 开盘价: {stock_data.get("open")}')
            market_summary.append(f'- 最高价: {stock_data.get("high")}')
            market_summary.append(f'- 最低价: {stock_data.get("low")}')
            market_summary.append(f'- 收盘价: {stock_data.get("close")}')
            market_summary.append(f'- 成交量: {stock_data.get("volume")}')
            change_percent = stock_data.get("change_percent")
            if change_percent:
                trend = '上涨' if change_percent > 0 else '下跌'
                market_summary.append(f'- 涨跌幅: {abs(change_percent)}% ({trend})')
        else:
            market_summary.append('- 没有可用的股票行情数据')

        result['market_summary'] = '\n'.join(market_summary)
        return result
    except Exception as e:
        result['error'] = f'生成市场摘要出错: {str(e)}'
        print(result['error'])
        return result


def generate_technical_analysis_section_tool(technical: dict, summary: dict) -> dict:
    """生成技术分析部分"""
    print('调用generate_technical_analysis_section_tool工具')
    result = {}
    try:
        technical_section = []
        tech_summary = summary.get('technical_summary', '没有足够的技术分析数据')
        technical_section.append(f'- {tech_summary}')

        if technical.get('rsi'):
            technical_section.append(f'- RSI指标: {technical["rsi"]}')
            technical_section.append(f'  解读: {technical.get("rsi_interpretation", "无")}')
            # 添加RSI详细分析
            if technical["rsi"] > 70:
                technical_section.append(f'  分析: RSI值超过70，表明股票处于超买状态，短期可能面临回调压力。')
            elif technical["rsi"] < 30:
                technical_section.append(f'  分析: RSI值低于30，表明股票处于超卖状态，短期可能出现反弹。')
            else:
                technical_section.append(f'  分析: RSI值处于中性区域，市场情绪较为平稳。')

        if technical.get('macd') and technical.get('macd_signal'):
            technical_section.append(f'- MACD: {technical["macd"]}, 信号线: {technical["macd_signal"]}')
            technical_section.append(f'  解读: {technical.get("macd_interpretation", "无")}')
            # 添加MACD详细分析
            if technical["macd"] > technical["macd_signal"]:
                technical_section.append(f'  分析: MACD线在信号线之上，形成金叉，是看涨信号。')
            else:
                technical_section.append(f'  分析: MACD线在信号线之下，形成死叉，是看跌信号。')

        if technical.get('ema5') and technical.get('ema20'):
            technical_section.append(f'- EMA5: {technical["ema5"]}, EMA20: {technical["ema20"]}')
            technical_section.append(f'  解读: {technical.get("ema_interpretation", "无")}')
            # 添加EMA详细分析
            if technical["ema5"] > technical["ema20"]:
                technical_section.append(f'  分析: 短期均线上穿长期均线，形成金叉，看涨信号。')
            else:
                technical_section.append(f'  分析: 短期均线下穿长期均线，形成死叉，看跌信号。')

        # 添加综合趋势判断
        technical_section.append('\n- 综合趋势判断:')
        bullish_signals = 0
        bearish_signals = 0

        if technical.get('rsi') and technical['rsi'] < 30:
            bullish_signals += 1
        elif technical.get('rsi') and technical['rsi'] > 70:
            bearish_signals += 1

        if technical.get('macd') and technical.get('macd_signal') and technical['macd'] > technical['macd_signal']:
            bullish_signals += 1
        elif technical.get('macd') and technical.get('macd_signal'):
            bearish_signals += 1

        if technical.get('ema5') and technical.get('ema20') and technical['ema5'] > technical['ema20']:
            bullish_signals += 1
        elif technical.get('ema5') and technical.get('ema20'):
            bearish_signals += 1

        if bullish_signals > bearish_signals:
            technical_section.append(f'  基于技术指标分析，当前市场整体呈现看涨趋势。')
        elif bearish_signals > bullish_signals:
            technical_section.append(f'  基于技术指标分析，当前市场整体呈现看跌趋势。')
        else:
            technical_section.append(f'  基于技术指标分析，当前市场处于震荡整理阶段，趋势不明显。')

        result['technical_section'] = '\n'.join(technical_section)
        return result
    except Exception as e:
        result['error'] = f'生成技术分析部分出错: {str(e)}'
        print(result['error'])
        return result


def generate_recommendation_section_tool(recommendation: dict, summary: dict) -> dict:
    """生成投资建议部分"""
    print('调用generate_recommendation_section_tool工具')
    result = {}
    try:
        recommendation_section = []
        rec_summary = summary.get('recommendation_summary', '没有足够的分析师评级数据')
        recommendation_section.append(f'- {rec_summary}')

        if recommendation.get('consensus'):
            recommendation_section.append(f'- 分析师共识: {recommendation["consensus"]}')

        if recommendation.get('buy_percentage') and recommendation.get('sell_percentage'):
            recommendation_section.append(f'- 买入比例: {recommendation["buy_percentage"]}%')
            recommendation_section.append(f'- 卖出比例: {recommendation["sell_percentage"]}%')

        result['recommendation_section'] = '\n'.join(recommendation_section)
        return result
    except Exception as e:
        result['error'] = f'生成投资建议部分出错: {str(e)}'
        print(result['error'])
        return result


def generate_news_section_tool(news_sentiment: dict, summary: dict) -> dict:
    """生成新闻情绪部分"""
    print('调用generate_news_section_tool工具')
    result = {}
    try:
        news_section = []
        news_summary = summary.get('news_summary', '没有足够的新闻数据')
        news_section.append(f'- {news_summary}')

        if news_sentiment.get('overall_sentiment'):
            news_section.append(f'- 整体情绪: {news_sentiment["overall_sentiment"]}')

        if news_sentiment.get('positive_news_count') and news_sentiment.get('negative_news_count'):
            news_section.append(f'- 正面新闻: {news_sentiment["positive_news_count"]}条')
            news_section.append(f'- 负面新闻: {news_sentiment["negative_news_count"]}条')

        result['news_section'] = '\n'.join(news_section)
        return result
    except Exception as e:
        result['error'] = f'生成新闻情绪部分出错: {str(e)}'
        print(result['error'])
        return result


def generate_final_recommendation_tool(summary: dict) -> dict:
    """生成最终建议部分"""
    print('调用generate_final_recommendation_tool工具 ')
    result = {}
    try:
        final_section = []
        recommendation = summary.get('recommendation', '持有')
        final_section.append(f'- 最终建议: {recommendation}')

        # 根据建议设置信心指数
        confidence = 50
        if recommendation == '买入':
            confidence = 75
        elif recommendation == '卖出':
            confidence = 75
        elif recommendation == '强烈买入':
            confidence = 90
        elif recommendation == '强烈卖出':
            confidence = 90

        final_section.append(f'- 信心指数: {confidence}%')

        # 生成建议理由
        final_section.append('- 建议理由:')

        # 技术分析理由
        tech_summary = summary.get('technical_summary', '')
        if tech_summary:
            final_section.append(f'  - 技术面: {tech_summary}')

        # 投资建议理由
        rec_summary = summary.get('recommendation_summary', '')
        if rec_summary:
            final_section.append(f'  - 基本面: {rec_summary}')

        # 新闻情绪理由
        news_summary = summary.get('news_summary', '')
        if news_summary:
            final_section.append(f'  - 市场情绪: {news_summary}')

        # 添加风险提示
        final_section.append('\n- 风险提示:')
        final_section.append('  - 市场波动风险: 股价可能受到整体市场波动的影响')
        final_section.append('  - 行业政策风险: 相关行业政策变化可能影响公司业绩')
        final_section.append('  - 公司特定风险: 公司基本面变化可能导致股价波动')

        result['final_section'] = '\n'.join(final_section)
        return result
    except Exception as e:
        result['error'] = f'生成最终建议部分出错: {str(e)}'
        print(result['error'])
        return result


# ———————————————报告生成子图节点 —————————————————————
def prepare_summary_node(state: ReportSubgraphState) -> ReportSubgraphState:
    """准备summary字典"""
    print('prepare_summary_node 执行')
    summary = {
        "technical_summary": "基于技术指标分析，当前市场呈现中性走势，投资者应谨慎观望。",
        "recommendation_summary": "分析师评级显示中性态度，建议投资者根据自身风险偏好决定。",
        "news_summary": "近期新闻情绪整体中性，对股价影响有限。",
        "recommendation": "持有"
    }

    # 将summary存储在状态中以供后续节点使用
    return ReportSubgraphState(
        stock_data=state.stock_data,
        analyst_recommendations=state.analyst_recommendations,
        news_sentiment=state.news_sentiment,
        technical=state.technical,
        recommendations=state.recommendations,
        sentiment=state.sentiment,
        summary=summary  # 添加summary字段
    )

def generate_market_summary_node(state: ReportSubgraphState) -> ReportSubgraphState:
    """生成市场摘要"""
    print('generate_market_summary_node 执行')
    try:
        market_summary_result = generate_market_summary_tool({"stock_data": state.stock_data} if state.stock_data else {})
        return ReportSubgraphState(
            stock_data=state.stock_data,
            analyst_recommendations=state.analyst_recommendations,
            news_sentiment=state.news_sentiment,
            technical=state.technical,
            recommendations=state.recommendations,
            sentiment=state.sentiment,
            summary=getattr(state, 'summary', {}),
            market_summary=market_summary_result.get('market_summary', '')
        )
    except Exception as e:
        print(f"生成市场摘要失败: {e}")
        return state

def generate_technical_section_node(state: ReportSubgraphState) -> ReportSubgraphState:
    """生成技术分析部分"""
    print('generate_technical_section_node 执行')
    try:
        summary = getattr(state, 'summary', {})
        technical_section_result = generate_technical_analysis_section_tool(state.technical or {}, summary)
        return ReportSubgraphState(
            stock_data=state.stock_data,
            analyst_recommendations=state.analyst_recommendations,
            news_sentiment=state.news_sentiment,
            technical=state.technical,
            recommendations=state.recommendations,
            sentiment=state.sentiment,
            summary=summary,
            market_summary=state.market_summary,
            technical_section=technical_section_result.get('technical_section', '')
        )
    except Exception as e:
        print(f"生成技术分析部分失败: {e}")
        return state

def generate_recommendation_section_node(state: ReportSubgraphState) -> ReportSubgraphState:
    """生成投资建议部分"""
    print('generate_recommendation_section_node 执行')
    try:
        summary = getattr(state, 'summary', {})
        recommendation_section_result = generate_recommendation_section_tool(state.recommendations or {}, summary)
        return ReportSubgraphState(
            stock_data=state.stock_data,
            analyst_recommendations=state.analyst_recommendations,
            news_sentiment=state.news_sentiment,
            technical=state.technical,
            recommendations=state.recommendations,
            sentiment=state.sentiment,
            summary=summary,
            market_summary=state.market_summary,
            technical_section=state.technical_section,
            recommendation_section=recommendation_section_result.get('recommendation_section', '')
        )
    except Exception as e:
        print(f"生成投资建议部分失败: {e}")
        return state

def generate_news_section_node(state: ReportSubgraphState) -> ReportSubgraphState:
    """生成新闻情绪部分"""
    print('generate_news_section_node 执行')
    try:
        summary = getattr(state, 'summary', {})
        news_section_result = generate_news_section_tool(state.news_sentiment or {}, summary)
        return ReportSubgraphState(
            stock_data=state.stock_data,
            analyst_recommendations=state.analyst_recommendations,
            news_sentiment=state.news_sentiment,
            technical=state.technical,
            recommendations=state.recommendations,
            sentiment=state.sentiment,
            summary=summary,
            market_summary=state.market_summary,
            technical_section=state.technical_section,
            recommendation_section=state.recommendation_section,
            news_section=news_section_result.get('news_section', '')
        )
    except Exception as e:
        print(f"生成新闻情绪部分失败: {e}")
        return state

def generate_final_section_node(state: ReportSubgraphState) -> ReportSubgraphState:
    """生成最终建议部分"""
    print('generate_final_section_node 执行')
    try:
        summary = getattr(state, 'summary', {})
        final_section_result = generate_final_recommendation_tool(summary)
        return ReportSubgraphState(
            stock_data=state.stock_data,
            analyst_recommendations=state.analyst_recommendations,
            news_sentiment=state.news_sentiment,
            technical=state.technical,
            recommendations=state.recommendations,
            sentiment=state.sentiment,
            summary=summary,
            market_summary=state.market_summary,
            technical_section=state.technical_section,
            recommendation_section=state.recommendation_section,
            news_section=state.news_section,
            final_section=final_section_result.get('final_section', '')
        )
    except Exception as e:
        print(f"生成最终建议部分失败: {e}")
        return state

def compile_full_report_node(state: ReportSubgraphState) -> ReportSubgraphState:
    """编译完整报告"""
    print('compile_full_report_node 执行')
    try:
        full_report_parts = []

        if state.market_summary:
            full_report_parts.append('### 市场摘要')
            full_report_parts.append(state.market_summary)

        if state.technical_section:
            full_report_parts.append('### 技术分析')
            full_report_parts.append(state.technical_section)

        if state.recommendation_section:
            full_report_parts.append('### 投资建议')
            full_report_parts.append(state.recommendation_section)

        if state.news_section:
            full_report_parts.append('### 新闻情绪')
            full_report_parts.append(state.news_section)

        if state.final_section:
            full_report_parts.append('### 最终建议')
            full_report_parts.append(state.final_section)

        full_report = '\n\n'.join(full_report_parts) if full_report_parts else ''

        print(f"编译完整报告成功，长度: {len(full_report)}")

        return ReportSubgraphState(
            stock_data=state.stock_data,
            analyst_recommendations=state.analyst_recommendations,
            news_sentiment=state.news_sentiment,
            technical=state.technical,
            recommendations=state.recommendations,
            sentiment=state.sentiment,
            summary=getattr(state, 'summary', {}),
            market_summary=state.market_summary,
            technical_section=state.technical_section,
            recommendation_section=state.recommendation_section,
            news_section=state.news_section,
            final_section=state.final_section,
            full_report=full_report
        )
    except Exception as e:
        print(f"编译完整报告失败: {e}")
        return state

def create_report_subgraph():
    """创建报告生成子图"""
    from langgraph.graph import StateGraph

    subgraph = StateGraph(ReportSubgraphState)

    # 添加节点
    subgraph.add_node("prepare_summary", prepare_summary_node)
    subgraph.add_node("generate_market_summary", generate_market_summary_node)
    subgraph.add_node("generate_technical_section", generate_technical_section_node)
    subgraph.add_node("generate_recommendation_section", generate_recommendation_section_node)
    subgraph.add_node("generate_news_section", generate_news_section_node)
    subgraph.add_node("generate_final_section", generate_final_section_node)
    subgraph.add_node("compile_full_report", compile_full_report_node)

    # 定义执行顺序
    subgraph.add_edge("prepare_summary", "generate_market_summary")
    subgraph.add_edge("generate_market_summary", "generate_technical_section")
    subgraph.add_edge("generate_technical_section", "generate_recommendation_section")
    subgraph.add_edge("generate_recommendation_section", "generate_news_section")
    subgraph.add_edge("generate_news_section", "generate_final_section")
    subgraph.add_edge("generate_final_section", "compile_full_report")

    # 设置入口和出口
    subgraph.set_entry_point("prepare_summary")
    subgraph.set_finish_point("compile_full_report")

    return subgraph.compile()


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

def data_fetch_subgraph_node(state: SupervisorState) -> SupervisorState:
    """数据获取子图节点"""
    print('data_fetch_subgraph_node 执行')

    try:
        # 创建数据获取子图
        subgraph = create_data_fetch_subgraph()

        # 准备子图输入状态
        subgraph_input = DataFetchSubgraphState(stock_symbol=state.stock_symbol)

        # 执行子图
        result = subgraph.invoke(subgraph_input)

        # 更新主状态
        return SupervisorState(
            stock_symbol=state.stock_symbol,
            fetch_data=result,  # result已经是DataFetchSubgraphState类型
            analysis=state.analysis,
            report=state.report,
            messages=state.messages
        )
    except Exception as e:
        error_msg = f"数据获取子图执行失败: {e}"
        print(error_msg)
        return SupervisorState(
            stock_symbol=state.stock_symbol,
            fetch_data=state.fetch_data,
            analysis=state.analysis,
            report=state.report,
            messages=state.messages,
            error=error_msg
        )

def analysis_subgraph_node(state: SupervisorState) -> SupervisorState:
    """分析子图节点"""
    print('analysis_subgraph_node 执行')

    try:
        # 创建分析子图
        subgraph = create_analysis_subgraph()

        # 准备子图输入状态
        subgraph_input = AnalysisSubgraphState(
            stock_data=state.fetch_data.stock_data,
            analyst_recommendations=state.fetch_data.analyst_recommendations,
            news_sentiment=state.fetch_data.news_sentiment
        )

        # 执行子图
        result = subgraph.invoke(subgraph_input)

        # 更新主状态
        return SupervisorState(
            stock_symbol=state.stock_symbol,
            fetch_data=state.fetch_data,
            analysis=result,  # result已经是AnalysisSubgraphState类型
            report=state.report,
            messages=state.messages
        )
    except Exception as e:
        error_msg = f"分析子图执行失败: {e}"
        print(error_msg)
        return SupervisorState(
            stock_symbol=state.stock_symbol,
            fetch_data=state.fetch_data,
            analysis=state.analysis,
            report=state.report,
            messages=state.messages,
            error=error_msg
        )

def report_subgraph_node(state: SupervisorState) -> SupervisorState:
    """报告生成子图节点"""
    print('report_subgraph_node 执行')

    try:
        # 创建报告生成子图
        subgraph = create_report_subgraph()

        # 准备子图输入状态
        subgraph_input = ReportSubgraphState(
            stock_data=state.fetch_data.stock_data,
            analyst_recommendations=state.fetch_data.analyst_recommendations,
            news_sentiment=state.fetch_data.news_sentiment,
            technical=state.analysis.technical,
            recommendations=state.analysis.recommendations,
            sentiment=state.analysis.sentiment
        )

        # 执行子图
        result = subgraph.invoke(subgraph_input)

        # 更新主状态
        return SupervisorState(
            stock_symbol=state.stock_symbol,
            fetch_data=state.fetch_data,
            analysis=state.analysis,
            report=result,  # result已经是ReportSubgraphState类型
            messages=state.messages
        )
    except Exception as e:
        error_msg = f"报告生成子图执行失败: {e}"
        print(error_msg)
        return SupervisorState(
            stock_symbol=state.stock_symbol,
            fetch_data=state.fetch_data,
            analysis=state.analysis,
            report=state.report,
            messages=state.messages,
            error=error_msg
        )


def compile_workflow():
    # 创建图
    graph = StateGraph(SupervisorState)
    # 注册节点
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("data_fetch", data_fetch_subgraph_node)
    graph.add_node("analysis", analysis_subgraph_node)
    graph.add_node("report", report_subgraph_node)
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


def main(stock_symbol: str = 'TSLA') -> Dict[str, Any]:
    """主函数，启动supervisor多agent系统

    Args:
        stock_symbol (str): 要分析的股票代码，默认为'AAPL'

    Returns:
        Dict[str, Any]: 包含分析结果的字典
    """
    print(f'启动股票 {stock_symbol} 分析')

    try:
        # 编译工作流
        print('编译supervisor工作流')
        graph = compile_workflow()
        print('工作流编译完成')

        # 设置初始状态
        initial_state = SupervisorState(
            stock_symbol=stock_symbol,
            messages=[
                HumanMessage(content=f"请分析股票 {stock_symbol} 并生成完整报告。")
            ]
        )
        print(f'初始状态: {initial_state}')

        print('开始运行supervisor工作流')
        result = graph.invoke(initial_state)
        print(f'工作流执行结果: {result}')

        # 检查是否有错误
        if result.get('error'):
            error_msg = f'工作流执行出错: {result["error"]}'
            print(error_msg)
            return {'success': False, 'error': error_msg}

        # 打印报告
        if result.get('report') and hasattr(result['report'], 'full_report') and result['report'].full_report:
            print(f'股票 {stock_symbol} 分析报告生成成功')
            print('\n' + '='*50)
            print(f'股票 {stock_symbol} 市场分析报告')
            print('='*50)
            print(result['report'].full_report)
            print('='*50)
            
            # 保存报告到md文件
            try:
                # 生成文件名：股票代码_分析报告_时间戳.md
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{stock_symbol}_分析报告_{timestamp}.md"
                filepath = pathlib.Path(__file__).parent / filename
                
                # 写入文件
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"# {stock_symbol} 股票市场分析报告\n\n")
                    f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write("---\n\n")
                    f.write(result['report'].full_report)
                
                print(f'\n报告已保存到: {filepath}')
                return {'success': True, 'report': result['report'].full_report, 'filepath': str(filepath)}
            except Exception as e:
                print(f'保存报告到文件失败: {e}')
                # 即使保存失败，也返回成功（报告已生成）
                return {'success': True, 'report': result['report'].full_report, 'filepath': None}
        else:
            error_msg = f'股票 {stock_symbol} 分析报告生成失败'
            print(error_msg)
            # 打印结果中的所有字段，以便调试
            print(f'结果中的其他字段: {[k for k in result.keys() if k != "report"]}')
            return {'success': False, 'error': error_msg}
    except Exception as e:
        error_msg = f'分析过程中发生错误: {str(e)}'
        print(error_msg)
        # 打印异常的详细信息
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': error_msg}


if __name__ == "__main__":
    # 可以在这里指定股票代码，默认为'TSLA'
    result = main()
    if result['success']:
        print("分析完成！")
    else:
        print(f"分析失败: {result['error']}")