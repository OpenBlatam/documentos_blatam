#!/usr/bin/env python3
"""
Script de Automatización de Outreach a Influencers
==================================================
Este script ayuda a automatizar el proceso de outreach,
pero SIEMPRE personaliza los mensajes antes de enviar.

IMPORTANTE: Este script es una herramienta de ayuda.
NO envíes mensajes sin personalizar profundamente.
"""

import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict, List
import os

class OutreachAutomation:
    def __init__(self, csv_path: str):
        """Inicializa el sistema de outreach"""
        self.csv_path = csv_path
        self.df = None
        self.load_data()
        
    def load_data(self):
        """Carga los datos del CSV"""
        try:
            self.df = pd.read_csv(self.csv_path)
            print(f"✅ Cargados {len(self.df)} influencers")
        except Exception as e:
            print(f"❌ Error cargando CSV: {e}")
            
    def filter_by_category(self, category: str) -> pd.DataFrame:
        """Filtra influencers por categoría"""
        return self.df[self.df['Categoría'] == category]
    
    def filter_by_followers(self, min_followers: int = 0, max_followers: int = None) -> pd.DataFrame:
        """Filtra por rango de seguidores"""
        # Esto requeriría parsear los valores como "~500K"
        # Por ahora, retornamos todos
        return self.df
    
    def filter_verified_only(self) -> pd.DataFrame:
        """Filtra solo influencers verificados"""
        return self.df[self.df['Verificado'] == '✅']
    
    def generate_personalized_message(self, influencer_row: pd.Series, template_type: str = "premium") -> str:
        """
        Genera un mensaje personalizado basado en el template
        
        IMPORTANTE: Este es solo un punto de partida.
        DEBES personalizar cada mensaje manualmente.
        """
        nombre = influencer_row['Nombre']
        categoria = influencer_row['Categoría']
        especialidad = influencer_row.get('Especialidad', 'tecnología')
        link = influencer_row['Link Directo Perfil']
        
        templates = {
            "premium": f"""
Hola {nombre},

Vi tu contenido sobre {especialidad} y me encantó.

¿Sabías que puedes automatizar procesos con IA en menos de 5 minutos?

Estamos lanzando una IA que no se para de hacer - automatiza procesos de forma continua. Tu audiencia de {categoria} la amaría.

¿QUÉ INCLUYE LA COLABORACIÓN?
✅ Acceso premium GRATIS de por vida
✅ Materiales listos para usar (videos, posts, stories)
✅ Comisión del 25% por cada conversión
✅ Contenido exclusivo para tu audiencia
✅ Soporte 24/7

PRÓXIMOS PASOS:
1. Te doy acceso ahora mismo
2. Pruebas la plataforma 7 días
3. Si te gusta, creamos contenido juntos
4. Si no, no pasa nada - te quedas con el acceso gratis

¿Te parece? Puedo darte acceso en los próximos 5 minutos.

Link: {link}

¿Hablamos? 🚀

Saludos,
[TU_NOMBRE]
[TU_EMPRESA]
""",
            "short": f"""
Hola {nombre}! 👋

Vi tu contenido sobre {especialidad} y me encantó.

Tenemos una IA que automatiza procesos de forma continua. Tu audiencia la amaría.

✅ Acceso premium gratis
✅ 25% comisión
✅ Materiales listos

¿Te interesa? Link: {link}

¿Hablamos? 🚀
""",
            "linkedin": f"""
Hola {nombre},

Vi tu contenido sobre {especialidad} en LinkedIn y me pareció muy interesante.

Estamos lanzando una IA que automatiza procesos y creemos que tu audiencia profesional la encontraría valiosa.

PROPUESTA DE COLABORACIÓN:
- Acceso premium gratuito
- Comisión del 25% por conversiones
- Materiales profesionales listos para usar

¿Te interesaría explorar una colaboración? Estoy disponible para una breve llamada esta semana.

Link: {link}

Saludos,
[TU_NOMBRE]
[TU_CARGO]
[TU_EMPRESA]
"""
        }
        
        return templates.get(template_type, templates["premium"])
    
    def create_outreach_schedule(self, influencers: pd.DataFrame, days_to_send: int = 30) -> pd.DataFrame:
        """
        Crea un calendario de envío distribuido en varios días
        """
        schedule = []
        total = len(influencers)
        influencers_per_day = max(1, total // days_to_send)
        
        current_date = datetime.now()
        
        for idx, (_, row) in enumerate(influencers.iterrows()):
            day_offset = idx // influencers_per_day
            send_date = current_date + timedelta(days=day_offset)
            
            schedule.append({
                'Nombre': row['Nombre'],
                'Fecha Envío': send_date.strftime('%Y-%m-%d'),
                'Hora Envío': '10:00',  # Mejor hora
                'Plataforma': row.get('Mejor Canal Contacto', 'Instagram DM'),
                'Link': row['Link Directo Perfil'],
                'Estado': 'Pendiente'
            })
        
        return pd.DataFrame(schedule)
    
    def generate_follow_up_message(self, influencer_row: pd.Series, follow_up_day: int = 4) -> str:
        """Genera mensaje de follow-up"""
        nombre = influencer_row['Nombre']
        link = influencer_row['Link Directo Perfil']
        
        if follow_up_day == 4:
            return f"""
Hola {nombre},

Solo quería asegurarme de que viste mi mensaje anterior.

Si no te interesa, no hay problema. Pero si quieres probar la IA gratis por 7 días sin compromiso, aquí está: {link}

¿Te parece?
"""
        elif follow_up_day == 8:
            return f"""
Hola {nombre},

Esta es mi última vez contactándote sobre esto.

Si no te interesa, perfecto. Pero si quieres probar la IA gratis + un bonus exclusivo, aquí está: {link}

Solo disponible hasta {datetime.now() + timedelta(days=7)}.

¿Te parece?
"""
        else:
            return ""
    
    def export_messages(self, influencers: pd.DataFrame, template_type: str = "premium", output_file: str = "mensajes_generados.txt"):
        """
        Exporta mensajes generados a un archivo de texto
        """
        messages = []
        
        for _, row in influencers.iterrows():
            message = self.generate_personalized_message(row, template_type)
            messages.append(f"\n{'='*80}\n")
            messages.append(f"PARA: {row['Nombre']}\n")
            messages.append(f"PLATAFORMA: {row.get('Mejor Canal Contacto', 'Instagram DM')}\n")
            messages.append(f"LINK: {row['Link Directo Perfil']}\n")
            messages.append(f"{'='*80}\n")
            messages.append(message)
            messages.append("\n\n")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("".join(messages))
        
        print(f"✅ Mensajes exportados a {output_file}")
        print(f"⚠️  IMPORTANTE: Personaliza cada mensaje antes de enviar")
    
    def create_tracking_sheet(self, influencers: pd.DataFrame, output_file: str = "tracking_outreach.xlsx"):
        """
        Crea una hoja de cálculo para tracking
        """
        tracking_data = []
        
        for _, row in influencers.iterrows():
            tracking_data.append({
                'Nombre': row['Nombre'],
                'Categoría': row.get('Categoría', ''),
                'Seguidores': row.get('Seguidores', ''),
                'Engagement Rate': row.get('Engagement Rate', ''),
                'Plataforma': row.get('Mejor Canal Contacto', ''),
                'Link': row['Link Directo Perfil'],
                'Fecha Contacto': '',
                'Estado': 'Pendiente',
                'Fecha Respuesta': '',
                'Resultado': '',
                'Notas': ''
            })
        
        df_tracking = pd.DataFrame(tracking_data)
        df_tracking.to_excel(output_file, index=False)
        print(f"✅ Hoja de tracking creada: {output_file}")


def main():
    """Función principal"""
    print("🚀 Script de Automatización de Outreach a Influencers")
    print("=" * 60)
    
    # Ruta al CSV
    csv_path = "100_micro_influencers_ia_colaboracion.csv"
    
    if not os.path.exists(csv_path):
        print(f"❌ No se encontró el archivo: {csv_path}")
        print("   Asegúrate de que el CSV esté en el mismo directorio")
        return
    
    # Inicializar sistema
    outreach = OutreachAutomation(csv_path)
    
    # Menú interactivo
    print("\n¿Qué quieres hacer?")
    print("1. Generar mensajes para todos los influencers")
    print("2. Generar mensajes por categoría")
    print("3. Generar solo para verificados")
    print("4. Crear calendario de envío")
    print("5. Crear hoja de tracking")
    print("6. Salir")
    
    choice = input("\nElige una opción (1-6): ")
    
    if choice == "1":
        template = input("Tipo de template (premium/short/linkedin): ") or "premium"
        outreach.export_messages(outreach.df, template)
        
    elif choice == "2":
        category = input("Categoría (IA y Tecnología/Productividad/Negocios/etc): ")
        filtered = outreach.filter_by_category(category)
        if len(filtered) > 0:
            template = input("Tipo de template (premium/short/linkedin): ") or "premium"
            outreach.export_messages(filtered, template, f"mensajes_{category.replace(' ', '_')}.txt")
        else:
            print("❌ No se encontraron influencers en esa categoría")
            
    elif choice == "3":
        verified = outreach.filter_verified_only()
        if len(verified) > 0:
            template = input("Tipo de template (premium/short/linkedin): ") or "premium"
            outreach.export_messages(verified, template, "mensajes_verificados.txt")
        else:
            print("❌ No se encontraron influencers verificados")
            
    elif choice == "4":
        days = int(input("¿En cuántos días quieres distribuir los envíos? (default 30): ") or "30")
        schedule = outreach.create_outreach_schedule(outreach.df, days)
        schedule.to_excel("calendario_envio.xlsx", index=False)
        print(f"✅ Calendario creado: calendario_envio.xlsx")
        
    elif choice == "5":
        outreach.create_tracking_sheet(outreach.df)
        
    else:
        print("👋 Hasta luego!")
        return
    
    print("\n⚠️  RECUERDA:")
    print("   - Personaliza cada mensaje antes de enviar")
    print("   - Verifica que los links funcionen")
    print("   - No envíes todos el mismo día")
    print("   - Trackea tus resultados")


if __name__ == "__main__":
    main()




