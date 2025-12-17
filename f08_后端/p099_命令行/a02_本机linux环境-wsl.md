linux 环境变量存放在 .bashrc 文件中
# windows 上的linux子系统 wsl
1 下载
wsl --install

2 打开虚拟机
wsl.exe -d Ubuntu

3 设置
用户名aaa
密码123

4 wsl --list --online 查看可安装的linux发行版

# vscode 连接到 wsl
1 安装插件 remote-wsl
2 ctrl + shift + p 打开命令面板
3 选择 connect to wsl
4 选择定位到某个文件夹
5 打开终端输入 sudo chmod 777 /mnt/aaa 获取写入权限
6 查看wsl的ip地址 
wsl内部 hostname -I
wsl外部 wsl hostname -I