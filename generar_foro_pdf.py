from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT

def create_forum_pdf(filename):
    doc = SimpleDocTemplate(filename, pagesize=A4,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    
    Story = []
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
    styles.add(ParagraphStyle(name='HeaderCustom', parent=styles['Heading1'], textColor=HexColor('#2c3e50')))
    styles.add(ParagraphStyle(name='SubHeaderCustom', parent=styles['Heading2'], textColor=HexColor('#34495e'), spaceBefore=12))

    # Title
    Story.append(Paragraph("Participación en Foro: Protección de Equipo de Cómputo", styles['HeaderCustom']))
    Story.append(Paragraph("Alumno: Adán Muñoz Pablo", styles['Normal']))
    Story.append(Spacer(1, 24))

    # Main Post
    Story.append(Paragraph("Aportación Principal", styles['SubHeaderCustom']))
    Story.append(Paragraph("<b>Asunto:</b> 5 Estrategias Integrales para la Protección de Equipos de Cómputo", styles['Normal']))
    Story.append(Spacer(1, 12))
    
    intro = """Hola a todos,<br/><br/>
    Después de analizar las mejores prácticas de mantenimiento y seguridad, comparto las cinco medidas fundamentales que implemento para proteger mis equipos, abarcando tanto la integridad física (hardware) como la lógica (software):"""
    Story.append(Paragraph(intro, styles['Justify']))
    Story.append(Spacer(1, 12))

    points = [
        ("1. Uso de Sistema de Alimentación Ininterrumpida (No-Break/UPS)", 
         "Protege el hardware contra picos de voltaje y cortes repentinos de energía. Los apagones bruscos pueden dañar físicamente los discos duros mecánicos y corromper archivos del sistema operativo irremediablemente."),
        ("2. Limpieza Física Semestral (Aire Comprimido y Pasta Térmica)",
         "El polvo actúa como aislante térmico, provocando sobrecalentamiento que reduce la vida útil de los componentes (CPU, GPU). Mantener los ventiladores limpios asegura un flujo de aire óptimo."),
        ("3. Actualizaciones Automáticas del Sistema Operativo y Drivers",
         "Las actualizaciones no solo traen nuevas funciones, sino 'parches de seguridad' críticos. Los ciberdelincuentes explotan vulnerabilidades conocidas en versiones antiguas de software."),
        ("4. Solución Antimalware con Protección en Tiempo Real",
         "Hoy en día no basta con escanear archivos manualmente. La protección en tiempo real bloquea scripts maliciosos al navegar por internet o descargar correos, actuando antes de que el virus infecte el sistema."),
        ("5. Estrategia de Respaldo 3-2-1",
         "Ningún sistema es infalible. Mantengo 3 copias de mis datos, en 2 medios diferentes (ej. disco duro local y disco externo), y 1 copia en la nube. Esto garantiza que la información siempre sea recuperable.")
    ]

    for title, body in points:
        Story.append(Paragraph(f"<b>{title}</b>", styles['Normal']))
        Story.append(Paragraph(f"<i>¿Por qué?</i> {body}", styles['Justify']))
        Story.append(Spacer(1, 8))

    Story.append(Paragraph("Saludos,<br/><b>Adán Muñoz Pablo</b>", styles['Normal']))
    Story.append(Spacer(1, 24))
    
    # Replies
    Story.append(Paragraph("Aportaciones a Compañeros", styles['SubHeaderCustom']))
    
    # Reply 1
    Story.append(Paragraph("<b>Respuesta a Compañero 1 (Enfoque: Mantenimiento Físico)</b>", styles['Normal']))
    reply1 = """Hola [Compañero],<br/><br/>
    Coincido totalmente contigo en la importancia de la ubicación física del equipo. A menudo subestimamos cómo factores ambientales como la humedad o la luz solar directa pueden degradar los plásticos y circuitos. Me pareció muy interesante tu punto, ya que complementa muy bien la necesidad de una limpieza interna periódica. ¡Buen aporte!<br/><br/>
    Saludos."""
    Story.append(Paragraph(reply1, styles['Justify']))
    Story.append(Spacer(1, 12))

    # Reply 2
    Story.append(Paragraph("<b>Respuesta a Compañero 2 (Enfoque: Seguridad Software)</b>", styles['Normal']))
    reply2 = """Hola [Compañero],<br/><br/>
    Muy acertado tu comentario sobre el software. Quisiera agregar que, además del antivirus que mencionas, el uso de gestores de contraseñas y la autenticación en dos pasos (2FA) son barreras vitales hoy en día. Muchas veces la 'ingeniería social' logra saltarse el antivirus, pero el 2FA detiene el acceso no autorizado. Gracias por compartir tus estrategias.<br/><br/>
    Saludos."""
    Story.append(Paragraph(reply2, styles['Justify']))

    doc.build(Story)
    print(f"PDF guardado como {filename}")

if __name__ == "__main__":
    create_forum_pdf("Adan_Munoz_Pablo_Foro_Discusion.pdf")


