import psycopg2
import streamlit as st
from dotenv import load_dotenv
load_dotenv()


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

def gerar_notas_fiscais_mes(data_inicio, data_fim, competencia):
    """
    Gera notas fiscais do mês (uma por paciente) com total e dados do pagador.
    """
    conn = get_connection()
    if conn is None:
        return 0

    try:
        cur = conn.cursor()

        sql = """
        INSERT INTO nota_fiscal (
            paciente_id,
            competencia,
            total,
            pagador_nome,
            pagador_cpf
        )
        SELECT
            p.id,
            %s AS competencia,
            SUM(COALESCE(e.valor_cobrado, t.valor)) AS total,
            CASE
                WHEN COALESCE(p.pagador_mesmo_paciente, TRUE) THEN p.nome
                ELSE COALESCE(NULLIF(p.pagador_nome, ''), p.nome)
            END AS pagador_nome,
            CASE
                WHEN COALESCE(p.pagador_mesmo_paciente, TRUE) THEN p.cpf
                ELSE COALESCE(NULLIF(p.pagador_cpf, ''), p.cpf)
            END AS pagador_cpf
        FROM paciente p
        JOIN evolucao e ON e.paciente_id = p.id
        JOIN tipo_atendimento t ON e.tipo_atendimento_id = t.id
        WHERE p.solicita_nota = TRUE
          AND e.data_registro::date BETWEEN %s AND %s
        GROUP BY p.id,
                 CASE
                     WHEN COALESCE(p.pagador_mesmo_paciente, TRUE) THEN p.nome
                     ELSE COALESCE(NULLIF(p.pagador_nome, ''), p.nome)
                 END,
                 CASE
                     WHEN COALESCE(p.pagador_mesmo_paciente, TRUE) THEN p.cpf
                     ELSE COALESCE(NULLIF(p.pagador_cpf, ''), p.cpf)
                 END
        ON CONFLICT (paciente_id, competencia) DO NOTHING
        """

        cur.execute(sql, (competencia, data_inicio, data_fim))
        inseridos = cur.rowcount

        conn.commit()
        cur.close()
        conn.close()

        return inseridos

    except Exception:
        conn.close()
        return 0


def listar_notas_fiscais_mes(competencia):
    """
    Lista notas fiscais por mês.
    """
    conn = get_connection()
    if conn is None:
        return []

    try:
        cur = conn.cursor()

        sql = """
        SELECT
            nf.id,
            p.nome AS paciente,
            nf.pagador_nome,
            nf.pagador_cpf,
            nf.total,
            nf.status,
            nf.competencia
        FROM nota_fiscal nf
        JOIN paciente p ON nf.paciente_id = p.id
        WHERE nf.competencia = %s
        ORDER BY p.nome
        """

        cur.execute(sql, (competencia,))
        dados = cur.fetchall()

        cur.close()
        conn.close()

        return dados

    except Exception:
        conn.close()
        return []

def definir_pagador_nf(paciente_id, competencia, data_inicio, data_fim,
                       pagador_mesmo_paciente, pagador_nome, pagador_cpf):
    """
    Define/atualiza pagador da NF do mês para um paciente.
    Cria a NF do mês se necessário.
    """
    conn = get_connection()
    if conn is None:
        return False

    try:
        cur = conn.cursor()

        sql = """
        INSERT INTO nota_fiscal (
            paciente_id,
            competencia,
            total,
            pagador_nome,
            pagador_cpf
        )
        SELECT
            p.id,
            %s AS competencia,
            COALESCE(SUM(COALESCE(e.valor_cobrado, t.valor)), 0) AS total,
            CASE
                WHEN %s THEN p.nome
                ELSE %s
            END AS pagador_nome,
            CASE
                WHEN %s THEN p.cpf
                ELSE %s
            END AS pagador_cpf
        FROM paciente p
        LEFT JOIN evolucao e
            ON e.paciente_id = p.id
            AND e.data_registro::date BETWEEN %s AND %s
        LEFT JOIN tipo_atendimento t
            ON e.tipo_atendimento_id = t.id
        WHERE p.id = %s
        GROUP BY p.id, p.nome, p.cpf
        HAVING COUNT(e.id) > 0
        ON CONFLICT (paciente_id, competencia) DO UPDATE
        SET pagador_nome = EXCLUDED.pagador_nome,
            pagador_cpf = EXCLUDED.pagador_cpf,
            total = EXCLUDED.total
        """

        cur.execute(sql, (
            competencia,
            pagador_mesmo_paciente,
            pagador_nome,
            pagador_mesmo_paciente,
            pagador_cpf,
            data_inicio,
            data_fim,
            paciente_id
        ))

        afetados = cur.rowcount

        conn.commit()
        cur.close()
        conn.close()

        return afetados

    except Exception as e:
        conn.close()
        return str(e)


