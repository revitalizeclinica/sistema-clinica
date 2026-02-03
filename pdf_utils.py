from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from io import BytesIO
import os


def gerar_pdf_relatorio_paciente(nome_paciente, periodo, dados):

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    largura, altura = A4
    def preparar_pagina():
        # Fundo
        c.setFillColorRGB(1, 1, 0.9)
        c.rect(0, 0, largura, altura, fill=1)
        # Texto e traços em preto para não ficar invisível no fundo claro
        c.setFillColorRGB(0, 0, 0)
        c.setStrokeColorRGB(0, 0, 0)

    preparar_pagina()

    # Logo (centralizado, abaixo da margem)
    base_dir = os.path.dirname(__file__)
    logo_path = os.path.normpath(os.path.join(base_dir, "..", "assets", "logo.png"))
    topo_margem = 1.2 * cm
    logo_width = 12 * cm
    logo_height = 4.5 * cm

    if os.path.exists(logo_path):
        x_logo = (largura - logo_width) / 2
        y_logo = altura - topo_margem - logo_height
        c.drawImage(
            logo_path,
            x_logo,
            y_logo,
            width=logo_width,
            height=logo_height,
            preserveAspectRatio=True
        )
        y = y_logo - 1.2 * cm
    else:
        y = altura - 4.0 * cm

    # Título
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(largura / 2, y, f"Controle de Sessões e Pagamentos – {nome_paciente}")
    y -= 1.2 * cm

    # Cabeçalho da tabela
    c.setFont("Helvetica-Bold", 10)
    c.drawString(3*cm, y, "Data")
    c.drawString(7*cm, y, "Sessão")
    c.drawRightString(17*cm, y, "Valor")
    y -= 0.4 * cm

    c.setLineWidth(0.5)
    c.line(3*cm, y, 17*cm, y)
    y -= 0.5 * cm

    c.setFont("Helvetica", 10)

    total = 0
    contador = 1

    for data, tipo, valor in dados:
        c.drawString(3*cm, y, data.strftime("%d/%m/%Y"))
        c.drawString(7*cm, y, f"{contador} ({tipo})")
        c.drawRightString(17*cm, y, f"R$ {valor:.2f}")
        total += valor
        contador += 1
        y -= 0.5 * cm

        if y < 4 * cm:
            c.showPage()
            preparar_pagina()
            y = altura - 3 * cm

    y -= 0.8 * cm
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(17*cm, y, f"Total: R$ {total:.2f}")

    # Rodapé
    y -= 1.2 * cm
    c.setFont("Helvetica", 9)
    c.drawString(3*cm, y, "Os pagamentos devem ser realizados até o 5º dia útil de cada mês via PIX:")
    y -= 0.5 * cm
    c.drawString(3*cm, y, "CNPJ: 42054842000176")
    y -= 0.4 * cm
    c.drawString(3*cm, y, "Msv Fisioterapia Ltda – Nubank")

    y -= 1.2 * cm
    c.setFont("Helvetica-Oblique", 9)
    c.drawCentredString(largura / 2, y, "Cuidar do corpo é investir no futuro. Obrigada por confiar em nossa equipe!")

    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer
