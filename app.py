import streamlit as st
from datetime import date
from database import get_connection, inserir_paciente, listar_pacientes

st.title("Sistema Revitalize - Clínica")

menu = st.sidebar.selectbox(
    "Menu",
    [
        "Início",
        "Cadastrar Paciente",
        "Nova Evolução",
        "Histórico do Paciente",
        "Avaliação Inicial"
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

            from database import listar_tipos_atendimento

            tipos = listar_tipos_atendimento()

            opcoes = [f"{t[0]} - {t[2]}" for t in tipos]

            tipo_escolhido = st.selectbox("Tipo de atendimento", opcoes)

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









