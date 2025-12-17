// import React, { useState } from 'react';

// const ImageWithPlaceholder = ({ src, style, alt, width, height }) => {
//     const [loading, setLoading] = useState(true); // 图片加载状态

//     const handleImageLoad = () => {
//         setLoading(false); // 图片加载完成，更新状态
//     };

//     return (
//         <div
//             style={{
//                 width: width, // 默认宽度
//                 height: height, // 默认高度
//                 backgroundColor: loading ? '#ccc' : 'transparent', // 加载中显示灰色占位框
//                 display: 'flex',
//                 justifyContent: 'center',
//                 alignItems: 'center',
//                 border: '1px solid #ddd',
//                 overflow: 'hidden',
//                 ...style, // 合并父组件传入的样式
//             }}
//         >

//             <img
//                 src={src}
//                 alt={alt}
//                 style={{
//                     width: width,
//                     height: height,
//                     objectFit: 'cover', // 保持图片的比例并填充容器
//                 }}
//                 onLoad={handleImageLoad} // 图片加载完成时触发
//             />
//         </div>
//     );
// };

// export default ImageWithPlaceholder;

// import React, { useState } from 'react';

// const ImageWithPlaceholder = ({ src, style, alt, width, height, onSelect, index, isSelected }) => {
//     const [loading, setLoading] = useState(true); // 图片加载状态

//     const handleImageLoad = () => {
//         setLoading(false); // 图片加载完成，更新状态
//     };

//     const handleClick = () => {
//         onSelect(index); // 调用父组件传入的 onSelect 函数，传递当前图片的 index
//     };

//     return (
//         <div
//             style={{
//                 width: width, // 默认宽度
//                 height: height, // 默认高度
//                 backgroundColor: loading ? '#ccc' : 'transparent', // 加载时显示灰色占位框
//                 display: 'flex',
//                 justifyContent: 'center',
//                 alignItems: 'center',
//                 border: `2px solid ${isSelected ? 'blue' : '#ddd'}`, // 如果选中，边框变蓝
//                 overflow: 'hidden',
//                 ...style, // 合并父组件传入的样式
//             }}
//         >
//             <img
//                 src={src}
//                 alt={alt}
//                 style={{
//                     width: width,
//                     height: height,
//                     objectFit: 'cover', // 保持图片比例并填充容器
//                 }}
//                 onLoad={handleImageLoad} // 图片加载完成时触发
//                 onClick={handleClick} // 点击事件触发
//             />
//         </div>
//     );
// };

// export default ImageWithPlaceholder;
