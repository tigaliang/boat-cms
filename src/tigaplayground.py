import streamlit as st

import igen

if st.button("Generate now"):
    instructions = igen.generate(subject='扫地机器人', operation='开始扫地', style='常规',
                                 examples=['Start cleaning.', 'Begin cleaning.'])

    st.text(instructions)

else:
    st.text("Generated data")
