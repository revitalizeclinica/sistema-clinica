import streamlit as st
from screens import (
    render_inicio,
    render_cadastrar_paciente,
    render_listar_pacientes,
    render_nova_evolucao,
    render_historico_paciente,
    render_avaliacao_inicial,
    render_relatorio_paciente,
    render_relatorio_contador,
    render_atualizar_precos,
    render_relatorio_geral,
    render_financeiro,
    render_financeiro_graficos,
    render_cadastrar_profissional,
    render_notas_fiscais
)



# Estado para controlar menus e permitir "voltar" do administrativo
if "main_menu" not in st.session_state:
    st.session_state.main_menu = "Início"
if "admin_menu" not in st.session_state:
    st.session_state.admin_menu = "Selecione..."
if "financeiro_menu" not in st.session_state:
    st.session_state.financeiro_menu = "Selecione..."
if "nav_to" not in st.session_state:
    st.session_state.nav_to = None
if "admin_authed" not in st.session_state:
    st.session_state.admin_authed = False
if "admin_reset" not in st.session_state:
    st.session_state.admin_reset = False
if "financeiro_reset" not in st.session_state:
    st.session_state.financeiro_reset = False
if "admin_pwd_reset" not in st.session_state:
    st.session_state.admin_pwd_reset = False

# Aplicar navegação pendente ANTES de criar os widgets
if st.session_state.nav_to == "Início":
    st.session_state.main_menu = "Início"
    st.session_state.admin_menu = "Selecione..."
    st.session_state.financeiro_menu = "Selecione..."
    st.session_state.nav_to = None
if st.session_state.admin_reset:
    st.session_state.admin_menu = "Selecione..."
    st.session_state.admin_reset = False
if st.session_state.financeiro_reset:
    st.session_state.financeiro_menu = "Selecione..."
    st.session_state.financeiro_reset = False
if st.session_state.admin_pwd_reset:
    st.session_state.admin_pwd = ""
    st.session_state.admin_pwd_reset = False


def on_main_menu_change():
    # Ao escolher uma opção do menu principal, sai do menu administrativo
    st.session_state.admin_menu = "Selecione..."
    st.session_state.financeiro_menu = "Selecione..."


def on_admin_menu_change():
    st.session_state.financeiro_menu = "Selecione..."


def on_financeiro_menu_change():
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
        if senha_admin == "revitalize":
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
            "Atualizar Preços",
            "Relatório Geral",
            "Notas Fiscais"
        ],
        key="admin_menu",
        on_change=on_admin_menu_change
    )

    if st.sidebar.button("Sair", key="admin_logout"):
        st.session_state.admin_authed = False
        st.session_state.admin_reset = True
        st.session_state.financeiro_reset = True
        st.rerun()


st.sidebar.markdown("---")
st.sidebar.subheader("Financeiro")

if not st.session_state.admin_authed:
    financeiro_menu = st.sidebar.selectbox(
        "Financeiro",
        ["Selecione..."],
        key="financeiro_menu",
        disabled=True
    )
else:
    financeiro_menu = st.sidebar.selectbox(
        "Financeiro",
        ["Selecione...", "Financeiro", "Gráficos Financeiros", "Cadastrar Profissional"],
        key="financeiro_menu",
        on_change=on_financeiro_menu_change
    )

menu = (
    financeiro_menu if financeiro_menu != "Selecione..." else
    admin_menu if admin_menu != "Selecione..." else
    main_menu
)

# Controle de mensagens após rerun
if "mensagem_sucesso" not in st.session_state:
    st.session_state.mensagem_sucesso = ""

# Controle para resetar o formulário
if "form_key" not in st.session_state:
    st.session_state.form_key = 0


MENU_HANDLERS = {
    "Início": render_inicio,
    "Cadastrar Paciente": render_cadastrar_paciente,
    "Listar Pacientes": render_listar_pacientes,
    "Nova Evolução": render_nova_evolucao,
    "Histórico do Paciente": render_historico_paciente,
    "Avaliação Inicial": render_avaliacao_inicial,
    "Relatório por Paciente": render_relatorio_paciente,
    "Relatório para Contador": render_relatorio_contador,
    "Atualizar Preços": render_atualizar_precos,
    "Relatório Geral": render_relatorio_geral,
    "Financeiro": render_financeiro,
    "Gráficos Financeiros": render_financeiro_graficos,
    "Cadastrar Profissional": render_cadastrar_profissional,
    "Notas Fiscais": render_notas_fiscais
}

handler = MENU_HANDLERS.get(menu)
if handler:
    handler()


st.markdown(
    """
    <style>
    .app-footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        display: flex;
        justify-content: center;
        align-items: center;
        text-align: center;
        color: #6b7280;
        background: rgba(255, 255, 255, 0.8);
        padding: 8px 0;
        font-size: 0.85rem;
        z-index: 9999;
    }
    .app-footer .footer-content {
        display: flex;
        flex-direction: column;
        gap: 2px;
        line-height: 1.2;
    }
    </style>
    <div class="app-footer">
        <div class="footer-content">
            <div>Desenvolvido por Alan Alves</div>
            <div>Contato: galves.alan@gmail.com</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
