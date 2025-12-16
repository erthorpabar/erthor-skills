
'''  
                                 ┌──> FAQ   ──┐ 
用户输入 -> 意图识别 -> 槽位填充 ──┼──> RAG   ──┼──> 生成结果 -> 
               ↑__________↓      ├──> 人工  ───┤
                                 └──>       ───┘
'''

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
from typing import Literal, List, Dict, Annotated
import requests
from operator import add

# 图节点管理
from langgraph.graph import StateGraph, START, END

# 聊天
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langchain_core.messages import BaseMessage

# prompt
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage

# 记忆
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages

# 工具
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode

# 反思
from langchain_community.tools.tavily_search import TavilySearchResults


# —————————公共变量—————————
llm = ChatOpenAI(model=model, api_key=api_key, base_url=api_url)  

class CustomerServiceState(TypedDict):
    # 用户信息
    user_id: str
    user_tier: str  # vip/premium/regular

    # 消息历史
    messages: Annotated[list[BaseMessage], add]

    # 分类结果
    intent: str  # greeting/faq/query/complaint/other
    category: str  # technical/billing/product/other
    sentiment: str  # positive/negative/neutral
    urgency: str  # high/medium/low

    # 处理路径
    routing_path: str  # faq/knowledge_base/technical/human
    requires_human: bool

    # 响应
    response: str
    confidence: float

    # 元数据
    timestamp: str
    processing_time: float


# ——————————定义函数——————————

# 2.1 意图分类节点
def intent_classification_node(state: CustomerServiceState) -> dict:
    """分析用户消息,识别意图、类别、情感、紧急度"""

    user_message = state["messages"][-1].content

    # 使用 LLM 进行分类
    classifier_prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个客服消息分类器。分析用户消息并返回分类结果。

请严格按照以下JSON格式返回，不要添加任何其他文字：
{{
  "intent": "选择一个: greeting/faq/query/complaint/other",
  "category": "选择一个: technical/billing/product/other",
  "sentiment": "选择一个: positive/negative/neutral",
  "urgency": "选择一个: high/medium/low"
}}

分类说明：
- intent（意图）: greeting=问候, faq=常见问题, query=查询, complaint=投诉, other=其他
- category（类别）: technical=技术, billing=账单, product=产品, other=其他
- sentiment（情感）: positive=积极, negative=消极, neutral=中性
- urgency（紧急度）: high=高, medium=中, low=低

