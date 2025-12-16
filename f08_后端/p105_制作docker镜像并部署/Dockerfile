# 使用官方py继承镜像
FROM python:3.10-slim

# 创建工作目录
RUN mkdir /app
# 设定工作目录 并 切换到这个目录
WORKDIR /app

# 将上一个目录文件 拷贝到 当前目录
COPY . .

# 下载依赖
RUN pip install --no-cache-dir -r requirements.txt

# 设置变量
ARG PPP=7005

# 设置环境变量
ENV HOST=0.0.0.0
ENV PORT=$PPP
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 暴露端口号
EXPOSE $PPP

# 这是正确的方式
CMD ["python", "server.py"]