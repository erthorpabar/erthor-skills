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
from typing import TypedDict, Dict, Any, List, Literal, Optional, List, Annotated, Sequence
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

# 图节点管理
from langgraph.graph import StateGraph, START, END

# state
from langgraph.graph import MessagesState
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages

# 聊天
from langchain_openai import ChatOpenAI

# 记忆
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.memory import InMemorySaver

# 工具
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode

# 格式化输出
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.output_parsers import PydanticOutputParser

# prompt模板
from langchain_core.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# 反思
from langchain_community.tools.tavily_search import TavilySearchResults

# 中断
from langgraph.types import interrupt

# supervisor
from langgraph.types import Command

# —————————公共变量—————————
llm = ChatOpenAI(model=model, api_key=api_key, base_url=api_url)

# 用户会话信息
user_id = "123"
session_id = "456"
config = {"configurable": {"thread_id": f"{user_id}_{session_id}"}}

# 自带类
# class MessagesState(TypedDict):
#     messages: Annotated[list[BaseMessage], add_messages]
class State(MessagesState):
    research_brief: Optional[str]    # 生成研究简报
    supervisor_messages: Annotated[Sequence[BaseMessage], add_messages] # 与supervisor的对话历史



# 
''' 
1 scoping 模糊需求 -> 澄清需求

'''

# scoping
# 1 
# class ClarifyWithUser(BaseModel):
#     need_clarification: bool = Field(description="是否需要向用户提问以澄清需求")
#     question: str = Field(description="如果需要澄清，向用户提出的问题（使用 Markdown 格式")
#     verification: str = Field(description="如果不需要澄清，确认开始研究的消息")
# parser = PydanticOutputParser(pydantic_object=ClarifyWithUser)
# format_instructions = parser.get_format_instructions()

# user_input = '我想研究旧金山最好的咖啡店。'

# # 提示词替换模板
# prompt = ChatPromptTemplate.from_messages([
#     ("system", "从文本中提取人物信息并输出{format_instructions}"),
#     ("human", "{user_input}")
# ])
# chain = prompt | llm 
# date = datetime.now().strftime("%Y-%m-%d")
# response = chain.invoke({
#     "user_input": user_input, 
#     "format_instructions": format_instructions
# })
# print(response.content)


# 2 
system_prompt = ''' 
这是用户与你的对话历史:
<Messages>
{messages}
</Messages>

今天的日期是 {date}。

评估是否需要提问澄清，或者用户已经提供了足够信息。

重要提示: 如果你已经在对话历史中问过澄清问题，几乎总是不需要再问。
只在绝对必要时才提出新问题。

如果有缩写、简称或未知术语，请用户澄清。

如果需要提问，遵循以下准则:
- 简洁的同时收集所有必要信息
- 确保收集执行研究任务所需的全部信息
- 适当时使用项目符号或编号列表以提高清晰度
- 确保使用 Markdown 格式，可被 Markdown 渲染器正确显示
- 不要询问不必要的信息或用户已经提供的信息

以有效 JSON 格式响应，包含以下键:
"need_clarification": boolean,
"question": "<向用户提问以澄清研究范围>",
"verification": "<确认我们将开始研究的消息>"

如果需要澄清问题，返回:
"need_clarification": true,
"question": "<你的澄清问题>",
"verification": ""

如果不需要澄清问题，返回:
"need_clarification": false,
"question": "",
"verification": "<确认消息：你将基于提供的信息开始研究>"

对于不需要澄清时的确认消息:
- 确认你有足够信息继续
- 简要总结你从请求中理解的关键内容
- 确认你现在将开始研究过程
- 保持简洁和专业
'''
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "请根据上述对话历史分析并回答。")
])
chain = prompt | llm
date = datetime.now().strftime("%Y-%m-%d")
user_input = '我想研究旧金山最好的咖啡店。'

response = chain.invoke({
    "messages": user_input,
    "date": date
})
print(response.content)

# # 3 
# class ClarifyWithUser(BaseModel):
#     need_clarification: bool = Field(description="是否需要向用户提问以澄清需求")
#     question: str = Field(description="如果需要澄清，向用户提出的问题（使用 Markdown 格式")
#     verification: str = Field(description="如果不需要澄清，确认开始研究的消息")

# user_input = '''我想研究旧金山基于咖啡质量的最佳咖啡店。
# 请关注专业评分（Coffee Review）、豆源和烘焙技术。
# 优先使用官网和专业评测网站。'''
# response = llm.with_structured_output(ClarifyWithUser, method="function_calling").invoke(user_input)
# print(response)
# # with_structured_output 依赖function call
# # method 强制使用某一种方式输出