def buscar_pagador_paciente(paciente_id):
    """
    Retorna dados do pagador padrão do paciente.
    """
    conn = get_connection()
    if conn is None:
        return None

    try:
        cur = conn.cursor()

        sql = """
        SELECT
            nome,
            cpf,
            COALESCE(pagador_mesmo_paciente, TRUE) AS pagador_mesmo_paciente,
            pagador_nome,
            pagador_cpf
        FROM paciente
        WHERE id = %s
        """

        cur.execute(sql, (paciente_id,))
        dados = cur.fetchone()

        cur.close()
        conn.close()

        return dados

    except Exception:
        conn.close()
        return None


def atualizar_pagador_paciente(paciente_id, pagador_mesmo_paciente, pagador_nome, pagador_cpf):
    """
    Atualiza o pagador padrão do paciente.
    """
    conn = get_connection()
    if conn is None:
        return False

    try:
        cur = conn.cursor()

        sql = """
        UPDATE paciente
        SET pagador_mesmo_paciente = %s,
            pagador_nome = %s,
            pagador_cpf = %s
        WHERE id = %s
        """

        cur.execute(sql, (
            pagador_mesmo_paciente,
            pagador_nome,
            pagador_cpf,
            paciente_id
        ))
        conn.commit()

        cur.close()
        conn.close()

        return True

    except Exception as e:
        conn.close()
        return str(e)


def listar_evolucoes_financeiro(filtro, data_inicio, data_fim):
    conn = get_connection()
    if conn is None:
        return []

    try:
        cur = conn.cursor()

        sql = '''
        SELECT
            e.id,
            e.paciente_id,
            p.nome,
            p.cpf,
            e.data_registro,
            t.descricao,
            COALESCE(e.valor_cobrado, t.valor) AS valor
        FROM evolucao e
        JOIN paciente p ON e.paciente_id = p.id
        JOIN tipo_atendimento t ON e.tipo_atendimento_id = t.id
        WHERE (p.nome ILIKE %s OR p.cpf ILIKE %s)
          AND e.data_registro::date BETWEEN %s AND %s
        ORDER BY e.data_registro DESC
        '''

        cur.execute(sql, (f"%{filtro}%", f"%{filtro}%", data_inicio, data_fim))
        dados = cur.fetchall()

        cur.close()
        conn.close()

        return dados

    except Exception:
        conn.close()
        return []




def listar_evolucoes_pendentes_pagamento(filtro, data_inicio, data_fim):
    conn = get_connection()
    if conn is None:
        return []

    try:
        cur = conn.cursor()

        sql = '''
        SELECT
            e.id,
            e.paciente_id,
            p.nome,
            p.cpf,
            e.data_registro,
            t.descricao,
            COALESCE(e.valor_cobrado, t.valor) AS valor
        FROM evolucao e
        JOIN paciente p ON e.paciente_id = p.id
        JOIN tipo_atendimento t ON e.tipo_atendimento_id = t.id
        LEFT JOIN pagamento pg
            ON pg.atendimento_id = e.id
            AND pg.status = 'pago'
        WHERE (p.nome ILIKE %s OR p.cpf ILIKE %s)
          AND e.data_registro::date BETWEEN %s AND %s
          AND pg.id IS NULL
        ORDER BY e.data_registro DESC
        '''

        cur.execute(sql, (f"%{filtro}%", f"%{filtro}%", data_inicio, data_fim))
        dados = cur.fetchall()

        cur.close()
        conn.close()

        return dados

    except Exception:
        conn.close()
        return []



