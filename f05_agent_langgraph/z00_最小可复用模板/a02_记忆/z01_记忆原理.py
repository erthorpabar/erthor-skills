'''记忆方案 '''

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
import requests


# 对话函数
def chat(messages):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    data = {
        "model": model,
        "messages": messages
    }

    response = requests.post(api_url + "/chat/completions", headers=headers, json=data)
    answer = response.json()["choices"][0]["message"]["content"] 
    return answer


# 对话系统
messages = [] # 历史记录

# 对话系统
while True:
    # 开始打印


    # 用户输入
    user_input = input("用户: ")
    if user_input == "quit":
        break
    
    messages.append({"role": "user", "content": user_input})

    # ai回答
    answer = chat(messages)
    messages.append({"role": "assistant", "content": answer})
    print("ai: ", answer)