
# 远程登陆linux主机
ssh 用户名@ip地址

# 查看和更改 linux系统环境变量
linux主机的环境变量在 .bashrc 中
sudo apt install gedit
gedit ~/.bashrc

# linux基础命令
pwd = 当前文件夹路径
ls = 查看当前文件夹内容
cd aaa = 移动到到aaa文件夹
cd ../ = 返回上一级目录
sudo mkdir aaa = 创建文件夹aaa

# 安装 python
1 安装miniforge 最小conda安装
curl -L -O https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
2 给执行权限 
chmod +x Miniforge3-Linux-x86_64.sh
3 执行安装
bash Miniforge3-Linux-x86_64.sh
4 刷新环境变量
source ~/.bashrc
5 验证安装
conda --version
python --version