def listar_evolucoes_pagamentos_paciente(paciente_id, data_inicio, data_fim):
    conn = get_connection()
    if conn is None:
        return []

    try:
        cur = conn.cursor()

        sql = '''
        SELECT
            e.id,
            e.data_registro,
            t.descricao,
            COALESCE(e.valor_cobrado, t.valor) AS valor,
            pg.status,
            pg.data_pagamento
        FROM evolucao e
        JOIN tipo_atendimento t ON e.tipo_atendimento_id = t.id
        LEFT JOIN LATERAL (
            SELECT pg.status, pg.data_pagamento
            FROM pagamento pg
            WHERE pg.atendimento_id = e.id
            ORDER BY pg.data_pagamento DESC NULLS LAST, pg.id DESC
            LIMIT 1
        ) pg ON TRUE
        WHERE e.paciente_id = %s
          AND e.data_registro::date BETWEEN %s AND %s
        ORDER BY e.data_registro DESC
        '''

        cur.execute(sql, (paciente_id, data_inicio, data_fim))
        dados = cur.fetchall()

        cur.close()
        conn.close()

        return dados

    except Exception:
        conn.close()
        return []

def inserir_pagamento(paciente_id, atendimento_id, data_pagamento, valor, forma_pagamento, status):
    conn = get_connection()
    if conn is None:
        return False

    try:
        cur = conn.cursor()

        sql = '''
        INSERT INTO pagamento (
            paciente_id,
            atendimento_id,
            data_pagamento,
            valor,
            forma_pagamento,
            status
        ) VALUES (%s, %s, %s, %s, %s, %s)
        '''

        cur.execute(sql, (
            paciente_id,
            atendimento_id,
            data_pagamento,
            valor,
            forma_pagamento,
            status
        ))
        conn.commit()

        cur.close()
        conn.close()

        return True

    except Exception as e:
        conn.close()
        return str(e)


def listar_pagamentos(filtro, data_inicio, data_fim, status, forma_pagamento):
    conn = get_connection()
    if conn is None:
        return []

    try:
        cur = conn.cursor()

        sql = '''
        SELECT
            pg.id,
            p.nome,
            p.cpf,
            e.data_registro,
            pg.data_pagamento,
            pg.valor,
            pg.forma_pagamento,
            pg.status
        FROM pagamento pg
        JOIN paciente p ON pg.paciente_id = p.id
        JOIN evolucao e ON pg.atendimento_id = e.id
        WHERE (p.nome ILIKE %s OR p.cpf ILIKE %s)
          AND pg.data_pagamento BETWEEN %s AND %s
          AND (%s = 'TODOS' OR pg.status = %s)
          AND (%s = 'TODOS' OR pg.forma_pagamento = %s)
        ORDER BY pg.data_pagamento DESC
        '''

        cur.execute(sql, (
            f"%{filtro}%",
            f"%{filtro}%",
            data_inicio,
            data_fim,
            status,
            status,
            forma_pagamento,
            forma_pagamento
        ))
        dados = cur.fetchall()

        cur.close()
        conn.close()

        return dados

    except Exception:
        conn.close()
        return []


def inserir_despesa(data, descricao, categoria, valor, tipo, recorrente):
    conn = get_connection()
    if conn is None:
        return False

    try:
        cur = conn.cursor()

        sql = '''
        INSERT INTO despesa (
            data,
            descricao,
            categoria,
            valor,
            tipo,
            recorrente
        ) VALUES (%s, %s, %s, %s, %s, %s)
        '''

        cur.execute(sql, (data, descricao, categoria, valor, tipo, recorrente))
        conn.commit()

        cur.close()
        conn.close()

        return True

    except Exception as e:
        conn.close()
        return str(e)


def listar_despesas(data_inicio, data_fim, categoria, tipo):
    conn = get_connection()
    if conn is None:
        return []

    try:
        cur = conn.cursor()

        sql = '''
        SELECT
            id,
            data,
            descricao,
            categoria,
            valor,
            tipo,
            recorrente
        FROM despesa
        WHERE data BETWEEN %s AND %s
          AND (%s = 'TODOS' OR categoria = %s)
          AND (%s = 'TODOS' OR tipo = %s)
        ORDER BY data DESC
        '''

        cur.execute(sql, (
            data_inicio,
            data_fim,
            categoria,
            categoria,
            tipo,
            tipo
        ))
        dados = cur.fetchall()

        cur.close()
        conn.close()

        return dados

    except Exception:
        conn.close()
        return []


