
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


# 聊天
from langchain_openai import ChatOpenAI

# prompt
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate

# 格式化输出
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser

# —————————公共变量—————————
llm = ChatOpenAI(model=model, api_key=api_key, base_url=api_url)  



# —————————运行—————————
# 写法1
class Person(BaseModel):
    name: str = Field(description="姓名")
    age: int = Field(description="年龄")
    occupation: str = Field(description="职业")
    skills: list[str] = Field(description="技能列表")

parser = PydanticOutputParser(pydantic_object=Person)

prompt = ChatPromptTemplate.from_messages([
    ("system", "从文本中提取人物信息并输出\n{format_instructions}"),
    ("human", "{text}")
])

chain = prompt | llm | parser

# get_format_instructions() 根据pydantic格式 自动化形成prompt 告诉模型输出什么格式
result = chain.invoke({
    "text": "小明是一位 35 岁的资深算法工程师，精通 Python、机器学习、深度学习",
    "format_instructions": parser.get_format_instructions()
})

print(f"姓名：{result.name}")
print(f"年龄：{result.age}")
print(f"职业：{result.occupation}")
print(f"技能列表：{result.skills}")



# ——————————写法2——————————
class ClarifyWithUser(BaseModel):
    need_clarification: bool = Field(description="是否需要向用户提问以澄清需求")
    question: str = Field(description="如果需要澄清，向用户提出的问题（使用 Markdown 格式")
    verification: str = Field(description="如果不需要澄清，确认开始研究的消息")


user_input = "研究雀巢公司财报"
response = llm.with_structured_output(ClarifyWithUser).invoke(user_input)
print(response)