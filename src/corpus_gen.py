import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
import sqlite3
import igen

def manage_corpus_gen(conn):
    st.subheader("语料生成")

    # 获取产品列表
    c = conn.cursor()
    c.execute("SELECT product_id, name FROM products")
    products = c.fetchall()
    product_options = {p[1]: p[0] for p in products}
    selected_product = st.selectbox("选择产品", list(product_options.keys()), key="product_select")
    selected_product_id = product_options[selected_product]

    # 获取功能列表
    c.execute("SELECT feature_id, name FROM features WHERE product_id = ?", (selected_product_id,))
    features = c.fetchall()
    feature_options = {f[1]: f[0] for f in features}
    selected_feature = st.selectbox("选择功能", list(feature_options.keys()), key="feature_select")
    selected_feature_id = feature_options[selected_feature]

    # 获取意图列表
    c.execute("SELECT intent_id, intent_ch FROM intents WHERE product_id = ? AND feature_id = ?", (selected_product_id, selected_feature_id))
    intents = c.fetchall()
    intent_options = {i[1]: i[0] for i in intents}
    selected_intent = st.selectbox("选择意图", list(intent_options.keys()), key="intent_select")
    selected_intent_id = intent_options[selected_intent]

    # 表单
    with st.form("corpus_gen_form"):
        # 获取产品描述
        c.execute("SELECT description FROM products WHERE product_id = ?", (selected_product_id,))
        product_description = c.fetchone()[0]
        st.text_area("产品描述", value=product_description, height=100, key="product_description")

        # 获取功能说明
        c.execute("SELECT description FROM features WHERE feature_id = ?", (selected_feature_id,))
        feature_description = c.fetchone()[0]
        st.text_area("功能说明", value=feature_description, height=100, key="feature_description")

        # 获取意图说明
        c.execute("SELECT description FROM intents WHERE intent_id = ?", (selected_intent_id,))
        intent_description = c.fetchone()[0]
        st.text_area("意图说明", value=intent_description, height=100, key="intent_description")

        # 新增 Example TextArea
        corpus_example = st.text_area(
            "Example",
            placeholder="请输入示例,每行一个",
            height=100,
            key="corpus_example"
        )

        # 额外信息
        extra_info = st.text_area("额外信息", height=100, key="extra_info",value=feature_description)

        # 风格选择和生成条数输入框并排显示
        col1, col2 = st.columns(2)
        with col1:
            style_options = ["常规(Normal)", "正式(Formal)", "随意(Casual)", "口语化(Colloquial)"]
            selected_style = st.selectbox("选择风格", style_options, key="style_select")
        with col2:
            num_generations = st.number_input("生成条数", min_value=1, max_value=100, value=10, step=1, key="num_generations")

        generate_button = st.form_submit_button("一键生成")

    # 处理 Example 输入,分割成数组
    example_array = [line.strip() for line in corpus_example.split('\n') if line.strip()]
    
    # 初始化会话状态
    if 'generated_corpus' not in st.session_state:
        st.session_state.generated_corpus = None
    if 'import_clicked' not in st.session_state:
        st.session_state.import_clicked = False

    # 生成语料按钮
    if generate_button:
        st.session_state.generated_corpus = generate_corpus(
            selected_intent_id,
            selected_product,
            selected_intent,
            intent_description,
            feature_description,
            extra_info,
            selected_style,
            example_array,
            num_generations  # 新增参数
        )

    # 显示生成的语料
    if st.session_state.generated_corpus is not None:
        st.subheader("生成的语料")
        df = pd.DataFrame(st.session_state.generated_corpus, columns=["意图ID", "槽位ID", "英文意图", "分数"])
        
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_selection('multiple', use_checkbox=True)
        gb.configure_column("英文意图", editable=True)
        gb.configure_column("分数", editable=True)
        grid_options = gb.build()

        grid_response = AgGrid(
            df,
            gridOptions=grid_options,
            data_return_mode='AS_INPUT', 
            update_mode='MODEL_CHANGED',
            fit_columns_on_grid_load=True,
            theme='streamlit'
        )

        selected_rows = grid_response['selected_rows']
        updated_df = grid_response['data']

        if not selected_rows is None and not selected_rows.empty:
            print("First element of selected_rows:", selected_rows[0])
            print("Type of first element:", type(selected_rows[0]))
        print("Type of selected_rows:", type(selected_rows))

        if st.button("删除选中行"):
            updated_df = updated_df[~updated_df.index.isin([row['_selectedRowNodeInfo']['nodeRowIndex'] for row in selected_rows])]
            st.success("已删除选中行")

        # 使用会话状态来标记导入按钮是否被点击
        if st.button("一键确认导入"):
            st.session_state.import_clicked = True

        # 如果导入按钮被点击,执行导入操作
        if st.session_state.import_clicked:
            st.write("开始导入语料...")
            st.write(f"数据: {updated_df}")
            try:
                import_corpus(conn, updated_df, selected_intent_id)
                st.success("语料已成功导入")
                # 重置导入状态
                st.session_state.import_clicked = False
                st.session_state.generated_corpus = None
            except Exception as e:
                st.error(f"导入过程中出错: {str(e)}")
            st.write("导入过程完成")

def generate_corpus(intent_id, product_name, intent_name, intent_description, feature_description, extra_info, style, examples, nums):
    # 这里应该实现您的语料生成逻辑
    # 现在只返回一些示例数据
    # 导入必要的库
  
    import igen
    import streamlit as st
    
    # 调试信息
    st.write("调试信息:")
    st.write(f"产品名称: {product_name}")
    st.write(f"意图名称: {intent_name}")
    st.write(f"意图描述: {intent_description}")
    st.write(f"额外信息: {extra_info}")
    st.write(f"示例: {examples}")

    # 根据提供的信息生成语料
    generated_phrases = igen.generate(
        subject=product_name,
        operation=intent_name,
        style=style.split('(')[1].strip(')'),  # 只取英文部分
        examples=examples,  # 使用处理后的示例数组
        slots="",
        n=nums,  # 使用用户指定的生成条数
        extra=extra_info,
        runs=1
    )
    
    st.text("info: " + str(generated_phrases))

    # 将生成的语转换为语料数据式
    corpus_data = []
    for instruction in generated_phrases:
        for phrase in instruction.phrases:
            corpus_data.append([
                intent_id,
                None,  # 假设暂时没有槽位信息
                phrase,
                0.9  # 假设默认分数为0.9
            ])
    
    return corpus_data

    # # 处理生成的语料
    # corpus = []
    # for i, phrase in enumerate(generated_phrases, start=1):
    #     corpus.append([intent_id, i, phrase, 0.9])  # 假设每个短语的分数为0.9
    # return [
    #     [1, 1, "Example corpus 1", 0.9],
    #     [1, 2, "Example corpus 2", 0.8],
    #     [1, 3, "Example corpus 3", 0.7],
    # ]

def import_corpus(conn, df, intent_id):
    c = conn.cursor()
    st.write("开始执行import_corpus函数")
    st.write(f"意图ID: {intent_id}")
    st.write(f"数据: {df}")
    for _, row in df.iterrows():
        query = """
            INSERT INTO corpus (intent_id, slot_id, intent_en, score, is_active)
            VALUES (?, ?, ?, ?, 1)
        """
        st.write(f"SQL 查询语句: {query}")
        st.write(f"插入的数据: {(intent_id, row['槽位ID'], row['英文意图'], row['分数'])}")
        
        c.execute(query, (intent_id, row['槽位ID'], row['英文意图'], row['分数']))
    conn.commit()
    st.write("import_corpus函数执行完毕")
