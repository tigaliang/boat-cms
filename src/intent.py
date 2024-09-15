import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3
import io

# 在函数开始处定义 CSV 表头
CSV_HEADERS = [
    'intent_ch',      # 中文意图
    'intent_en',      # 英文意图
    'description',    # 意图描述
    'feature_name',   # 功能名称
    'slot_name',      # 关联的Slot名称（可选）
]

def manage_intents(conn):
    st.header("意图管理")

    # 获取所有产品
    c = conn.cursor()
    c.execute("SELECT product_id, name FROM products")
    products = c.fetchall()

    # 创建产品选择下拉框
    product_options = {product[1]: product[0] for product in products}
    selected_product = st.selectbox("选择产品", options=list(product_options.keys()))
    
    # 获取选中产品的ID
    product_id = product_options[selected_product]

    # 获取当前产品的所有features
    c.execute("SELECT feature_id, name FROM features WHERE product_id = ?", (product_id,))
    features = c.fetchall()
    feature_options = {"所有功能": None}
    feature_options.update({feature[1]: feature[0] for feature in features})

    # 创建功能选择下拉框
    selected_feature = st.selectbox("选择功能", options=list(feature_options.keys()))
    selected_feature_id = feature_options[selected_feature]

    # 获取当前产品的所有slots
    c.execute("SELECT slot_id, name FROM slots WHERE product_id = ?", (product_id,))
    slots = c.fetchall()
    slot_options = {slot[1]: slot[0] for slot in slots}
    slot_options['无'] = None

    # 添加新意图
    st.subheader("添加新意图", divider="rainbow")
    col1, col2, col3 = st.columns(3)
    with col1:
        intent_ch = st.text_input("中文意图")
        intent_en = st.text_input("英文意图")
    with col2:
        description = st.text_area("意图描述")
    with col3:
        selected_feature_for_add = st.selectbox("选择功能", options=list(feature_options.keys())[1:], key="add_feature")
        selected_slot = st.selectbox("关联的Slot", options=list(slot_options.keys()))
        is_active = st.checkbox("是否激活", value=True)
        add_intent = st.button("添加意图")

    if add_intent:
        if intent_ch and intent_en and selected_feature_for_add != "所有功能":
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("""INSERT INTO intents (product_id, feature_id, slot_id, intent_ch, intent_en, description, created_at, is_active) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                      (product_id, feature_options[selected_feature_for_add], slot_options[selected_slot], 
                       intent_ch, intent_en, description, created_at, is_active))
            conn.commit()
            st.success("意图添加成功！")
            st.rerun()
        else:
            st.error("中文意图、英文意图和功能不能为空")

    # 显示意图列表
    st.subheader("意图列表", divider="rainbow")
    if selected_feature_id is None:
        c.execute("""SELECT i.intent_id, i.intent_ch, i.intent_en, i.description, 
                     f.name as feature_name, s.name as slot_name, i.created_at, i.is_active 
                     FROM intents i 
                     LEFT JOIN features f ON i.feature_id = f.feature_id
                     LEFT JOIN slots s ON i.slot_id = s.slot_id 
                     WHERE i.product_id = ? 
                     ORDER BY i.created_at DESC""", (product_id,))
    else:
        c.execute("""SELECT i.intent_id, i.intent_ch, i.intent_en, i.description, 
                     f.name as feature_name, s.name as slot_name, i.created_at, i.is_active 
                     FROM intents i 
                     LEFT JOIN features f ON i.feature_id = f.feature_id
                     LEFT JOIN slots s ON i.slot_id = s.slot_id 
                     WHERE i.product_id = ? AND i.feature_id = ?
                     ORDER BY i.created_at DESC""", (product_id, selected_feature_id))
    intents = c.fetchall()

    if intents:
        df = pd.DataFrame(intents, columns=['ID', '中文意图', '英文意图', '描述', '功能', '关联Slot', '创建时间', '是否激活'])
        df['创建时间'] = pd.to_datetime(df['创建时间']).dt.strftime('%Y-%m-%d')
        df['是否激活'] = df['是否激活'].map({1: '是', 0: '否'})
        st.dataframe(df, use_container_width=True)

        # 删除意图
        col1, col2 = st.columns(2)
        with col1:
            intent_to_delete = st.selectbox("选择要删除的意图", df['中文意图'])
        with col2:
            if st.button("删除选中的意图", type="secondary"):
                c.execute("DELETE FROM intents WHERE product_id = ? AND intent_ch = ?", (product_id, intent_to_delete))
                conn.commit()
                st.success(f"成功删除意图: {intent_to_delete}")
                st.rerun()

        # 更新意图状态
        st.subheader("更新意图状态", divider="rainbow")
        col1, col2, col3 = st.columns(3)
        with col1:
            intent_to_update = st.selectbox("选择要更新的意图", df['中文意图'], key="update_intent")
        with col2:
            new_status = st.checkbox("激活状态", value=True)
        with col3:
            if st.button("更新意图状态"):
                c.execute("UPDATE intents SET is_active = ? WHERE product_id = ? AND intent_ch = ?", 
                          (new_status, product_id, intent_to_update))
                conn.commit()
                st.success(f"成功更新意图状态: {intent_to_update}")
                st.rerun()
    else:
        st.info("该产品目前没有添加任何意图。")

    # 批量上传 CSV
    st.subheader("批量上传意图", divider="rainbow")

    #模版
    template_df = pd.DataFrame(columns=CSV_HEADERS)
    csv = template_df.to_csv(index=False)
    st.download_button(
                label="点击下载 CSV 模板",
                data=csv,
                file_name="intent_template.csv",
                mime="text/csv",
        )

    uploaded_file = st.file_uploader("选择 CSV 文件", type="csv")
   
   
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        
        # 验证 CSV 格式
        if not all(header in df.columns for header in CSV_HEADERS):
            st.error("CSV 文件格式不正确。请确保包含所有必要的列。")
        else:
            st.write("预览上传的数据:")
            st.dataframe(df)
            print(len(df))

            if st.button("确认导入"):
                c = conn.cursor()
                for _, row in df.iterrows():
                    # 获取 feature_id
                    c.execute("SELECT feature_id FROM features WHERE name = ? AND product_id = ?", 
                              (row['feature_name'], product_id))
                    feature_id = c.fetchone()
                    if feature_id:
                        feature_id = feature_id[0]
                    else:
                        st.warning(f"功能 '{row['feature_name']}' 不存在,跳过该行")
                        continue

                    # 获取 slot_id
                    slot_id = None
                    if pd.notna(row['slot_name']):
                        c.execute("SELECT slot_id FROM slots WHERE name = ? AND product_id = ?", 
                                  (row['slot_name'], product_id))
                        slot_result = c.fetchone()
                        if slot_result:
                            slot_id = slot_result[0]
                        else:
                            st.warning(f"Slot '{row['slot_name']}' 不存在,该意图将不关联 Slot")

                    # 插入新意图
                    c.execute("""
                        INSERT INTO intents (product_id, feature_id, slot_id, intent_ch, intent_en, description, created_at, is_active)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (product_id, feature_id, slot_id, row['intent_ch'], row['intent_en'], 
                          row['description'], datetime.now(), row.get('is_active', True)))

                conn.commit()
                st.success("成功导入意图!")
                st.rerun()

    # 下载当前意图为 CSV
    st.subheader("下载意图", divider="rainbow")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("下载当前意图"):
            if intents:
                df_download = pd.DataFrame(intents, columns=['ID', 'intent_ch', 'intent_en', 'description', 'feature_name', 'slot_name', 'created_at', 'is_active'])
                df_download = df_download[CSV_HEADERS]  # 只包含需要的列
                csv = df_download.to_csv(index=False)
                st.download_button(
                    label="点击下载当前意图 CSV",
                    data=csv,
                    file_name="current_intents.csv",
                    mime="text/csv",
                )
            else:
                st.info("当前没有可下载的意图")
