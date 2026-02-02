import psycopg2
import streamlit as st

def get_connection():
    try:
        conn = psycopg2.connect(st.secrets["DATABASE_URL"])
        return conn
    except Exception as e:
        st.error(f"Erro ao conectar ao banco: {e}")
        return None

def inserir_paciente(nome, cpf, data_nascimento, telefone, email, contato_emergencia, observacoes):
    conn = get_connection()
    if conn is None:
        return False

    try:
        cur = conn.cursor()

        sql = """
        INSERT INTO paciente 
        (nome, cpf, data_nascimento, telefone, email, contato_emergencia, observacoes)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        cur.execute(sql, (nome, cpf, data_nascimento, telefone, email, contato_emergencia, observacoes))
        conn.commit()

        cur.close()
        conn.close()

        return True

    except Exception as e:
        conn.close()
        return str(e)

def listar_pacientes(filtro=""):
    conn = get_connection()
    if conn is None:
        return []

    try:
        cur = conn.cursor()

        if filtro:
            sql = """
            SELECT id, nome, cpf, data_nascimento, telefone, email
            FROM paciente
            WHERE nome ILIKE %s OR cpf ILIKE %s
            ORDER BY nome
            """
            cur.execute(sql, (f"%{filtro}%", f"%{filtro}%"))
        else:
            sql = """
            SELECT id, nome, cpf, data_nascimento, telefone, email
            FROM paciente
            ORDER BY nome
            """
            cur.execute(sql)

        resultados = cur.fetchall()

        cur.close()
        conn.close()

        return resultados

    except Exception as e:
        conn.close()
        return []


