
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



# —————————运行—————————
# 1 直接输入
response = llm.invoke('你是哪家的模型 什么版本型号')
# 直接输出
print(response.content) 
# 流式输出
for chunk in llm.stream('你是哪家的模型 什么版本型号'):
    print(chunk.content, end="", flush=True)


# 2 输入list
messages_1 = [
    SystemMessage(content="你是一个宠物猫 回答后缀附带 喵~"),
    HumanMessage(content="'你是哪家的模型 什么版本型号'"),
]
response = llm.invoke(messages_1)
print(response.content)


# 3 提示词模板替换
messages_2 = ChatPromptTemplate.from_messages([
    ("system", "你是一个 {role} "),
    ("human", "{question}")
])
chain = messages_2 | llm
response = chain.invoke({"role": "宠物猫", "question": "你好"})
print(response.content)
