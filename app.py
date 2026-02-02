import streamlit as st
from datetime import date
from database import get_connection, inserir_paciente

st.title("Sistema Revitalize - Clínica")

menu = st.sidebar.selectbox(
    "Menu",
    ["Início", "Cadastrar Paciente"]
)

# Controle de mensagens após rerun
if "mensagem_sucesso" not in st.session_state:
    st.session_state.mensagem_sucesso = ""

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

    with st.form("form_paciente"):

        nome = st.text_input("Nome completo", key="nome")
        cpf = st.text_input("CPF", key="cpf")

        data_nascimento = st.date_input(
            "Data de nascimento",
            min_value=date(1900, 1, 1),
            max_value=date.today(),
            format="DD/MM/YYYY",
            key="data_nascimento"
        )

        telefone = st.text_input("Telefone", key="telefone")
        email = st.text_input("Email", key="email")
        contato_emergencia = st.text_input("Contato de emergência", key="contato_emergencia")
        observacoes = st.text_area("Observações", key="observacoes")

        enviado = st.form_submit_button("Salvar")

        if enviado:

            if not nome:
                st.error("Nome é obrigatório!")

            elif not cpf:
                st.error("CPF é obrigatório!")

            else:
                resultado = inserir_paciente(
                    nome,
                    cpf,
                    data_nascimento,
                    telefone,
                    email,
                    contato_emergencia,
                    observacoes
                )

                if resultado is True:
                    st.session_state.mensagem_sucesso = "Paciente cadastrado com sucesso!"
                    st.rerun()
                else:
                    st.error(f"Erro ao salvar: {resultado}")
