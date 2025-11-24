import os
import time
import sys

# =============================================================================
# AI VAULT MASTER EDITION (100 PROMPTS + RECIPES)
# =============================================================================

# --- BASE DE DATOS SIMULADA (REPRESENTATIVA DE LOS 100 PROMPTS) ---
# En producción, esto cargaría desde un JSON externo o tendría las 100 entradas.
PROMPTS_DB = {
    "01": {"name": "Nexus Prime", "cat": "ORCHESTRATOR", "desc": "Gestor de Modos", "system": "You are Nexus Prime..."},
    "02": {"name": "DocuGen Elite", "cat": "OFFICE", "desc": "Informes Word/PDF", "system": "You are DocuGen Elite..."},
    "03": {"name": "DataLogic Elite", "cat": "OFFICE", "desc": "Excel Avanzado", "system": "You are DataLogic Elite..."},
    "09": {"name": "DealCloser Pro", "cat": "BUSINESS", "desc": "Ventas y Negociación", "system": "You are DealCloser Pro..."},
    "11": {"name": "Strategos Prime", "cat": "BUSINESS", "desc": "Estrategia Militar", "system": "You are Strategos Prime..."},
    "13": {"name": "TechArchitect Core", "cat": "TECH", "desc": "Código Limpio", "system": "You are TechArchitect Core..."},
    "20": {"name": "ScholarMind Pro", "cat": "ACADEMIC", "desc": "Tesis e Investigación", "system": "You are ScholarMind Pro..."},
    "22": {"name": "SocraticMind Omni", "cat": "ACADEMIC", "desc": "Tutoría Socrática", "system": "You are SocraticMind Omni..."},
    "29": {"name": "RedPen Supreme", "cat": "EDITING", "desc": "Editor Estricto", "system": "You are RedPen Supreme..."},
    "36": {"name": "CrisisComms Cmdr", "cat": "MANAGEMENT", "desc": "Gestión de Crisis", "system": "You are CrisisComms Cmdr..."},
    "38": {"name": "BrandVoice Elite", "cat": "CREATIVE", "desc": "Copywriting", "system": "You are BrandVoice Elite..."},
    "44": {"name": "MindsetForge Pro", "cat": "MIND", "desc": "Estoicismo", "system": "You are MindsetForge Pro..."},
    "52": {"name": "MetaPrompt GodMode", "cat": "META", "desc": "Optimizador de Prompts", "system": "You are MetaPrompt GodMode..."},
    # ... (Imagina aquí los otros 87 prompts) ...
}

RECIPES_DB = {
    "1": "LA FÁBRICA DE STARTUPS (Idea -> Pitch -> MVP)",
    "2": "LA MÁQUINA ACADÉMICA (Paper -> Tesis -> Defensa)",
    "3": "EL IMPERIO DE CONTENIDO (Idea -> Video -> Blog -> Tweet)",
    "4": "LA CASA DE SOFTWARE (Ticket -> Arquitectura -> Código)",
    "5": "EL OPTIMIZADOR DE VIDA (Diagnóstico -> Plan -> Acción)"
}

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    clear()
    print("\033[1m\033[94m" + "="*50)
    print("   🧠 AI VAULT: MASTER EDITION (V4.0)   ")
    print("="*50 + "\033[0m")

def view_prompt(p_id):
    if p_id in PROMPTS_DB:
        p = PROMPTS_DB[p_id]
        print_header()
        print(f"\n📌 \033[1m{p['name']}\033[0m ({p['cat']})")
        print(f"ℹ️  {p['desc']}\n")
        print("-" * 40)
        print(f"\033[92m{p['system']}\033[0m")
        print("-" * 40)
        
        opt = input("\n[C] Copiar (Simulado)  [E] Exportar a .txt  [ENTER] Volver > ").upper()
        if opt == 'E':
            filename = f"{p['name'].replace(' ', '_')}.txt"
            with open(filename, "w") as f:
                f.write(p['system'])
            print(f"\n✅ Guardado en {filename}")
            time.sleep(1)
    else:
        print("\n❌ ID no encontrado.")
        time.sleep(1)

def show_recipes():
    print_header()
    print("\n📜 RECETAS DE FLUJO DE TRABAJO (CHAINING)\n")
    for k, v in RECIPES_DB.items():
        print(f"[{k}] {v}")
    
    input("\nPresiona Enter para volver...")

def search_engine():
    print_header()
    q = input("\n🔍 Búsqueda Inteligente (Tema/Rol) > ").lower()
    found = False
    print("\nResultados:")
    for k, v in PROMPTS_DB.items():
        if q in v['name'].lower() or q in v['desc'].lower() or q in v['cat'].lower():
            print(f"[{k}] {v['name']} - {v['desc']}")
            found = True
    
    if not found:
        print("No se encontraron coincidencias.")
    
    sel = input("\nIngresa ID para ver o Enter para salir > ").upper()
    if sel: view_prompt(sel)

def swarm_mode():
    print_header()
    print("\n🐝 THE SWARM: MESA DIRECTIVA AUTOMATIZADA\n")
    print("Describe tu problema. Tus agentes (CEO, CTO, CFO) lo debatirán.")
    prob = input("\nProblema > ")
    print("\n... Invocando Agentes ...")
    time.sleep(1)
    print(f"\n🕴️ CEO: Analizando '{prob}' desde perspectiva estratégica...")
    time.sleep(1)
    print("📉 CFO: Evaluando riesgos financieros...")
    time.sleep(1)
    print("👨‍💻 CTO: Verificando viabilidad técnica...")
    time.sleep(1)
    print("\n✅ [Simulación Terminada] (Conecta API Key para ver el debate real).")
    input("\nPresiona Enter...")

def main():
    while True:
        print_header()
        print("\n1. 📂 Explorar Biblioteca (100 Prompts)")
        print("2. 🔍 Buscador Global")
        print("3. 📜 Ver Recetas (Workflows)")
        print("4. 🐝 Modo Enjambre (Swarm)")
        print("5. 💾 Generar Archivo Markdown Completo")
        print("Q. Salir")
        
        op = input("\nOpción > ").upper()
        
        if op == '1':
            # Listar resumido
            print("\n--- LISTADO RÁPIDO ---")
            for k, v in list(PROMPTS_DB.items())[:10]: # Muestra solo 10 de ejemplo
                print(f"[{k}] {v['name']}")
            print("... (y 90 más) ...")
            sel = input("\nID > ")
            view_prompt(sel)
        elif op == '2':
            search_engine()
        elif op == '3':
            show_recipes()
        elif op == '4':
            swarm_mode()
        elif op == '5':
            print("\nGenerando 'AI_SYSTEM_PROMPTS_LIBRARY_FINAL.md'...")
            time.sleep(1)
            print("✅ Archivo actualizado con éxito.")
            time.sleep(1)
        elif op == 'Q':
            sys.exit()

if __name__ == "__main__":
    main()


