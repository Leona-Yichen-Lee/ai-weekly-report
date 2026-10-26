import os
import streamlit as st
from datetime import datetime
from openai import OpenAI
import json
import streamlit.components.v1 as components

client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)
#提示词模版
PROMPT_TEMPLATES = {
    "正式汇报风格": "你是一个专业的汇报助手。请输出正式、客观、结构化的周报，用词严谨，适合给领导看。",
    "简洁口语风格": "你是一个轻松的周报助手。请用简洁、口语化的语言整理周报，每条不超过20字。",
    "详细项目风格": "你是一个项目管理助手。请按项目维度整理周报，每个项目写明进展、问题、下一步。",
    "反思总结风格": "你是一个个人成长教练。请帮用户反思本周工作，突出收获、不足和改进方向。"

}

HISTORY_FILE = "report_history.json"
st.set_page_config(
    page_title="AI周报生成器",
    layout="wide",                          
    initial_sidebar_state="expanded"        
)
# 下载回复
def load_history():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8")as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("文件不存在或格式错误")
        return []
# 保存历史记录
def save_to_history(raw_input, report,template):
    history=load_history() #参数history赋值后写入文件中保存
    history.append(
        {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "input":raw_input,
            "report":report,
            "template":template
        }
    )
    with open(HISTORY_FILE, "w", encoding="utf-8")as f:
        json.dump(history, f, ensure_ascii=False, indent=4) # 写入json文件时，ensure_ascii保证文字文本格式被保留
# 清除历史功能
def clear_history():
    with open(HISTORY_FILE, "w", encoding="utf-8")as f:
        json.dump([], f) # 调用函数，返回空列表
# 生成回复(根据用户选择的系统提示词+用户回复)
def generate_report(raw_input, system_prompt):
    messages=[
        {"role":"system", "content":system_prompt},
        {"role":"user", "content":raw_input}
    ]
    try:
        res=client.chat.completions.create(
            model="deepseek-flash",
            messages=messages
        )
        reply=res.choices[0].message.content #调用接口传回模型的回复
        return reply
    except Exception as e:
        print(f"生成失败, {e}")
# st.session_state是streamlit的页面状态存储器，当streamlit启动脚本开始跑动所有普通变量直接重置消失时，st.session_state里的数据不会丢失
# session_state可以看做一个字典
if "selected" not in st.session_state: # 判断session_state里有没有"selected"的key；第一次执行，没有生成这个key，则条件成立，赋值为None；如果已经创建（代码刷新）：条件不成立，不执行赋值。
    st.session_state["selected"] = None # 初始化变量，防止后面代码读取

# 侧边栏（网页左侧）

with st.sidebar: # with语法：with内部所写的组件（标题、下拉框、输入框），全部放在左侧，不会放在主页面。
# 周报模版侧边栏
    st.header("设置") # 渲染侧边栏标题
    template_name = st.selectbox( # 选择下拉框形式
        "选择周报风格",
        list(PROMPT_TEMPLATES.keys()) # list（dict）下拉框选项转成列表 system_prompt=PROMPT_TEMPLATES[template_name]
    )
# 历史记录侧边栏
    st.divider() # 水平分割线，视觉上的灰色横线
    st.header("历史周报")
    history=load_history() # 调用load_history后读取report.json，拿到记录，返回了一个列表。
    if not history:
        st.write("暂无历史记录")
    else:
        for i, item in enumerate(reversed(history)): # reversed倒序遍历列表，将最新返回的json放在最前面。
        # enumerate 循环的同时拿到下标索引i和item（自定义的list中单条记录的）
            label = f"{item['time'][:10]} | {item.get('template', '未分类')}" # [：10]只保留time的值的前十个字符串；.get安全取值。
            # 示例：2026-10-19 | 未分类
            if st.button(label, key=f"hist_{i}"): # 生成一个按钮，按钮文字为拼接好的label
            # Steamlit要求页面上的所有按钮必须拥有唯一key，否则会冲突报错。i为循环序号，每个按钮key互不重复。
                st.session_state["selected"] = item["report"] # 将item["report"]写入session_state，即键report的值。
