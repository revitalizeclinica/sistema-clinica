from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
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
    candidatos_logo = [
        os.path.normpath(os.path.join(base_dir, "assets", "logo.png")),
        os.path.normpath(os.path.join(base_dir, "..", "assets", "logo.png")),
    ]
    logo_path = next((p for p in candidatos_logo if os.path.exists(p)), None)
    topo_margem = 1.2 * cm
    logo_width = 12 * cm
    logo_height = 4.5 * cm

    if logo_path:
        try:
            logo_reader = ImageReader(logo_path)
            img_w, img_h = logo_reader.getSize()
            escala = min(logo_width / img_w, logo_height / img_h)
            draw_w = img_w * escala
            draw_h = img_h * escala
            x_logo = (largura - draw_w) / 2
            y_logo = altura - topo_margem - draw_h
            c.drawImage(
                logo_reader,
                x_logo,
                y_logo,
                width=draw_w,
                height=draw_h,
                mask="auto"
            )
            y = y_logo - 1.2 * cm
        except Exception:
            y = altura - 4.0 * cm
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


def gerar_pdf_relatorio_profissional(nome_profissional, periodo, dados):
    # dados: lista de tuplas (data, paciente, tipo, valor_consulta, repasse_fixo)
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    largura, altura = A4

    def preparar_pagina():
        c.setFillColorRGB(1, 1, 0.9)
        c.rect(0, 0, largura, altura, fill=1)
        c.setFillColorRGB(0, 0, 0)
        c.setStrokeColorRGB(0, 0, 0)

    preparar_pagina()

    base_dir = os.path.dirname(__file__)
    candidatos_logo = [
        os.path.normpath(os.path.join(base_dir, "assets", "logo.png")),
        os.path.normpath(os.path.join(base_dir, "..", "assets", "logo.png")),
    ]
    logo_path = next((p for p in candidatos_logo if os.path.exists(p)), None)
    topo_margem = 1.2 * cm
    logo_width = 12 * cm
    logo_height = 4.5 * cm

    if logo_path:
        try:
            logo_reader = ImageReader(logo_path)
            img_w, img_h = logo_reader.getSize()
            escala = min(logo_width / img_w, logo_height / img_h)
            draw_w = img_w * escala
            draw_h = img_h * escala
            x_logo = (largura - draw_w) / 2
            y_logo = altura - topo_margem - draw_h
            c.drawImage(
                logo_reader,
                x_logo,
                y_logo,
                width=draw_w,
                height=draw_h,
                mask="auto"
            )
            y = y_logo - 1.0 * cm
        except Exception:
            y = altura - 4.0 * cm
    else:
        y = altura - 4.0 * cm

    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(largura / 2, y, f"Relatório de Consultas – {nome_profissional}")
    y -= 0.8 * cm

    c.setFont("Helvetica", 10)
    c.drawCentredString(largura / 2, y, f"Período: {periodo}")
    y -= 1.0 * cm

    c.setFont("Helvetica-Bold", 9)
    c.drawString(2.2*cm, y, "Data")
    c.drawString(5.4*cm, y, "Paciente")
    c.drawString(10.5*cm, y, "Tipo")
    c.drawRightString(16.5*cm, y, "Valor")
    c.drawRightString(19.0*cm, y, "Repasse")
    y -= 0.4 * cm

    c.setLineWidth(0.5)
    c.line(2.2*cm, y, 19.0*cm, y)
    y -= 0.5 * cm

    c.setFont("Helvetica", 9)

    total_consultas = 0
    total_valor = 0.0
    total_repasse = 0.0

    for data, paciente, tipo, valor, repasse_fixo in dados:
        c.drawString(2.2*cm, y, data.strftime("%d/%m/%Y"))
        c.drawString(5.4*cm, y, str(paciente)[:25])
        c.drawString(10.5*cm, y, str(tipo)[:20])
        c.drawRightString(16.5*cm, y, f"R$ {valor:.2f}")
        c.drawRightString(19.0*cm, y, f"R$ {repasse_fixo:.2f}")

        total_consultas += 1
        total_valor += float(valor)
        total_repasse += float(repasse_fixo)

        y -= 0.45 * cm

        if y < 4 * cm:
            c.showPage()
            preparar_pagina()
            y = altura - 3 * cm

    y -= 0.6 * cm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2.2*cm, y, f"Consultas: {total_consultas}")
    c.drawRightString(19.0*cm, y, f"Total: R$ {total_valor:.2f}")

    y -= 0.5 * cm
    c.drawRightString(19.0*cm, y, f"Repasse: R$ {total_repasse:.2f}")

    y -= 1.2 * cm
    c.setFont("Helvetica", 9)
    c.drawString(2.2*cm, y, "Relatório gerado para conferência e pagamento do profissional.")

    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer
