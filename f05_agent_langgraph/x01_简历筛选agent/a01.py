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
from typing import TypedDict, Dict, Any, List, Literal

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

# 格式化
from langchain_core.output_parsers import JsonOutputParser

# prompt模板
from langchain_core.prompts import PromptTemplate

# 反思
from langchain_community.tools.tavily_search import TavilySearchResults

# 中断
from langgraph.types import interrupt

# 加载路径
import pathlib

# —————————公共变量—————————
llm = ChatOpenAI(model=model, api_key=api_key, base_url=api_url)  

# 自带类
# class MessagesState(TypedDict):
#     messages: Annotated[list[BaseMessage], add_messages]
class State(TypedDict):
    jd: str  # 岗位描述文本
    resume: str  # 候选人简历文本
    skills: Dict[str, Any]  # 提取出来的技能信息，通常为键→值结构
    score: Dict[str, Any]  # 技能评分结果，包含 total_score、strengths、weaknesses
    decision: str  # 最终筛选决策，"通过"、"待定" 或 "不通过"
    total_score: int  # 总分，范围 0–100
    strengths: List[str]  # 优势
    weaknesses: List[str]  # 劣势

# 输出解析器
json_parser = JsonOutputParser()

# ————————函数—————————
# 加载文件
def load_file(path: str) -> str:
    return pathlib.Path(path).read_text(encoding="utf-8")

# 更新到状态
def init_inputs(state: State) -> State: 
    # 加载文件的路径
    state["jd"] = load_file("xxx/jd.md")
    state["resume"] = load_file("xxx/resume.md")
    return state


# ——————子图——————
# --- 技能提取  ---
extract_prompt = PromptTemplate.from_template(
    template="""
你是一位AI招聘专家，请阅读以下岗位描述与简历内容，并提取应聘者的核心技能，输出纯 JSON 格式，不要添加任何额外说明文字。

岗位描述：
{jd}

简历内容：
{resume}

输出格式示例：
{format_instructions}
""",
    partial_variables={"format_instructions": json_parser.get_format_instructions()}
)
extract_chain = extract_prompt | llm | json_parser

def extract_skills(state: State) -> State:
    parsed = extract_chain.invoke({
        "jd": state["jd"],
        "resume": state["resume"]
    })
    state["skills"] = parsed
    return state




# --- 技能评分  ---
score_prompt = PromptTemplate.from_template(
    template="""
你是 AI 招聘专家，请根据以下技能信息，为候选人的简历进行评分，返回纯 JSON 并且不要任何多余文字。

技能数据：
{skills}

评分规则：
- 总分为 100 分
- 请在 JSON 中返回：
  - total_score: 0~100 的整数
  - strengths: 在哪些维度表现优秀的列表
  - weaknesses: 在哪些维度表现不足的列表

{format_instructions}
""",
    partial_variables={"format_instructions": json_parser.get_format_instructions()}
)
score_chain = score_prompt | llm | json_parser


def calculate_score(state: State) -> State:
    parsed = score_chain.invoke({
        "skills": state["skills"]
    })
    state["score"] = parsed
    return state


# --- 决策 Agent ---
decision_prompt = PromptTemplate.from_template(
    template="""
你是资深 AI 招聘专家，请根据候选人的评分结果与技能优势劣势，给出是否通过初筛的判断，并输出精炼的总结。

输入如下：
评分信息：
{score}

技能结构化信息：
{skills}

请返回如下 JSON 格式（仅返回 JSON）：
- total_score: 整数分数
- strengths: 精选2-3条优势，总结清晰
- weaknesses: 精选1-2条明显劣势

{format_instructions}
""",
    partial_variables={"format_instructions": json_parser.get_format_instructions()}
)
decision_chain = decision_prompt | llm | json_parser


def make_decision(state: State) -> State:
    parsed = decision_chain.invoke({
        "score": state["score"],
        "skills": state["skills"]
    })
    total_score = state.get("score", {}).get("total_score", 0)
    if total_score >= 70:
        decision = "通过"
    elif total_score >= 60:
        decision = "待定"
    else:
        decision = "不通过"
    state["decision"] = decision
    state["total_score"] = total_score
    state["strengths"] = parsed.get("strengths", [])
    state["weaknesses"] = parsed.get("weaknesses", [])
    return state

# --- 子图构建 ---
def build_resume_screening_subgraph():
    # 创建图
    graph = StateGraph(State)
    # 注册节点
    graph.add_node("extract_skills", extract_skills)
    graph.add_node("calculate_score", calculate_score)
    graph.add_node("make_decision", make_decision)
    # 添加边
    graph.add_edge(START, "extract_skills")
    graph.add_edge("extract_skills", "calculate_score")
    graph.add_edge("calculate_score", "make_decision")
    graph.add_edge("make_decision", END)
    # 运行
    app = graph.compile()
    return app

# ———————主图构建—————————
def build_main_graph():
    # 创建图
    graph = StateGraph(State)
    # 注册节点
    graph.add_node("init_inputs", init_inputs)
    graph.add_node("resume_subgraph", build_resume_screening_subgraph())  # 将子图作为单节点
    # 添加边
    graph.add_edge(START, "init_inputs")
    graph.add_edge("init_inputs", "resume_subgraph")
    graph.add_edge("resume_subgraph", END)
    # 运行
    app = graph.compile()
    return app


if __name__ == "__main__":
    main_graph = build_main_graph()
    config = {"configurable": {"thread_id": "resume_001"}}

    print("=== 节点执行中间结果 ===")
    final_state = None
    for chunk in main_graph.stream({}, config, stream_mode="updates"):
        # 每次 chunk 是一个 dict，key 为节点名，value 为该节点更新的 state
        for node_name, update in chunk.items():
            print(f"[{node_name}] 执行完成，输出：")
            print(update)
            print("-" * 40)
            final_state = update  # 最后一个节点的更新

    # 如果你还想输出最终整体决策结果，可从 final_state 或 graph.get_state() 中获取
    if final_state is not None:
        print("\n=== 简历筛选最终结果 ===")
        # 假设最终 state 包含 decision、total_score、strengths、weaknesses
        print(f"决策结果：{final_state.get('decision')}")
        print(f"总分：{final_state.get('total_score')}")
        print("优势：")
        for s in final_state.get('strengths', []):
            print(f"- {s}")
        print("劣势：")
        for w in final_state.get('weaknesses', []):
            print(f"- {w}")