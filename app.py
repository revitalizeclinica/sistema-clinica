import streamlit as st
from datetime import date
from database import (
    get_connection,
    inserir_paciente,
    listar_pacientes,
    relatorio_paciente,
    relatorio_paciente_agrupado,
    relatorio_paciente_detalhado,
    relatorio_contador
)
from pdf_utils import gerar_pdf_relatorio_paciente


# Estado para controlar menus e permitir "voltar" do administrativo
if "main_menu" not in st.session_state:
    st.session_state.main_menu = "Início"
if "admin_menu" not in st.session_state:
    st.session_state.admin_menu = "Selecione..."
if "nav_to" not in st.session_state:
    st.session_state.nav_to = None
if "admin_authed" not in st.session_state:
    st.session_state.admin_authed = False
if "admin_reset" not in st.session_state:
    st.session_state.admin_reset = False
if "admin_pwd_reset" not in st.session_state:
    st.session_state.admin_pwd_reset = False

# Aplicar navegação pendente ANTES de criar os widgets
if st.session_state.nav_to == "Início":
    st.session_state.main_menu = "Início"
    st.session_state.admin_menu = "Selecione..."
    st.session_state.nav_to = None
if st.session_state.admin_reset:
    st.session_state.admin_menu = "Selecione..."
    st.session_state.admin_reset = False
if st.session_state.admin_pwd_reset:
    st.session_state.admin_pwd = ""
    st.session_state.admin_pwd_reset = False

def on_main_menu_change():
    # Ao escolher uma opção do menu principal, sai do menu administrativo
    st.session_state.admin_menu = "Selecione..."

main_menu = st.sidebar.selectbox(
    "Menu",
    [
        "Início",
        "Cadastrar Paciente",
        "Nova Evolução",
        "Histórico do Paciente",
        "Avaliação Inicial"
    ],
    key="main_menu",
    on_change=on_main_menu_change
)

st.sidebar.markdown("---")
st.sidebar.subheader("Administrativo")

if not st.session_state.admin_authed:
    senha_admin = st.sidebar.text_input("Senha", type="password", key="admin_pwd")
    if st.sidebar.button("Entrar", key="admin_login"):
        if senha_admin == "r3v1t4l1z3":
            st.session_state.admin_authed = True
            st.session_state.admin_pwd_reset = True
            st.rerun()
        else:
            st.sidebar.error("Senha incorreta.")

    if st.session_state.admin_menu != "Selecione...":
        st.session_state.admin_menu = "Selecione..."

    admin_menu = st.sidebar.selectbox(
        "Administrativo",
        ["Selecione..."],
        key="admin_menu",
        disabled=True
    )
else:
    admin_menu = st.sidebar.selectbox(
        "Administrativo",
        [
            "Selecione...",
            "Relatório por Paciente",
            "Relatório para Contador",
            "Atualizar Preços"
        ],
        key="admin_menu"
    )

    if st.sidebar.button("Sair", key="admin_logout"):
        st.session_state.admin_authed = False
        st.session_state.admin_reset = True
        st.rerun()

menu = admin_menu if admin_menu != "Selecione..." else main_menu

# Controle de mensagens após rerun
if "mensagem_sucesso" not in st.session_state:
    st.session_state.mensagem_sucesso = ""

# Controle para resetar o formulário
if "form_key" not in st.session_state:
    st.session_state.form_key = 0



## Incio do menú

if menu == "Início":
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

elif menu == "Cadastrar Paciente":
    st.subheader("Cadastro de Paciente")
    
    # Exibir mensagem de sucesso caso exista
    if st.session_state.mensagem_sucesso:
        st.success(st.session_state.mensagem_sucesso)
        st.session_state.mensagem_sucesso = ""
    
    # Usar uma key dinâmica para forçar a recriação do formulário
    with st.form(key=f"form_paciente_{st.session_state.form_key}"):
        nome = st.text_input("Nome completo")
        cpf = st.text_input("CPF")
        data_nascimento = st.date_input(
            "Data de nascimento",
            min_value=date(1900, 1, 1),
            max_value=date.today(),
            format="DD/MM/YYYY"
        )
        telefone = st.text_input("Telefone")
        email = st.text_input("Email")
        contato_emergencia = st.text_input("Contato de emergência")
        observacoes = st.text_area("Observações")
        solicita_nota = st.checkbox("Solicita nota fiscal?")
        
        enviado = st.form_submit_button("Salvar")
    
    if enviado:
        cpf_digits = "".join([c for c in cpf if c.isdigit()])
        if not nome:
            st.error("Nome é obrigatório!")
        elif not cpf:
            st.error("CPF é obrigatório!")
        elif len(cpf_digits) != 11:
            st.error("CPF deve ter 11 dígitos.")
        else:
            resultado = inserir_paciente(
                nome, cpf_digits, data_nascimento,
                telefone, email, contato_emergencia, observacoes, solicita_nota
            )
            
            if resultado is True:
                # Incrementar a key do formulário para forçar recriação
                st.session_state.form_key += 1
                st.session_state.mensagem_sucesso = "Paciente cadastrado com sucesso!"
                st.rerun()
            else:
                st.error(f"Erro ao salvar: {resultado}")

