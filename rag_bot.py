import streamlit as st
from openai import OpenAI

# --- 页面配置 ---
st.set_page_config(page_title="筑梦智能体 (Real AI)", page_icon="🧠", layout="wide")

# --- 侧边栏：配置“大脑” ---
with st.sidebar:
    st.title("⚙️ 开发控制台")
    st.markdown("这是**二阶实训**的核心：配置模型参数。")
    # API 配置
    api_key = st.text_input("API Key", type="password", help="OpenAI 或 DeepSeek 的 Key")
    # 自动处理 Base URL，防止小白填错
    provider = st.selectbox("选择服务商", ["OpenAI", "DeepSeek", "自定义"])

    if provider == "OpenAI":
        base_url = "https://api.openai.com/v1"
        default_model = "gpt-3.5-turbo"
    elif provider == "DeepSeek":
        base_url = "https://api.deepseek.com"  # DeepSeek 官方兼容地址
        default_model = "deepseek-chat"
    else:
        base_url = st.text_input("Base URL", value="https://api.openai.com/v1")
        default_model = "gpt-3.5-turbo"
    model_name = st.text_input("模型名称", value=default_model)

    # 2. 角色设定 (Prompt Engineering)
    st.divider()
    system_prompt = st.text_area(
        "系统提示词 (System Prompt)",
        value="你是由创鹤智能开发的“筑梦”校园助手。请用亲切、专业的语气回答学生关于AI实训的问题。",
        height=100
    )

    # 3. 清空记忆
    if st.button("🗑️ 清空对话历史"):
        st.session_state.messages = []
        st.rerun()

# --- 初始化 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 聊天主界面 ---
st.title("🧠 筑梦真实 AI 助手")
st.caption("🚀 已连接真实大模型 API | 支持多轮对话与流式输出")

# 1. 渲染历史消息
for msg in st.session_state.messages:
    # 不显示 system prompt，只显示 user 和 assistant
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# 2. 处理用户输入
if prompt := st.chat_input("问我任何问题..."):
    if not api_key:
        st.warning("⚠️ 请先在左侧侧边栏输入 API Key 才能启动大脑！")
        st.stop()

    # 显示用户提问
    with st.chat_message("user"):
        st.markdown(prompt)

    # 构建完整的消息上下文 (System Prompt + History + Current Prompt)
    # 这一步非常重要，保证 AI 记得住之前的对话
    messages_payload = [{"role": "system", "content": system_prompt}] + \
                       [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages] + \
                       [{"role": "user", "content": prompt}]

    # 存入 session 用于显示
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 3. 调用真实 API 并流式输出
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            # 初始化客户端
            client = OpenAI(api_key=api_key, base_url=base_url)

            # 发起请求 (开启 stream=True 实现打字机效果)
            stream = client.chat.completions.create(
                model=model_name,
                messages=messages_payload,
                stream=True,
                temperature=0.7
            )

            # 实时接收数据块
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    message_placeholder.markdown(full_response + "▌")

            message_placeholder.markdown(full_response)

            # 将 AI 的回复存入历史，形成闭环
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"❌ 调用失败: {e}")