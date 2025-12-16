
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
from langchain_core.output_parsers import JsonOutputParser


# —————————公共变量—————————
llm = ChatOpenAI(model=model, api_key=api_key, base_url=api_url)  



# 4 输出格式化
prompt = ChatPromptTemplate.from_messages([
    ("system", "请以 JSON 格式输出，必须包含 'title' 和 'summary' 字段"),
    ("human", "简化为5个字：{article}")
])
output_parser = JsonOutputParser()

chain = prompt | llm | output_parser
response = chain.invoke({"article": "AI 是一种智能化的技术，它可以帮助我们完成很多工作，提高工作效率。"})
print(response)