def inserir_profissional(nome, cpf, crefito, telefone, endereco, tipo_contrato, valor_repasse_fixo, ativo):
    conn = get_connection()
    if conn is None:
        return False

    try:
        cur = conn.cursor()

        sql = '''
        INSERT INTO profissional (
            nome,
            cpf,
            crefito,
            telefone,
            endereco,
            tipo_contrato,
            valor_repasse_fixo,
            ativo
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        '''

        cur.execute(sql, (nome, cpf, crefito, telefone, endereco, tipo_contrato, valor_repasse_fixo, ativo))
        conn.commit()

        cur.close()
        conn.close()

        return True

    except Exception as e:
        conn.close()
        return str(e)


def listar_profissionais(ativos_only):
    conn = get_connection()
    if conn is None:
        return []

    try:
        cur = conn.cursor()

        if ativos_only:
            sql = '''
            SELECT id, nome, tipo_contrato, valor_repasse_fixo, ativo, cpf, crefito, telefone, endereco
            FROM profissional
            WHERE ativo = TRUE
            ORDER BY nome
            '''
            cur.execute(sql)
        else:
            sql = '''
            SELECT id, nome, tipo_contrato, valor_repasse_fixo, ativo, cpf, crefito, telefone, endereco
            FROM profissional
            ORDER BY nome
            '''
            cur.execute(sql)

        dados = cur.fetchall()

        cur.close()
        conn.close()

        return dados

    except Exception:
        conn.close()
        return []




def deletar_despesa(despesa_id):
    conn = get_connection()
    if conn is None:
        return False

    try:
        cur = conn.cursor()

        sql = '''
        DELETE FROM despesa
        WHERE id = %s
        '''

        cur.execute(sql, (despesa_id,))
        afetados = cur.rowcount
        conn.commit()

        cur.close()
        conn.close()

        return afetados

    except Exception as e:
        conn.close()
        return str(e)

def inserir_repasse_profissional(profissional_id, atendimento_id, valor, data_repasse, status):
    conn = get_connection()
    if conn is None:
        return False

    try:
        cur = conn.cursor()

        sql = '''
        INSERT INTO repasse_profissional (
            profissional_id,
            atendimento_id,
            valor,
            data_repasse,
            status
        ) VALUES (%s, %s, %s, %s, %s)
        '''

        cur.execute(sql, (profissional_id, atendimento_id, valor, data_repasse, status))
        conn.commit()

        cur.close()
        conn.close()

        return True

    except Exception as e:
        conn.close()
        return str(e)


def listar_repasses(data_inicio, data_fim, status, profissional_id):
    conn = get_connection()
    if conn is None:
        return []

    try:
        cur = conn.cursor()

        sql = '''
        SELECT
            rp.id,
            pr.nome AS profissional,
            p.nome AS paciente,
            e.data_registro,
            rp.data_repasse,
            rp.valor,
            rp.status
        FROM repasse_profissional rp
        JOIN profissional pr ON rp.profissional_id = pr.id
        JOIN evolucao e ON rp.atendimento_id = e.id
        JOIN paciente p ON e.paciente_id = p.id
        WHERE rp.data_repasse BETWEEN %s AND %s
          AND (%s = 'TODOS' OR rp.status = %s)
          AND (%s = 0 OR rp.profissional_id = %s)
        ORDER BY rp.data_repasse DESC
        '''

        cur.execute(sql, (
            data_inicio,
            data_fim,
            status,
            status,
            profissional_id,
            profissional_id
        ))
        dados = cur.fetchall()

        cur.close()
        conn.close()

        return dados

    except Exception:
        conn.close()
        return []


def resumo_financeiro(data_inicio, data_fim):
    conn = get_connection()
    if conn is None:
        return None

    try:
        cur = conn.cursor()

        cur.execute(
            '''
            SELECT status, COALESCE(SUM(valor), 0)
            FROM pagamento
            WHERE data_pagamento BETWEEN %s AND %s
            GROUP BY status
            ''',
            (data_inicio, data_fim)
        )
        pagamentos = {row[0]: float(row[1]) for row in cur.fetchall()}

        cur.execute(
            '''
            SELECT COALESCE(SUM(valor), 0)
            FROM despesa
            WHERE data BETWEEN %s AND %s
            ''',
            (data_inicio, data_fim)
        )
        despesas_total = float(cur.fetchone()[0] or 0)

        cur.execute(
            '''
            SELECT status, COALESCE(SUM(valor), 0)
            FROM repasse_profissional
            WHERE data_repasse BETWEEN %s AND %s
            GROUP BY status
            ''',
            (data_inicio, data_fim)
        )
        repasses = {row[0]: float(row[1]) for row in cur.fetchall()}

        cur.close()
        conn.close()

        return {
            "pagamentos": pagamentos,
            "despesas_total": despesas_total,
            "repasses": repasses
        }

    except Exception:
        conn.close()
        return None



