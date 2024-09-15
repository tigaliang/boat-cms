import streamlit as st
import pandas as pd
import io

def manage_slots(conn):
    st.header("Slots 管理")
    
    # 获取所有产品
    c = conn.cursor()
    c.execute("SELECT product_id, name FROM products")
    products = c.fetchall()
    
    # 创建产品选择下拉列表
    product_options = {product[1]: product[0] for product in products}
    selected_product_name = st.selectbox("选择产品", list(product_options.keys()))
    product_id = product_options[selected_product_name]
    
    # 更新 session state 中的 selected_product_id
    st.session_state.selected_product_id = product_id
    
    st.write(f"当前产品：{selected_product_name}")

    # 添加新的 slot
    st.subheader("添加新的 Slot", divider="rainbow")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        new_slot_name = st.text_input("Slot 名称")
    
    with col2:
        new_slot_description = st.text_area("Slot 描述", height=100)
    
    with col3:
        new_slot_examples = st.text_area("Slot 示例", height=100)
        new_slot_is_active = st.checkbox("是否激活", value=True)
    
    if st.button("添加 Slot", type="primary"):
        if new_slot_name:
            c.execute("""INSERT INTO slots (product_id, name, description, examples, is_active) 
                         VALUES (?, ?, ?, ?, ?)""",
                      (product_id, new_slot_name, new_slot_description, new_slot_examples, new_slot_is_active))
            conn.commit()
            st.success(f"成功添加 Slot: {new_slot_name}")
            st.rerun()
        else:
            st.error("Slot 名称不能为空")

    # 批量上传 Slots
    st.subheader("批量上传 Slots", divider="rainbow")

    # 创建模板数据
    template_data = {
        'name': ['天气查询', '闹钟设置'],
        'description': ['用于查询天气信息的槽位', '用于设置闹钟的槽位'],
        'examples': ['今天天气怎么样？|明天会下雨吗？', '设置一个早上7点的闹钟|帮我定个下午3点的闹钟']
    }
    template_df = pd.DataFrame(template_data)


    # 创建下载模板的按钮
    csv = template_df.to_csv(index=False)
    st.download_button(
        label="下载CSV模板",
        data=csv,
        file_name="slots_template.csv",
        mime="text/csv",
    )

    # 文件上传部分
    uploaded_file = st.file_uploader("选择 CSV 文件上传", type="csv")
    
    if uploaded_file is not None:
        # 读取 CSV 文件
        df = pd.read_csv(uploaded_file)
        
        # 检查必要的列是否存在
        required_columns = ['name', 'description', 'examples']
        if not all(col in df.columns for col in required_columns):
            st.error("CSV 文件必须包含以下列: name, description, examples")
        else:
            # 预览数据
            st.write("预览上传的数据:")
            st.dataframe(df, use_container_width=True)
            
            # 确认上传
            if st.button("确认上传"):
                c = conn.cursor()
                for _, row in df.iterrows():
                    c.execute("""
                        INSERT INTO slots (product_id, name, description, examples, is_active)
                        VALUES (?, ?, ?, ?, ?)
                    """, (product_id, row['name'], row['description'], row['examples'], True))
                conn.commit()
                st.success(f"成功上传 {len(df)} 个 Slots")
                st.rerun()

    # 显示现有的 Slots
    st.subheader("现有 Slots", divider="rainbow")
    c.execute("SELECT * FROM slots WHERE product_id = ?", (product_id,))
    slots = c.fetchall()
    
    if slots:
        df_slots = pd.DataFrame(slots, columns=['slot_id', 'product_id', 'name', 'description', 'examples', 'is_active'])
        st.dataframe(df_slots[['name', 'description', 'examples', 'is_active']], use_container_width=True)
        
        # 删除 Slot
        col1, col2 = st.columns(2)
        with col1:
            slot_to_delete = st.selectbox("选择要删除的 Slot", df_slots['name'])
        with col2:
            if st.button("删除选中的 Slot", type="secondary"):
                c.execute("DELETE FROM slots WHERE product_id = ? AND name = ?", (product_id, slot_to_delete))
                conn.commit()
                st.success(f"成功删除 Slot: {slot_to_delete}")
                st.rerun()
    else:
        st.info("当前产品还没有添加任何 Slots")

    # 更新 Slot 状态
    if slots:
        st.subheader("更新 Slot 状态", divider="rainbow")
        col1, col2, col3 = st.columns(3)
        with col1:
            slot_to_update = st.selectbox("选择要更新的 Slot", df_slots['name'], key="update_slot")
        with col2:
            new_status = st.checkbox("激活状态", value=True)
        with col3:
            if st.button("更新 Slot 状态"):
                c.execute("UPDATE slots SET is_active = ? WHERE product_id = ? AND name = ?", 
                          (new_status, product_id, slot_to_update))
                conn.commit()
                st.success(f"成功更新 Slot 状态: {slot_to_update}")
                st.rerun()

    # 下载当前 Slots 为 CSV
    st.subheader("下载当前 Slots", divider="rainbow")
    if st.button("下载 CSV"):
        c = conn.cursor()
        c.execute("SELECT name, description, examples FROM slots WHERE product_id = ?", (product_id,))
        current_slots = c.fetchall()
        if current_slots:
            df_download = pd.DataFrame(current_slots, columns=['name', 'description', 'examples'])
            csv = df_download.to_csv(index=False)
            st.download_button(
                label="点击下载 CSV",
                data=csv,
                file_name="slots.csv",
                mime="text/csv",
            )
        else:
            st.info("当前没有可下载的 Slots")