只返回JSON，不要有其他内容！
        """),
        ("human", "{message}")
    ])

    llm_classifier = ChatOpenAI(model=model, api_key=api_key, base_url=api_url, temperature=0)
    chain = classifier_prompt | llm_classifier

    result = chain.invoke({"message": user_message})
    
    # 提取和解析 JSON
    import json
    import re
    
    content = result.content.strip()
    
    # 尝试直接解析
    try:
        classification = json.loads(content)
    except json.JSONDecodeError:
        # 如果失败，尝试提取 JSON 部分
        json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
        if json_match:
            classification = json.loads(json_match.group())
        else:
            # 如果还是失败，使用默认值
            print(f"无法解析分类结果，使用默认值。原始内容: {content}")
            classification = {
                "intent": "other",
                "category": "other",
                "sentiment": "neutral",
                "urgency": "medium"
            }

    return {
        "intent": classification.get("intent", "other"),
        "category": classification.get("category", "other"),
        "sentiment": classification.get("sentiment", "neutral"),
        "urgency": classification.get("urgency", "medium")
    }


# 2.2 FAQ 处理节点
def faq_node(state: CustomerServiceState) -> dict:
    """处理常见问题"""

    # FAQ 数据库 (实际应用应该用向量数据库)
    faq_database = {
        "营业时间": "我们的营业时间是周一至周五 9:00-18:00",
        "退货政策": "购买后 7 天内可以无理由退货",
        "配送时间": "一般 3-5 个工作日送达",
        "支付方式": "支持支付宝、微信、银行卡支付"
    }

    user_message = state["messages"][-1].content

    # 简单匹配 (实际应用应该用语义搜索)
    response = "抱歉,未找到相关 FAQ"
    for key, value in faq_database.items():
        if key in user_message:
            response = value
            break

    return {
        "response": response,
        "confidence": 0.9 if response != "抱歉,未找到相关 FAQ" else 0.3,
        "routing_path": "faq"
    }


# 2.3 知识库查询节点
def knowledge_base_node(state: CustomerServiceState) -> dict:
    """查询知识库 (RAG)"""

    user_message = state["messages"][-1].content

    # 模拟 RAG 流程
    # 1. 向量检索
    retrieved_docs = [
        "产品 X 的技术规格是...",
        "关于计费方式,我们支持...",
    ]

    # 2. LLM 生成答案
    rag_prompt = ChatPromptTemplate.from_messages([
        ("system", """基于以下知识库内容回答用户问题:
        {context}

        如果知识库中没有相关信息,请说明并建议转人工客服。
        """),
        ("human", "{question}")
    ])


    chain = rag_prompt | llm

    response = chain.invoke({
        "context": "\n".join(retrieved_docs),
        "question": user_message
    })

    return {
        "response": response.content,
        "confidence": 0.8,
        "routing_path": "knowledge_base"
    }


# 2.4 技术支持节点
def technical_support_node(state: CustomerServiceState) -> dict:
    """处理技术问题"""

    user_message = state["messages"][-1].content

    # 调用专门的技术支持 LLM (可能有特殊提示或工具)
    tech_prompt = ChatPromptTemplate.from_messages([
        ("system", """你是专业的技术支持工程师。
        分析用户的技术问题,提供详细的解决方案。
        如果问题复杂,建议转人工工程师。
        """),
        ("human", "{problem}")
    ])

    llm_tech = ChatOpenAI(model=model, api_key=api_key, base_url=api_url)
    chain = tech_prompt | llm_tech

    response = chain.invoke({"problem": user_message})

    # 检查是否需要人工
    requires_human = "转人工" in response.content or state["urgency"] == "high"

    return {
        "response": response.content,
        "requires_human": requires_human,
        "confidence": 0.7,
        "routing_path": "technical"
    }


# 2.5 人工转接节点
def human_handoff_node(state: CustomerServiceState) -> dict:
    """转接人工客服"""

    # 收集所有上下文信息
    context = {
        "user_id": state["user_id"],
        "tier": state["user_tier"],
        "intent": state["intent"],
        "category": state["category"],
        "sentiment": state["sentiment"],
        "urgency": state["urgency"],
        "conversation": [m.content for m in state["messages"]]
    }

    response = f"""已为您转接人工客服。
    工单编号: {state['user_id']}-{state['timestamp']}
    预计等待时间: {"立即接入" if state['user_tier'] == 'vip' else "3-5 分钟"}
    """

    return {
        "response": response,
        "routing_path": "human",
        "requires_human": True
    }

# 2.6 响应生成节点
def response_generation_node(state: CustomerServiceState) -> dict:
    """生成最终响应"""

    # 添加 AI 响应到消息历史
    return {
        "messages": [AIMessage(content=state["response"])]
    }







def route_after_classification(state: CustomerServiceState) -> Literal["faq", "knowledge_base", "technical", "human", "end"]:
    """根据分类结果路由"""

    # 规则 1: VIP 用户直接转人工
    if state["user_tier"] == "vip":
        return "human"

    # 规则 2: 投诉 + 负面情绪 → 人工
    if state["intent"] == "complaint" and state["sentiment"] == "negative":
        return "human"

    # 规则 3: 高紧急度 → 人工
    if state["urgency"] == "high":
        return "human"

    # 规则 4: 问候 → 直接结束
    if state["intent"] == "greeting":
        return "end"

    # 规则 5: FAQ → FAQ 节点
    if state["intent"] == "faq":
        return "faq"

    # 规则 6: 技术问题 → 技术支持
    if state["category"] == "technical":
        return "technical"

    # 规则 7: 其他查询 → 知识库
    if state["intent"] == "query":
        return "knowledge_base"

    # 默认: 结束
    return "end"

def route_after_processing(state: CustomerServiceState) -> Literal["response", "human"]:
    """处理后的路由: 检查是否需要转人工"""

    # 置信度低 → 转人工
    if state["confidence"] < 0.5:
        return "human"

    # 明确标记需要人工
    if state.get("requires_human", False):
        return "human"

    # 正常响应
    return "response"


# ========== 4. 构建图 ==========

graph = StateGraph(CustomerServiceState)

# 添加节点
graph.add_node("classify", intent_classification_node)
graph.add_node("faq", faq_node)
graph.add_node("knowledge_base", knowledge_base_node)
graph.add_node("technical", technical_support_node)
graph.add_node("human", human_handoff_node)
graph.add_node("respond", response_generation_node)

# 添加边
graph.add_edge(START, "classify")

# 分类后的条件路由
graph.add_conditional_edges(
    "classify",
    route_after_classification,
    {
        "faq": "faq",
        "knowledge_base": "knowledge_base",
        "technical": "technical",
        "human": "human",
        "end": END
    }
)

# FAQ 处理后检查是否需要转人工
graph.add_conditional_edges(
    "faq",
    route_after_processing,
    {
        "response": "respond",
        "human": "human"
    }
)

# 知识库查询后检查
graph.add_conditional_edges(
    "knowledge_base",
    route_after_processing,
    {
        "response": "respond",
        "human": "human"
    }
)

# 技术支持后检查
graph.add_conditional_edges(
    "technical",
    route_after_processing,
    {
        "response": "respond",
        "human": "human"
    }
)

# 所有路径最终都到 END
graph.add_edge("respond", END)
graph.add_edge("human", END)

# 编译
app = graph.compile()




# 测试用例 1: FAQ
result1 = app.invoke({
    "user_id": "user123",
    "user_tier": "regular",
    "messages": [HumanMessage("你们的营业时间是?")],
    "timestamp": "2024-10-30 10:00:00"
})

print("测试 1 - FAQ:")
print(f"路径: {result1['routing_path']}")
print(f"响应: {result1['response']}")
print()

# 测试用例 2: 技术问题
result2 = app.invoke({
    "user_id": "user456",
    "user_tier": "premium",
    "messages": [HumanMessage("我的软件崩溃了,无法启动")],
    "timestamp": "2024-10-30 10:05:00"
})

print("测试 2 - 技术问题:")
print(f"路径: {result2['routing_path']}")
print(f"响应: {result2['response'][:100]}...")
print()

# 测试用例 3: VIP 用户
result3 = app.invoke({
    "user_id": "user789",
    "user_tier": "vip",
    "messages": [HumanMessage("我需要咨询一个问题")],
    "timestamp": "2024-10-30 10:10:00"
})

print("测试 3 - VIP 用户:")
print(f"路径: {result3['routing_path']}")
print(f"响应: {result3['response']}")








