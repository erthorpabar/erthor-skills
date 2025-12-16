# 直接在 jupyter 中创建 app.py 文件

import streamlit as st
import pickle

# 加载模型 
pickle_in = open("classifier.pkl", "rb")
classifier = pickle.load(pickle_in)

# 
def main():
    # header
    html_temp = """ 
    <div style ="background-color:yellow;padding:13px"> 
    <h1 style ="color:black;text-align:center;">Check Loan Eligibility</h1> 
    </div> 
    """
    st.markdown(html_temp, unsafe_allow_html = True) 

    # 下拉框
    Gender = st.selectbox('性别',("Male","Female","Other")) # 男 女 其他
    Married = st.selectbox('婚姻状况',("Unmarried","Married","Other")) # 未婚 已婚 其他

    # 输入框
    ApplicantIncome = st.number_input("月收入（卢比）") # 月收入 
    LoanAmount = st.number_input("贷款金额（卢比）") # 贷款金额

    def prediction(Gender, Married, ApplicantIncome, LoanAmount):
        # 处理分类数据
        if Gender == "Male":
            Gender = 0
        else:
            Gender = 1

        if Married == "Married":
            Married = 1
        else:
            Married = 0

        result = classifier.predict([[Gender, Married, ApplicantIncome, LoanAmount]])

        if result == 0:
            pred = '不批准'
        else:
            pred = '批准'
        
        return pred
    
    # 
    result = ""
    if st.button("检测"):
        result = prediction(Gender, Married, ApplicantIncome, LoanAmount)
        st.success(f'您的贷款批准结果为：{result}')


if __name__ == "__main__":
    main()

    
       
