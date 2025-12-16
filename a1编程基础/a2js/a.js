/*
js 的设计思路
为了保持页面的响应，
比如图片加载不出来，也照样能够浏览界面。
这就需要异步执行，
即，
等待耗时操作，同时执行非耗时操作

所以代码运行顺序
0 收集所有变量名称
1 从上到下运行
2 遇到耗时操作 定义为 异步 放入到任务队列 什么时候执行完 什么时候返回 不影响同步代码顺序执行

有一些操作默认是异步的
比如 
1 网络请求
2 文件读写
3 定时器


如果需要等待异步耗时操作执行完，再继续向下执行
就需要
async/await

*/

// ————async/await————

async function cook() {
    console.log('1 接待 客人a')
    console.log('2 客人a 点餐 红烧肉')
    await new Promise(resolve => {
        setTimeout(() => {
            console.log('厨师为客人a做完红烧肉')
            console.log('客人a的红烧肉上菜')
            resolve() // resolve 执行完代表 耗时操作完成
        }, 2000)
    })

    console.log('3 接待 客人b')
    console.log('4 客人b 点餐 鱼香肉丝')
    await new Promise(resolve => {
        setTimeout(() => {
            console.log('厨师为客人b做完鱼香肉丝')
            console.log('客人b的鱼香肉丝上菜')
            resolve() // resolve 执行完代表 耗时操作完成
        }, 2000)
    })
}

cook()

console.log('——————') // 这个顺序执行只在函数内部有效，两个函数之间还是异步执行的















