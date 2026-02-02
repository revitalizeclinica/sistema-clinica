import os
import psycopg2
import streamlit as st

def get_connection():
    try:
        conn = psycopg2.connect(
            host=st.secrets["SUPABASE_HOST"],
            port=st.secrets["SUPABASE_PORT"],
            database=st.secrets["SUPABASE_DB"],
            user=st.secrets["SUPABASE_USER"],
            password=st.secrets["SUPABASE_PASSWORD"]
        )
        return conn
    except Exception as e:
        st.error(f"Erro ao conectar ao banco: {e}")
        return None
