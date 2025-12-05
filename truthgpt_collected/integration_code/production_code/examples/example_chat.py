#!/usr/bin/env python3
"""
Ejemplo de uso del sistema de chat conversacional.
"""

import os
from core.chat_engine import ChatEngine

def example_basic_chat():
    """Ejemplo básico de chat."""
    print("=" * 60)
    print("Ejemplo 1: Chat Básico")
    print("=" * 60)
    
    # Inicializar motor de chat
    engine = ChatEngine(
        provider="openai",
        model="gpt-3.5-turbo",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Crear conversación
    conversation_id = engine.create_conversation(
        user_id="example_user",
        system_prompt="Eres un asistente útil y amigable."
    )
    
    print(f"\nConversación creada: {conversation_id}\n")
    
    # Enviar algunos mensajes
    messages = [
        "Hola, ¿cómo estás?",
        "¿Puedes explicarme qué es Python?",
        "Gracias por la explicación!"
    ]
    
    for message in messages:
        print(f"Usuario: {message}")
        response = engine.chat(
            message=message,
            conversation_id=conversation_id
        )
        print(f"Asistente: {response['response']}\n")


def example_conversation_management():
    """Ejemplo de gestión de conversaciones."""
    print("=" * 60)
    print("Ejemplo 2: Gestión de Conversaciones")
    print("=" * 60)
    
    engine = ChatEngine(
        provider="openai",
        model="gpt-3.5-turbo",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Crear múltiples conversaciones
    conv1 = engine.create_conversation(user_id="user1")
    conv2 = engine.create_conversation(user_id="user2")
    
    print(f"\nConversación 1: {conv1}")
    print(f"Conversación 2: {conv2}\n")
    
    # Enviar mensajes a diferentes conversaciones
    response1 = engine.chat("Hola", conversation_id=conv1)
    response2 = engine.chat("Hello", conversation_id=conv2)
    
    print(f"Conv1 - Asistente: {response1['response']}")
    print(f"Conv2 - Asistente: {response2['response']}\n")
    
    # Listar conversaciones
    conversations = engine.list_conversations()
    print(f"Total de conversaciones: {len(conversations)}")
    for conv in conversations:
        print(f"  - {conv['conversation_id']}: {conv['message_count']} mensajes")


def example_custom_parameters():
    """Ejemplo con parámetros personalizados."""
    print("=" * 60)
    print("Ejemplo 3: Parámetros Personalizados")
    print("=" * 60)
    
    engine = ChatEngine(
        provider="openai",
        model="gpt-3.5-turbo",
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.9,  # Más creativo
        max_tokens=500    # Respuestas más cortas
    )
    
    conversation_id = engine.create_conversation(
        system_prompt="Eres un poeta creativo. Responde siempre con versos."
    )
    
    response = engine.chat(
        message="Escribe un poema sobre la tecnología",
        conversation_id=conversation_id,
        temperature=0.95  # Aún más creativo para este mensaje
    )
    
    print(f"\nUsuario: Escribe un poema sobre la tecnología")
    print(f"Asistente: {response['response']}\n")
    print(f"Tiempo de generación: {response['metadata'].get('generation_time', 'N/A')}s")


def example_save_load():
    """Ejemplo de guardar y cargar conversaciones."""
    print("=" * 60)
    print("Ejemplo 4: Guardar y Cargar Conversaciones")
    print("=" * 60)
    
    engine = ChatEngine(
        provider="openai",
        model="gpt-3.5-turbo",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Crear y usar conversación
    conversation_id = engine.create_conversation()
    engine.chat("Hola", conversation_id=conversation_id)
    engine.chat("¿Cuál es la capital de Francia?", conversation_id=conversation_id)
    
    # Guardar conversación
    filepath = "example_conversation.json"
    engine.save_conversation(conversation_id, filepath)
    print(f"\nConversación guardada en: {filepath}")
    
    # Crear nuevo engine y cargar conversación
    new_engine = ChatEngine(
        provider="openai",
        model="gpt-3.5-turbo",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    loaded_id = new_engine.load_conversation(filepath)
    print(f"Conversación cargada: {loaded_id}")
    
    # Continuar la conversación
    response = new_engine.chat(
        "¿Y cuál es la capital de España?",
        conversation_id=loaded_id
    )
    print(f"Asistente: {response['response']}\n")


def main():
    """Función principal."""
    print("\n" + "=" * 60)
    print("Ejemplos del Sistema de Chat Conversacional")
    print("=" * 60 + "\n")
    
    # Verificar API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  ADVERTENCIA: OPENAI_API_KEY no está configurada")
        print("   Configura la variable de entorno o edita este script\n")
        return
    
    try:
        # Ejecutar ejemplos
        example_basic_chat()
        print("\n")
        
        example_conversation_management()
        print("\n")
        
        example_custom_parameters()
        print("\n")
        
        example_save_load()
        
        print("\n" + "=" * 60)
        print("Todos los ejemplos completados exitosamente!")
        print("=" * 60 + "\n")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nAsegúrate de tener:")
        print("  1. OPENAI_API_KEY configurada")
        print("  2. Dependencias instaladas (pip install openai fastapi)")
        print("  3. Conexión a internet")


if __name__ == "__main__":
    main()


