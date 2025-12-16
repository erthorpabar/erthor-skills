# rust + cargo包管理器 

# 安装rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y


# 查看版本
rustc --version
cargo --version

# 后缀
.rs

# 运行文件
先编译成二进制 再运行
rustc a.rs ; ./a

# 运行项目
初始化
cargo new aaa
运行项目
cargo run