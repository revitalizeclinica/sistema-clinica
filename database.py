import psycopg2
import streamlit as st

def get_connection():
    try:
        conn = psycopg2.connect(st.secrets["DATABASE_URL"])
        return conn
    except Exception as e:
        st.error(f"Erro ao conectar ao banco: {e}")
        return None

def inserir_paciente(
    nome,
    cpf,
    data_nascimento,
    telefone,
    email,
    contato_emergencia,
    observacoes,
    solicita_nota=False,
    pagador_mesmo_paciente=True,
    pagador_nome=None,
    pagador_cpf=None
):
    conn = get_connection()
    if conn is None:
        return False

    try:
        cur = conn.cursor()

        sql = """
        INSERT INTO paciente 
        (
            nome,
            cpf,
            data_nascimento,
            telefone,
            email,
            contato_emergencia,
            observacoes,
            solicita_nota,
            pagador_mesmo_paciente,
            pagador_nome,
            pagador_cpf
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        cur.execute(sql, (
            nome,
            cpf,
            data_nascimento,
            telefone,
            email,
            contato_emergencia,
            observacoes,
            solicita_nota,
            pagador_mesmo_paciente,
            pagador_nome,
            pagador_cpf
        ))
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
    

def inserir_evolucao(paciente_id, tipo_id, data, profissional,
                     resumo, condutas, resposta, objetivos, observacoes, valor_cobrado):

    conn = get_connection()
    if conn is None:
        return False

    try:
        cur = conn.cursor()

        sql = """
        INSERT INTO evolucao (
            paciente_id,
            tipo_atendimento_id,
            data_registro,
            profissional,
            resumo_evolucao,
            condutas,
            resposta_paciente,
            objetivos,
            observacoes,
            valor_cobrado
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """

        cur.execute(sql, (
            paciente_id,
            tipo_id,
            data,
            profissional,
            resumo,
            condutas,
            resposta,
            objetivos,
            observacoes,
            valor_cobrado
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
            e.id,
            e.data_registro,
            e.profissional,
            t.descricao,
            e.resumo_evolucao,
            e.condutas,
            e.resposta_paciente,
            e.objetivos,
            e.observacoes
        FROM evolucao e
        JOIN tipo_atendimento t ON e.tipo_atendimento_id = t.id
        WHERE e.paciente_id = %s
        ORDER BY e.data_registro DESC

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
    
def listar_tipos_atendimento():

    conn = get_connection()
    if conn is None:
        return []

    try:
        cur = conn.cursor()

        sql = """
        SELECT id, codigo, descricao
        FROM tipo_atendimento
        WHERE ativo = TRUE
        ORDER BY descricao
        """

        cur.execute(sql)
        resultados = cur.fetchall()

        cur.close()
        conn.close()

        return resultados

    except Exception as e:
        conn.close()
        return []

def listar_tipos_atendimento_com_valor():

    conn = get_connection()
    if conn is None:
        return []

    try:
        cur = conn.cursor()

        sql = """
        SELECT id, codigo, descricao, valor
        FROM tipo_atendimento
        WHERE ativo = TRUE
        ORDER BY descricao
        """

        cur.execute(sql)
        resultados = cur.fetchall()

        cur.close()
        conn.close()

        return resultados

    except Exception as e:
        conn.close()
        return []

def atualizar_preco_tipo_atendimento(tipo_id, novo_valor):

    conn = get_connection()
    if conn is None:
        return False

    try:
        cur = conn.cursor()

        sql = """
        UPDATE tipo_atendimento
        SET valor = %s
        WHERE id = %s
        """

        cur.execute(sql, (novo_valor, tipo_id))
        conn.commit()

        cur.close()
        conn.close()

        return True

    except Exception as e:
        conn.close()
        return str(e)

def relatorio_paciente(paciente_id, data_inicio, data_fim):

    conn = get_connection()
    cur = conn.cursor()

    sql = """
    SELECT
        t.descricao,
        COUNT(e.id) AS quantidade,
        COALESCE(e.valor_cobrado, t.valor) AS valor,
        COUNT(e.id) * COALESCE(e.valor_cobrado, t.valor) AS subtotal
    FROM evolucao e
    JOIN tipo_atendimento t ON e.tipo_atendimento_id = t.id
    WHERE e.paciente_id = %s
      AND e.data_registro::date BETWEEN %s AND %s
    GROUP BY t.descricao, COALESCE(e.valor_cobrado, t.valor)
    ORDER BY t.descricao;
    """

    cur.execute(sql, (paciente_id, data_inicio, data_fim))
    dados = cur.fetchall()

    cur.close()
    conn.close()

    return dados

def relatorio_paciente_agrupado(paciente_id, data_inicio, data_fim):
    """
    Relatório agrupado por tipo de atendimento.
    Retorna quantidade e subtotal por tipo.
    """
    conn = get_connection()
    if conn is None:
        return []

    try:
        cur = conn.cursor()

        sql = """
        SELECT
            t.descricao,
            COUNT(e.id) AS quantidade,
            COALESCE(e.valor_cobrado, t.valor) AS valor,
            COUNT(e.id) * COALESCE(e.valor_cobrado, t.valor) AS subtotal
        FROM evolucao e
        JOIN tipo_atendimento t ON e.tipo_atendimento_id = t.id
        WHERE e.paciente_id = %s
          AND e.data_registro::date BETWEEN %s AND %s
        GROUP BY t.descricao, COALESCE(e.valor_cobrado, t.valor)
        ORDER BY t.descricao;
        """

        cur.execute(sql, (paciente_id, data_inicio, data_fim))
        dados = cur.fetchall()

        cur.close()
        conn.close()

        return dados

    except Exception as e:
        conn.close()
        return []


def relatorio_paciente_detalhado(paciente_id, data_inicio, data_fim):
    """
    Relatório detalhado por paciente e período.
    Retorna uma linha por atendimento (para PDF e visualização).
    """
    conn = get_connection()
    if conn is None:
        return []

    try:
        cur = conn.cursor()

        sql = """
        SELECT
            e.data_registro,
            t.descricao AS tipo_atendimento,
            COALESCE(e.valor_cobrado, t.valor) AS valor,
            e.profissional,
            e.resumo_evolucao
        FROM evolucao e
        JOIN tipo_atendimento t
            ON e.tipo_atendimento_id = t.id
        WHERE e.paciente_id = %s
          AND e.data_registro::date BETWEEN %s AND %s
        ORDER BY e.data_registro
        """

        cur.execute(sql, (paciente_id, data_inicio, data_fim))
        dados = cur.fetchall()

        cur.close()
        conn.close()

        return dados

    except Exception as e:
        conn.close()
        return []

    conn = get_connection()
    cur = conn.cursor()

    sql = """
    SELECT
        e.data_registro,
        t.descricao,
        COALESCE(e.valor_cobrado, t.valor) AS valor
    FROM evolucao e
    JOIN tipo_atendimento t ON e.tipo_atendimento_id = t.id
    WHERE e.paciente_id = %s
      AND e.data_registro::date BETWEEN %s AND %s
    ORDER BY e.data_registro;
    """

    cur.execute(sql, (paciente_id, data_inicio, data_fim))
    dados = cur.fetchall()

    cur.close()
    conn.close()

    return dados


def relatorio_contador(data_inicio, data_fim):
    """
    Relatório para contador: pacientes que solicitam nota fiscal no período.
    Retorna uma linha por paciente com quantidade de atendimentos e total.
    """
    conn = get_connection()
    if conn is None:
        return []

    try:
        cur = conn.cursor()

        sql = """
        SELECT
            p.id,
            CASE
                WHEN COALESCE(p.pagador_mesmo_paciente, TRUE) THEN p.nome
                ELSE COALESCE(NULLIF(p.pagador_nome, ''), p.nome)
            END AS nome,
            CASE
                WHEN COALESCE(p.pagador_mesmo_paciente, TRUE) THEN p.cpf
                ELSE COALESCE(NULLIF(p.pagador_cpf, ''), p.cpf)
            END AS cpf,
            COUNT(e.id) AS quantidade,
            SUM(COALESCE(e.valor_cobrado, t.valor)) AS total
        FROM paciente p
        JOIN evolucao e ON e.paciente_id = p.id
        JOIN tipo_atendimento t ON e.tipo_atendimento_id = t.id
        WHERE p.solicita_nota = TRUE
          AND e.data_registro::date BETWEEN %s AND %s
        GROUP BY p.id, p.nome, p.cpf
        ORDER BY p.nome;
        """

        cur.execute(sql, (data_inicio, data_fim))
        dados = cur.fetchall()

        cur.close()
        conn.close()

        return dados

    except Exception:
        conn.close()
        return []

def relatorio_geral_resumo(data_inicio, data_fim):
    """
    Resumo do mês: entradas, pacientes pagantes e tipos de sessão.
    """
    conn = get_connection()
    if conn is None:
        return None

    try:
        cur = conn.cursor()

        sql = """
        SELECT
            COALESCE(SUM(COALESCE(e.valor_cobrado, t.valor)), 0) AS total_entradas,
            COUNT(DISTINCT e.paciente_id) AS pacientes_pagantes,
            COUNT(DISTINCT e.tipo_atendimento_id) AS tipos_sessao
        FROM evolucao e
        JOIN tipo_atendimento t ON e.tipo_atendimento_id = t.id
        WHERE e.data_registro::date BETWEEN %s AND %s
        """

        cur.execute(sql, (data_inicio, data_fim))
        resultado = cur.fetchone()

        cur.close()
        conn.close()

        return resultado

    except Exception:
        conn.close()
        return None


def relatorio_geral_por_tipo(data_inicio, data_fim):
    """
    Entradas do mês por tipo de sessão.
    Retorna: tipo, pacientes distintos, sessões, total.
    """
    conn = get_connection()
    if conn is None:
        return []

    try:
        cur = conn.cursor()

        sql = """
        SELECT
            t.descricao AS tipo_sessao,
            COUNT(DISTINCT e.paciente_id) AS pacientes,
            COUNT(e.id) AS sessoes,
            SUM(COALESCE(e.valor_cobrado, t.valor)) AS total
        FROM evolucao e
        JOIN tipo_atendimento t ON e.tipo_atendimento_id = t.id
        WHERE e.data_registro::date BETWEEN %s AND %s
        GROUP BY t.descricao
        ORDER BY t.descricao
        """

        cur.execute(sql, (data_inicio, data_fim))
        dados = cur.fetchall()

        cur.close()
        conn.close()

        return dados

    except Exception:
        conn.close()
        return []




    










