"""上传图片"""
# 路由
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from fastapi import Depends

from services.v1.basic_02_cpu_upimg import upload_img
import requests

# 路由
router = APIRouter()

# 数据格式验证
class UploadImgRequest(BaseModel):
    img_path: str

# api 数据库，身份验证，数据格式验证，返回响应数据，错误响应
@router.post("", summary="上传图片")
def upload_img_route(request: UploadImgRequest): # 数据格式验证
    """
    上传图片
    - **img_path**: 图片路径

    返回:name, subfolder, type
    """
    # ————————功能————————
    response = upload_img(request.img_path)
    # ————————错误响应————————
    if response is None:
        raise HTTPException(status_code=512, detail="服务器返回空值")
    # ————————返回响应数据————————
    return response.json()