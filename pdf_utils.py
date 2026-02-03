from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from io import BytesIO


def gerar_pdf_relatorio_paciente(nome_paciente, periodo, dados_df, total):

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    largura, altura = A4

    y = altura - 2 * cm

    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, y, "Relatório de Atendimentos")
    y -= 1 * cm

    c.setFont("Helvetica", 10)
    c.drawString(2 * cm, y, f"Paciente: {nome_paciente}")
    y -= 0.6 * cm

    c.drawString(2 * cm, y, f"Período: {periodo}")
    y -= 1 * cm

    # Cabeçalho da tabela
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2 * cm, y, "Tipo")
    c.drawString(9 * cm, y, "Qtd")
    c.drawString(11 * cm, y, "Valor")
    c.drawString(14 * cm, y, "Subtotal")
    y -= 0.5 * cm

    c.setFont("Helvetica", 10)

    for _, row in dados_df.iterrows():
        c.drawString(2 * cm, y, str(row["Tipo de atendimento"]))
        c.drawRightString(10 * cm, y, str(row["Quantidade"]))
        c.drawRightString(13 * cm, y, f"R$ {row['Valor unitário']:.2f}")
        c.drawRightString(18 * cm, y, f"R$ {row['Subtotal']:.2f}")
        y -= 0.5 * cm

        if y < 3 * cm:
            c.showPage()
            y = altura - 2 * cm

    y -= 0.8 * cm
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(18 * cm, y, f"Total: R$ {total:.2f}")

    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer
