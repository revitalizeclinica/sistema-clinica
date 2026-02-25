import calendar
import io
import re
import zipfile
from datetime import date

import streamlit as st

from database import (
    get_connection,
    inserir_paciente,
    listar_pacientes,
    inserir_evolucao,
    listar_tipos_atendimento_com_valor,
    listar_evolucoes_por_paciente,
    inserir_avaliacao_clinica,
    inserir_avaliacao_inicial,
    listar_avaliacoes_clinicas,
    buscar_avaliacao_clinica,
    buscar_avaliacao_inicial,
    relatorio_paciente_agrupado,
    relatorio_paciente_detalhado,
    relatorio_contador,
    atualizar_preco_tipo_atendimento,
    relatorio_geral_resumo,
    relatorio_geral_por_tipo,
    listar_notas_fiscais_mes,
    definir_pagador_nf,
    buscar_pagador_paciente,
    atualizar_pagador_paciente,
    listar_evolucoes_financeiro,
    listar_evolucoes_pendentes_pagamento,
    listar_evolucoes_pagamentos_paciente,
    inserir_pagamento,
    listar_pagamentos,
    inserir_despesa,
    listar_despesas,
    deletar_despesa,
    inserir_profissional,
    atualizar_profissional,
    listar_profissionais,
    inserir_repasse_profissional,
    listar_repasses,
    resumo_financeiro,
    relatorio_profissional_consultas,
    financeiro_receita_mensal,
    financeiro_despesa_mensal,
    financeiro_pagamentos_por_status,
    financeiro_receita_por_profissional,
    financeiro_receita_por_tipo_atendimento,
    financeiro_repasse_mensal
)
from pdf_utils import gerar_pdf_relatorio_paciente, gerar_pdf_relatorio_profissional
from utils import mask_cpf, mask_email, mask_nome, mask_phone, only_digits


def _botao_voltar_inicio(key):
    if st.button("Voltar para Início", key=key):
        st.session_state.nav_to = "Início"
        st.rerun()


def _mes_range(mes_ref):
    data_inicio = date(mes_ref.year, mes_ref.month, 1)
    ultimo_dia = calendar.monthrange(mes_ref.year, mes_ref.month)[1]
    data_fim = date(mes_ref.year, mes_ref.month, ultimo_dia)
    return data_inicio, data_fim

def _shift_month(data_ref, months):
    ano = data_ref.year + (data_ref.month - 1 + months) // 12
    mes = (data_ref.month - 1 + months) % 12 + 1
    dia = min(data_ref.day, calendar.monthrange(ano, mes)[1])
    return date(ano, mes, dia)


def _month_list(data_inicio, data_fim):
    meses = []
    atual = date(data_inicio.year, data_inicio.month, 1)
    fim = date(data_fim.year, data_fim.month, 1)
    while atual <= fim:
        meses.append(atual)
        atual = _shift_month(atual, 1)
    return meses




def _safe_filename(value):
    if not value:
        return "paciente"
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", value.strip())
    return cleaned.strip("_") or "paciente"



STATUS_PAGAMENTO_OPCOES = ["pago", "pendente", "atrasado", "cancelado"]
STATUS_REPASSE_OPCOES = ["pendente", "pago", "cancelado"]
FORMA_PAGAMENTO_OPCOES = ["pix", "dinheiro", "transferencia", "cartao", "boleto", "outro"]
DESPESA_TIPO_OPCOES = ["fixa", "variavel"]
DESPESA_CATEGORIA_OPCOES = [
    "combustivel",
    "transporte",
    "material",
    "imposto",
    "repasse_profissional",
    "marketing",
    "sistema",
    "outros"
]

