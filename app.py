import streamlit as st
from datetime import date
from database import get_connection, inserir_paciente

st.title("Sistema Revitalize - Clínica")

menu = st.sidebar.selectbox(
    "Menu",
    ["Início", "Cadastrar Paciente", "Listar Pacientes"]
)

# Controle de mensagens após rerun
if "mensagem_sucesso" not in st.session_state:
    st.session_state.mensagem_sucesso = ""

# Controle para resetar o formulário
if "form_key" not in st.session_state:
    st.session_state.form_key = 0

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

    from database import listar_pacientes

    pacientes = listar_pacientes(filtro)

    if not pacientes:
        st.info("Nenhum paciente encontrado.")
    else:
        for p in pacientes:
            st.write("---")
            st.write(f"**Nome:** {p[1]}")
            st.write(f"**CPF:** {p[2]}")
            st.write(f"**Nascimento:** {p[3]}")
            st.write(f"**Telefone:** {p[4]}")
            st.write(f"**Email:** {p[5]}")

