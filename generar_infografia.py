from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, black, white, lightgrey
import os

def create_infographic(filename):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    
    # Background
    c.setFillColor(HexColor('#f0f2f5'))
    c.rect(0, 0, width, height, fill=1)
    
    # Title Section
    c.setFillColor(HexColor('#2c3e50'))
    c.rect(0, height - 100, width, 100, fill=1, stroke=0)
    
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width/2, height - 50, "Solución de Problemas en la Tarjeta Madre")
    
    c.setFont("Helvetica", 14)
    c.drawCentredString(width/2, height - 75, "Experiencias Prácticas y Soluciones")

    # Content Settings
    y_position = height - 130
    margin = 50
    box_height = 180
    
    components = [
        {
            "title": "1. Memoria RAM (Ranuras DIMM)",
            "problem": "Problema: El equipo enciende pero no da video (pantalla negra).",
            "cause": "Causa: Suciedad o polvo en los contactos dorados.",
            "solution": "Solución: Limpiar contactos con goma blanca y ranuras con aire.",
            "image_path": "ram.png"
        },
        {
            "title": "2. Batería CMOS (Pila CR2032)",
            "problem": "Problema: La fecha y hora se desconfiguran al apagar el PC.",
            "cause": "Causa: La batería ha agotado su vida útil.",
            "solution": "Solución: Reemplazar por una nueva batería CR2032.",
            "image_path": "battery.png"
        },
        {
            "title": "3. Panel Frontal (Conexiones)",
            "problem": "Problema: El botón de encendido o LEDs no funcionan.",
            "cause": "Causa: Cables conectados en pines incorrectos.",
            "solution": "Solución: Verificar manual y conectar respetando polaridad.",
            "image_path": "panel.png"
        }
    ]
    
    for comp in components:
        # Container Box
        c.setFillColor(white)
        c.setStrokeColor(HexColor('#bdc3c7'))
        c.roundRect(margin, y_position - box_height, width - 2*margin, box_height, 10, fill=1, stroke=1)
        
        # Text
        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(margin + 20, y_position - 30, comp['title'])
        
        c.setFont("Helvetica", 10)
        c.drawString(margin + 20, y_position - 55, comp['problem'])
        c.drawString(margin + 20, y_position - 70, comp['cause'])
        c.drawString(margin + 20, y_position - 85, comp['solution'])
        
        # Image
        img_x = width - margin - 170
        img_y = y_position - box_height + 40
        img_w = 150
        img_h = 100
        
        if os.path.exists(comp['image_path']):
            try:
                c.drawImage(comp['image_path'], img_x, img_y, width=img_w, height=img_h)
            except Exception as e:
                print(f"Error drawing image {comp['image_path']}: {e}")
                c.setFillColor(lightgrey)
                c.rect(img_x, img_y, img_w, img_h, fill=1)
                c.setFillColor(black)
                c.drawString(img_x + 10, img_y + 40, "Imagen no disponible")
        else:
            c.setFillColor(lightgrey)
            c.rect(img_x, img_y, img_w, img_h, fill=1)
            c.setFillColor(black)
            c.drawString(img_x + 10, img_y + 40, "Imagen no encontrada")
        
        y_position -= (box_height + 20)

    # Footer / Credits
    c.setFillColor(HexColor('#34495e'))
    c.rect(0, 0, width, 60, fill=1, stroke=0)
    
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin, 35, "Fuentes:")
    c.setFont("Helvetica", 9)
    c.drawString(margin, 20, "Manuales de Fabricante, Experiencia Personal.")
    
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(width - margin, 35, "Créditos:")
    c.setFont("Helvetica", 9)
    c.drawRightString(width - margin, 20, "Elaborado por: Adán Muñoz Pablo")
    
    c.save()
    print(f"Infografía guardada como {filename}")

if __name__ == "__main__":
    create_infographic("Adan_Munoz_Pablo_Entregable_1.pdf")
