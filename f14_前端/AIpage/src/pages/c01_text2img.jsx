

import React, { useState, memo, useCallback } from "react";
import axios from "axios";

/*

运行逻辑

首次加载
<Place_holder>
<Input_text>
<Submit_button>

输入提示词
<Input_text>[text]

提交作图
<Submit_button>[isGenerating = true]
  Generate(text) 
    -> [img_path]
    -> [isGenerating = false]
        加载图片<Show_img>[img_path]
        卸载占位<Place_holder>


*/

function C01Text2Img() {
    // ————————————————————1定义公共数据(不变量)——————————————————————
    const url = '/basic/param/t2i_ws_everytime';


    // ——————————————————————2定义公共变量————————————————————————
    const [text, setText] = useState(""); // 输入提示词
    const [using, setUsing] = useState(false); // 按钮是否可用
    const [img_path, setImg_path] = useState(""); // 图片地址

    // ———————————————————————3定义子组件————————————————————————

    // 1<Place_holder>默认无图占位
    const Place_holder = useCallback(memo(
        function() {
            return <div style={styles.Place_holder}>图片将在这里显示</div>;
        },
        [] // 空依赖，确保组件只渲染一次
    )); 

    // 2<Show_img>显示图片
    const Show_img = useCallback(memo(
        function({ x }) {
            return <img src={x} alt="生成的图像" style={styles.Show_img} />;
        }), 
        [] // 空依赖，确保组件只渲染一次
    ); 

    // 3<Input_text>输入框
    const Input_text = useCallback(memo(
        function({ x, setX }) {
            return (
                <textarea 
                    value={x} 
                    onChange={(e) => setX(e.target.value)}
                    rows="6" 
                    placeholder="请输入描述文本..."
                    style={styles.Input_text}
                />
            );
        }), 
        [] // 空依赖，确保组件只渲染一次
    ); 

    // 4<Submit_button>提交按钮
    const Submit_button = useCallback(memo(
        function({ click }) {
            return (
                <button onClick={click} disabled={using}>
                    {using ? "生成中..." : "提交"}
                </button>
            );
        }), 
        [using] // 检查using是否变化
    ); 

    // 生成图片，返回图片地址
    const Generate = useCallback(async () => {
        setUsing(true); // 禁用按钮
        
        const data = {
            prompt: text,
            width: 512,
            height: 512,
        }

        try {
            const response = await axios.post(url, data);
            // const img_url = response.data.img_url
            setImg_path(response.data.img_url)
            console.log(response.data.img_url)
            console.log(response.data.generate_time)
        } 
        catch (error) {console.error("请求失败:", error);} 
        finally {setUsing(false);} // 启用按钮
    }, 
    [text,url] // 检查text、url、width、height是否变化
    );


    // ——————————————————————4渲染组件————————————————————————
    return (
        <>
            <h3>Comfyui Text2Img</h3>

            {img_path ? (<Show_img x={img_path} />) : (<Place_holder />)}
            <br/>

            <Input_text x={text} setX={setText}/>
            <br/>

            <Submit_button click={Generate}/>

        </>
    );
}

export default C01Text2Img;




// 样式
const styles = {

    Place_holder: {
      width: "300px",
      height: "300px",
      border: "1px solid #ccc",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      color: "#999"
    },

    Show_img: {
        width: "300px",
        height: "300px"
    },

    Input_text: {
      width: "25%",
      padding: "10px",
      marginBottom: "20px"
    },

};


