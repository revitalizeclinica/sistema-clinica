import streamlit as st
from database import get_connection

st.title("Sistema Revitalize - Clínica")

st.write("Teste de conexão com o banco de dados:")

conn = get_connection()

if conn:
    st.success("Conectado com sucesso ao Supabase!")
    conn.close()
else:
    st.error("Falha na conexão com o banco.")