elif menu == "Listar Pacientes":

    st.subheader("Pacientes Cadastrados")

    filtro = st.text_input("Buscar por nome ou CPF")
    st.caption("Digite parte do nome ou CPF para filtrar")


    pacientes = listar_pacientes(filtro)

    if not pacientes:
        st.info("Nenhum paciente encontrado.")
    else:
        import pandas as pd

        df = pd.DataFrame(
            pacientes,
            columns=["ID", "Nome", "CPF", "Nascimento", "Telefone", "Email"]
        )

        st.dataframe(df, use_container_width=True)

elif menu == "Nova Evolução":

    st.subheader("Registrar Nova Evolução")

    from database import listar_pacientes, inserir_evolucao

    filtro = st.text_input("Buscar paciente por nome ou CPF")

    pacientes = listar_pacientes(filtro)

    if not pacientes:
        st.info("Nenhum paciente encontrado.")
    else:
        import pandas as pd

        df = pd.DataFrame(
            pacientes,
            columns=["ID", "Nome", "CPF", "Nascimento", "Telefone", "Email"]
        )

        st.dataframe(df, use_container_width=True)

        # Criar lista de opções para seleção
        opcoes = [f"{p[0]} - {p[1]} (CPF: {p[2]})" for p in pacientes]

        escolha = st.selectbox("Selecione o paciente", opcoes)

        # Extrair o ID do paciente selecionado
        paciente_id = int(escolha.split(" - ")[0])

        with st.form("form_evolucao", clear_on_submit=True):

            data_registro = st.date_input("Data do atendimento")
            profissional = st.text_input("Profissional responsável")

            from database import listar_tipos_atendimento

            tipos = listar_tipos_atendimento()

            if not tipos:
                st.info("Nenhum tipo de atendimento cadastrado.")
                st.stop()

            opcoes = ["Selecione o tipo de atendimento"] + [f"{t[0]} - {t[2]}" for t in tipos]

            tipo_escolhido = st.selectbox("Tipo de atendimento", opcoes)

            tipo_id = None
            if tipo_escolhido != opcoes[0]:
                tipo_id = int(tipo_escolhido.split(" - ")[0])


            resumo = st.text_area("Resumo da evolução")
            condutas = st.text_area("Condutas realizadas")
            resposta = st.text_area("Resposta do paciente")
            objetivos = st.text_area("Objetivos para o próximo período")
            observacoes = st.text_area("Observações adicionais")

            enviado = st.form_submit_button("Salvar evolução")

            if enviado:

                if not profissional:
                    st.error("Informe o nome do profissional.")
                elif tipo_id is None:
                    st.error("Selecione o tipo de atendimento.")
                else:
                    resultado = inserir_evolucao(
                        paciente_id,
                        tipo_id,
                        data_registro,
                        profissional,
                        resumo,
                        condutas,
                        resposta,
                        objetivos,
                        observacoes
                    )


                    if resultado is True:
                        st.success("Evolução registrada com sucesso!")
                    else:
                        st.error(f"Erro ao salvar: {resultado}")

elif menu == "Histórico do Paciente":

    st.subheader("Histórico de Evoluções")

    from database import listar_pacientes, listar_evolucoes_por_paciente

    # Garantir que o estado existe
    if "evolucao_aberta" not in st.session_state:
        st.session_state.evolucao_aberta = None

    filtro = st.text_input("Buscar paciente por nome ou CPF")

    pacientes = listar_pacientes(filtro)

    if not pacientes:
        st.info("Nenhum paciente encontrado.")
    else:
        opcoes = [f"{p[0]} - {p[1]} (CPF: {p[2]})" for p in pacientes]

        escolha = st.selectbox("Selecione o paciente", opcoes)

        paciente_id = int(escolha.split(" - ")[0])

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


            # Exibir detalhes APENAS se alguma evolução foi aberta
        if st.session_state.evolucao_aberta:

            st.markdown("---")
            st.subheader("Detalhes da Evolução")

            detalhe = st.session_state.evolucao_aberta

            st.write(f"**Data:** {detalhe[1]}")
            st.write(f"**Profissional:** {detalhe[2]}")

            def exibir_titulo_valor(titulo, valor):
                st.write(f"### {titulo}")
                st.write(valor if valor else "Não informado")

            exibir_titulo_valor("Resumo da evolução", detalhe[3])
            exibir_titulo_valor("Condutas realizadas", detalhe[4])
            exibir_titulo_valor("Resposta do paciente", detalhe[5])
            exibir_titulo_valor("Objetivos", detalhe[6])
            exibir_titulo_valor("Observações", detalhe[7])


elif menu == "Avaliação Inicial":

    st.subheader("Avaliação Clínica Inicial")

    from database import listar_pacientes, inserir_avaliacao, buscar_avaliacao

    filtro = st.text_input("Buscar paciente")

    pacientes = listar_pacientes(filtro)

    if not pacientes:
        st.info("Nenhum paciente encontrado.")
    else:
        opcoes = [f"{p[0]} - {p[1]}" for p in pacientes]
        escolha = st.selectbox("Selecione o paciente", opcoes)

        paciente_id = int(escolha.split(" - ")[0])

        existente = buscar_avaliacao(paciente_id)

        if existente:
            st.success("Este paciente já possui avaliação inicial cadastrada.")

            st.markdown("---")
            st.subheader("Detalhes da Avaliação Inicial")

            st.write(f"**Data da avaliação:** {existente[2]}")
            st.write(f"**Profissional:** {existente[3]}")

            def mostrar_campo(titulo, valor):
                st.write(f"### {titulo}")
                st.write(valor if valor else "Não informado")

            mostrar_campo("Queixa principal", existente[4])
            mostrar_campo("Diagnóstico", existente[5])

            mostrar_campo("Histórico", existente[6])
            mostrar_campo("Medicamentos em uso", existente[7])

            mostrar_campo("Avaliação da dor", existente[8])
            mostrar_campo("Mobilidade", existente[9])
            mostrar_campo("Força muscular", existente[10])
            mostrar_campo("Limitações funcionais", existente[11])
            mostrar_campo("Marcha", existente[12])
            mostrar_campo("Equilíbrio", existente[13])

            mostrar_campo("Objetivos do tratamento", existente[14])
            mostrar_campo("Plano terapêutico", existente[15])

elif menu == "Relatório por Paciente":

    st.subheader("Relatório por Paciente")

    if st.button("Voltar para Início", key="voltar_rel_paciente"):
        st.session_state.nav_to = "Início"
        st.rerun()

    filtro = st.text_input("Buscar paciente por nome ou CPF")
    pacientes = listar_pacientes(filtro)

    if not pacientes:
        st.info("Nenhum paciente encontrado.")
    else:
        pacientes_por_id = {p[0]: p[1] for p in pacientes}
        opcoes = [f"{p[0]} - {p[1]} (CPF: {p[2]})" for p in pacientes]
        escolha = st.selectbox("Selecione o paciente", opcoes)

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

            dados_detalhados = relatorio_paciente_detalhado(paciente_id, data_inicio, data_fim)
            if dados_detalhados:
                dados_pdf = [(d[0], d[1], d[2]) for d in dados_detalhados]
                periodo = f"{data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}"
                pdf_buffer = gerar_pdf_relatorio_paciente(nome_paciente, periodo, dados_pdf)

                st.download_button(
                    "Baixar relatório do paciente (PDF)",
                    data=pdf_buffer.getvalue(),
                    file_name=f"relatorio_paciente_{paciente_id}_{data_inicio}_a_{data_fim}.pdf",
                    mime="application/pdf"
                )
            else:
                st.info("Sem dados para gerar o PDF do paciente.")


elif menu == "Relatório para Contador":

    st.subheader("Relatório para Contador")

    if st.button("Voltar para Início", key="voltar_rel_contador"):
        st.session_state.nav_to = "Início"
        st.rerun()

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

            df = pd.DataFrame(
                dados,
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

elif menu == "Atualizar Preços":

    st.subheader("Atualizar Preços de Consultas")

    if st.button("Voltar para Início", key="voltar_preco"):
        st.session_state.nav_to = "Início"
        st.rerun()

    from database import listar_tipos_atendimento_com_valor, atualizar_preco_tipo_atendimento

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

st.markdown(
    """
    <style>
    .app-footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        text-align: center;
        color: #6b7280;
        background: rgba(255, 255, 255, 0.8);
        padding: 6px 0;
        font-size: 0.85rem;
        z-index: 9999;
    }
    </style>
    <div class="app-footer">
        Desenvolvido por Alan Alves | Contato: galves.alan@gmail.com
    </div>
    """,
    unsafe_allow_html=True
)














