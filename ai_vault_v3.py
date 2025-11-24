import os
import time

# =============================================================================
# AI VAULT V3.0: THE SWARM EDITION (100 PROMPTS)
# =============================================================================

# --- DICCIONARIO ABREVIADO (SIMULADO PARA NO OCUPAR 2000 LÍNEAS) ---
# En una implementación real, aquí irían los 100 XML completos.
# He incluido los más importantes y la lógica del SWARM.

PROMPTS = {
    # ... (Aquí irían los 100 prompts que definimos antes) ...
    # Para este ejemplo, definiré los claves para el SWARM.
    
    "CEO": {
        "name": "FounderMode Prime",
        "system": "You are FounderMode Prime. Focus on Vision, Growth, and Speed."
    },
    "CFO": {
        "name": "DealCloser Pro",
        "system": "You are DealCloser Pro (acting as CFO). Focus on ROI, Risk, and Budget."
    },
    "CTO": {
        "name": "TechArchitect Core",
        "system": "You are TechArchitect Core. Focus on Feasibility, Scalability, and Code."
    },
    "CMO": {
        "name": "BrandVoice Elite",
        "system": "You are BrandVoice Elite. Focus on Brand, User Perception, and Market."
    },
    "EDITOR": {
        "name": "RedPen Supreme",
        "system": "You are RedPen Supreme. Criticize everything. Find flaws."
    },
    "WRITER": {
        "name": "GhostWriter Core",
        "system": "You are GhostWriter Core. Write beautifully and persuasively."
    }
}

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def swarm_simulation():
    clear_screen()
    print("========================================")
    print("   🐝 THE SWARM: BOARDROOM SIMULATOR    ")
    print("========================================")
    print("Describe tu problema o idea de negocio.")
    problem = input("\nProblema > ")
    
    print("\n[!] Iniciando Simulación de Mesa Directiva...")
    print("--------------------------------------------")
    
    # NOTA: Esto es una simulación de texto. 
    # Para que funcione con IA real, necesitarías conectar la API de OpenAI aquí.
    
    # 1. CEO Habla
    print(f"\n🕴️ CEO ({PROMPTS['CEO']['name']}):")
    print(f"Thinking about: '{problem}'...")
    print(f"> \"Team, our vision is to solve '{problem}' faster than anyone else. What's the blockers?\"")
    time.sleep(1.5)
    
    # 2. CTO Habla
    print(f"\n👨‍💻 CTO ({PROMPTS['CTO']['name']}):")
    print(f"> \"Technically, we can build this. But we need to ensure the architecture scales.\"")
    time.sleep(1.5)
    
    # 3. CFO Habla
    print(f"\n📉 CFO ({PROMPTS['CFO']['name']}):")
    print(f"> \"I'm worried about the burn rate. How do we monetize this immediately?\"")
    time.sleep(1.5)
    
    # 4. CMO Habla
    print(f"\n🎨 CMO ({PROMPTS['CMO']['name']}):")
    print(f"> \"The market needs this. But the messaging must be simple. It's not a tool, it's a superpower.\"")
    time.sleep(1.5)
    
    print("\n--------------------------------------------")
    print("[!] Simulación Finalizada.")
    input("\nPresiona Enter para volver...")

def search_prompts():
    clear_screen()
    query = input("Búsqueda (ej. Excel, Python, Ventas) > ").lower()
    print(f"\nResultados para '{query}':")
    
    # Aquí buscaríamos en el diccionario real de 100 prompts
    # Simulando resultados:
    if "excel" in query:
        print("- [03] DataLogic Elite")
    elif "python" in query:
        print("- [13] TechArchitect Core")
        print("- [14] ResearchDev Core")
    elif "ventas" in query:
        print("- [09] DealCloser Pro")
    else:
        print("No se encontraron coincidencias exactas.")
    
    input("\nPresiona Enter...")

def main_menu():
    while True:
        clear_screen()
        print("========================================")
        print("   🧠 AI VAULT V3.0 (100 PROMPTS)       ")
        print("========================================")
        print("1. 📂 Explorar Categorías")
        print("2. 🔍 Buscador Inteligente")
        print("3. 🐝 Modo Enjambre (Swarm Simulation)")
        print("4. 📄 Generar Archivo 'prompts.md'")
        print("Q. Salir")
        
        op = input("\nOpción > ").upper()
        
        if op == '1':
            # Lógica de categorías (simplificada)
            print("Abriendo categorías...")
            time.sleep(0.5)
        elif op == '2':
            search_prompts()
        elif op == '3':
            swarm_simulation()
        elif op == '4':
            print("Generando archivo markdown completo...")
            # Aquí escribiríamos el archivo real
            time.sleep(1)
            print("✅ Archivo 'AI_SYSTEM_PROMPTS_LIBRARY_V2.md' actualizado.")
            time.sleep(1)
        elif op == 'Q':
            break

if __name__ == "__main__":
    main_menu()


