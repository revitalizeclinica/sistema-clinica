import psycopg2
import streamlit as st

def get_connection():
    try:
        conn = psycopg2.connect(st.secrets["DATABASE_URL"])
        return conn
    except Exception as e:
        st.error(f"Erro ao conectar ao banco: {e}")
        return None

def inserir_paciente(nome, data_nascimento, telefone, email, contato_emergencia, observacoes):
    conn = get_connection()
    if conn is None:
        return False

    try:
        cur = conn.cursor()

        sql = """
        INSERT INTO paciente 
        (nome, data_nascimento, telefone, email, contato_emergencia, observacoes)
        VALUES (%s, %s, %s, %s, %s, %s)
        """

        cur.execute(sql, (nome, data_nascimento, telefone, email, contato_emergencia, observacoes))
        conn.commit()

        cur.close()
        conn.close()

        return True

    except Exception as e:
        conn.close()
        return str(e)

