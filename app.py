import pandas as pd
import streamlit as st

import gen

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=['patient_id', 'patient_name', 'diagnosis_code', 'procedure_code',
                                                'total_charge', 'insurance_claim_amount'])

if st.button("Append random value"):
    billings = gen.gen_billings()

    st.session_state.df = pd.concat(
        [st.session_state.df, pd.DataFrame(map(lambda billing: vars(billing), billings))])
    st.text("Generated data")
    st.data_editor(st.session_state.df, hide_index=True)
else:
    st.text("Generated data")
