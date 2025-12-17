"""文生图websocket长连接"""
# 路由
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from fastapi import Depends

# 功能函数
from services.v1.basic_01_gpu_t2iws import generate_image

# 路由
router = APIRouter()

# 数据格式验证
class T2IRequest(BaseModel):
    prompt: str
    width: int
    height: int

# api 接收参数，验证参数格式，请求资格key验证，数据库，报错处理等
@router.post("", summary="文生图websocket长连接")
async def t2i(request: T2IRequest): # 数据格式验证
    """
    文生图websocket长连接
    - **prompt**: 生成图像的描述
    - **width**: 图像宽度
    - **height**: 图像高度

    返回: img_url, generate_time, prompt
    """
    # ————————功能————————
    response = generate_image(request.prompt, request.width, request.height)
    # ————————错误响应————————
    if response is None:
        raise HTTPException(status_code=512, detail="服务器返回空值")
    # ————————返回响应数据————————
    return response  