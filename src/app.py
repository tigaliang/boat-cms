import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid import GridUpdateMode, DataReturnMode
import streamlit.components.v1 as components
from streamlit.components.v1.custom_component import MarshallComponentException
from feature import manage_features
from slot import manage_slots  # 确保这行导入存在
from intent import manage_intents
from corpus import manage_corpus  # 导入 manage_corpus 函数
from corpus_gen import manage_corpus_gen  # 导入新的函数

# 设置页面配置
st.set_page_config(layout="wide", page_title="语料管理系统")

# 添加自定义 CSS
st.markdown("""
<style>
    .main .block-container {
        max-width: 100%;
        padding-top: 2rem;
        padding-bottom: 2rem;
        margin: 0 auto;  /* 添加这行来使内容居中 */
    }
    .stButton > button {
        width: 100%;
    }
    .stTextInput > div > div > input {
        font-size: 16px;
    }
    .stTextArea > div > div > textarea {
        font-size: 16px;
    }
    .stDataFrame {
        font-size: 14px;
    }
    .main-content {
        display: flex;
        justify-content: center;  /* 水平居中 */
    }
    .content-wrapper {
        width: 100%;
        max-width: 1000px;  /* 可以根据需要调整 */
    }
</style>
""", unsafe_allow_html=True)

# 数库连接
conn = sqlite3.connect('cms_data_test.db')
c = conn.cursor()


# 创建必要的表
c.execute('''CREATE TABLE IF NOT EXISTS products
             (product_id INTEGER PRIMARY KEY, 
              name TEXT, 
              description TEXT, 
              created_at DATETIME)''')

c.execute('''CREATE TABLE IF NOT EXISTS features
             (feature_id INTEGER PRIMARY KEY,
              product_id INTEGER,
              name TEXT,
              description TEXT,
              created_at DATETIME,
              is_active BOOLEAN DEFAULT 1,
              FOREIGN KEY(product_id) REFERENCES products(product_id))''')

c.execute('''CREATE TABLE IF NOT EXISTS slots
             (slot_id INTEGER PRIMARY KEY,
              product_id INTEGER,
              name TEXT,
              description TEXT,
              examples TEXT,
              is_active BOOLEAN DEFAULT 1,
              FOREIGN KEY(product_id) REFERENCES products(product_id))''')

c.execute('''CREATE TABLE IF NOT EXISTS intents
             (intent_id INTEGER PRIMARY KEY,
              product_id INTEGER NOT NULL,
              feature_id INTEGER NOT NULL,
              slot_id INTEGER,
              intent_ch TEXT,
              intent_en TEXT,
              description TEXT,
              created_at DATETIME,
              is_active BOOLEAN DEFAULT 1,
              FOREIGN KEY(product_id) REFERENCES products(product_id),
              FOREIGN KEY(feature_id) REFERENCES features(feature_id),
              FOREIGN KEY(slot_id) REFERENCES slots(slot_id))''')

c.execute('''CREATE TABLE IF NOT EXISTS corpus
             (corpus_id INTEGER PRIMARY KEY,
              intent_id INTEGER NOT NULL,
              slot_id INTEGER,
              intent_en TEXT,
              score FLOAT,
              is_active BOOLEAN DEFAULT 0,
              FOREIGN KEY(intent_id) REFERENCES intents(intent_id),
              FOREIGN KEY(slot_id) REFERENCES slots(slot_id))''')

conn.commit()




def main():
    # 主内容区域
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)

    # 添加导航栏
    col1, col2 = st.columns([1, 4])
    
    with col1:
        st.sidebar.title("导航")
        navigation = st.sidebar.radio("选择页面", ["产品列表", "功能管理", "Slots管理", "意图管理", "语料管理", "语料生成"])

    with col2:
        if 'selected_product_id' not in st.session_state:
            st.session_state.selected_product_id = None

        if navigation == "产品列表":
            manage_products()
        elif navigation == "功能管理":
            if 'selected_product_id' not in st.session_state or st.session_state.selected_product_id is None:
                st.warning("请先选择一个产品")
                c.execute("SELECT product_id, name FROM products")
                products = c.fetchall()
                product_options = {p[1]: p[0] for p in products}
                selected_product = st.selectbox("选择产品", list(product_options.keys()))
                if selected_product:
                    st.session_state.selected_product_id = product_options[selected_product]
                    st.rerun()
            else:
                manage_features(conn)
        elif navigation == "Slots管理":
                manage_slots(conn)  # 只传递 conn 参数
        elif navigation == "意图管理":
                manage_intents(conn)
        elif navigation == "语料管理":
                manage_corpus(conn)
        elif navigation == "语料生成":
                manage_corpus_gen(conn)

    st.markdown('</div>', unsafe_allow_html=True)  # 关闭 content-wrapper
    st.markdown('</div>', unsafe_allow_html=True)  # 关闭 main-content

def manage_products():
    st.subheader("产品管理")
    
    # 产品录入区
    st.subheader("添加新产品")
    col1, col2, col3, col4 = st.columns([3, 3, 3, 1])
    with col1:
        name = st.text_input("产品名称")
    with col2:
        description = st.text_area("产品背景描述 (支持 Markdown)")
    with col3:
        created_at = st.date_input("创建日期", datetime.now())
    with col4:
        submit_button = st.button('添加产品')
    
    if submit_button:
        created_at_str = created_at.strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO products (name, description, created_at) VALUES (?, ?, ?)", 
                  (name, description, created_at_str))
        conn.commit()
        st.success("产品添加成功！")
        st.rerun()  # 将 experimental_rerun() 改为 rerun()

    # 分割线
    st.markdown("---")

    # 产品列表区
    st.subheader("产品列表")
    c.execute("SELECT product_id, name, description, created_at FROM products ORDER BY created_at DESC")
    products = c.fetchall()
    
    if products:
        # 将查询结果转换为 DataFrame
        df = pd.DataFrame(products, columns=['ID', '名称', '描述', '创建时间'])
        
        # 格式化创建时间
        df['创建时间'] = pd.to_datetime(df['创建时间']).dt.strftime('%Y-%m-%d')
        
        # 显示产品列表
        st.table(df)
    else:
        st.info("目前没有添加任何产品。")


# 在 main 函数中添加：
if 'view_product' not in st.session_state:
    st.session_state.view_product = False
if 'edit_product' not in st.session_state:
    st.session_state.edit_product = False
if 'delete_product' not in st.session_state:
    st.session_state.delete_product = False
if 'manage_product' not in st.session_state:
    st.session_state.manage_product = False


if __name__ == '__main__':
    main()


