# ——————————当前文件夹路径加入搜索路径——————————
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 仅限本机，设置网络代理
# os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
# os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"

# ——————————————创建app——————————————
import uvicorn
from fastapi import FastAPI
app = FastAPI()

# ——————————环境变量——————————
from dotenv import load_dotenv
load_dotenv()

# ——————————route 功能区——————————
from api.A_basic_01_gpu_t2iws import router as basic_01_gpu_t2iws
app.include_router(basic_01_gpu_t2iws, prefix="/basic/gpu/t2iws", tags=["basic"])

from api.A_basic_02_cpu_upimg import router as basic_02_cpu_upimg
app.include_router(basic_02_cpu_upimg, prefix="/basic/cpu/upimg", tags=["basic"])

from api.A_two_character_01_gpu import router as two_character_01_gpu
app.include_router(two_character_01_gpu, prefix="/two_character/gpu/01", tags=["two_character"])

from api.A_two_character_02_gpu import router as two_character_02_gpu
app.include_router(two_character_02_gpu, prefix="/two_character/gpu/02", tags=["two_character"])


# ——————————日志——————————
# from fastapi import Request # 接收参数
# from fastapi.responses import JSONResponse # 格式
# import logging
# from datetime import datetime
'''
这个日志记录有一个bug,reload=True时候会不断写入log,但不重要，正式使用中关闭热重载
'''
# logging.basicConfig(filename='app.log', level=logging.INFO, format='%(message)s')
# ——————————————全局逻辑错误记录——————————————
# @app.exception_handler(Exception)  # 捕获所有异常
# async def global_exception_handler(request: Request, exc: Exception):
#     # 记录代码逻辑错误
#     logging.error("时间: %s", datetime.now())  # 记录时间
#     logging.error("异常类型: %s", type(exc))  # 记录异常类型
#     logging.error("异常值: %s", str(exc))  # 记录异常值
#     logging.error("异常回溯信息:", exc_info=True )  # 记录回溯信息
#     logging.error("————————————————————" )

#     return JSONResponse(
#         status_code=500,
#         content={"detail": "服务器逻辑错误"},
#     )
"""
HTTPException 的报错不会记录 
try except 的报错不会记录 
逻辑运行错误 的报错会记录 
raise 的报错会记录 所以在services中使用raise 
"""

if __name__ == "__main__":
    port = int(os.getenv("PORT", 7004)) # 端口
    host = os.getenv("HOST", "0.0.0.0") # 主机

    uvicorn.run("server:app", host=host, port=port,reload=True) # 启动服务
