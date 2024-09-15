import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3
import io

def manage_features(conn):
    st.header("功能管理")

    # 获取所有产品
    c = conn.cursor()
    c.execute("SELECT product_id, name FROM products")
    products = c.fetchall()

    # 创建产品选择下拉框
    product_options = {product[1]: product[0] for product in products}
    selected_product = st.selectbox("选择产品", options=list(product_options.keys()))
    
    # 获取选中产品的ID
    product_id = product_options[selected_product]

    st.write(f"当前产品：{selected_product}")

    # 添加新特性
    st.subheader("添加新特性", divider="rainbow")
    col1, col2, col3 = st.columns(3)
    with col1:
        feature_name = st.text_input("特性名称")
    with col2:
        feature_description = st.text_area("特性描述")
    with col3:
        is_active = st.checkbox("是否激活", value=True)
        add_feature = st.button("添加特性")

    if add_feature:
        if feature_name:
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO features (product_id, name, description, created_at, is_active) VALUES (?, ?, ?, ?, ?)",
                      (product_id, feature_name, feature_description, created_at, is_active))
            conn.commit()
            st.success("特性添加成功！")
            st.rerun()
        else:
            st.error("特性名称不能为空")

    # 批量导入特性
    st.subheader("批量导入特性", divider="rainbow")
    uploaded_file = st.file_uploader("上传CSV文件", type="csv")
    
    if uploaded_file is not None:
        # 读取CSV文件
        df = pd.read_csv(uploaded_file)
        
        # 检查CSV文件的列
        required_columns = ['name', 'description']
        if not all(col in df.columns for col in required_columns):
            st.error("CSV文件格式不正确。请确保文件包含'name'和'description'列。")
        else:
            # 预览数据
            st.write("数据预览:")
            st.dataframe(df)
            
            # 确认导入按钮
            if st.button("确认导入"):
                c = conn.cursor()
                created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                for _, row in df.iterrows():
                    c.execute("INSERT INTO features (product_id, name, description, created_at, is_active) VALUES (?, ?, ?, ?, ?)",
                              (product_id, row['name'], row['description'], created_at, True))
                
                conn.commit()
                st.success(f"成功导入 {len(df)} 条特性记录！")
                st.rerun()

    # 显示特性列表
    st.subheader("特性列表", divider="rainbow")
    c.execute("SELECT feature_id, name, description, created_at, is_active FROM features WHERE product_id = ? ORDER BY created_at DESC", (product_id,))
    features = c.fetchall()

    if features:
        df = pd.DataFrame(features, columns=['ID', '名称', '描述', '创建时间', '是否激活'])
        df['创建时间'] = pd.to_datetime(df['创建时间']).dt.strftime('%Y-%m-%d')
        df['是否激活'] = df['是否激活'].map({1: '是', 0: '否'})
        st.dataframe(df, use_container_width=True)

        # 删除特性
        col1, col2 = st.columns(2)
        with col1:
            feature_to_delete = st.selectbox("选择要删除的特性", df['名称'])
        with col2:
            if st.button("删除选中的特性", type="secondary"):
                c.execute("DELETE FROM features WHERE product_id = ? AND name = ?", (product_id, feature_to_delete))
                conn.commit()
                st.success(f"成功删除特性: {feature_to_delete}")
                st.rerun()

        # 更新特性状态
        st.subheader("更新特性状态", divider="rainbow")
        col1, col2, col3 = st.columns(3)
        with col1:
            feature_to_update = st.selectbox("选择要更新的特性", df['名称'], key="update_feature")
        with col2:
            new_status = st.checkbox("激活状态", value=True)
        with col3:
            if st.button("更新特性状态"):
                c.execute("UPDATE features SET is_active = ? WHERE product_id = ? AND name = ?", 
                          (new_status, product_id, feature_to_update))
                conn.commit()
                st.success(f"成功更新特性状态: {feature_to_update}")
                st.rerun()
    else:
        st.info("该产品目前没有添加任何特性。")

    # 下载当前特性为 CSV
    st.subheader("下载当前特性", divider="rainbow")
    if st.button("下载 CSV"):
        if features:
            df_download = pd.DataFrame(features, columns=['ID', 'name', 'description', 'created_at', 'is_active'])
            df_download = df_download[['name', 'description']]  # 只包含名称和描述
            csv = df_download.to_csv(index=False)
            st.download_button(
                label="点击下载 CSV",
                data=csv,
                file_name="features.csv",
                mime="text/csv",
            )
        else:
            st.info("当前没有可下载的特性")
