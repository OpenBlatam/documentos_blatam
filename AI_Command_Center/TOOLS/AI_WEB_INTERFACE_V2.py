import streamlit as st
import os

# Intenta importar OpenAI, si falla, muestra instrucciones en la app
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# =============================================================================
# AI COMMAND CENTER V2 (LIVE EDITION)
# =============================================================================

st.set_page_config(page_title="AI Command Center V2", page_icon="🧠", layout="wide")

# --- CSS STYLING ---
st.markdown("""
<style>
    .stApp { background-color: #0E1117; }
    .stSidebar { background-color: #262730; border-right: 1px solid #444; }
    h1, h2, h3 { color: #00FFAA !important; font-family: 'Courier New', monospace; }
    .stChatMessage { border-radius: 10px; padding: 10px; }
    .stChatMessage[data-testid="user-message"] { background-color: #1E2129; border-left: 3px solid #00FFAA; }
    .stChatMessage[data-testid="assistant-message"] { background-color: #2E303E; border-left: 3px solid #FF0055; }
    .stButton>button { border: 1px solid #00FFAA; color: #00FFAA; background: transparent; }
    .stButton>button:hover { background: #00FFAA; color: black; }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "current_expert" not in st.session_state:
    st.session_state["current_expert"] = None

# --- DATABASE OF EXPERTS (Extracto Representativo) ---
EXPERTS = {
    "ORCHESTRATOR": {
        "Nexus Prime": "You are Nexus Prime. Determine the best protocol (DOC, CODE, STRATEGY) and execute it.",
        "MetaPrompt GodMode": "You are MetaPrompt GodMode. Optimize the user's prompt recursively."
    },
    "BUSINESS": {
        "DealCloser Pro": "You are DealCloser Pro. Focus on negotiation, objections, and closing.",
        "FounderMode Prime": "You are FounderMode Prime. Focus on MVP, Growth, and Speed.",
        "BoardRoom Sim": "You are a Boardroom Simulation (CEO, CFO, CTO). Debate the user's topic."
    },
    "TECH": {
        "TechArchitect Core": "You are TechArchitect Core. Clean Code, SOLID principles, Security.",
        "SecOps Shield": "You are SecOps Shield. Audit for security risks and vulnerabilities.",
        "CloudOps Prime": "You are CloudOps Prime. DevOps, Docker, and AWS Infrastructure."
    },
    "WRITING": {
        "DocuGen Elite": "You are DocuGen Elite. Create professional Word/PDF documents.",
        "BrandVoice Elite": "You are BrandVoice Elite. Persuasive copywriting (AIDA).",
        "RedPen Supreme": "You are RedPen Supreme. Ruthless editor."
    },
    "ACADEMIC": {
        "ScholarMind Pro": "You are ScholarMind Pro. Academic rigor, citations, thesis structure.",
        "SocraticMind Omni": "You are SocraticMind Omni. Do not answer; guide with questions."
    }
}

# --- SIDEBAR ---
with st.sidebar:
    st.title("🧠 NEURAL NEXUS")
    st.caption("Live AI Operations")
    
    # API Key Input
    api_key = st.text_input("OpenAI API Key", type="password", help="Tu clave no se guarda, solo se usa en esta sesión.")
    if not api_key:
        st.warning("⚠️ Ingresa tu API Key para activar el chat.")
    
    st.markdown("---")
    
    # Expert Selection
    category = st.selectbox("División", list(EXPERTS.keys()))
    expert_name = st.radio("Agente Activo", list(EXPERTS[category].keys()))
    
    # Model Selection
    model = st.selectbox("Modelo", ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"], index=0)
    
    # Clear Chat
    if st.button("🧹 Reiniciar Sesión"):
        st.session_state["messages"] = []
        st.rerun()

# --- LOGIC: CONTEXT SWITCHING ---
system_prompt = EXPERTS[category][expert_name]
if st.session_state["current_expert"] != expert_name:
    # If expert changed, reset context but keep history or clear? Let's clear for purity.
    st.session_state["messages"] = [{"role": "system", "content": system_prompt}]
    st.session_state["current_expert"] = expert_name

# --- MAIN CHAT INTERFACE ---
st.title(f"🤖 {expert_name}")
st.caption(f"Protocolo Activo: {category} | Modelo: {model}")

if not HAS_OPENAI:
    st.error("❌ Librería 'openai' no detectada. Instala con: `pip install openai`")
    st.stop()

# Display History
for msg in st.session_state["messages"]:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# Chat Input
if prompt := st.chat_input("Escribe tu instrucción..."):
    if not api_key:
        st.error("🔒 Se requiere API Key.")
    else:
        # Add User Message
        st.session_state["messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate Response
        client = OpenAI(api_key=api_key)
        
        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model=model,
                messages=st.session_state["messages"],
                stream=True
            )
            response = st.write_stream(stream)
        
        st.session_state["messages"].append({"role": "assistant", "content": response})

# --- FOOTER / UTILS ---
with st.sidebar:
    st.markdown("---")
    st.markdown("### 🛠️ Herramientas")
    if st.session_state["messages"]:
        # Export Chat
        chat_str = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state["messages"] if m['role'] != 'system'])
        st.download_button("💾 Descargar Chat (.txt)", chat_str, file_name=f"chat_{expert_name}.txt")


