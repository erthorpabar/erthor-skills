
# 为什么不在浏览器端，直接请求comfyui？
浏览器的各种限制
1 跨域限制CORS,需要额外配置
2 即使配置了跨域，也不能用完整请求地址，不方便管理
3 浏览器端不能打开json文件，不能用fs
4 图片无法直接保存到特定文件夹
安全问题
1 不能直接暴露comfyui的完整网络地址
2 暴露请求的json文件，不安全



# 配置跨域路由
打开vite.config.js
配置代理
proxy: {
      '/basic': {  // 匹配所有以 /basic 开头的请求
        target: 'http://192.168.31.34:7004/',
        changeOrigin: true,
        // secure: false,  // 如果是 https 可能需要设置
      },
}

