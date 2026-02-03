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
            SELECT id, nome, cpf, TO_CHAR(data_nascimento, 'DD/MM/YYYY'), telefone, email
            FROM paciente
            WHERE nome ILIKE %s OR cpf ILIKE %s
            ORDER BY nome
            """
            cur.execute(sql, (f"%{filtro}%", f"%{filtro}%"))
        else:
            sql = """
            SELECT id, nome, cpf, TO_CHAR(data_nascimento, 'DD/MM/YYYY'), telefone, email
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
    

def inserir_evolucao(paciente_id, data_registro, profissional, resumo, condutas, resposta, objetivos, observacoes):

    conn = get_connection()
    if conn is None:
        return False

    try:
        cur = conn.cursor()

        sql = """
        INSERT INTO evolucao
        (paciente_id, data_registro, profissional, resumo_evolucao, condutas, resposta_paciente, objetivos, observacoes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        cur.execute(sql, (
            paciente_id,
            data_registro,
            profissional,
            resumo,
            condutas,
            resposta,
            objetivos,
            observacoes
        ))

        conn.commit()
        cur.close()
        conn.close()

        return True

    except Exception as e:
        conn.close()
        return str(e)

def listar_evolucoes_por_paciente(paciente_id):

    conn = get_connection()
    if conn is None:
        return []

    try:
        cur = conn.cursor()

        sql = """
        SELECT 
            id,
            data_registro,
            profissional,
            resumo_evolucao,
            condutas,
            resposta_paciente,
            objetivos,
            observacoes
        FROM evolucao
        WHERE paciente_id = %s
        ORDER BY data_registro DESC
        """

        cur.execute(sql, (paciente_id,))
        resultados = cur.fetchall()

        cur.close()
        conn.close()

        return resultados

    except Exception as e:
        conn.close()
        return []

def buscar_avaliacao(paciente_id):

    conn = get_connection()
    if conn is None:
        return None

    try:
        cur = conn.cursor()

        sql = """
        SELECT *
        FROM avaliacao_inicial
        WHERE paciente_id = %s
        """

        cur.execute(sql, (paciente_id,))
        resultado = cur.fetchone()

        cur.close()
        conn.close()

        return resultado

    except Exception:
        conn.close()
        return None
    
def inserir_avaliacao(paciente_id, dados):

    conn = get_connection()
    if conn is None:
        return False

    try:
        cur = conn.cursor()

        sql = """
        INSERT INTO avaliacao_inicial (
            paciente_id,
            data_avaliacao,
            profissional,
            queixa_principal,
            diagnostico,
            historico,
            medicamentos,
            dor,
            mobilidade,
            forca,
            limitacoes,
            marcha,
            equilibrio,
            objetivos,
            plano_terapeutico
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """

        cur.execute(sql, (
            paciente_id,
            dados["data"],
            dados["profissional"],
            dados["queixa"],
            dados["diagnostico"],
            dados["historico"],
            dados["medicamentos"],
            dados["dor"],
            dados["mobilidade"],
            dados["forca"],
            dados["limitacoes"],
            dados["marcha"],
            dados["equilibrio"],
            dados["objetivos"],
            dados["plano"]
        ))

        conn.commit()
        cur.close()
        conn.close()

        return True

    except Exception as e:
        conn.close()
        return str(e)





