import React, { useState, useCallback, useMemo, memo } from "react";


function A00Home() {

    // 1 定义公共数据(不变量)

    // 调用环境变量
    const aaa = import.meta.env.VITE_AAA 
    console.log("环境变量",aaa)

    // 定义公共变量
    const data = useMemo(
        () => {return "III";},
        []
    );
    

    // 2 定义公共变量
    const [x, setX] = useState(0); // state

    const addX = useCallback(
        () => {setX(prevX => prevX + 1);}, 
        []
    );

    const doubleX = useMemo(
        () => {return x * 2;}, 
        [x]
    );

    // 3 定义子组件

    const A00_counter = memo(() => {
        return (
        <>
            <h3>{data}</h3>
            <p>x: {x}</p>
            <p>2x: {doubleX}</p>
            <button onClick={addX}>+1</button>
        </>
        );
    });

    // 4 渲染组件
    return (
    <>    
        <div className="app-container">
            <A00_counter />
        </div>
    </>    
    );
}

export default A00Home




/*
代码书写结构最佳实践

0 定义主组件 
function APP() {
    1 定义公共数据（不变量）
    -使用useMemo确保主组件更新，变量不会重新创建（依赖为[]，则只会在首次渲染计算一次）

    2 定义公共变量
    -使用useState创建[变量，修改变量的函数]
    -如果引用了函数，使用useCallback确保主组件更新，函数不会重新创建
    -如果引用了变量，使用useMemo确保主组件更新，变量不会重新创建

    
    3 定义组件
    -使用memo确保主组件更新时，如果收到相同数据，组件不会重新创建


    4 渲染组件
    return(
    <>    
        <div className="css">
            <组件>
        </div>
    </>    
    )
}
*/





