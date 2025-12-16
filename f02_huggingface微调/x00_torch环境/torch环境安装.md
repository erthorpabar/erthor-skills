
# 版本匹配
本机 cuda toolkit 版本 > torch 支持的版本
如
cuda toolkit = 12.2 -> (12.2)
torch-2.9.1+cu121 -> (12.1)

# 查看 cuda toolkit 版本
nvcc --version 

# 查看 torch 版本
python -c "import torch; print(torch.__version__)"


# 卸载torch
pip uninstall -y torch torchvision torchaudio
pip cache purge

# 安装torch
在官网查找匹配的版本
https://pytorch.org/