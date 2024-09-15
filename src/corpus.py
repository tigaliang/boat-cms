import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder
import chardet

# 在文件开头添加这些行
if 'upload_state' not in st.session_state:
    st.session_state.upload_state = 'initial'
if 'preview_data' not in st.session_state:
    st.session_state.preview_data = None

def manage_corpus(conn):
    st.header("语料管理")

    # 获取所有产品
    c = conn.cursor()
    c.execute("SELECT product_id, name FROM products")
    products = c.fetchall()

    # 创建产品选择下拉框
    product_options = {product[1]: product[0] for product in products}
    selected_product = st.selectbox("选择产品", options=list(product_options.keys()), index=0)
    
    # 获取选中产品的ID
    product_id = product_options[selected_product]

    # 获取该产品下的所有意图
    c.execute("SELECT intent_id, intent_ch FROM intents WHERE product_id = ?", (product_id,))
    intents = c.fetchall()
    intent_options = {"全部": None}
    intent_options.update({intent[1]: intent[0] for intent in intents})

    # 创建意图选择下拉框
    selected_intent = st.selectbox("选择意图", options=list(intent_options.keys()), index=0)
    selected_intent_id = intent_options[selected_intent]

    # 查询语料
    if selected_intent_id:
        c.execute("""
            SELECT c.corpus_id, i.intent_ch, c.intent_en, s.name as slot_name, c.score, c.is_active 
            FROM corpus c
            JOIN intents i ON c.intent_id = i.intent_id
            LEFT JOIN slots s ON c.slot_id = s.slot_id
            WHERE i.intent_id = ?
        """, (selected_intent_id,))
    else:
        c.execute("""
            SELECT c.corpus_id, i.intent_ch, c.intent_en, s.name as slot_name, c.score, c.is_active 
            FROM corpus c
            JOIN intents i ON c.intent_id = i.intent_id
            LEFT JOIN slots s ON c.slot_id = s.slot_id
            WHERE i.product_id = ?
        """, (product_id,))

    corpus_data = c.fetchall()

    # 添加"意图列表"标题
    st.subheader("意图列表", divider="rainbow")

    # 显示语料列表
    if corpus_data:
        df = pd.DataFrame(corpus_data, columns=['ID', '中文意图', '英文语料', '关联Slot', '得分', '是否激活'])
        
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_pagination(paginationAutoPageSize=True)
        gb.configure_side_bar()
        gb.configure_selection('multiple', use_checkbox=True, groupSelectsChildren="Group checkbox select children")
        gridOptions = gb.build()

        grid_response = AgGrid(
            df,
            gridOptions=gridOptions,
            data_return_mode='AS_INPUT', 
            update_mode='MODEL_CHANGED', 
            fit_columns_on_grid_load=False,
            theme='streamlit', 
            enable_enterprise_modules=True,
            height=400, 
            width='100%',
            reload_data=True
        )

        selected = grid_response['selected_rows']
        if selected:
            st.write('选中的行:')
            st.json(selected)
    else:
        st.info("没有找到相关语料")

    # 添加新语料
    st.subheader("添加新语料", divider="rainbow")
    new_intent_en = st.text_input("英文语料")
    new_score = st.number_input("得分", min_value=0.0, max_value=1.0, value=0.5, step=0.1)
    new_is_active = st.checkbox("是否激活", value=True)

    if st.button("添加语料"):
        if new_intent_en and selected_intent_id:
            c.execute("""
                INSERT INTO corpus (intent_id, intent_en, score, is_active)
                VALUES (?, ?, ?, ?)
            """, (selected_intent_id, new_intent_en, new_score, new_is_active))
            conn.commit()
            st.success("语料添加成功！")
            st.rerun()
        else:
            st.error("请填写英文语料并选择一个意图")

    # CSV模板和批量上传
    st.subheader("批量上传语料", divider="rainbow")

    # 创建CSV模板
    template_data = {
        'intent_ch': ['查询余额', '转账'],
        'intent_en': ['check_balance', 'transfer'],
        'corpus_en': ['What is my account balance?', 'I want to transfer money'],
        'score': [0.9, 0.8],
        'is_active': [True, True]
    }
    template_df = pd.DataFrame(template_data)

    # 显示模板预览
    st.write("CSV模板预览：")
    st.dataframe(template_df, use_container_width=True)

    # 下载模板按钮
    csv = template_df.to_csv(index=False)
    st.download_button(
        label="下载CSV模板",
        data=csv,
        file_name="corpus_template.csv",
        mime="text/csv",
    )

    # 文件上传
    uploaded_file = st.file_uploader("选择CSV文件上传", type="csv")

    if uploaded_file is not None and st.session_state.upload_state == 'initial':
        # 读取CSV文件
        df = pd.read_csv(uploaded_file)
        
        # 处理数据并创建preview_data
        preview_data = []
        for _, row in df.iterrows():
            # 这里添加处理每行数据的逻辑
            preview_data.append({
                'intent_ch': row['intent_ch'],
                'intent_en': row['intent_en'],
                'corpus_en': row['corpus_en'],
                'score': row['score'],
                'is_active': row['is_active'],
                'status': '准备导入'  # 可以根据需要设置状态
            })

        if st.button("确认导入"):
            # 将预览数据保存到session state
            st.session_state.preview_data = preview_data
            st.session_state.upload_state = 'preview'
            st.rerun()

    if st.session_state.upload_state == 'preview':
        # 显示预览数据
        st.write("导入预览:")
        preview_df = pd.DataFrame(st.session_state.preview_data)
        st.dataframe(preview_df, use_container_width=True)

        if st.button("确认最终导入"):
            st.session_state.upload_state = 'importing'
            st.rerun()

    if st.session_state.upload_state == 'importing':
        success_count = 0
        error_count = 0
        try:
            for row in st.session_state.preview_data:
                if row['status'] == '准备导入':
                    try:
                        c.execute("""
                            INSERT INTO corpus (intent_id, intent_en, score, is_active)
                            VALUES (?, ?, ?, ?)
                        """, (row['intent_id'], row['corpus_en'], row['score'], row['is_active']))
                        success_count += 1
                    except Exception as e:
                        st.error(f"导入错误: {str(e)}")
                        error_count += 1
                else:
                    error_count += 1

            conn.commit()
            st.success(f"成功导入 {success_count} 条语料，失败 {error_count} 条")
        except Exception as e:
            st.error(f"导入过程中发生错误: {str(e)}")
        finally:
            st.session_state.upload_state = 'initial'
            st.session_state.preview_data = None
            if st.button("刷新页面"):
                st.rerun()

    # 在这里可以添更多功能，如批量导入、导出等

# 在 app.py 中调用这个函数
