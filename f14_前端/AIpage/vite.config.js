import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],

  // 添加代理绕过浏览器逆天的CORS
  server: {
    proxy: {
      '/basic': {  // 匹配所有以 /basic 开头的网页请求
        target: 'http://192.168.31.34:7005/',
        changeOrigin: true,
        // secure: false,  // 如果是 https 可能需要设置
      },
      '/one_character': {  // 匹配所有以 /one_character 开头的网页请求
        target: 'http://192.168.31.34:7004/', // 替换为目标网址
        changeOrigin: true,
        // secure: false,  // 如果是 https 可能需要设置
      },
      '/two_character': {  // 匹配所有以 /two_character 开头的网页请求
        target: 'http://192.168.31.34:7005/', // 替换为目标网址
        changeOrigin: true,
        // secure: false,  // 如果是 https 可能需要设置
      }
    },

    // 让网页可以被外网访问
    host: '0.0.0.0',
    port: 5173,
  }

})
