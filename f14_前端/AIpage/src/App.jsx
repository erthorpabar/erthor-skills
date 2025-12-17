// 导入库
import { BrowserRouter as Router, Route, Routes, useNavigate } from "react-router-dom";
import React from 'react'; 

// 导入页面组件
import A00Home from "./pages/a00_home.jsx";
import C01Text2Img from "./pages/c01_text2img.jsx";

import C04OneCharacterV1 from "./pages/c04_one_character_v1.jsx";
import C05TwoCharacterV1 from "./pages/c05_two_character_v1.jsx";

import C11RemoveBackground from "./pages/c11_remove_background.jsx";



function App() {

  // ————————————————1定义公共数据————————————————
  // 注册页面
  const page_list = [
    { name: '主页',  path: '/' , page: A00Home},
    { name: '文生图', path: '/text2img', page: C01Text2Img },
    { name: '角色一致性v1', path: '/OneCharacterV1', page: C04OneCharacterV1 },
    { name: '双角色一致性v1', path: '/TwoCharacterV1', page: C05TwoCharacterV1 },
    { name: '移除背景', path: '/RemoveBackground', page: C11RemoveBackground },
  ]

  // ————————————————2定义公共变量————————————————
  
  // ————————————————3定义子组件————————————————
  // <Page_button>输入一个列表，遍历生成带onclick的按钮
  function Page_button({ list }) {
    const navigate = useNavigate(); 

    return(
      <>
        {list.map(
          (x) => (<button key={x.name} onClick={() => navigate(x.path)}>{x.name}</button>)
        )}
      </>
    )
  }

  // <Page_Route>输入一个列表，遍历生成一组<Route>组件，
  function Page_Route({ list }) {
    return(
      <Routes>
        {list.map(
          (x) => (<Route key={x.path} path={x.path} element={<x.page />} />)
        )}
      </Routes>
    )
  }

  // ————————————————4渲染组件————————————————
  return (
    <Router>
      <Page_button list={page_list}/>
      <Page_Route list={page_list}/>
    </Router>
  );
}

export default App;


/*

定义组件必须以大写字母开头


首页路由书写结构最佳实践

点击button -> navigate(x.path)改变url
Router 监听rul变化
Rotes 根据url渲染对应组件

*/