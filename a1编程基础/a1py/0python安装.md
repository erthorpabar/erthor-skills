# py + conda包管理器

# 查看版本
python --version

# 创建虚拟环境
conda create -n comfy_py python=3.10 -y

# 激活虚拟环境
conda activate comfy_py

# 查看虚拟环境
conda env list

# 删除虚拟环境
conda remove --name comfy_py --all

# 退出虚拟环境
conda deactivate

# 运行代码
python a.py


# 后缀
.py 
.ipynb 