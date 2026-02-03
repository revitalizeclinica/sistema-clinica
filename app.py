import streamlit as st
from datetime import date
from database import get_connection, inserir_paciente, listar_pacientes

st.title("Sistema Revitalize - Clínica")

menu = st.sidebar.selectbox(
    "Menu",
    [
        "Início",
        "Cadastrar Paciente",
        "Listar Pacientes",
        "Nova Evolução",
        "Histórico do Paciente"
    ]
)


# Controle de mensagens após rerun
if "mensagem_sucesso" not in st.session_state:
    st.session_state.mensagem_sucesso = ""

# Controle para resetar o formulário
if "form_key" not in st.session_state:
    st.session_state.form_key = 0

## Incio do menú

if menu == "Início":
    st.write("Bem-vindo ao sistema da clínica!")
    conn = get_connection()
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
        
        enviado = st.form_submit_button("Salvar")
    
    if enviado:
        if not nome:
            st.error("Nome é obrigatório!")
        elif not cpf:
            st.error("CPF é obrigatório!")
        else:
            resultado = inserir_paciente(
                nome, cpf, data_nascimento,
                telefone, email, contato_emergencia, observacoes
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

            resumo = st.text_area("Resumo da evolução")
            condutas = st.text_area("Condutas realizadas")
            resposta = st.text_area("Resposta do paciente")
            objetivos = st.text_area("Objetivos para o próximo período")
            observacoes = st.text_area("Observações adicionais")

            enviado = st.form_submit_button("Salvar evolução")

            if enviado:

                if not profissional:
                    st.error("Informe o nome do profissional.")
                else:
                    resultado = inserir_evolucao(
                        paciente_id,
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

    filtro = st.text_input("Buscar paciente por nome ou CPF")

    pacientes = listar_pacientes(filtro)

    if not pacientes:
        st.info("Nenhum paciente encontrado.")
    else:
        # Criar lista de seleção
        opcoes = [f"{p[0]} - {p[1]} (CPF: {p[2]})" for p in pacientes]

        escolha = st.selectbox("Selecione o paciente", opcoes)

        paciente_id = int(escolha.split(" - ")[0])

        st.write(f"**Paciente selecionado:** {escolha}")

        evolucoes = listar_evolucoes_por_paciente(paciente_id)

        if not evolucoes:
            st.info("Nenhuma evolução registrada para este paciente.")
        else:
            for e in evolucoes:
                st.markdown("---")
                st.write(f"**Data:** {e[1]}")
                st.write(f"**Profissional:** {e[2]}")
                st.write("**Resumo:**")
                st.write(e[3])



