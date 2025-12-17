app
│
├── server.py # 匹配路径
│
├── api # 数据库，身份验证，数据格式，错误处理等综合功能
├── services # 请求comfyui
│   └── comfyui_workflow # 作图核心逻辑
├── core # 配置
│   └── config.py # 配置文件
│
├── tests # 测试各接口文件
│
├── requirements.txt # 依赖库


————————————————comfyui再包装一层api的原因————————————————
前端直接调用comfyui会有问题：
1 工作流json泄露
2 comfyui地址泄露
3 可以调用多个comfyui

————————————————命名规则————————————————
项目分类/序号/资源类型(cpu/gpu)/功能名称

一级路由
1 basic 无项目仅测试或基础功能
2 data 使用数据库
3 项目名称

二级路由
001

三级路由
1 gpu ：本地gpu
2 cpu ：本地cpu
3 request ：调用第三方接口

四级路由
作用名称

——————————————————访问——————————————————
export HOST=127.0.0.1 PORT=7004 本地测试
export HOST=0.0.0.0 PORT=7004 外网访问

——————————————————报错设计——————————————————
返回 None
则 api HTTPException 500

记录在 app.log 中

—————————————————api逻辑————————————————

启动
server.py
    -> 指定 HOST 和 PORT
    -> .env 环境变量


功能
server.py 请求路径匹配
    -> api/A_aaa.py 接收参数，验证参数格式，请求资格key验证，数据库，报错处理等
        -> services/S_aaa.py 核心功能 返回json数据
            -> comfyui_api/aaa.json 工作流
            -> core/config.py
                -> .env 请求 url 和 key


——————————————————请求作图逻辑——————————————————

poll轮询
    -> prompt接口 提交任务 返回prompt_id
    -> history接口 根据 prompt_id 等待图片生成 轮询获取 img_name
    -> view接口 根据 img_name 返回 url

ws
    -> ws on_open 服务开启（prompt接口 提交任务）
    -> ws on_message 接收comfyui消息 
        完成后获取 img_name 
        view接口 根据img_name 返回 url
        触发 ws.close()
    -> ws on_close 服务关闭

——————————————————启动——————————————————
export HOST=127.0.0.1 PORT=7004 本地测试
export HOST=0.0.0.0 PORT=7004 外网访问

# 创建环境
conda create -n fastapi_aaa python=3.10 -y

# 激活环境
conda activate fastapi_aaa

# 下载依赖
pip install -r requirements.txt

# 查看端口号占用
lsof -i:7005
lsof -i:7003

# 开启服务
linux
export HOST=0.0.0.0 PORT=7005
python server.py
或
nohup python server.py # 关闭电脑仍然运行服务

# 访问服务
http://127.0.0.1:7005/
# fastapi文档
http://127.0.0.1:7005/docs

# 关闭服务
sudo kill -9 $(lsof -t -i:7005)
kill $(lsof -t -i:7005)
kill PID
crtl+c

# 退出环境
conda deactivate