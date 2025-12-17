import React, { useState, useCallback, useMemo, memo, useEffect } from "react";
import axios from "axios";

function C05TwoCharacterV1() {

    // ——————————1定义公共数据(不变量)
    // 请求后端功能的路径
    const url1 = "/two_character/gpu/01";
    const url2 = "/basic/cpu/upimg";
    const url3 = "/two_character/gpu/02";

    const lora_path_list = {
        "2d": "flux_lora/推文韩漫都市言情_V1.0.safetensors",
        // "3d": "HH_lora/3d-ani.safetensors",
    };

    // ——————————2定义公共变量 和 函数 
    const [using, setUsing] = useState(false); // 按钮是否可用

    const [lora_path, setLora_path] = useState(lora_path_list["2d"]); // lora类型,默认2d
    useEffect(() => {
        console.log(lora_path);
    }, [lora_path]);

    // 生成角色信息
    const [role_a_text, setRole_a_text] = useState(''); // 角色描述
    const [role_a_img_path, setRole_a_img_path] = useState(''); // 角色图片路径

    const [role_b_text, setRole_b_text] = useState(''); // 角色描述
    const [role_b_img_path, setRole_b_img_path] = useState(''); // 角色图片路径
   
    // comfyui后端中的图片名称
    const [img_name_a, setImg_name_a] = useState(''); // 图片a在comfyui后端中的引用名称
    const [img_name_b, setImg_name_b] = useState(''); // 图片b在comfyui后端中的引用名称

    // 定义分镜信息
    // {id: {text: '分镜描述', img_path: '分镜的图片路径'}}
    const [storyboards, setStoryboards] = useState({}); // 分镜列表
    // 每次变化打印分镜信息
    useEffect(() => {
        console.log(storyboards);
    }, [storyboards]);

    


    // ——————————3定义子组件  
    //————————————定义角色 Role 阶段
    //<Role_display>
    const Role_display = useCallback(memo(
        function({x}) {
            return x ? 
            (<img src={x} alt="生成的图像" style={styles.Role_display_yes} />) 
            :
            (<div style={styles.Role_display_no}>人物将在这里显示</div>);
        }), 
        [] // 空依赖，确保组件只渲染一次
    );

    //<Role_text>
    const Role_text_input = useCallback(memo(
        function({x,setX}) {
            return (<textarea value={x} onChange={e => setX(e.target.value)} rows="6" placeholder="请输入描述文本..." style={styles.Role_text} />);
        }), 
        [] // 空依赖，确保组件只渲染一次
    );


    //<Lora_select>
    const Lora_select = useCallback(memo(
        function({x,setX}) {
            return (
            <>
                <label>lora:</label>
                <select value={x} onChange={e => setX(e.target.value)}>
                    {Object.keys(lora_path_list).map(
                    key => <option key={key} value={lora_path_list[key]}>{key}</option>
                    )}
                </select>
            </>
            );
        }), 
        [] // 空依赖，确保组件只渲染一次
    );

    //<Role_button>
    const Role_button = useCallback(memo(
        function({click}) {
            return (<button onClick={click} disabled={using}>{using ? "生成中..." : "生成人物"}</button>);
        }), 
        [using] // 空依赖，确保组件只渲染一次
    );

    const generate_role = useCallback(async(role_text, set_role_imgpath, set_img_name) => {
        console.log("生成人物");
        console.log(role_text);
        setUsing(true); // 禁用所有按钮

        const data = {
            prompt: role_text,
            width: 1024,
            height: 1024,
            lora_name: lora_path,
            checkpoint_name: "flux-dev-fp8.safetensors",
            // lora_strength: 1.0,
        }
        try{
            // 生成人物形象
            const response = await axios.post(url1, data); // 请求comfyui作图
            // console.log(response.data)
            set_role_imgpath(response.data.img_url_list[0]) // 设置角色图片路径
            console.log(response.data.img_url_list[0])

            // 上传图片
            const response2 = await axios.post(url2, {img_path: response.data.img_url_list[0]});
            console.log(response2.data)

            // 获取图片在后端的名称
            set_img_name(response2.data.name) // 设置图片在comfyui后端中的引用名称
        }catch(error){
            if(error.response){
                console.error("错误响应:", error.response.data);
                console.error("错误状态码:", error.response.status);
            }
        }finally{
            setUsing(false); // 启用所有按钮
        }
    }, 
    [lora_path]
    );

    //————————————生成分镜 Storyboard 阶段
    //<Add_sb>
    const Add_sb_button = useCallback(memo(
        function({add_sb}) {
            return(
            <>
                <button onClick={add_sb}>分镜+1</button>
            </>
            )
        }),
        []
    );
    const add_sb = useCallback(() => {
        const new_id = Object.keys(storyboards).length + 1;     
        setStoryboards(prev => ({...prev, [new_id]: {text: '', img_path: ''}}));
    }, 
    [storyboards]
    );

    //<Delete_sb>
    const Delete_sb_button = useCallback(memo(
        function({delete_sb}) {
            return(
            <>
                <button onClick={delete_sb}>分镜-1</button>
            </>
            )
        }),
        []
    );
    const delete_sb = useCallback(() => {
        const keys = Object.keys(storyboards).map(Number);
        if (keys.length === 0) return;

        const lastKey = Math.max(...keys); // 比较大小，获取最后一个id
        const { [lastKey]: _ , ...others } = storyboards; // 把最后一个kv对 和 其他剩下的 分开
        setStoryboards(others); // 把剩下的赋值给分镜内容 
    }, 
    [storyboards]
    );


    //<Storyboard_display>
    const Storyboard_display = useCallback(memo(
        function({x}) {
            return x ? 
            (<img src={x} alt="生成的分镜图像" style={styles.Storyboard_display_yes} />) 
            :
            (<div style={styles.Storyboard_display_no}>分镜将在这里显示</div>);
        }), 
        [] // 空依赖，确保组件只渲染一次
    );
    //<Storyboard_text>
    const Storyboard_text_input = useCallback(memo(
        function({x,setX}) {
            return (<textarea value={x} onChange={e => setX(e.target.value)} rows="6" placeholder="请输入分镜描述文本..." style={styles.Storyboard_text} />);
        }), 
        [] // 空依赖，确保组件只渲染一次
    );
    const setStoryboard_text = useCallback((id, text) => {
        setStoryboards(prev => ({...prev, [id]: {...prev[id], text}}));
    }, 
    [] // 移除 storyboards 依赖
    );
    
    //<Storyboard_button>
    const Storyboard_button = useCallback(memo(
        function({click}) {
            return (<button onClick={click} disabled={using}>{using ? "生成中..." : "生成分镜"}</button>);
        }), 
        [using] // 空依赖，确保组件只渲染一次
    );

    const generate_storyboard = useCallback(async(id) => {
        console.log("生成分镜");

        const storyboard = storyboards[id]; // 获取当前生成的分镜id
        console.log(storyboard.text)

        setUsing(true); // 禁用所有按钮

        const data = {
            prompt:"The people was on the left side of the picture,"+"\n"+role_a_text+"and the people was on the right side of the picture,"+"\n"+role_b_text+"\n"+storyboard.text,
            width: 1536,
            height: 1024,
            lora_name: lora_path,
            // lora_strength: 1.0,
            left_image: img_name_a,
            right_image: img_name_b,
            checkpoint_name: "flux-dev-fp8.safetensors",
        }
        try{
            const response3 = await axios.post(url3,data);

            // 更新显示图片地址
            // 分离两次，...prev代表出来当前id的其他所有kv，...prev[id]代表除了img_path的其他kv
            setStoryboards(prev => ({...prev,[id]:{ ...prev[id],img_path:response3.data.img_url_list[0]}}));
        }
        catch(error){
            console.error("生成分镜失败", error);
        }
        finally{
            setUsing(false); // 启用所有按钮
        }
    }, 
    [storyboards, img_name_a, img_name_b, lora_path]
    );
    
    // ——————————4渲染组件
    return (
    <>  
        <h3>双角色一致性v1</h3>
        <p>使用技术:pulid</p>
        <p>控制方式:prompt + 参考图</p>


        <Lora_select x={lora_path} setX={setLora_path} />

        {/* 角色a */}
        <h4>生成角色参考a 左边</h4>
        <div style={styles.Role_array}>
            <Role_display x={role_a_img_path} />
            <Role_text_input x={role_a_text} setX={setRole_a_text} />
            <Role_button click={() => generate_role(role_a_text, setRole_a_img_path, setImg_name_a)} />
        </div>
        

        {/* 角色b */}
        <h4>生成角色参考b 右边</h4>
        <div style={styles.Role_array}>
            <Role_display x={role_b_img_path} />
            <Role_text_input x={role_b_text} setX={setRole_b_text} />
            <Role_button click={() => generate_role(role_b_text, setRole_b_img_path, setImg_name_b)} />
        </div>


        {/* 分镜数量按钮 */}
        <h4>分镜</h4>   
        <Add_sb_button add_sb={add_sb} />
        <Delete_sb_button delete_sb={delete_sb} />

        {/* 动态渲染分镜组件 */}
        {/* 遍历循环字典的kv对 */}
        {Object.entries(storyboards).map(([id, storyboard]) => (
           <div key={id} style={styles.Storyboard_array}>
               <Storyboard_display x={storyboard.img_path} />
               <Storyboard_text_input x={storyboard.text} setX={text => setStoryboard_text(id, text)}/>
               <Storyboard_button click={() => generate_storyboard(id)} />
           </div>
        ))}
    </>
    )
}

export default C05TwoCharacterV1;



const styles = {
    // 角色参考
    Role_array: {
        display: 'flex',
        alignItems: 'center'
    },
    Role_display_yes: {
        width: "200px",
        height: "200px",
        objectFit: "cover",
    },
    Role_display_no: {
        width: "200px",
        height: "200px",
        border: "1px solid #ccc",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: "#999",
        backgroundColor: "#f0f0f0",
    },
    Role_text: {
        width: "15%",
        padding: "10px",
        marginBottom: "20px"
    },


    // 分镜显示
    Storyboard_array: {
        display: 'flex',
        alignItems: 'center'
    },
    Storyboard_display_yes: {
        width: "200px",
        height: "200px",
        objectFit: "cover",
    },
    Storyboard_display_no: {
        width: "200px",
        height: "200px",
        border: "1px solid #ccc",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: "#999",
        backgroundColor: "#f0f0f0",
    },
    Storyboard_text: {
        width: "15%",
        padding: "10px",
        marginBottom: "20px"
    },

}