def financeiro_receita_mensal(data_inicio, data_fim):
    conn = get_connection()
    if conn is None:
        return []

    try:
        cur = conn.cursor()

        sql = '''
        SELECT
            date_trunc('month', pg.data_pagamento)::date AS mes,
            SUM(pg.valor) AS total
        FROM pagamento pg
        WHERE pg.status = 'pago'
          AND pg.data_pagamento BETWEEN %s AND %s
        GROUP BY mes
        ORDER BY mes
        '''

        cur.execute(sql, (data_inicio, data_fim))
        dados = cur.fetchall()

        cur.close()
        conn.close()

        return dados

    except Exception:
        conn.close()
        return []


def financeiro_despesa_mensal(data_inicio, data_fim):
    conn = get_connection()
    if conn is None:
        return []

    try:
        cur = conn.cursor()

        sql = '''
        SELECT
            date_trunc('month', d.data)::date AS mes,
            SUM(d.valor) AS total
        FROM despesa d
        WHERE d.data BETWEEN %s AND %s
        GROUP BY mes
        ORDER BY mes
        '''

        cur.execute(sql, (data_inicio, data_fim))
        dados = cur.fetchall()

        cur.close()
        conn.close()

        return dados

    except Exception:
        conn.close()
        return []


def financeiro_pagamentos_por_status(data_inicio, data_fim):
    conn = get_connection()
    if conn is None:
        return []

    try:
        cur = conn.cursor()

        sql = '''
        SELECT
            pg.status,
            SUM(pg.valor) AS total
        FROM pagamento pg
        WHERE pg.data_pagamento BETWEEN %s AND %s
        GROUP BY pg.status
        ORDER BY pg.status
        '''

        cur.execute(sql, (data_inicio, data_fim))
        dados = cur.fetchall()

        cur.close()
        conn.close()

        return dados

    except Exception:
        conn.close()
        return []


def financeiro_receita_por_profissional(data_inicio, data_fim):
    conn = get_connection()
    if conn is None:
        return []

    try:
        cur = conn.cursor()

        sql = '''
        SELECT
            COALESCE(NULLIF(e.profissional, ''), 'Não informado') AS profissional,
            SUM(pg.valor) AS total
        FROM pagamento pg
        JOIN evolucao e ON pg.atendimento_id = e.id
        WHERE pg.status = 'pago'
          AND pg.data_pagamento BETWEEN %s AND %s
        GROUP BY profissional
        ORDER BY total DESC
        '''

        cur.execute(sql, (data_inicio, data_fim))
        dados = cur.fetchall()

        cur.close()
        conn.close()

        return dados

    except Exception:
        conn.close()
        return []


def financeiro_receita_por_tipo_atendimento(data_inicio, data_fim):
    conn = get_connection()
    if conn is None:
        return []

    try:
        cur = conn.cursor()

        sql = '''
        SELECT
            t.descricao AS tipo,
            SUM(pg.valor) AS total
        FROM pagamento pg
        JOIN evolucao e ON pg.atendimento_id = e.id
        JOIN tipo_atendimento t ON e.tipo_atendimento_id = t.id
        WHERE pg.status = 'pago'
          AND pg.data_pagamento BETWEEN %s AND %s
        GROUP BY t.descricao
        ORDER BY total DESC
        '''

        cur.execute(sql, (data_inicio, data_fim))
        dados = cur.fetchall()

        cur.close()
        conn.close()

        return dados

    except Exception:
        conn.close()
        return []


def financeiro_repasse_mensal(data_inicio, data_fim):
    conn = get_connection()
    if conn is None:
        return []

    try:
        cur = conn.cursor()

        sql = '''
        SELECT
            date_trunc('month', rp.data_repasse)::date AS mes,
            SUM(rp.valor) AS total
        FROM repasse_profissional rp
        WHERE rp.status <> 'cancelado'
          AND rp.data_repasse BETWEEN %s AND %s
        GROUP BY mes
        ORDER BY mes
        '''

        cur.execute(sql, (data_inicio, data_fim))
        dados = cur.fetchall()

        cur.close()
        conn.close()

        return dados

    except Exception:
        conn.close()
        return []