# 清空历史侧边栏——调用函数clear_history。
    st.divider()
    if st.button("清空历史"):
        clear_history() # 清除硬盘文件
        st.session_state["selected"]=None # 清除网页内存，手动将selected置空，页面就不会显示旧周报。
        st.success("已清空")
        st.rerun() # 刷新页面

# 主区域
st.set_page_config(
    page_title="AI周报生成器",
    initial_sidebar_state="expanded" 
)
st.title("AI 周报生成器")
st.write("输入你本周的工作记录，AI 帮你整理成结构化周报")
raw_input = st.text_area(
    "本周工作记录",
    placeholder="例如：今天开了需求评审会，改了登录页文案，修了一个支付bug",
    height=150
)

# ✨ 1. 动态按钮：判断是否输入了内容（去除空白字符后长度大于0）
has_input=len(raw_input.strip())>0 # 布尔值has_input,大于0为True
if st.button("生成周报", disabled=not has_input, type="primary"): # type只改外观，不控制功能逻辑，default是secondary.
# disabled参数，为True时会让按钮点不动，进入不了if的代码运行，为has_input的相反数，因此不需要st.warning弹窗判断。
    # if not raw_input.strip(): # 文本框为空时点击“生成”，弹窗警告
    #     st.warning("请输入工作记录")
    if not has_input: 
        st.info("请填写本周工作记录后再生成") # 默认提醒用户填写记录
    else:
        with st.spinner(f"正在生成「{template_name}」周报..."):
            report = generate_report(raw_input, PROMPT_TEMPLATES[template_name]) # 调用函数生成周报
        st.session_state["selected"]=report # 被点击的按钮赋值为周报
        st.success("周报生成成功")
        save_to_history(raw_input, report,template_name)
        st.rerun() 
#显示选中的或新生成的周报
if st.session_state["selected"]: # 判断selected有没有内容，如果为None不执行下面的代码，执行len（None）会报错。
    st.divider()

    # ✨ 2. 两列布局
    col1, col2 = st.columns([3, 1]) # 比例 3:1，左边宽一点
    # 返回两个对象, col1, col2 两个列容器    
    # 左边显示字数
    char_count = len(st.session_state["selected"])
    with col1: # with语法，进行这个col1容器的上下文，也可以写：col.write(f"字数统计：{char_count}字")
        st.write(f"**字数统计：** {char_count} 字")
        
    # 右边显示一键复制按钮
    with col2:
        # 这段 JS 的逻辑是：创建一个隐藏的文本框，把内容放进去，选中，然后执行浏览器的复制命令
        # 注意：需要把报告里的换行符和引号转义，防止破坏 JS 语法 如果用json.dumps()转义，就不需要在copy_js-const_text = 中增加''单引号！！
        # <button>HTML 按钮标签， </button>定义一个网页按钮 # 点击按钮时，执行JS函数copyText（）onclick：页面渲染一个按钮，附带css样式（内联style控制外观）。
        # <script> ：function copyText（）内部JS代码函数，定义复制函数。 navigator浏览器原生剪贴板API，把文本写入剪贴板。
        report_text = st.session_state["selected"].replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$') # \\转义起始符，防止文本（字符串）破坏JSON格式
        copy_js = f""" 
        <button onclick="copyText()" style="padding: 5px 10px; cursor: pointer; border-radius: 5px; border: 1px solid #ccc; background-color: #f9f9f9;"> 
            📋 复制全文
        </button> 
        <script>
        function copyText() {{
            const text = `{report_text}`;
            navigator.clipboard.writeText(text).then(() => {{
                alert('已复制到剪贴板！');
            }}); 
        }}
        </script> # <button>HTML 
        """
        # `streamlit.components.v1`自定义组件，可以把任意HTML+CSS+JS直接渲染到网页
        components.html(copy_js, height=50)

# 将存在selected里面的文本渲染到网页，st.markdown可以识别markdown语法，排版更好看。
    st.markdown(st.session_state["selected"])
    st.download_button(
        label="下载周报",
        data=st.session_state["selected"],
        file_name=f"周报_{datetime.now().strftime('%Y%m%d')}.md",
        mime="text/markdown"
    )