def render_inicio():
    st.markdown(
        "<h1 style='text-align:center; margin-bottom: 0;'>Clínica Revitalize</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<h3 style='text-align:center; margin-top: 0;'>Bem vindo ao sistema.</h3>",
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("assets/logo.png", use_container_width=True)

    conn = get_connection()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if conn:
            st.success("Conectado com sucesso ao Supabase!")
            conn.close()
        else:
            st.error("Falha na conexão com o banco.")


def render_cadastrar_paciente():
    st.subheader("Cadastro de Paciente")

    if st.session_state.mensagem_sucesso:
        st.success(st.session_state.mensagem_sucesso)
        st.session_state.mensagem_sucesso = ""

    form_key = st.session_state.form_key

    nome = st.text_input("Nome completo", key=f"nome_{form_key}")
    cpf = st.text_input("CPF", key=f"cpf_{form_key}")
    data_nascimento = st.date_input(
        "Data de nascimento",
        min_value=date(1900, 1, 1),
        max_value=date.today(),
        format="DD/MM/YYYY",
        key=f"data_nascimento_{form_key}"
    )
    telefone = st.text_input("Telefone", key=f"telefone_{form_key}")
    email = st.text_input("Email", key=f"email_{form_key}")
    contato_emergencia = st.text_input("Contato de emergência", key=f"contato_{form_key}")
    observacoes = st.text_area("Observações", key=f"observacoes_{form_key}")

    solicita_nota = st.checkbox("Solicita nota fiscal?", key=f"solicita_nota_{form_key}")

    pagador_mesmo_paciente = True
    pagador_nome = ""
    pagador_cpf = ""

    if solicita_nota:
        pagador_mesmo_paciente = st.checkbox(
            "Pagador é o paciente?",
            value=True,
            key=f"pagador_mesmo_{form_key}"
        )
        if not pagador_mesmo_paciente:
            st.markdown("**Dados do pagador**")
            pagador_nome = st.text_input("Nome do pagador", key=f"pagador_nome_{form_key}")
            pagador_cpf = st.text_input("CPF do pagador", key=f"pagador_cpf_{form_key}")

    enviado = st.button("Salvar", key=f"salvar_paciente_{form_key}")

    if enviado:
        cpf_digits = only_digits(cpf)
        if not nome:
            st.error("Nome é obrigatório!")
        elif not cpf:
            st.error("CPF é obrigatório!")
        elif len(cpf_digits) != 11:
            st.error("CPF deve ter 11 dígitos.")
        else:
            pagador_cpf_digits = only_digits(pagador_cpf)

            if solicita_nota and not pagador_mesmo_paciente:
                if not pagador_nome:
                    st.error("Nome do pagador é obrigatório.")
                    st.stop()
                if not pagador_cpf:
                    st.error("CPF do pagador é obrigatório.")
                    st.stop()
                if len(pagador_cpf_digits) != 11:
                    st.error("CPF do pagador deve ter 11 dígitos.")
                    st.stop()

            if not solicita_nota:
                pagador_mesmo_paciente = True
                pagador_nome = None
                pagador_cpf_digits = None
            elif pagador_mesmo_paciente:
                pagador_nome = None
                pagador_cpf_digits = None

            resultado = inserir_paciente(
                nome, cpf_digits, data_nascimento,
                telefone, email, contato_emergencia, observacoes, solicita_nota,
                pagador_mesmo_paciente,
                pagador_nome if pagador_nome else None,
                pagador_cpf_digits if pagador_cpf_digits else None
            )

            if resultado is True:
                st.session_state.form_key += 1
                st.session_state.mensagem_sucesso = "Paciente cadastrado com sucesso!"
                st.rerun()
            else:
                st.error(f"Erro ao salvar: {resultado}")


def render_listar_pacientes():
    st.subheader("Pacientes Cadastrados")

    if "listar_pacientes_filtro" not in st.session_state:
        st.session_state.listar_pacientes_filtro = ""
    if "listar_pacientes_dados" not in st.session_state:
        st.session_state.listar_pacientes_dados = []
    if "listar_pacientes_busca_feita" not in st.session_state:
        st.session_state.listar_pacientes_busca_feita = False

    with st.form("listar_pacientes_form"):
        filtro = st.text_input(
            "Buscar por nome ou CPF",
            value=st.session_state.listar_pacientes_filtro,
            key="listar_pacientes_filtro_input"
        )
        st.caption("Digite parte do nome ou CPF para filtrar")
        buscar = st.form_submit_button("Buscar")

    if buscar:
        st.session_state.listar_pacientes_filtro = filtro
        st.session_state.listar_pacientes_dados = listar_pacientes(filtro)
        st.session_state.listar_pacientes_busca_feita = True

    pacientes = st.session_state.listar_pacientes_dados

    if not pacientes:
        if st.session_state.listar_pacientes_busca_feita:
            st.info("Nenhum paciente encontrado.")
        else:
            st.info("Faça uma busca para listar pacientes.")
    else:
        import pandas as pd

        dados = []
        for p in pacientes:
            dados.append([
                p[0],
                mask_nome(p[1]),
                mask_cpf(p[2]),
                p[3],
                mask_phone(p[4]),
                mask_email(p[5])
            ])

        df = pd.DataFrame(
            dados,
            columns=["ID", "Nome", "CPF", "Nascimento", "Telefone", "Email"]
        )

        st.dataframe(df, use_container_width=True)


def render_nova_evolucao():
    st.subheader("Avaliação / Evolução diária")

    if "nova_evo_pacientes" not in st.session_state:
        st.session_state.nova_evo_pacientes = []
    if "nova_evo_filtro" not in st.session_state:
        st.session_state.nova_evo_filtro = ""
    if "nova_evo_busca_feita" not in st.session_state:
        st.session_state.nova_evo_busca_feita = False

    with st.form("form_busca_paciente"):
        filtro = st.text_input(
            "Buscar paciente por nome ou CPF",
            value=st.session_state.nova_evo_filtro,
            key="nova_evo_filtro_input"
        )
        buscar = st.form_submit_button("Buscar")

    if buscar:
        st.session_state.nova_evo_filtro = filtro
        st.session_state.nova_evo_pacientes = listar_pacientes(filtro)
        st.session_state.nova_evo_busca_feita = True

    pacientes = st.session_state.nova_evo_pacientes

    if not pacientes:
        if st.session_state.nova_evo_busca_feita:
            st.info("Nenhum paciente encontrado.")
        else:
            st.info("Faça uma busca para selecionar o paciente.")
        return

    opcoes = [f"{p[0]} - {p[1]} (CPF: {mask_cpf(p[2])})" for p in pacientes]
    escolha = st.selectbox("Selecione o paciente", opcoes, key="nova_evo_paciente_select")
    paciente_id = int(escolha.split(" - ")[0])

    with st.form("form_evolucao", clear_on_submit=True):
        data_registro = st.date_input("Data do atendimento")

        profissionais = listar_profissionais(True)
        if not profissionais:
            st.error("Cadastre um profissional ativo no Financeiro para continuar.")
            st.stop()

        op_prof = ["Selecione o profissional"] + [f"{p[0]} - {p[1]}" for p in profissionais]
        escolha_prof = st.selectbox("Profissional responsável", op_prof, index=0)
        profissional = None
        if escolha_prof != op_prof[0]:
            profissional = escolha_prof.split(" - ", 1)[1]

        tipos = listar_tipos_atendimento_com_valor()

        if not tipos:
            st.info("Nenhum tipo de atendimento cadastrado.")
            st.stop()

        opcoes = ["Selecione o tipo de atendimento"] + [
            f"{t[0]} - {t[2]} (R$ {t[3]:.2f})" for t in tipos
        ]
        tipo_escolhido = st.selectbox("Tipo de atendimento", opcoes)

        tipo_id = None
        valor_cobrado = None
        if tipo_escolhido != opcoes[0]:
            tipo_id = int(tipo_escolhido.split(" - ")[0])
            tipo_dict = {t[0]: t for t in tipos}
            valor_cobrado = float(tipo_dict[tipo_id][3])

        queixas = st.text_area("Queixas")
        condutas = st.text_area("Condutas")
        resposta = st.text_area("Respostas")

        enviado = st.form_submit_button("Salvar atendimento")

        if enviado:
            if not profissional:
                st.error("Selecione o profissional.")
            elif tipo_id is None:
                st.error("Selecione o tipo de atendimento.")
            elif valor_cobrado is None:
                st.error("Valor do atendimento não encontrado.")
            else:
                resultado = inserir_evolucao(
                    paciente_id,
                    tipo_id,
                    data_registro,
                    profissional,
                    queixas,
                    condutas,
                    resposta,
                    "",
                    "",
                    valor_cobrado
                )

                if resultado is True:
                    st.success("Atendimento registrado com sucesso!")
                else:
                    st.error(f"Erro ao salvar: {resultado}")


def render_historico_paciente():
    st.subheader("Histórico de Evoluções")

    if "evolucao_aberta" not in st.session_state:
        st.session_state.evolucao_aberta = None
    if "historico_paciente_id" not in st.session_state:
        st.session_state.historico_paciente_id = None

    if "historico_pacientes" not in st.session_state:
        st.session_state.historico_pacientes = []
    if "historico_filtro" not in st.session_state:
        st.session_state.historico_filtro = ""
    if "historico_busca_feita" not in st.session_state:
        st.session_state.historico_busca_feita = False

    with st.form("historico_busca_form"):
        filtro = st.text_input(
            "Buscar paciente por nome ou CPF",
            value=st.session_state.historico_filtro,
            key="historico_filtro_input"
        )
        buscar = st.form_submit_button("Buscar")

    if buscar:
        st.session_state.historico_filtro = filtro
        st.session_state.historico_pacientes = listar_pacientes(filtro)
        st.session_state.historico_busca_feita = True

    pacientes = st.session_state.historico_pacientes

    if not pacientes:
        if st.session_state.historico_busca_feita:
            st.info("Nenhum paciente encontrado.")
        else:
            st.info("Faça uma busca para selecionar o paciente.")
        return
    else:
        opcoes = [f"{p[0]} - {p[1]} (CPF: {mask_cpf(p[2])})" for p in pacientes]
        escolha = st.selectbox("Selecione o paciente", opcoes)
        paciente_id = int(escolha.split(" - ")[0])

        if st.session_state.historico_paciente_id != paciente_id:
            st.session_state.evolucao_aberta = None
            st.session_state.historico_paciente_id = paciente_id

        st.write(f"**Paciente selecionado:** {escolha}")
        evolucoes = listar_evolucoes_por_paciente(paciente_id)

        if not evolucoes:
            st.info("Nenhuma evolução registrada para este paciente.")
        else:
            st.write("### Registros")

            for e in evolucoes:
                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    st.write(f"**Data:** {e[1]}")
                    st.write(f"**Tipo:** {e[3]}")

                with col2:
                    st.write(f"**Profissional:** {e[2]}")

                with col3:
                    if st.button("Abrir", key=f"abrir_{e[0]}"):
                        st.session_state.evolucao_aberta = e

        if st.session_state.evolucao_aberta:
            st.markdown("---")
            st.subheader("Detalhes do Atendimento")

            detalhe = st.session_state.evolucao_aberta

            st.write(f"**Data:** {detalhe[1]}")
            st.write(f"**Profissional:** {detalhe[2]}")

            def exibir_titulo_valor(titulo, valor):
                st.write(f"### {titulo}")
                st.write(valor if valor else "Não informado")

            exibir_titulo_valor("Queixas", detalhe[3])
            exibir_titulo_valor("Condutas", detalhe[4])
            exibir_titulo_valor("Respostas", detalhe[5])
            exibir_titulo_valor("Objetivos", detalhe[6])
            exibir_titulo_valor("Observações", detalhe[7])


def render_avaliacao_clinica():
    st.subheader("Avaliação Clínica")
    st.caption("Nesta fase o sistema apenas armazena os valores digitados, sem cálculo automático.")

    if "avaliacao_clinica_form_ativo" not in st.session_state:
        st.session_state.avaliacao_clinica_form_ativo = False
    if "avaliacao_clinica_selecionado_id" not in st.session_state:
        st.session_state.avaliacao_clinica_selecionado_id = None
    if "avaliacao_clinica_aberta_id" not in st.session_state:
        st.session_state.avaliacao_clinica_aberta_id = None

    if "avaliacao_clinica_pacientes" not in st.session_state:
        st.session_state.avaliacao_clinica_pacientes = []
    if "avaliacao_clinica_filtro" not in st.session_state:
        st.session_state.avaliacao_clinica_filtro = ""
    if "avaliacao_clinica_busca_feita" not in st.session_state:
        st.session_state.avaliacao_clinica_busca_feita = False

    with st.form("avaliacao_clinica_busca_form"):
        filtro = st.text_input(
            "Buscar paciente",
            value=st.session_state.avaliacao_clinica_filtro,
            key="avaliacao_clinica_filtro_input"
        )
        buscar = st.form_submit_button("Buscar")

    if buscar:
        st.session_state.avaliacao_clinica_filtro = filtro
        st.session_state.avaliacao_clinica_pacientes = listar_pacientes(filtro)
        st.session_state.avaliacao_clinica_busca_feita = True

    pacientes = st.session_state.avaliacao_clinica_pacientes

    if not pacientes:
        if st.session_state.avaliacao_clinica_busca_feita:
            st.info("Nenhum paciente encontrado.")
        else:
            st.info("Faça uma busca para selecionar o paciente.")
        return

    opcoes = [f"{p[0]} - {p[1]}" for p in pacientes]
    escolha = st.selectbox("Selecione o paciente", opcoes)
    paciente_id = int(escolha.split(" - ")[0])

    if st.session_state.avaliacao_clinica_selecionado_id != paciente_id:
        st.session_state.avaliacao_clinica_form_ativo = False
        st.session_state.avaliacao_clinica_aberta_id = None
        st.session_state.avaliacao_clinica_selecionado_id = paciente_id

    avaliacoes = listar_avaliacoes_clinicas(paciente_id)

    if st.button("Nova avaliação clínica", key=f"nova_avaliacao_{paciente_id}"):
        st.session_state.avaliacao_clinica_form_ativo = True
        st.session_state.avaliacao_clinica_aberta_id = None
        st.rerun()

    if avaliacoes:
        st.markdown("---")
        st.subheader("Avaliações registradas")

        for avaliacao in avaliacoes:
            col1, col2, col3 = st.columns([2, 3, 1])
            with col1:
                st.write(f"**Data:** {avaliacao[1]}")
            with col2:
                st.write(f"**Profissional:** {avaliacao[2] if avaliacao[2] else 'Não informado'}")
            with col3:
                if st.button("Abrir", key=f"abrir_avaliacao_{avaliacao[0]}"):
                    st.session_state.avaliacao_clinica_aberta_id = avaliacao[0]

        if st.session_state.avaliacao_clinica_aberta_id:
            detalhe = buscar_avaliacao_clinica(st.session_state.avaliacao_clinica_aberta_id)
            if detalhe:
                st.markdown("---")
                st.subheader("Detalhes da Avaliação Clínica")

                st.write(f"**Data da avaliação:** {detalhe[2]}")
                st.write(f"**Profissional:** {detalhe[3] if detalhe[3] else 'Não informado'}")

                def mostrar_campo(titulo, valor):
                    st.write(f"### {titulo}")
                    st.write(valor if valor not in (None, "") else "Não informado")

                mostrar_campo("Queixa", detalhe[4])
                mostrar_campo("Diagnóstico", detalhe[5])
                mostrar_campo("Histórico clínico", detalhe[6])
                mostrar_campo("Histórico de vida", detalhe[7])
                mostrar_campo("Medicamentos em uso", detalhe[8])
    else:
        st.info("Este paciente ainda não possui avaliações clínicas.")

    if st.session_state.avaliacao_clinica_form_ativo:
        st.markdown("---")
        st.subheader("Nova Avaliação Clínica")

        with st.form("form_avaliacao_clinica"):
            col1, col2 = st.columns(2)
            with col1:
                data_avaliacao = st.date_input("Data da avaliação", value=date.today())
            with col2:
                profissionais = listar_profissionais(True)
                if not profissionais:
                    st.error("Cadastre um profissional ativo no Financeiro para continuar.")
                    st.stop()

                op_prof = ["Selecione..."] + [f"{p[0]} - {p[1]}" for p in profissionais]
                escolha_prof = st.selectbox("Profissional", op_prof)
                profissional = None if escolha_prof == "Selecione..." else escolha_prof.split(" - ", 1)[1]

            queixa = st.text_area("Queixa")
            diagnostico = st.text_area("Diagnóstico")
            historico_clinico = st.text_area("Histórico clínico")
            historico_vida = st.text_area("Histórico de vida")
            medicamentos_uso = st.text_area("Medicamentos em uso")

            enviado = st.form_submit_button("Salvar avaliação clínica")

        if enviado:
            if not profissional:
                st.error("Selecione o profissional.")
                return

            dados = {
                "data": data_avaliacao,
                "profissional": profissional,
                "queixa": queixa,
                "diagnostico": diagnostico,
                "historico_clinico": historico_clinico,
                "historico_vida": historico_vida,
                "medicamentos_uso": medicamentos_uso
            }

            resultado = inserir_avaliacao_clinica(paciente_id, dados)

            if resultado is True:
                st.success("Avaliação clínica cadastrada com sucesso!")
                st.session_state.avaliacao_clinica_form_ativo = False
                st.rerun()
            else:
                st.error(f"Erro ao salvar: {resultado}")


def render_avaliacao_inicial():
    st.subheader("Avaliação Funcional")

    if "avaliacao_inicial_form_ativo" not in st.session_state:
        st.session_state.avaliacao_inicial_form_ativo = False
    if "avaliacao_inicial_selecionado_id" not in st.session_state:
        st.session_state.avaliacao_inicial_selecionado_id = None

    if "avaliacao_inicial_pacientes" not in st.session_state:
        st.session_state.avaliacao_inicial_pacientes = []
    if "avaliacao_inicial_filtro" not in st.session_state:
        st.session_state.avaliacao_inicial_filtro = ""
    if "avaliacao_inicial_busca_feita" not in st.session_state:
        st.session_state.avaliacao_inicial_busca_feita = False

    with st.form("avaliacao_inicial_busca_form"):
        filtro = st.text_input(
            "Buscar paciente",
            value=st.session_state.avaliacao_inicial_filtro,
            key="avaliacao_inicial_filtro_input"
        )
        buscar = st.form_submit_button("Buscar")

    if buscar:
        st.session_state.avaliacao_inicial_filtro = filtro
        st.session_state.avaliacao_inicial_pacientes = listar_pacientes(filtro)
        st.session_state.avaliacao_inicial_busca_feita = True

    pacientes = st.session_state.avaliacao_inicial_pacientes

    if not pacientes:
        if st.session_state.avaliacao_inicial_busca_feita:
            st.info("Nenhum paciente encontrado.")
        else:
            st.info("Faça uma busca para selecionar o paciente.")
        return
    else:
        opcoes = [f"{p[0]} - {p[1]}" for p in pacientes]
        escolha = st.selectbox("Selecione o paciente", opcoes)
        paciente_id = int(escolha.split(" - ")[0])

        if st.session_state.avaliacao_inicial_selecionado_id != paciente_id:
            st.session_state.avaliacao_inicial_form_ativo = False
            st.session_state.avaliacao_inicial_selecionado_id = paciente_id

        existente = buscar_avaliacao_inicial(paciente_id)

        if existente:
            st.success("Este paciente já possui avaliação funcional cadastrada.")

            st.markdown("---")
            st.subheader("Detalhes da Avaliação Funcional")

            st.write(f"**Data da avaliação:** {existente[2]}")
            st.write(f"**Profissional:** {existente[3]}")

            def mostrar_campo(titulo, valor):
                st.write(f"### {titulo}")
                st.write(valor if valor else "Não informado")

            st.write("### Sinais Vitais")
            mostrar_campo("Pressão arterial sistólica", existente[4])
            mostrar_campo("Pressão arterial diastólica", existente[5])
            mostrar_campo("Frequência cardíaca", existente[6])
            mostrar_campo("SpO2", existente[7])
            mostrar_campo("Ausculta pulmonar", existente[8])

            mostrar_campo("Avaliação da dor (0-10)", existente[9])

            st.write("### Mobilidade")
            mostrar_campo("Grau de dependência", existente[10])
            mostrar_campo("Descrição", existente[11])

            mostrar_campo("Atividades básicas e instrumentais do cotidiano", existente[12])
            mostrar_campo("TUG", existente[13])
            mostrar_campo("Marcha", existente[14])

            st.write("### Avaliação dos Reflexos")
            mostrar_campo("Anteriores", existente[15])
            mostrar_campo("Posteriores", existente[16])
            mostrar_campo("Descrição", existente[17])

            mostrar_campo("Risco de quedas", existente[18])
            mostrar_campo("Equilíbrio", existente[19])
            mostrar_campo("Perimetria de panturrilha", existente[20])

            st.write("### SARC-F")
            mostrar_campo("Força", existente[21])
            mostrar_campo("Ajuda para caminhar", existente[22])
            mostrar_campo("Levantar da cadeira", existente[23])
            mostrar_campo("Subir escadas", existente[24])
            mostrar_campo("Quedas", existente[25])
            mostrar_campo("Panturrilha", existente[26])

            st.write("### Teste de Caminhada 6 Minutos")
            mostrar_campo("Distância", existente[27])
            mostrar_campo("Descrição", existente[28])

            mostrar_campo("Chair stand test", existente[29])
            mostrar_campo("Diagnóstico Cinético Funcional", existente[30])
            mostrar_campo("Plano terapêutico", existente[31])
        else:
            st.info("Este paciente ainda não possui avaliação funcional.")

            if st.button("Habilitar preenchimento", key=f"habilitar_avaliacao_inicial_{paciente_id}"):
                st.session_state.avaliacao_inicial_form_ativo = True
                st.rerun()

            if st.session_state.avaliacao_inicial_form_ativo:
                with st.form("form_avaliacao_inicial"):
                    col1, col2 = st.columns(2)
                    with col1:
                        data_avaliacao = st.date_input("Data da avaliação", value=date.today())
                    with col2:
                        profissionais = listar_profissionais(True)
                        if not profissionais:
                            st.error("Cadastre um profissional ativo no Financeiro para continuar.")
                            st.stop()

                        op_prof = ["Selecione..."] + [f"{p[0]} - {p[1]}" for p in profissionais]
                        escolha_prof = st.selectbox("Profissional", op_prof)
                        profissional = None if escolha_prof == "Selecione..." else escolha_prof.split(" - ", 1)[1]

                    st.write("### Sinais Vitais")
                    pressao_arterial_sistolica = st.text_input("Pressão arterial sistólica")
                    pressao_arterial_diastolica = st.text_input("Pressão arterial diastólica")
                    frequencia_cardiaca = st.text_input("Frequência cardíaca")
                    spo2 = st.text_input("SpO2")
                    ausculta_pulmonar = st.text_input("Ausculta pulmonar")

                    dor = st.number_input("Avaliação da dor (0-10)", min_value=0, max_value=10, step=1)

                    st.write("### Mobilidade")
                    mobilidade_grau_opcoes = ["Selecione...", "Nível 1", "Nível 2", "Nível 3", "Nível 4"]
                    mobilidade_grau = st.selectbox("Grau de dependência", mobilidade_grau_opcoes)
                    mobilidade_descricao = st.text_area("Descrição da mobilidade")

                    atividades = st.text_area("Atividades básicas e instrumentais do cotidiano")
                    tug = st.text_input("TUG")
                    marcha = st.text_area("Marcha")

                    st.write("### Avaliação dos Reflexos")
                    reflexos_opcoes = ["Selecione...", "Preservados", "Ausentes", "Insuficientes"]
                    reflexos_anteriores = st.selectbox("Reflexos anteriores", reflexos_opcoes)
                    reflexos_posteriores = st.selectbox("Reflexos posteriores", reflexos_opcoes)
                    reflexos_descricao = st.text_area("Descrição dos reflexos")

                    risco_quedas_opcoes = ["Selecione...", "Baixo", "Moderado", "Alto", "Sem risco"]
                    risco_quedas = st.selectbox("Risco de quedas", risco_quedas_opcoes)
                    equilibrio = st.text_area("Equilíbrio")
                    perimetria_panturrilha = st.text_input("Perimetria de panturrilha")

                    st.write("### SARC-F")
                    sarc_forca_opcoes = ["Selecione...", "Nenhuma (0)", "Alguma (1)", "Muita ou não consegue (2)"]
                    sarc_forca = st.selectbox("Força - dificuldade para levantar e carregar 5kg", sarc_forca_opcoes)
                    sarc_ajuda_opcoes = ["Selecione...", "Nenhuma (0)", "Alguma (1)", "Muita ou não consegue (2)"]
                    sarc_ajuda = st.selectbox("Ajuda para caminhar - atravessar um cômodo", sarc_ajuda_opcoes)
                    sarc_levantar_opcoes = ["Selecione...", "Nenhuma (0)", "Alguma (1)", "Muita ou não consegue (2)"]
                    sarc_levantar = st.selectbox("Levantar da cadeira - cama ou cadeira", sarc_levantar_opcoes)
                    sarc_escadas_opcoes = ["Selecione...", "Nenhuma (0)", "Alguma (1)", "Muita ou não consegue (2)"]
                    sarc_escadas = st.selectbox("Subir escadas - 10 degraus", sarc_escadas_opcoes)
                    sarc_quedas_opcoes = ["Selecione...", "Nenhuma (0)", "1-3 quedas (1)", "4 ou mais quedas (2)"]
                    sarc_quedas = st.selectbox("Quedas no último ano", sarc_quedas_opcoes)
                    sarc_panturrilha_opcoes = ["Selecione...", ">33 cm (0)", "<=33 cm (10)"]
                    sarc_panturrilha = st.selectbox("Panturrilha (considerando sexo)", sarc_panturrilha_opcoes)

                    st.write("### Teste de Caminhada 6 Minutos")
                    caminhada_6min_distancia = st.text_input("Distância")
                    caminhada_6min_observacao = st.text_area("Descrição do teste")

                    chair_stand_test = st.text_input("Chair stand test")
                    diagnostico_cinetico = st.text_area("Diagnóstico Cinético Funcional")
                    plano = st.text_area("Plano terapêutico")

                    enviado = st.form_submit_button("Salvar avaliação")

                if enviado:
                    if not profissional:
                        st.error("Selecione o profissional.")
                    else:
                        erros = []

                        def parse_float(valor, campo):
                            valor = valor.strip().replace(",", ".")
                            if not valor:
                                return None
                            try:
                                return float(valor)
                            except ValueError:
                                erros.append(f"{campo} deve ser numérico.")
                                return None

                        def map_sarc_opcao(valor, opcoes):
                            if valor == "Selecione...":
                                return None
                            return opcoes.get(valor)

                        sarc_forca_map = {
                            "Nenhuma (0)": 0,
                            "Alguma (1)": 1,
                            "Muita ou não consegue (2)": 2
                        }
                        sarc_ajuda_map = sarc_forca_map
                        sarc_levantar_map = sarc_forca_map
                        sarc_escadas_map = sarc_forca_map
                        sarc_quedas_map = {
                            "Nenhuma (0)": 0,
                            "1-3 quedas (1)": 1,
                            "4 ou mais quedas (2)": 2
                        }
                        sarc_panturrilha_map = {
                            ">33 cm (0)": 0,
                            "<=33 cm (10)": 10
                        }

                        dados = {
                            "data": data_avaliacao,
                            "profissional": profissional,
                            "pressao_arterial_sistolica": parse_float(pressao_arterial_sistolica, "Pressão arterial sistólica"),
                            "pressao_arterial_diastolica": parse_float(pressao_arterial_diastolica, "Pressão arterial diastólica"),
                            "frequencia_cardiaca": parse_float(frequencia_cardiaca, "Frequência cardíaca"),
                            "spo2": parse_float(spo2, "SpO2"),
                            "ausculta_pulmonar": parse_float(ausculta_pulmonar, "Ausculta pulmonar"),
                            "dor": int(dor),
                            "mobilidade_grau": None if mobilidade_grau == "Selecione..." else mobilidade_grau,
                            "mobilidade_descricao": mobilidade_descricao,
                            "atividades": atividades,
                            "tug": parse_float(tug, "TUG"),
                            "marcha": marcha,
                            "reflexos_anteriores": None if reflexos_anteriores == "Selecione..." else reflexos_anteriores,
                            "reflexos_posteriores": None if reflexos_posteriores == "Selecione..." else reflexos_posteriores,
                            "reflexos_descricao": reflexos_descricao,
                            "risco_quedas": None if risco_quedas == "Selecione..." else risco_quedas,
                            "equilibrio": equilibrio,
                            "perimetria_panturrilha": parse_float(perimetria_panturrilha, "Perimetria de panturrilha"),
                            "sarc_f_forca": map_sarc_opcao(sarc_forca, sarc_forca_map),
                            "sarc_f_ajuda_caminhar": map_sarc_opcao(sarc_ajuda, sarc_ajuda_map),
                            "sarc_f_levantar_cadeira": map_sarc_opcao(sarc_levantar, sarc_levantar_map),
                            "sarc_f_subir_escadas": map_sarc_opcao(sarc_escadas, sarc_escadas_map),
                            "sarc_f_quedas": map_sarc_opcao(sarc_quedas, sarc_quedas_map),
                            "sarc_f_panturrilha": map_sarc_opcao(sarc_panturrilha, sarc_panturrilha_map),
                            "caminhada_6min_distancia": parse_float(caminhada_6min_distancia, "Caminhada 6 minutos (distância)"),
                            "caminhada_6min_observacao": caminhada_6min_observacao,
                            "chair_stand_test": parse_float(chair_stand_test, "Chair stand test"),
                            "diagnostico_cinetico": diagnostico_cinetico,
                            "plano": plano
                        }

                        if erros:
                            st.error(" ".join(erros))
                            return

                        resultado = inserir_avaliacao_inicial(paciente_id, dados)

                        if resultado is True:
                            st.success("Avaliação funcional cadastrada com sucesso!")
                            st.session_state.avaliacao_inicial_form_ativo = False
                            st.rerun()
                        else:
                            st.error(f"Erro ao salvar: {resultado}")


def render_relatorio_paciente():
    st.subheader("Relatório por Paciente")

    _botao_voltar_inicio("voltar_rel_paciente")

    if "relatorio_pacientes" not in st.session_state:
        st.session_state.relatorio_pacientes = []
    if "relatorio_filtro" not in st.session_state:
        st.session_state.relatorio_filtro = ""
    if "relatorio_busca_feita" not in st.session_state:
        st.session_state.relatorio_busca_feita = False

    with st.form("relatorio_busca_form"):
        filtro = st.text_input(
            "Buscar paciente por nome ou CPF",
            value=st.session_state.relatorio_filtro,
            key="relatorio_filtro_input"
        )
        buscar = st.form_submit_button("Buscar")

    if buscar:
        st.session_state.relatorio_filtro = filtro
        st.session_state.relatorio_pacientes = listar_pacientes(filtro)
        st.session_state.relatorio_busca_feita = True

    pacientes = st.session_state.relatorio_pacientes

    if not pacientes:
        if st.session_state.relatorio_busca_feita:
            st.info("Nenhum paciente encontrado.")
        else:
            st.info("Faça uma busca para selecionar o paciente.")
        return
    else:
        pacientes_por_id = {p[0]: p[1] for p in pacientes}
        opcoes = ["Todos os pacientes do período"] + [
            f"{p[0]} - {p[1]} (CPF: {mask_cpf(p[2])})" for p in pacientes
        ]
        if "relatorio_paciente_escolha" not in st.session_state:
            st.session_state.relatorio_paciente_escolha = opcoes[0]
        if st.session_state.relatorio_paciente_escolha not in opcoes:
            st.session_state.relatorio_paciente_escolha = opcoes[0]

        escolha = st.selectbox(
            "Selecione o paciente",
            opcoes,
            key="relatorio_paciente_escolha"
        )

        todos_pacientes = escolha == opcoes[0]
        paciente_id = None
        nome_paciente = None
        if not todos_pacientes:
            paciente_id = int(escolha.split(" - ")[0])
            nome_paciente = pacientes_por_id.get(paciente_id, "Paciente")

        col1, col2 = st.columns(2)
        with col1:
            data_inicio = st.date_input("Data inicial")
        with col2:
            data_fim = st.date_input("Data final")

        if data_fim < data_inicio:
            st.error("A data final deve ser maior ou igual à data inicial.")
        elif st.button("Gerar relatório"):
            periodo = f"{data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}"
            mes_ref = data_inicio.strftime("%Y-%m")

            if todos_pacientes:
                zip_buffer = io.BytesIO()
                total_arquivos = 0

                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    for p in pacientes:
                        paciente_id_loop = p[0]
                        nome_paciente_loop = p[1]

                        dados_detalhados = relatorio_paciente_detalhado(
                            paciente_id_loop, data_inicio, data_fim
                        )
                        if not dados_detalhados:
                            continue

                        dados_pdf = [(d[0], d[1], d[2]) for d in dados_detalhados]
                        pdf_buffer = gerar_pdf_relatorio_paciente(
                            nome_paciente_loop, periodo, dados_pdf
                        )

                        nome_arquivo = f"relatorio_{_safe_filename(nome_paciente_loop)}_{mes_ref}.pdf"
                        zf.writestr(nome_arquivo, pdf_buffer.getvalue())
                        total_arquivos += 1

                if total_arquivos == 0:
                    st.info("Nenhum atendimento no período para gerar relatórios.")
                else:
                    zip_buffer.seek(0)
                    st.success(f"{total_arquivos} relatórios gerados.")
                    st.download_button(
                        "Baixar relatórios do mês (ZIP)",
                        data=zip_buffer.getvalue(),
                        file_name=f"relatorios_{mes_ref}.zip",
                        mime="application/zip"
                    )
            else:
                dados = relatorio_paciente_agrupado(paciente_id, data_inicio, data_fim)

                if not dados:
                    st.info("Nenhum atendimento no período.")
                else:
                    st.write(f"Total de registros: {len(dados)}")
                    st.write("### Atendimentos por Tipo")

                    total_geral = 0

                    for row in dados:
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.write(f"**{row[0]}**")
                        with col2:
                            st.write(f"Qtd: {row[1]}")
                        with col3:
                            st.write(f"Valor: R$ {row[2]:.2f}")
                        with col4:
                            st.write(f"Subtotal: R$ {row[3]:.2f}")

                        total_geral += row[3]
                        st.markdown("---")

                    st.markdown(f"### 💰 Total do período: **R$ {total_geral:.2f}**")

                dados_detalhados = relatorio_paciente_detalhado(
                    paciente_id, data_inicio, data_fim
                )
                if dados_detalhados:
                    dados_pdf = [(d[0], d[1], d[2]) for d in dados_detalhados]
                    pdf_buffer = gerar_pdf_relatorio_paciente(
                        nome_paciente, periodo, dados_pdf
                    )

                    st.download_button(
                        "Baixar relatório do paciente (PDF)",
                        data=pdf_buffer.getvalue(),
                        file_name=f"relatorio_{_safe_filename(nome_paciente)}_{mes_ref}.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.info("Sem dados para gerar o PDF do paciente.")


def render_relatorio_contador():
    st.subheader("Relatório para Contador")

    _botao_voltar_inicio("voltar_rel_contador")

    col1, col2 = st.columns(2)
    with col1:
        data_inicio = st.date_input("Data inicial")
    with col2:
        data_fim = st.date_input("Data final")

    if data_fim < data_inicio:
        st.error("A data final deve ser maior ou igual à data inicial.")
    elif st.button("Gerar relatório do contador"):
        dados = relatorio_contador(data_inicio, data_fim)

        if not dados:
            st.info("Nenhum paciente com nota fiscal no período.")
        else:
            import pandas as pd

            dados_masked = []
            for d in dados:
                dados_masked.append([
                    d[0],
                    mask_nome(d[1]),
                    d[2],
                    d[3],
                    d[4]
                ])

            df = pd.DataFrame(
                dados_masked,
                columns=["ID", "Nome", "CPF", "Quantidade", "Total"]
            )

            st.dataframe(df, use_container_width=True)

            csv_bytes = df.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")

            st.download_button(
                "Baixar relatório do contador (CSV)",
                data=csv_bytes,
                file_name=f"relatorio_contador_{data_inicio}_a_{data_fim}.csv",
                mime="text/csv"
            )


def render_atualizar_precos():
    st.subheader("Atualizar Preços de Consultas")

    _botao_voltar_inicio("voltar_preco")

    tipos = listar_tipos_atendimento_com_valor()

    if not tipos:
        st.info("Nenhum tipo de atendimento encontrado.")
    else:
        import pandas as pd

        df_tipos = pd.DataFrame(
            tipos,
            columns=["ID", "Código", "Descrição", "Valor"]
        )

        st.dataframe(df_tipos, use_container_width=True)

        opcoes = [f"{t[0]} - {t[2]} (R$ {t[3]:.2f})" for t in tipos]
        escolha = st.selectbox("Selecione o tipo de atendimento", opcoes)

        tipo_id = int(escolha.split(" - ")[0])
        tipo_dict = {t[0]: t for t in tipos}
        valor_atual = float(tipo_dict[tipo_id][3])

        novo_valor = st.number_input(
            "Novo valor (R$)",
            min_value=0.0,
            value=valor_atual,
            step=1.0,
            format="%.2f"
        )

        if st.button("Atualizar preço", key="btn_atualizar_preco"):
            resultado = atualizar_preco_tipo_atendimento(tipo_id, novo_valor)

            if resultado is True:
                st.success("Preço atualizado com sucesso!")
                st.rerun()
            else:
                st.error(f"Erro ao atualizar: {resultado}")


def render_relatorio_geral():
    st.subheader("Relatório Geral do Mês")

    _botao_voltar_inicio("voltar_rel_geral")

    mes_ref = st.date_input("Mês de referência", value=date.today())
    data_inicio, data_fim = _mes_range(mes_ref)

    st.caption(
        f"Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}"
    )

    if st.button("Gerar relatório geral"):
        resumo = relatorio_geral_resumo(data_inicio, data_fim)
        por_tipo = relatorio_geral_por_tipo(data_inicio, data_fim)

        if resumo:
            total_entradas, pacientes_pagantes, tipos_sessao = resumo
        else:
            total_entradas, pacientes_pagantes, tipos_sessao = 0, 0, 0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Entradas no mês", f"R$ {total_entradas:.2f}")
        with col2:
            st.metric("Pacientes pagantes", pacientes_pagantes)
        with col3:
            st.metric("Tipos de sessão", tipos_sessao)

        if not por_tipo:
            st.info("Nenhuma entrada no período.")
        else:
            import pandas as pd

            df = pd.DataFrame(
                por_tipo,
                columns=["Tipo de sessão", "Pacientes", "Sessões", "Total (R$)"]
            )
            df = df.sort_values(by="Pacientes", ascending=False, kind="mergesort")
            df.insert(0, "Destaque", ["TOP" if i == 0 else "" for i in range(len(df))])
            st.dataframe(df, use_container_width=True)



def render_cadastrar_profissional():
    st.subheader("Cadastrar Profissional")

    _botao_voltar_inicio("voltar_profissional")

    st.markdown("### Registrar profissional")

    nome_prof = st.text_input("Nome", key="prof_nome")
    cpf_prof = st.text_input("CPF", key="prof_cpf")
    crefito_prof = st.text_input("CREFITO", key="prof_crefito")
    telefone_prof = st.text_input("Telefone", key="prof_telefone")
    endereco_prof = st.text_input("Endereço", key="prof_endereco")
    tipo_contrato = st.text_input("Tipo de contrato", key="prof_contrato")
    percentual = st.number_input(
        "Percentual de repasse (%)",
        min_value=0.0,
        max_value=100.0,
        value=0.0,
        step=1.0,
        format="%.2f",
        key="prof_percentual"
    )
    ativo = st.checkbox("Ativo", value=True, key="prof_ativo")

    if st.button("Salvar profissional", key="prof_salvar"):
        cpf_digits = only_digits(cpf_prof)
        telefone_digits = only_digits(telefone_prof)

        if not nome_prof.strip():
            st.error("Nome é obrigatório.")
        elif not cpf_digits:
            st.error("CPF é obrigatório.")
        elif not crefito_prof.strip():
            st.error("CREFITO é obrigatório.")
        elif not telefone_digits:
            st.error("Telefone é obrigatório.")
        elif percentual <= 0 or percentual > 100:
            st.error("Informe um percentual válido (1 a 100).")
        else:
            resultado = inserir_profissional(
                nome_prof.strip(),
                cpf_digits,
                crefito_prof.strip(),
                telefone_digits,
                endereco_prof.strip(),
                tipo_contrato.strip(),
                percentual,
                ativo
            )
            if resultado is True:
                st.success("Profissional registrado com sucesso!")
            else:
                st.error(f"Erro ao salvar: {resultado}")

    st.markdown("---")
    st.markdown("---")
    st.markdown("### Editar/Desativar profissional")

    profissionais_todos = listar_profissionais(False)
    if not profissionais_todos:
        st.info("Nenhum profissional encontrado.")
    else:
        opcoes_edit = [f"{p[0]} - {p[1]}" for p in profissionais_todos]
        escolha_edit = st.selectbox("Selecione o profissional", opcoes_edit, key="prof_edit_select")
        prof_id = int(escolha_edit.split(" - ")[0])
        prof_map = {p[0]: p for p in profissionais_todos}
        prof = prof_map.get(prof_id)

        if prof:
            with st.form(f"form_editar_prof_{prof_id}"):
                nome_edit = st.text_input("Nome", value=prof[1] or "", key=f"edit_nome_{prof_id}")
                cpf_edit = st.text_input("CPF", value=prof[5] or "", key=f"edit_cpf_{prof_id}")
                crefito_edit = st.text_input("CREFITO", value=prof[6] or "", key=f"edit_crefito_{prof_id}")
                telefone_edit = st.text_input("Telefone", value=prof[7] or "", key=f"edit_tel_{prof_id}")
                endereco_edit = st.text_input("Endereço", value=prof[8] or "", key=f"edit_end_{prof_id}")
                contrato_edit = st.text_input("Tipo de contrato", value=prof[2] or "", key=f"edit_contrato_{prof_id}")
                percentual_edit = st.number_input(
                    "Percentual de repasse (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(prof[3] or 0),
                    step=1.0,
                    format="%.2f",
                    key=f"edit_percentual_{prof_id}"
                )
                ativo_edit = st.checkbox("Ativo", value=bool(prof[4]), key=f"edit_ativo_{prof_id}")

                salvar_edit = st.form_submit_button("Salvar alterações")

            if salvar_edit:
                cpf_digits = only_digits(cpf_edit)
                tel_digits = only_digits(telefone_edit)

                if not nome_edit.strip():
                    st.error("Nome é obrigatório.")
                elif not cpf_digits:
                    st.error("CPF é obrigatório.")
                elif not crefito_edit.strip():
                    st.error("CREFITO é obrigatório.")
                elif not tel_digits:
                    st.error("Telefone é obrigatório.")
                elif percentual_edit <= 0 or percentual_edit > 100:
                    st.error("Informe um percentual válido (1 a 100).")
                else:
                    resultado = atualizar_profissional(
                        prof_id,
                        nome_edit.strip(),
                        cpf_digits,
                        crefito_edit.strip(),
                        tel_digits,
                        endereco_edit.strip(),
                        contrato_edit.strip(),
                        percentual_edit,
                        ativo_edit
                    )

                    if resultado == 1:
                        st.success("Profissional atualizado com sucesso!")
                        st.rerun()
                    elif isinstance(resultado, int) and resultado == 0:
                        st.error("Nenhuma alteração foi aplicada.")
                    else:
                        st.error(f"Erro ao atualizar: {resultado}")

    st.markdown("### Profissionais")

    ativos_only = st.checkbox("Mostrar apenas ativos", value=True, key="prof_ativos_only")
    dados = listar_profissionais(ativos_only)

    if not dados:
        st.info("Nenhum profissional encontrado.")
    else:
        import pandas as pd

        dados_fmt = []
        for p in dados:
            dados_fmt.append([
                p[0],
                p[1],
                p[5],
                p[6],
                p[7],
                p[8],
                p[2],
                p[3],
                p[4]
            ])

        df = pd.DataFrame(
            dados_fmt,
            columns=[
                "ID",
                "Nome",
                "CPF",
                "CREFITO",
                "Telefone",
                "Endereço",
                "Tipo contrato",
                "% Repasse",
                "Ativo"
            ]
        )
        st.dataframe(df, use_container_width=True)


def render_financeiro_graficos():
    st.subheader("Gráficos Financeiros")

    _botao_voltar_inicio("voltar_fin_graficos")

    min_graf_date = date(2026, 1, 1)
    hoje = date.today()
    fim_ref = date(hoje.year, hoje.month, 1)
    inicio_ref = _shift_month(fim_ref, -11)
    if inicio_ref < min_graf_date:
        inicio_ref = min_graf_date

    data_inicio = date(inicio_ref.year, inicio_ref.month, 1)
    ultimo_dia = calendar.monthrange(fim_ref.year, fim_ref.month)[1]
    data_fim = date(fim_ref.year, fim_ref.month, ultimo_dia)

    st.caption(
        f"Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}"
    )

    receitas = financeiro_receita_mensal(data_inicio, data_fim)
    despesas = financeiro_despesa_mensal(data_inicio, data_fim)
    repasses = financeiro_repasse_mensal(data_inicio, data_fim)

    receita_map = {r[0]: float(r[1] or 0) for r in receitas}
    despesa_map = {d[0]: float(d[1] or 0) for d in despesas}
    repasse_map = {r[0]: float(r[1] or 0) for r in repasses}

    meses = _month_list(data_inicio, data_fim)
    linhas = []
    for mes in meses:
        receita = receita_map.get(mes, 0.0)
        despesa = despesa_map.get(mes, 0.0)
        repasse = repasse_map.get(mes, 0.0)
        linhas.append({
            "Mês": mes.strftime("%Y-%m"),
            "Receita": receita,
            "Despesa": despesa,
            "Lucro": receita - despesa - repasse
        })

    st.markdown("### Receita e Despesa Mensal")
    if not linhas:
        st.info("Nenhum dado no período.")
    else:
        import pandas as pd
        import altair as alt

        df = pd.DataFrame(linhas)
        df_long = df.melt(id_vars=["Mês"], value_vars=["Receita", "Despesa"],
                          var_name="Categoria", value_name="Valor")
        df_long["Label"] = df_long["Valor"].apply(lambda v: f"R$ {v:,.2f}")
        max_val = df_long["Valor"].max() if not df_long.empty else 0

        chart = (
            alt.Chart(df_long)
            .mark_bar()
            .encode(
                x=alt.X(
                    "Mês:N",
                    sort=None,
                    axis=alt.Axis(labelAngle=0, labelPadding=12),
                    scale=alt.Scale(paddingInner=0.25, paddingOuter=0.25)
                ),
                y=alt.Y(
                    "Valor:Q",
                    scale=alt.Scale(domain=[0, max_val]),
                    axis=alt.Axis(format=",.2f")
                ),
                color=alt.Color(
                    "Categoria:N",
                    scale=alt.Scale(
                        domain=["Receita", "Despesa"],
                        range=["#2563eb", "#dc2626"]
                    )
                ),
                xOffset="Categoria:N"
            )
        )

        labels = (
            alt.Chart(df_long)
            .mark_text(dy=-6)
            .encode(
                x=alt.X(
                    "Mês:N",
                    sort=None,
                    axis=alt.Axis(labelAngle=0, labelPadding=12),
                    scale=alt.Scale(paddingInner=0.25, paddingOuter=0.25)
                ),
                y=alt.Y("Valor:Q"),
                text=alt.Text("Label:N"),
                xOffset="Categoria:N"
            )
        )
        st.altair_chart(chart + labels, use_container_width=True)

    st.markdown("### Lucro Mensal")
    if linhas:
        import pandas as pd
        import altair as alt

        df_lucro = pd.DataFrame(linhas)
        df_lucro["Label"] = df_lucro["Lucro"].apply(lambda v: f"R$ {v:,.2f}")
        min_lucro = df_lucro["Lucro"].min() if not df_lucro.empty else 0
        max_lucro = df_lucro["Lucro"].max() if not df_lucro.empty else 0
        domain_min = min(0, min_lucro)
        domain_max = max(0, max_lucro)
        chart_lucro = (
            alt.Chart(df_lucro)
            .mark_bar()
            .encode(
                x=alt.X("Mês:N", sort=None, axis=alt.Axis(labelAngle=0)),
                y=alt.Y(
                    "Lucro:Q",
                    scale=alt.Scale(domain=[domain_min, domain_max]),
                    axis=alt.Axis(format=",.2f")
                ),
                color=alt.condition(
                    alt.datum.Lucro >= 0,
                    alt.value("#2563eb"),
                    alt.value("#dc2626")
                )
            )
        )

        labels_lucro = (
            alt.Chart(df_lucro)
            .mark_text(dy=-6)
            .encode(
                x=alt.X("Mês:N", sort=None, axis=alt.Axis(labelAngle=0)),
                y=alt.Y("Lucro:Q"),
                text=alt.Text("Label:N")
            )
        )
        st.altair_chart(chart_lucro + labels_lucro, use_container_width=True)

    st.markdown("### Pagamentos por status")
    dados_status = financeiro_pagamentos_por_status(data_inicio, data_fim)
    if not dados_status:
        st.info("Nenhum pagamento encontrado no período.")
    else:
        import pandas as pd
        import altair as alt

        df_status = pd.DataFrame(dados_status, columns=["Status", "Total (R$)"])
        df_status["Total (R$)"] = df_status["Total (R$)"].astype(float)
        df_status["Label"] = df_status["Total (R$)"] .apply(lambda v: f"R$ {v:,.2f}")
        max_status = df_status["Total (R$)"].max() if not df_status.empty else 0
        chart_status = (
            alt.Chart(df_status)
            .mark_bar(color="#2563eb")
            .encode(
                x=alt.X("Status:N", sort=None, axis=alt.Axis(labelAngle=0)),
                y=alt.Y("Total (R$):Q", scale=alt.Scale(domain=[0, max_status]), axis=alt.Axis(format=",.2f"))
            )
        )

        labels_status = (
            alt.Chart(df_status)
            .mark_text(dy=-6)
            .encode(
                x=alt.X("Status:N", sort=None, axis=alt.Axis(labelAngle=0)),
                y=alt.Y("Total (R$):Q"),
                text=alt.Text("Label:N")
            )
        )
        st.altair_chart(chart_status + labels_status, use_container_width=True)

    meses_det = _month_list(data_inicio, data_fim)
    if not meses_det:
        st.info("Nenhum mês no período.")
        return

    mes_det_date = date(data_fim.year, data_fim.month, 1)
    det_inicio, det_fim = _mes_range(mes_det_date)

    st.caption(f"Referente ao mês: {mes_det_date.strftime('%Y-%m')}")

    st.markdown("### Receita por profissional")
    dados_prof = financeiro_receita_por_profissional(det_inicio, det_fim)
    if not dados_prof:
        st.info("Nenhuma receita encontrada no período.")
    else:
        import pandas as pd
        import altair as alt

        df_prof = pd.DataFrame(dados_prof, columns=["Profissional", "Total (R$)"])
        df_prof["Total (R$)"] = df_prof["Total (R$)"].astype(float)
        df_prof["Label"] = df_prof["Total (R$)"] .apply(lambda v: f"R$ {v:,.2f}")
        df_prof["Cor"] = ["Azul 1" if i % 2 == 0 else "Azul 2" for i in range(len(df_prof))]
        max_prof = df_prof["Total (R$)"].max() if not df_prof.empty else 0
        chart_prof = (
            alt.Chart(df_prof)
            .mark_bar()
            .encode(
                x=alt.X("Profissional:N", sort='-y', axis=alt.Axis(labelAngle=0)),
                y=alt.Y("Total (R$):Q", scale=alt.Scale(domain=[0, max_prof]), axis=alt.Axis(format=",.2f")),
                color=alt.Color(
                    "Cor:N",
                    scale=alt.Scale(domain=["Azul 1", "Azul 2"], range=["#2563eb", "#60a5fa"]),
                    legend=None
                ),
                tooltip=[
                    alt.Tooltip("Profissional:N"),
                    alt.Tooltip("Total (R$):Q", format=",.2f")
                ]
            )
        )

        labels_prof = (
            alt.Chart(df_prof)
            .mark_text(dy=-6)
            .encode(
                x=alt.X("Profissional:N", sort='-y', axis=alt.Axis(labelAngle=0)),
                y=alt.Y("Total (R$):Q"),
                text=alt.Text("Label:N")
            )
        )
        st.altair_chart(chart_prof + labels_prof, use_container_width=True)

    st.markdown("### Receita por tipo de atendimento")
    dados_tipo = financeiro_receita_por_tipo_atendimento(det_inicio, det_fim)
    if not dados_tipo:
        st.info("Nenhuma receita encontrada no período.")
    else:
        import pandas as pd
        import altair as alt

        df_tipo = pd.DataFrame(dados_tipo, columns=["Tipo", "Total (R$)"])
        df_tipo["Total (R$)"] = df_tipo["Total (R$)"] .astype(float)
        df_tipo["Label"] = df_tipo["Total (R$)"] .apply(lambda v: f"R$ {v:,.2f}")
        df_tipo["Cor"] = ["Azul 1" if i % 2 == 0 else "Azul 2" for i in range(len(df_tipo))]
        max_tipo = df_tipo["Total (R$)"].max() if not df_tipo.empty else 0
        chart_tipo = (
            alt.Chart(df_tipo)
            .mark_bar()
            .encode(
                x=alt.X("Tipo:N", sort='-y', axis=alt.Axis(labelAngle=0)),
                y=alt.Y("Total (R$):Q", scale=alt.Scale(domain=[0, max_tipo]), axis=alt.Axis(format=",.2f")),
                color=alt.Color(
                    "Cor:N",
                    scale=alt.Scale(domain=["Azul 1", "Azul 2"], range=["#2563eb", "#60a5fa"]),
                    legend=None
                ),
                tooltip=[
                    alt.Tooltip("Tipo:N"),
                    alt.Tooltip("Total (R$):Q", format=",.2f")
                ]
            )
        )

        labels_tipo = (
            alt.Chart(df_tipo)
            .mark_text(dy=-6)
            .encode(
                x=alt.X("Tipo:N", sort='-y', axis=alt.Axis(labelAngle=0)),
                y=alt.Y("Total (R$):Q"),
                text=alt.Text("Label:N")
            )
        )
        st.altair_chart(chart_tipo + labels_tipo, use_container_width=True)


def render_relatorio_profissional():
    st.subheader("Relatório por Profissional")

    _botao_voltar_inicio("voltar_rel_prof")

    profissionais = listar_profissionais(False)
    if not profissionais:
        st.info("Nenhum profissional encontrado.")
        return

    opcoes = [f"{p[0]} - {p[1]}" for p in profissionais]
    escolha = st.selectbox("Profissional", opcoes, key="rel_prof_select")
    prof_id = int(escolha.split(" - ")[0])
    prof_map = {p[0]: p for p in profissionais}
    prof = prof_map.get(prof_id)

    col1, col2 = st.columns(2)
    with col1:
        data_inicio = st.date_input("Data inicial", value=date.today().replace(day=1), key="rel_prof_ini")
    with col2:
        data_fim = st.date_input("Data final", value=date.today(), key="rel_prof_fim")

    if st.button("Gerar relatório", key="rel_prof_btn"):
        nome_prof = prof[1]
        percentual = float(prof[3] or 0)
        dados = relatorio_profissional_consultas(nome_prof, data_inicio, data_fim)

        if not dados:
            st.info("Nenhuma consulta encontrada no período.")
            return

        import pandas as pd

        linhas = []
        total_consultas = 0
        total_consulta_valor = 0.0
        total_repasse = 0.0

        for d in dados:
            total_consultas += 1
            total_consulta_valor += float(d[4] or 0)
            total_repasse += (float(d[4] or 0) * percentual) / 100.0
            linhas.append([
                d[0],
                d[1],
                d[2],
                d[3],
                float(d[4] or 0),
                (float(d[4] or 0) * percentual) / 100.0
            ])

        st.markdown("### Resumo")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Consultas", total_consultas)
        with col2:
            st.metric("Total consultas (R$)", f"R$ {total_consulta_valor:.2f}")
        with col3:
            st.metric("Total repasse (R$)", f"R$ {total_repasse:.2f}")

        df = pd.DataFrame(
            linhas,
            columns=[
                "ID",
                "Data",
                "Paciente",
                "Tipo atendimento",
                "Valor consulta (R$)",
                "Repasse fixo (R$)"
            ]
        )
        st.dataframe(df, use_container_width=True)

        periodo_txt = f"{data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}"
        dados_pdf = [
            (d[1], d[2], d[3], float(d[4] or 0), (float(d[4] or 0) * percentual) / 100.0)
            for d in dados
        ]
        pdf_buffer = gerar_pdf_relatorio_profissional(nome_prof, periodo_txt, dados_pdf)
        nome_arquivo = f"relatorio_{_safe_filename(nome_prof)}_{data_inicio.strftime('%Y%m')}.pdf"

        st.download_button(
            "Baixar relatório (PDF)",
            data=pdf_buffer,
            file_name=nome_arquivo,
            mime="application/pdf"
        )




def render_financeiro():
    st.subheader("Financeiro")

    _botao_voltar_inicio("voltar_financeiro")

    if "fin_periodo" not in st.session_state:
        st.session_state.fin_periodo = date.today()

    with st.form("fin_periodo_form"):
        mes_ref = st.date_input(
            "Mês de referência",
            value=st.session_state.fin_periodo,
            key="fin_mes_ref"
        )
        aplicar_periodo = st.form_submit_button("Aplicar período")

    if aplicar_periodo:
        st.session_state.fin_periodo = mes_ref
        st.session_state.pg_busca_feita = False
        st.session_state.pg_evolucoes = []
        st.session_state.rep_busca_feita = False
        st.session_state.rep_evolucoes = []

    mes_ref = st.session_state.fin_periodo
    data_inicio, data_fim = _mes_range(mes_ref)

    st.caption(
        f"Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}"
    )

    tab_resumo, tab_pagamentos, tab_despesas, tab_repasses = st.tabs(
        ["Resumo", "Pagamentos", "Despesas", "Repasses"]
    )

    with tab_resumo:
        resumo = resumo_financeiro(data_inicio, data_fim)
        if not resumo:
            st.info("Nenhum dado financeiro no período.")
        else:
            pagamentos = resumo.get("pagamentos", {})
            despesas_total = resumo.get("despesas_total", 0)
            repasses = resumo.get("repasses", {})

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Recebido", f"R$ {pagamentos.get('pago', 0):.2f}")
            with col2:
                st.metric("Pendente", f"R$ {pagamentos.get('pendente', 0):.2f}")
            with col3:
                st.metric("Atrasado", f"R$ {pagamentos.get('atrasado', 0):.2f}")
            with col4:
                st.metric("Cancelado", f"R$ {pagamentos.get('cancelado', 0):.2f}")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Despesas", f"R$ {despesas_total:.2f}")
            with col2:
                st.metric("Repasses pendentes", f"R$ {repasses.get('pendente', 0):.2f}")
            with col3:
                st.metric("Repasses pagos", f"R$ {repasses.get('pago', 0):.2f}")

    with tab_pagamentos:
        st.markdown("### Registrar pagamento")

        if "pg_evolucoes" not in st.session_state:
            st.session_state.pg_evolucoes = []
        if "pg_busca_feita" not in st.session_state:
            st.session_state.pg_busca_feita = False
        if "pg_filtro" not in st.session_state:
            st.session_state.pg_filtro = ""

        with st.form("pg_busca_form"):
            filtro_evolucao = st.text_input(
                "Buscar paciente (nome ou CPF)",
                value=st.session_state.pg_filtro,
                key="pg_busca_evo"
            )
            buscar = st.form_submit_button("Buscar atendimentos")

        if buscar:
            st.session_state.pg_filtro = filtro_evolucao
            st.session_state.pg_evolucoes = listar_evolucoes_pendentes_pagamento(
                filtro_evolucao,
                data_inicio,
                data_fim
            )
            st.session_state.pg_busca_feita = True

        evolucoes = st.session_state.pg_evolucoes

        if not evolucoes:
            if st.session_state.pg_busca_feita:
                st.info("Nenhum atendimento encontrado no período.")
            else:
                st.info("Faça uma busca para listar atendimentos.")
        else:
            grupos = {}
            for evo in evolucoes:
                paciente_id = evo[1]
                if paciente_id not in grupos:
                    grupos[paciente_id] = {
                        "nome": evo[2],
                        "cpf": evo[3],
                        "evolucoes": []
                    }
                grupos[paciente_id]["evolucoes"].append(evo)

            opcoes = []
            mapa = {}
            for paciente_id in sorted(grupos, key=lambda k: grupos[k]["nome"].lower()):
                info = grupos[paciente_id]
                total = sum(float(e[6]) for e in info["evolucoes"])
                qtde = len(info["evolucoes"])
                cpf_mask = mask_cpf(info["cpf"])
                label = (
                    f"{paciente_id} - {info['nome']} (CPF: {cpf_mask}) "
                    f"- {qtde} atendimentos - Total R$ {total:.2f}"
                )
                opcoes.append(label)
                mapa[label] = paciente_id

            escolha = st.selectbox("Paciente", opcoes, key="pg_paciente")
            paciente_id = mapa.get(escolha)
            info = grupos.get(paciente_id, {})
            evolucoes_paciente = info.get("evolucoes", [])
            total_paciente = sum(float(e[6]) for e in evolucoes_paciente)

            col1, col2 = st.columns(2)
            with col1:
                data_pagamento = st.date_input(
                    "Data do pagamento",
                    value=date.today(),
                    key="pg_data_pagamento"
                )
            with col2:
                st.metric("Total no período", f"R$ {total_paciente:.2f}")
            st.caption(f"{len(evolucoes_paciente)} atendimentos no período.")

            forma_pagamento = st.selectbox(
                "Forma de pagamento",
                FORMA_PAGAMENTO_OPCOES,
                key="pg_forma"
            )
            status_pagamento = st.selectbox(
                "Status",
                STATUS_PAGAMENTO_OPCOES,
                index=0,
                key="pg_status"
            )

            with st.expander("Ver atendimentos do paciente"):
                historico = listar_evolucoes_pagamentos_paciente(
                    paciente_id,
                    data_inicio,
                    data_fim
                )
                if not historico:
                    st.info("Nenhum atendimento no período.")
                else:
                    import pandas as pd

                    df_hist = pd.DataFrame(
                        historico,
                        columns=["ID", "Data", "Tipo", "Valor", "Status", "Data pagamento"]
                    )
                    df_hist["Status"] = df_hist["Status"].fillna("sem pagamento")
                    st.dataframe(df_hist, use_container_width=True)

            st.caption("Ao marcar como pago, os atendimentos somem da lista para evitar duplicidade.")

            if st.button("Salvar pagamento", key="pg_salvar"):
                if not evolucoes_paciente:
                    st.error("Selecione um paciente com atendimentos no período.")
                else:
                    erros = []
                    for evo in evolucoes_paciente:
                        resultado = inserir_pagamento(
                            paciente_id,
                            evo[0],
                            data_pagamento,
                            float(evo[6]),
                            forma_pagamento,
                            status_pagamento
                        )
                        if resultado is not True:
                            erros.append(resultado)

                    if not erros:
                        st.success("Pagamento registrado com sucesso!")
                        if status_pagamento == "pago":
                            st.session_state.pg_evolucoes = listar_evolucoes_pendentes_pagamento(
                                st.session_state.pg_filtro,
                                data_inicio,
                                data_fim
                            )
                            st.session_state.pg_busca_feita = True
                            if "pg_paciente" in st.session_state:
                                del st.session_state["pg_paciente"]
                            st.rerun()
                    else:
                        st.error(f"Erro ao salvar: {erros[0]}")

        st.markdown("---")
        st.markdown("### Pagamentos")

        if "pg_list_dados" not in st.session_state:
            st.session_state.pg_list_dados = None

        with st.form("pg_list_form"):
            col1, col2 = st.columns(2)
            with col1:
                filtro_pag = st.text_input("Buscar paciente (nome ou CPF)", key="pg_filtro_list")
                status_filtro = st.selectbox(
                    "Status",
                    ["TODOS"] + STATUS_PAGAMENTO_OPCOES,
                    key="pg_status_list"
                )
            with col2:
                forma_filtro = st.selectbox(
                    "Forma de pagamento",
                    ["TODOS"] + FORMA_PAGAMENTO_OPCOES,
                    key="pg_forma_list"
                )

            col1, col2 = st.columns(2)
            with col1:
                data_inicio_pag = st.date_input(
                    "Data inicial",
                    value=data_inicio,
                    key="pg_list_inicio"
                )
            with col2:
                data_fim_pag = st.date_input(
                    "Data final",
                    value=data_fim,
                    key="pg_list_fim"
                )

            buscar_list = st.form_submit_button("Buscar pagamentos")

        if buscar_list:
            st.session_state.pg_list_dados = listar_pagamentos(
                filtro_pag,
                data_inicio_pag,
                data_fim_pag,
                status_filtro,
                forma_filtro
            )

        dados = st.session_state.pg_list_dados

        if buscar_list or dados is not None:
            if not dados:
                st.info("Nenhum pagamento encontrado.")
            else:
                import pandas as pd

                df = pd.DataFrame(
                    dados,
                    columns=[
                        "ID",
                        "Paciente",
                        "CPF",
                        "Data atendimento",
                        "Data pagamento",
                        "Valor",
                        "Forma",
                        "Status"
                    ]
                )

                df_resumo = (
                    df.groupby(["Paciente", "CPF"], as_index=False)
                    .agg({"Valor": "sum", "ID": "count"})
                )
                df_resumo = df_resumo.rename(
                    columns={"Valor": "Total (R$)", "ID": "Atendimentos"}
                )
                st.dataframe(df_resumo, use_container_width=True)

                with st.expander("Ver detalhes por atendimento"):
                    st.dataframe(df, use_container_width=True)

    with tab_despesas:
        st.markdown("### Registrar despesa")

        with st.form("form_despesa"):
            col1, col2 = st.columns(2)
            with col1:
                data_despesa = st.date_input(
                    "Data",
                    value=date.today(),
                    key="desp_data"
                )
            with col2:
                valor_despesa = st.number_input(
                    "Valor",
                    min_value=0.0,
                    value=0.0,
                    step=1.0,
                    format="%.2f",
                    key="desp_valor"
                )

            descricao = st.text_input("Descrição", key="desp_desc")
            categoria = st.selectbox(
                "Categoria",
                DESPESA_CATEGORIA_OPCOES,
                key="desp_categoria"
            )
            tipo_despesa = st.selectbox(
                "Tipo",
                DESPESA_TIPO_OPCOES,
                key="desp_tipo"
            )
            recorrente = st.checkbox("Recorrente", key="desp_recorrente")

            salvar = st.form_submit_button("Salvar despesa")

        if salvar:
            if not descricao:
                st.error("Descrição é obrigatória.")
            else:
                resultado = inserir_despesa(
                    data_despesa,
                    descricao,
                    categoria,
                    valor_despesa,
                    tipo_despesa,
                    recorrente
                )

                if resultado is True:
                    st.success("Despesa registrada com sucesso!")
                else:
                    st.error(f"Erro ao salvar: {resultado}")

        st.markdown("---")
        st.markdown("### Despesas")

        if "desp_list_dados" not in st.session_state:
            st.session_state.desp_list_dados = None

        col1, col2 = st.columns(2)
        with col1:
            data_inicio_d = st.date_input(
                "Data inicial",
                value=data_inicio,
                key="desp_inicio"
            )
        with col2:
            data_fim_d = st.date_input(
                "Data final",
                value=data_fim,
                key="desp_fim"
            )

        col1, col2 = st.columns(2)
        with col1:
            categoria_filtro = st.selectbox(
                "Categoria",
                ["TODOS"] + DESPESA_CATEGORIA_OPCOES,
                key="desp_cat_filtro"
            )
        with col2:
            tipo_filtro = st.selectbox(
                "Tipo",
                ["TODOS"] + DESPESA_TIPO_OPCOES,
                key="desp_tipo_filtro"
            )

        if st.button("Buscar despesas", key="desp_buscar"):
            st.session_state.desp_list_dados = listar_despesas(
                data_inicio_d,
                data_fim_d,
                categoria_filtro,
                tipo_filtro
            )

        dados = st.session_state.desp_list_dados

        if dados is not None:
            if not dados:
                st.info("Nenhuma despesa encontrada.")
            else:
                import pandas as pd

                df = pd.DataFrame(
                    dados,
                    columns=["ID", "Data", "Descrição", "Categoria", "Valor", "Tipo", "Recorrente"]
                )
                st.dataframe(df, use_container_width=True)

                st.markdown("### Excluir despesa")
                opcoes = [
                    f"{d[0]} - {d[1]} - {d[2]} - R$ {float(d[4]):.2f}"
                    for d in dados
                ]
                escolha = st.selectbox("Selecione a despesa", opcoes, key="desp_delete_select")
                despesa_id = int(escolha.split(" - ")[0])
                confirmar = st.checkbox("Confirmar exclusão", key="desp_delete_confirm")

                if st.button("Excluir despesa", key="desp_delete_btn"):
                    if not confirmar:
                        st.error("Confirme a exclusão para continuar.")
                    else:
                        resultado = deletar_despesa(despesa_id)
                        if resultado == 1:
                            st.success("Despesa excluída com sucesso!")
                            st.session_state.desp_list_dados = listar_despesas(
                                data_inicio_d,
                                data_fim_d,
                                categoria_filtro,
                                tipo_filtro
                            )
                            st.rerun()
                        elif isinstance(resultado, int) and resultado == 0:
                            st.error("Despesa não encontrada.")
                        else:
                            st.error(f"Erro ao excluir: {resultado}")


    with tab_repasses:
        st.markdown("### Registrar repasse")

        profissionais = listar_profissionais(True)
        if not profissionais:
            st.info("Nenhum profissional ativo encontrado.")
        else:
            op_prof = [f"{p[0]} - {p[1]} ({float(p[3] or 0):.2f}%)" for p in profissionais]
            escolha_prof = st.selectbox("Profissional", op_prof, key="rep_prof")
            prof_id = int(escolha_prof.split(" - ")[0])
            prof_dict = {p[0]: p for p in profissionais}
            prof_sel = prof_dict.get(prof_id)

            if "rep_evolucoes" not in st.session_state:
                st.session_state.rep_evolucoes = []
            if "rep_busca_feita" not in st.session_state:
                st.session_state.rep_busca_feita = False
            if "rep_filtro" not in st.session_state:
                st.session_state.rep_filtro = ""

            with st.form("rep_busca_form"):
                filtro_evo = st.text_input(
                    "Buscar paciente (nome ou CPF)",
                    value=st.session_state.rep_filtro,
                    key="rep_busca_evo"
                )
                buscar_rep = st.form_submit_button("Buscar atendimentos")

            if buscar_rep:
                st.session_state.rep_filtro = filtro_evo
                st.session_state.rep_evolucoes = listar_evolucoes_financeiro(
                    filtro_evo,
                    data_inicio,
                    data_fim
                )
                st.session_state.rep_busca_feita = True

            evolucoes = st.session_state.rep_evolucoes
            if not evolucoes:
                if st.session_state.rep_busca_feita:
                    st.info("Nenhum atendimento encontrado no período.")
                else:
                    st.info("Faça uma busca para listar atendimentos.")
            else:
                op_evo = [
                    f"{e[0]} - {e[2]} - {e[4].strftime('%d/%m/%Y')} - {e[5]} - R$ {e[6]:.2f}"
                    for e in evolucoes
                ]
                escolha_evo = st.selectbox("Atendimento", op_evo, key="rep_atendimento")
                atendimento_id = int(escolha_evo.split(" - ")[0])
                evo_dict = {e[0]: e for e in evolucoes}
                evo = evo_dict.get(atendimento_id)

                percentual = float(prof_sel[3]) if prof_sel else 0.0
                valor_base = float(evo[6]) if evo else 0.0
                valor_sugerido = (valor_base * percentual) / 100.0

                col1, col2 = st.columns(2)
                with col1:
                    data_repasse = st.date_input(
                        "Data do repasse",
                        value=date.today(),
                        key="rep_data"
                    )
                with col2:
                    valor_repasse = st.number_input(
                        "Valor",
                        min_value=0.0,
                        value=valor_sugerido,
                        step=1.0,
                        format="%.2f",
                        key="rep_valor"
                    )

                status_repasse = st.selectbox(
                    "Status",
                    STATUS_REPASSE_OPCOES,
                    key="rep_status"
                )

                if st.button("Salvar repasse", key="rep_salvar"):
                    resultado = inserir_repasse_profissional(
                        prof_id,
                        atendimento_id,
                        valor_repasse,
                        data_repasse,
                        status_repasse
                    )

                    if resultado is True:
                        st.success("Repasse registrado com sucesso!")
                    else:
                        st.error(f"Erro ao salvar: {resultado}")

        st.markdown("---")
        st.markdown("### Repasses")

        col1, col2 = st.columns(2)
        with col1:
            data_inicio_r = st.date_input(
                "Data inicial",
                value=data_inicio,
                key="rep_inicio"
            )
        with col2:
            data_fim_r = st.date_input(
                "Data final",
                value=data_fim,
                key="rep_fim"
            )

        col1, col2 = st.columns(2)
        with col1:
            status_rep_filtro = st.selectbox(
                "Status",
                ["TODOS"] + STATUS_REPASSE_OPCOES,
                key="rep_status_filtro"
            )
        with col2:
            prof_filtro = st.selectbox(
                "Profissional",
                ["TODOS"] + [f"{p[0]} - {p[1]}" for p in profissionais],
                key="rep_prof_filtro"
            )

        prof_id_filtro = 0
        if prof_filtro != "TODOS":
            prof_id_filtro = int(prof_filtro.split(" - ")[0])

        if st.button("Buscar repasses", key="rep_buscar"):
            dados = listar_repasses(data_inicio_r, data_fim_r, status_rep_filtro, prof_id_filtro)

            if not dados:
                st.info("Nenhum repasse encontrado.")
            else:
                import pandas as pd

                df = pd.DataFrame(
                    dados,
                    columns=[
                        "ID", "Profissional", "Paciente", "Data atendimento", "Data repasse", "Valor", "Status"
                    ]
                )
                st.dataframe(df, use_container_width=True)

def render_notas_fiscais():
    st.subheader("Notas Fiscais")

    _botao_voltar_inicio("voltar_nf")

    mes_ref = st.date_input("Mês de referência", value=date.today(), key="nf_mes_ref")
    data_inicio, data_fim = _mes_range(mes_ref)
    competencia = data_inicio

    st.caption(
        f"Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}"
    )

    st.markdown("**Dados para NF (lembra para próximos meses)**")
    st.caption("Por padrão, usamos os dados do paciente para emissão da NF.")

    pacientes_nf = listar_pacientes("")
    if pacientes_nf:
        opcoes_nf = [f"{p[0]} - {p[1]} (CPF: {p[2]})" for p in pacientes_nf]
        escolha_nf = st.selectbox("Paciente", opcoes_nf, key="nf_paciente")
        paciente_id_nf = int(escolha_nf.split(" - ")[0])

        dados_pagador = buscar_pagador_paciente(paciente_id_nf)
        if dados_pagador:
            _, _, pagador_mesmo_padrao, pagador_nome_padrao, pagador_cpf_padrao = dados_pagador
        else:
            pagador_mesmo_padrao, pagador_nome_padrao, pagador_cpf_padrao = True, "", ""

        dados_nf = st.checkbox(
            "Dados para NF",
            value=not pagador_mesmo_padrao,
            key=f"nf_dados_nf_{paciente_id_nf}"
        )
        pagador_nome = ""
        pagador_cpf = ""
        if dados_nf:
            pagador_nome = st.text_input(
                "Nome do pagador",
                value=pagador_nome_padrao or "",
                key=f"nf_pagador_nome_{paciente_id_nf}"
            )
            pagador_cpf = st.text_input(
                "CPF do pagador",
                value=pagador_cpf_padrao or "",
                key=f"nf_pagador_cpf_{paciente_id_nf}"
            )

        if st.button("Salvar dados de NF", key="nf_salvar_pagador"):
            if dados_nf:
                pagador_cpf_digits = only_digits(pagador_cpf)
                if not pagador_nome:
                    st.error("Nome do pagador é obrigatório.")
                    st.stop()
                if not pagador_cpf:
                    st.error("CPF do pagador é obrigatório.")
                    st.stop()
                if len(pagador_cpf_digits) != 11:
                    st.error("CPF do pagador deve ter 11 dígitos.")
                    st.stop()
                pagador_cpf = pagador_cpf_digits
                pagador_mesmo = False
            else:
                pagador_nome = None
                pagador_cpf = None
                pagador_mesmo = True

            resultado = definir_pagador_nf(
                paciente_id_nf,
                competencia,
                data_inicio,
                data_fim,
                pagador_mesmo,
                pagador_nome,
                pagador_cpf
            )

            atualizacao = atualizar_pagador_paciente(
                paciente_id_nf,
                pagador_mesmo,
                pagador_nome,
                pagador_cpf
            )
            if atualizacao is not True:
                st.error(f"Erro ao atualizar padrão do paciente: {atualizacao}")

            if resultado is True or (isinstance(resultado, int) and resultado > 0):
                st.success("Pagador atualizado com sucesso.")
            elif resultado == 0:
                st.info("Sem atendimentos no mês para esse paciente.")
            else:
                st.error(f"Erro ao salvar pagador: {resultado}")
    else:
        st.info("Nenhum paciente encontrado.")

    st.markdown("---")

    notas = listar_notas_fiscais_mes(competencia)

    if not notas:
        st.info("Nenhuma NF encontrada para o mês selecionado.")
    else:
        import pandas as pd

        df = pd.DataFrame(
            notas,
            columns=["ID", "Paciente", "Pagador", "CPF", "Total (R$)", "Status", "Competência"]
        )
        st.dataframe(df, use_container_width=True)

    st.caption(
        "Próxima fase: gerar NFs do mês, QR Code de pagamento e rastrear status para emissão da NF."
    )
