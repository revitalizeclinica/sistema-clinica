import streamlit as st
from database import get_connection, inserir_paciente

st.title("Sistema Revitalize - Clínica")

menu = st.sidebar.selectbox(
    "Menu",
    ["Início", "Cadastrar Paciente"]
)

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

    with st.form("form_paciente"):

        nome = st.text_input("Nome completo")
        cpf = st.text_input("CPF")
    
        data_nascimento = st.date_input(
            "Data de nascimento",
            min_value=None,
            max_value=None,
            value=None,
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
                    nome,
                    cpf,
                    data_nascimento,
                    telefone,
                    email,
                    contato_emergencia,
                    observacoes
                )
        
                if resultado is True:
                    st.success("Paciente cadastrado com sucesso!")
                else:
                    st.error(f"Erro ao salvar: {resultado}")


