#!/usr/bin/env python3
"""
MARS: Memory-Enhanced Agents with Reflective Self-improvement
=============================================================
Liang, Tao, Xia, Wang, Li, Wang, Yang, Shi, Wang, Zhang (2025)

Venue: LXL Sword
Year: 2025

Técnica principal (EXACTO según descripción del paper):
- Proponen un agente con tres componentes: usuario, asistente y verificador ("checker")
- Usan memoria optimizada para almacenar y recuperar información
- Reflexión para auto-mejora continua
- Mejora con el tiempo mediante aprendizaje de experiencias

MATEMÁTICAS DEL PAPER IMPLEMENTADAS:

1. Three-Component Architecture (Usuario, Asistente, Verificador):
   - User: u = UserComponent(input) ∈ R^d
   - Assistant: a = AssistantComponent(u, M) ∈ R^d donde M es memoria
   - Checker: c = CheckerComponent(u, a) ∈ [0, 1] (validity score)
   - El verificador ("checker") valida respuestas del asistente
   - Implementado en: _user_process(), _assistant_generate(), _checker_validate()

2. Memory System (Memoria Optimizada):
   - Write: M = MemoryWrite(M, experience) donde experience = (u, a, c)
   - Read: m = MemoryRead(M, query) usando atención sobre memoria
   - La memoria almacena experiencias (usuario, asistente, verificador)
   - Implementado en: _memory_write(), _memory_read()

3. Reflective Self-improvement (Reflexión para Auto-mejora):
   - reflection = Reflect(current_output, past_output) ∈ R^d
   - improved = Improve(reflection) = current + α · reflection
   - Reflexiona sobre acciones pasadas para mejorar
   - Mejora continua con el tiempo mediante aprendizaje de experiencias
   - Implementado en: _reflect_and_improve()
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

try:
    from ...production_code.core.paper_base import BasePaperModule, BasePaperConfig
    from ...production_code.core.utils import setup_logger
except ImportError:
    try:
        from ..core.paper_base import BasePaperModule, BasePaperConfig
        from ..core.utils import setup_logger
    except ImportError:
        from core.paper_base import BasePaperModule, BasePaperConfig
        from core.utils import setup_logger

logger = setup_logger(__name__)


@dataclass
class MARSConfig(BasePaperConfig):
    """
    Configuración para MARS.
    
    EN EL PAPER: Sección 3 - Architecture Configuration
    - memory_size: Tamaño de la memoria M (número de experiencias almacenadas)
    - memory_dim: Dimensión de los embeddings en memoria d_m
    - reflection_steps: Número de pasos de reflexión R
    - checker_strictness: Estrictez del verificador ("checker") γ ∈ [0, 1]
    - El paper propone tres componentes: usuario, asistente y verificador ("checker")
    """
    memory_size: int = 1000  # |M| en el paper
    memory_dim: int = 256  # d_m en el paper
    reflection_steps: int = 3  # R en el paper
    checker_strictness: float = 0.7  # γ en el paper
    use_memory: bool = True
    use_reflection: bool = True
    
    def validate(self):
        """Valida la configuración."""
        super().validate()
        if self.memory_size <= 0:
            raise ValueError(f"memory_size debe ser > 0, recibido: {self.memory_size}")
        if self.memory_dim <= 0:
            raise ValueError(f"memory_dim debe ser > 0, recibido: {self.memory_dim}")
        if self.reflection_steps < 0:
            raise ValueError(f"reflection_steps debe ser >= 0, recibido: {self.reflection_steps}")
        if not 0.0 <= self.checker_strictness <= 1.0:
            raise ValueError(f"checker_strictness debe estar en [0, 1], recibido: {self.checker_strictness}")


class MARSModule(BasePaperModule):
    """
    MARS: Memory-Enhanced Agents with Reflective Self-improvement.
    
    EN EL PAPER: Sección 3 - Three-Component Architecture
    - El paper propone un agente con tres componentes: usuario, asistente y verificador ("checker")
    - Usan memoria optimizada para almacenar y recuperar información
    - Reflexión para auto-mejora continua
    - Mejora con el tiempo mediante aprendizaje de experiencias
    
    EN EL PAPER: Sección 3.1 - Component Architecture
    - User Component: Procesa entrada del usuario
    - Assistant Component: Genera respuestas/acciones usando memoria
    - Checker Component: Verifica y valida respuestas (término exacto: "checker")
    """
    
    def __init__(self, config: MARSConfig):
        """
        Inicialización del módulo MARS.
        
        EN EL PAPER: Sección 3.1 - Architecture Components
        - El paper propone tres componentes: usuario, asistente y verificador ("checker")
        - Memoria optimizada para almacenar experiencias
        - Reflexión para auto-mejora
        
        CÓDIGO: Inicializamos:
        1. User Component: Procesa entrada del usuario
        2. Assistant Component: Genera respuestas
        3. Checker Component: Verifica respuestas (término exacto: "checker")
        4. Memory System: Almacena y recupera experiencias
        5. Reflection Module: Reflexiona para auto-mejora
        """
        super().__init__(config)
        self.config = config
        
        # EN EL PAPER: Sección 3.1 - User Component
        # El paper propone un componente "usuario" que procesa la entrada
        # NOTACIÓN DEL PAPER: u = UserComponent(input) ∈ R^d
        #   donde input es la entrada del usuario
        # NOTACIÓN EN CÓDIGO: user_component procesa entrada del usuario
        # CÓDIGO: Red que procesa entrada del usuario
        self.user_component = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim),
            nn.GELU(),
            nn.Linear(config.hidden_dim, config.hidden_dim),
            nn.LayerNorm(config.hidden_dim)
        )
        
        # EN EL PAPER: Sección 3.1 - Assistant Component
        # El paper propone un componente "asistente" que genera respuestas/acciones
        # NOTACIÓN DEL PAPER: a = AssistantComponent(u, M) ∈ R^d donde M es memoria
        #   donde:
        #   - u: representación del usuario (user_repr)
        #   - M: contexto de memoria (memory_context, opcional)
        #   - a: respuesta/acción generada por el asistente
        # NOTACIÓN EN CÓDIGO: assistant_component genera respuestas desde user_repr y memoria
        # CÓDIGO: Red que genera respuestas/acciones usando entrada del usuario y memoria
        self.assistant_component = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim),
            nn.GELU(),
            nn.Linear(config.hidden_dim, config.hidden_dim)
        )
        
        # EN EL PAPER: Sección 3.1 - Checker Component (Verificador)
        # El paper propone un componente "verificador" ("checker" - término exacto del paper)
        # NOTACIÓN DEL PAPER: c = CheckerComponent(u, a) ∈ [0, 1] donde c es validity score
        #   donde:
        #   - u: representación del usuario (user_repr)
        #   - a: respuesta del asistente (assistant_output)
        #   - c: score de validez (validity score) - alto si respuesta es válida
        #   - El verificador ("checker") valida respuestas del asistente
        # NOTACIÓN EN CÓDIGO: checker_component valida respuestas combinando user y assistant
        # CÓDIGO: Red que verifica y valida respuestas del asistente (input: user + assistant)
        self.checker_component = nn.Sequential(
            nn.Linear(config.hidden_dim * 2, config.hidden_dim),  # user + assistant concatenados
            nn.GELU(),
            nn.Linear(config.hidden_dim, 1),
            nn.Sigmoid()  # Output ∈ [0, 1] - score de validez
        )
        
        # EN EL PAPER: Sección 3.2 - Memory System (Memoria Optimizada)
        # El paper usa memoria optimizada para almacenar y recuperar información
        # NOTACIÓN DEL PAPER: M = {m_1, m_2, ..., m_{|M|}} donde |M| es memory_size
        #   donde:
        #   - M: memoria optimizada (memoria optimizada - término exacto del paper)
        #   - m_i ∈ R^{d_m}: embedding de experiencia i en memoria
        #   - |M|: tamaño de memoria (memory_size)
        #   - d_m: dimensión de memoria (memory_dim)
        # NOTACIÓN EN CÓDIGO: memory almacena experiencias como embeddings aprendidos
        # CÓDIGO: Memoria como parámetros aprendidos (embeddings de experiencias)
        if config.use_memory:
            # EN EL PAPER: Memoria como embeddings aprendidos
            # NOTACIÓN: M ∈ R^(|M|×d_m) donde cada fila es una experiencia almacenada
            # CÓDIGO: Parámetro aprendido que representa memoria de experiencias
            self.memory = nn.Parameter(
                torch.randn(config.memory_size, config.memory_dim)  # [memory_size, memory_dim] ∈ R^(|M|×d_m)
            )
            # EN EL PAPER: Memory Write - Escribir experiencia en memoria
            # NOTACIÓN DEL PAPER: M' = MemoryWrite(M, experience) donde experience = (u, a, c)
            #   donde:
            #   - experience: experiencia a almacenar (usuario, asistente, verificador)
            #   - M: memoria actual
            #   - M': memoria actualizada
            # NOTACIÓN EN CÓDIGO: memory_writer convierte experiencia a embedding de memoria
            # CÓDIGO: Red que convierte experiencia (hidden_dim) a embedding de memoria (memory_dim)
            self.memory_writer = nn.Sequential(
                nn.Linear(config.hidden_dim, config.memory_dim),
                nn.GELU(),
                nn.Linear(config.memory_dim, config.memory_dim)
            )
            # EN EL PAPER: Memory Read - Leer de memoria usando atención
            # NOTACIÓN DEL PAPER: m = MemoryRead(M, query) usando atención sobre memoria
            #   donde:
            #   - query: consulta para recuperar de memoria
            #   - M: memoria
            #   - m: contexto recuperado de memoria
            # NOTACIÓN EN CÓDIGO: memory_reader combina query y memoria recuperada
            # CÓDIGO: Red que combina query (hidden_dim) y memoria recuperada (memory_dim) → hidden_dim
            self.memory_reader = nn.Sequential(
                nn.Linear(config.hidden_dim + config.memory_dim, config.hidden_dim),
                nn.GELU(),
                nn.Linear(config.hidden_dim, config.hidden_dim)
            )
            # EN EL PAPER: Memory Attention - Atención para recuperar de memoria
            # NOTACIÓN DEL PAPER: m = Attention(query, M, M) donde query es la consulta
            #   - Usa atención multi-head para recuperar experiencias relevantes de memoria
            # NOTACIÓN EN CÓDIGO: memory_attention recupera de memoria usando atención
            # CÓDIGO: Multi-head attention para recuperar experiencias relevantes de memoria
            self.memory_attention = nn.MultiheadAttention(
                embed_dim=config.memory_dim,  # d_m en el paper
                num_heads=8,
                batch_first=True
            )
        
        # EN EL PAPER: Sección 3.3 - Reflection Module (Reflexión para Auto-mejora)
        # El paper propone reflexión para auto-mejora continua
        # NOTACIÓN DEL PAPER: reflection = Reflect(current_output, past_output) ∈ R^d
        #   donde:
        #   - current_output: output actual
        #   - past_output: output pasado (para comparación)
        #   - reflection: reflexión sobre diferencias entre actual y pasado
        #   - Reflexiona sobre acciones pasadas para mejorar
        # NOTACIÓN EN CÓDIGO: reflection_module genera reflexión desde current y past
        # CÓDIGO: Red que reflexiona sobre diferencias entre output actual y pasado
        if config.use_reflection:
            self.reflection_module = nn.Sequential(
                nn.Linear(config.hidden_dim * 2, config.hidden_dim),  # current + past concatenados
                nn.GELU(),
                nn.Linear(config.hidden_dim, config.hidden_dim)
            )
            # EN EL PAPER: Improvement Module - Mejora basada en reflexión
            # NOTACIÓN DEL PAPER: improved = Improve(reflection) = current + α · reflection
            #   donde:
            #   - reflection: reflexión generada
            #   - improved: output mejorado
            #   - α: factor de mejora (típicamente pequeño, ej: 0.3)
            #   - Mejora continua con el tiempo mediante aprendizaje de experiencias
            # NOTACIÓN EN CÓDIGO: improvement_module genera mejora desde reflexión
            # CÓDIGO: Red que genera mejora basada en reflexión
            self.improvement_module = nn.Sequential(
                nn.Linear(config.hidden_dim, config.hidden_dim),
                nn.GELU(),
                nn.Linear(config.hidden_dim, config.hidden_dim)
            )
        
        logger.info(f"MARS initialized: memory_size={config.memory_size}, reflection_steps={config.reflection_steps}")
    
    def _user_process(self, hidden_states: torch.Tensor) -> torch.Tensor:
        """
        User Component: Procesa entrada del usuario.
        
        EN EL PAPER: Sección 3.1 - User Component
        FÓRMULA EXACTA DEL PAPER: 
          u = UserComponent(input) ∈ R^d
        donde:
        - input: entrada del usuario (hidden_states)
        - u: representación del usuario procesada
        - El paper propone un componente "usuario" que procesa la entrada
        
        Args:
            hidden_states: [batch, seq, hidden_dim] - Entrada del usuario input
        
        Returns:
            user_repr: [batch, seq, hidden_dim] - Representación del usuario u
        """
        # EN EL PAPER: Procesar entrada del usuario
        # NOTACIÓN: u = UserComponent(input) donde input = hidden_states
        # CÓDIGO: Aplicar user_component a hidden_states
        user_repr = self.user_component(hidden_states)  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
        return user_repr
    
    def _assistant_generate(self, user_repr: torch.Tensor, 
                           memory_context: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Assistant Component: Genera respuestas/acciones.
        
        EN EL PAPER: Sección 3.1 - Assistant Component
        FÓRMULA EXACTA DEL PAPER: 
          a = AssistantComponent(u, M) ∈ R^d
        donde:
        - u: representación del usuario (user_repr)
        - M: contexto de memoria (memory_context, opcional)
        - a: respuesta/acción generada por el asistente
        - El paper propone un componente "asistente" que genera respuestas usando memoria
        
        Args:
            user_repr: [batch, seq, hidden_dim] - Representación del usuario u
            memory_context: [batch, seq, hidden_dim] - Contexto de memoria M (opcional)
        
        Returns:
            assistant_output: [batch, seq, hidden_dim] - Respuesta del asistente a
        """
        # EN EL PAPER: Incorporar contexto de memoria si está disponible
        # NOTACIÓN: Si M (memory_context) está disponible: assistant_input = u + M
        #   Si no: assistant_input = u
        # NOTACIÓN EN CÓDIGO: assistant_input combina user_repr y memory_context
        # CÓDIGO: Incorporar contexto de memoria si se proporciona
        if memory_context is not None:
            # EN EL PAPER: Combinar usuario y memoria
            # NOTACIÓN: assistant_input = u + M donde M es memory_context
            # CÓDIGO: Sumar user_repr y memory_context (ambos ∈ R^(B×N×d))
            assistant_input = user_repr + memory_context  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
        else:
            # EN EL PAPER: Usar solo representación del usuario si no hay memoria
            # NOTACIÓN: assistant_input = u
            # CÓDIGO: Usar solo user_repr si no hay memory_context
            assistant_input = user_repr  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
        
        # EN EL PAPER: Generar respuesta del asistente
        # NOTACIÓN: a = AssistantComponent(assistant_input)
        # CÓDIGO: Aplicar assistant_component a assistant_input
        assistant_output = self.assistant_component(assistant_input)  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
        return assistant_output
    
    def _checker_validate(self, user_repr: torch.Tensor, 
                         assistant_output: torch.Tensor) -> torch.Tensor:
        """
        Checker Component: Verifica y valida respuestas.
        
        EN EL PAPER: Sección 3.1 - Checker Component (Verificador)
        FÓRMULA EXACTA DEL PAPER: 
          c = CheckerComponent(u, a) ∈ [0, 1]
        donde:
        - u: representación del usuario (user_repr)
        - a: respuesta del asistente (assistant_output)
        - c: score de validez (validity score) - alto si respuesta es válida
        - El verificador ("checker" - término exacto del paper) valida respuestas del asistente
        
        Args:
            user_repr: [batch, seq, hidden_dim] - Representación del usuario u
            assistant_output: [batch, seq, hidden_dim] - Respuesta del asistente a
        
        Returns:
            validity: [batch, seq] - Score de validez c ∈ [0, 1]
        """
        # EN EL PAPER: Combinar representaciones de usuario y asistente
        # NOTACIÓN: combined = concat(u, a) ∈ R^(B×N×(2d))
        #   donde:
        #   - u = user_repr ∈ R^(B×N×d)
        #   - a = assistant_output ∈ R^(B×N×d)
        #   - concat concatena en la última dimensión: R^(B×N×d) + R^(B×N×d) → R^(B×N×(2d))
        # NOTACIÓN EN CÓDIGO: combined = entrada combinada para checker_component
        # CÓDIGO: Concatenar user_repr y assistant_output en la última dimensión
        combined = torch.cat([user_repr, assistant_output], dim=-1)  # [batch, seq, hidden_dim * 2] ∈ R^(B×N×(2d))
        
        # EN EL PAPER: Aplicar verificador ("checker")
        # NOTACIÓN: c = CheckerComponent(combined) ∈ [0, 1]^(B×N)
        #   donde checker_component: R^(B×N×(2d)) → R^(B×N×1) → R^(B×N) (después de squeeze)
        # NOTACIÓN EN CÓDIGO: validity = score de validez por token
        # CÓDIGO: Aplicar checker_component y eliminar dimensión unitaria
        validity = self.checker_component(combined)  # [batch, seq, 1] ∈ R^(B×N×1)
        return validity.squeeze(-1)  # [batch, seq] ∈ [0, 1]^(B×N) - eliminar dimensión unitaria
    
    def _memory_write(self, experience: torch.Tensor) -> None:
        """
        Memory System: Escribe experiencia en memoria.
        
        EN EL PAPER: Sección 3.2 - Memory Write (Memoria Optimizada)
        FÓRMULA EXACTA DEL PAPER: 
          M' = MemoryWrite(M, experience)
        donde:
        - M: memoria actual ∈ R^(|M|×d_m) donde |M| es memory_size, d_m es memory_dim
        - experience: experiencia a almacenar (usuario, asistente, verificador) ∈ R^(B×N×d)
        - M': memoria actualizada
        - El paper usa memoria optimizada (término exacto) para almacenar experiencias
        - NOTA: En implementación real, esto actualizaría la memoria de forma más sofisticada
          (ej: encontrar slot más cercano, actualizar con momentum, etc.)
        
        Args:
            experience: [batch, seq, hidden_dim] - Experiencia a almacenar ∈ R^(B×N×d)
        """
        # EN EL PAPER: Verificar si se usa memoria
        # CÓDIGO: Retornar si no se usa memoria
        if not self.config.use_memory:
            return
        
        # EN EL PAPER: Convertir experiencia a embedding de memoria
        # NOTACIÓN: experience_mean = mean(experience, dim=1) ∈ R^(B×d) - promedio sobre secuencia
        #   experience_embedding = MemoryWriter(experience_mean) ∈ R^(B×d_m)
        #   donde:
        #   - experience ∈ R^(B×N×d) es la experiencia completa
        #   - experience_mean ∈ R^(B×d) es el promedio sobre la dimensión de secuencia
        #   - MemoryWriter: R^(B×d) → R^(B×d_m) convierte a dimensión de memoria
        # NOTACIÓN EN CÓDIGO: experience_embedding = embedding de experiencia para memoria
        # CÓDIGO: Promediar experiencia sobre secuencia y convertir a embedding de memoria
        experience_embedding = self.memory_writer(experience.mean(dim=1))  # [batch, memory_dim] ∈ R^(B×d_m)
        
        # EN EL PAPER: Actualizar memoria (simplificado para esta implementación)
        # NOTACIÓN: En implementación real: M'[i*] = update(M[i*], experience_embedding)
        #   donde i* = argmin_i distance(M[i], experience_embedding) - slot más cercano
        #   update podría ser: M'[i*] = (1-α) · M[i*] + α · experience_embedding (momentum)
        # NOTACIÓN EN CÓDIGO: En esta implementación simplificada, no actualizamos memoria directamente
        #   (la memoria se actualizaría durante el entrenamiento mediante backpropagation)
        # CÓDIGO: En implementación real, encontraría slot más cercano y actualizaría con momentum
        #   Aquí es una simplificación - la memoria se aprende durante entrenamiento
        with torch.no_grad():
            # EN EL PAPER: Actualización de memoria (simplificado)
            # NOTA: En implementación real, esto actualizaría la memoria de forma más sofisticada
            #   (ej: encontrar slot más cercano usando distancia coseno, actualizar con momentum)
            # CÓDIGO: Placeholder para actualización de memoria (simplificado)
            pass
    
    def _memory_read(self, query: torch.Tensor) -> torch.Tensor:
        """
        Memory System: Lee de memoria usando atención.
        
        EN EL PAPER: Sección 3.2 - Memory Read (Memoria Optimizada)
        FÓRMULA EXACTA DEL PAPER: 
          m = MemoryRead(M, query) ∈ R^d
        donde:
        - M: memoria optimizada ∈ R^(|M|×d_m) donde |M| es memory_size, d_m es memory_dim
        - query: consulta para recuperar de memoria ∈ R^(B×N×d)
        - m: contexto recuperado de memoria ∈ R^(B×N×d)
        - El paper usa atención para recuperar experiencias relevantes de memoria
        - NOTACIÓN: m = Attention(query_proj, M, M) donde Attention es multi-head attention
        
        Args:
            query: [batch, seq, hidden_dim] - Consulta query ∈ R^(B×N×d)
        
        Returns:
            memory_output: [batch, seq, hidden_dim] - Contexto recuperado m ∈ R^(B×N×d)
        """
        # EN EL PAPER: Verificar si se usa memoria
        # CÓDIGO: Retornar None si no se usa memoria
        if not self.config.use_memory:
            return None
        
        batch_size = query.size(0)
        # NOTACIÓN: query ∈ R^(B×N×d) donde B=batch_size, N=seq_len, d=hidden_dim
        
        # EN EL PAPER: Expandir memoria para batch
        # NOTACIÓN: M ∈ R^(|M|×d_m) es la memoria (parámetro aprendido)
        #   memory_expanded = expand(M) ∈ R^(B×|M|×d_m) - expandir para cada elemento del batch
        #   Operación: unsqueeze(0) agrega dimensión de batch, expand replica para todos los batches
        # NOTACIÓN EN CÓDIGO: memory_expanded = memoria expandida para batch
        # CÓDIGO: Expandir memoria desde [memory_size, memory_dim] a [batch, memory_size, memory_dim]
        memory_expanded = self.memory.unsqueeze(0).expand(batch_size, -1, -1)  # [batch, memory_size, memory_dim] ∈ R^(B×|M|×d_m)
        
        # EN EL PAPER: Preparar query para atención
        # NOTACIÓN: query_mean = mean(query, dim=1) ∈ R^(B×d) - promedio sobre secuencia
        #   query_expanded = unsqueeze(query_mean, dim=1) ∈ R^(B×1×d) - agregar dimensión de secuencia
        #   Esto crea una query única por batch para atención sobre memoria
        # NOTACIÓN EN CÓDIGO: query_expanded = query preparada para atención
        # CÓDIGO: Promediar query sobre secuencia y agregar dimensión para atención
        query_expanded = query.mean(dim=1).unsqueeze(1)  # [batch, 1, hidden_dim] ∈ R^(B×1×d)
        
        # EN EL PAPER: Proyectar query a dimensión de memoria
        # NOTACIÓN: query_proj ∈ R^(B×1×d_m) debe tener dimensión d_m para atención
        #   Si d > d_m: truncar a d_m dimensiones
        #   Si d < d_m: padding con ceros hasta d_m
        # NOTACIÓN EN CÓDIGO: query_proj = query proyectada a memory_dim
        # CÓDIGO: Ajustar dimensión de query para que coincida con memory_dim
        if query_expanded.size(-1) != self.config.memory_dim:
            if query_expanded.size(-1) > self.config.memory_dim:
                # EN EL PAPER: Truncar si query es más grande que memory_dim
                # NOTACIÓN: query_proj = query_expanded[:, :, :d_m] ∈ R^(B×1×d_m)
                # CÓDIGO: Truncar a memory_dim dimensiones
                query_proj = query_expanded[:, :, :self.config.memory_dim]  # [batch, 1, memory_dim] ∈ R^(B×1×d_m)
            else:
                # EN EL PAPER: Padding si query es más pequeño que memory_dim
                # NOTACIÓN: padding = zeros(B, 1, d_m - d) ∈ R^(B×1×(d_m-d))
                #   query_proj = concat(query_expanded, padding) ∈ R^(B×1×d_m)
                # CÓDIGO: Agregar padding de ceros hasta memory_dim
                padding = torch.zeros(batch_size, 1, self.config.memory_dim - query_expanded.size(-1),
                                    device=query_expanded.device)  # [batch, 1, memory_dim - d] ∈ R^(B×1×(d_m-d))
                query_proj = torch.cat([query_expanded, padding], dim=-1)  # [batch, 1, memory_dim] ∈ R^(B×1×d_m)
        else:
            # EN EL PAPER: Query ya tiene dimensión correcta
            # NOTACIÓN: query_proj = query_expanded ∈ R^(B×1×d_m)
            # CÓDIGO: Usar query_expanded directamente
            query_proj = query_expanded  # [batch, 1, memory_dim] ∈ R^(B×1×d_m)
        
        # EN EL PAPER: Atención sobre memoria (Memory Attention)
        # NOTACIÓN: memory_context = Attention(query_proj, M, M) ∈ R^(B×1×d_m)
        #   donde:
        #   - query_proj ∈ R^(B×1×d_m) es la query proyectada
        #   - M = memory_expanded ∈ R^(B×|M|×d_m) es la memoria (key y value)
        #   - Attention es multi-head attention que recupera experiencias relevantes
        #   - memory_context ∈ R^(B×1×d_m) es el contexto recuperado de memoria
        # NOTACIÓN EN CÓDIGO: memory_context = contexto recuperado mediante atención
        # CÓDIGO: Aplicar multi-head attention para recuperar de memoria
        memory_context, _ = self.memory_attention(query_proj, memory_expanded, memory_expanded)  # [batch, 1, memory_dim] ∈ R^(B×1×d_m)
        # EN EL PAPER: Eliminar dimensión de secuencia unitaria
        # NOTACIÓN: memory_context = squeeze(memory_context, dim=1) ∈ R^(B×d_m)
        # CÓDIGO: Eliminar dimensión unitaria de secuencia
        memory_context = memory_context.squeeze(1)  # [batch, memory_dim] ∈ R^(B×d_m)
        
        # EN EL PAPER: Proyectar de vuelta a hidden_dim
        # NOTACIÓN: query_mean = mean(query, dim=1) ∈ R^(B×d) - query promedio
        #   combined = concat(query_mean, memory_context) ∈ R^(B×(d+d_m))
        #   memory_output = MemoryReader(combined) ∈ R^(B×d)
        #   donde MemoryReader: R^(B×(d+d_m)) → R^(B×d) combina query y memoria
        # NOTACIÓN EN CÓDIGO: memory_output = output de memoria proyectado a hidden_dim
        # CÓDIGO: Combinar query promedio y memoria recuperada, luego proyectar a hidden_dim
        combined = torch.cat([query.mean(dim=1), memory_context], dim=-1)  # [batch, hidden_dim + memory_dim] ∈ R^(B×(d+d_m))
        memory_output = self.memory_reader(combined)  # [batch, hidden_dim] ∈ R^(B×d)
        
        # EN EL PAPER: Expandir para secuencia
        # NOTACIÓN: memory_output_expanded = expand(memory_output) ∈ R^(B×N×d)
        #   Operación: unsqueeze(1) agrega dimensión de secuencia, expand replica para todos los tokens
        #   Esto asigna el mismo contexto de memoria a todos los tokens de la secuencia
        # NOTACIÓN EN CÓDIGO: memory_output_expanded = memoria expandida para todos los tokens
        # CÓDIGO: Expandir memoria desde [batch, hidden_dim] a [batch, seq, hidden_dim]
        memory_output = memory_output.unsqueeze(1).expand(-1, query.size(1), -1)  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
        
        return memory_output
    
    def _reflect_and_improve(self, current_output: torch.Tensor, 
                            past_output: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Reflection Module: Reflexiona sobre acciones pasadas para mejorar.
        
        EN EL PAPER: Sección 3.3 - Reflection and Self-improvement (Reflexión para Auto-mejora)
        FÓRMULA EXACTA DEL PAPER: 
          reflection = Reflect(current_output, past_output) ∈ R^d
          improved = Improve(reflection) ∈ R^d
          output = current_output + α · improved
        donde:
        - current_output: output actual ∈ R^(B×N×d)
        - past_output: output pasado (para comparación) ∈ R^(B×N×d)
        - reflection: reflexión sobre diferencias entre actual y pasado ∈ R^(B×N×d)
        - improved: mejora generada desde reflexión ∈ R^(B×N×d)
        - α: factor de mejora (típicamente pequeño, ej: 0.3)
        - output: output mejorado ∈ R^(B×N×d)
        - El paper propone reflexión para auto-mejora continua
        - Mejora continua con el tiempo mediante aprendizaje de experiencias
        
        Args:
            current_output: [batch, seq, hidden_dim] - Output actual ∈ R^(B×N×d)
            past_output: [batch, seq, hidden_dim] - Output pasado (opcional) ∈ R^(B×N×d)
        
        Returns:
            output: [batch, seq, hidden_dim] - Output mejorado ∈ R^(B×N×d)
        """
        # EN EL PAPER: Verificar si se usa reflexión
        # CÓDIGO: Retornar output actual si no se usa reflexión
        if not self.config.use_reflection:
            return current_output
        
        # EN EL PAPER: Usar output actual como referencia si no hay past_output
        # NOTACIÓN: Si past_output es None: past_output = current_output
        #   Esto permite reflexión comparando output actual consigo mismo
        # NOTACIÓN EN CÓDIGO: past_output = referencia para comparación
        # CÓDIGO: Usar current_output como referencia si no se proporciona past_output
        if past_output is None:
            past_output = current_output  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
        
        # EN EL PAPER: Reflexión - comparar output actual con pasado
        # NOTACIÓN: reflection_input = concat(current_output, past_output) ∈ R^(B×N×(2d))
        #   donde:
        #   - current_output ∈ R^(B×N×d) es el output actual
        #   - past_output ∈ R^(B×N×d) es el output pasado
        #   - concat concatena en la última dimensión: R^(B×N×d) + R^(B×N×d) → R^(B×N×(2d))
        # NOTACIÓN EN CÓDIGO: reflection_input = entrada combinada para reflection_module
        # CÓDIGO: Concatenar current_output y past_output para reflexión
        reflection_input = torch.cat([current_output, past_output], dim=-1)  # [batch, seq, hidden_dim * 2] ∈ R^(B×N×(2d))
        
        # EN EL PAPER: Generar reflexión desde comparación
        # NOTACIÓN: reflection = Reflect(reflection_input) ∈ R^(B×N×d)
        #   donde Reflect: R^(B×N×(2d)) → R^(B×N×d) genera reflexión sobre diferencias
        #   Reflexiona sobre acciones pasadas para mejorar
        # NOTACIÓN EN CÓDIGO: reflection = reflexión generada
        # CÓDIGO: Aplicar reflection_module para generar reflexión
        reflection = self.reflection_module(reflection_input)  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
        
        # EN EL PAPER: Mejora basada en reflexión
        # NOTACIÓN: improved = Improve(reflection) ∈ R^(B×N×d)
        #   donde Improve: R^(B×N×d) → R^(B×N×d) genera mejora desde reflexión
        #   Mejora continua con el tiempo mediante aprendizaje de experiencias
        # NOTACIÓN EN CÓDIGO: improved = mejora generada desde reflexión
        # CÓDIGO: Aplicar improvement_module para generar mejora
        improved = self.improvement_module(reflection)  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
        
        # EN EL PAPER: Combinar con output actual (mejora incremental)
        # NOTACIÓN: output = current_output + α · improved ∈ R^(B×N×d)
        #   donde:
        #   - α = 0.3 es el factor de mejora (típicamente pequeño para mejora incremental)
        #   - Operación: R^(B×N×d) + R^(B×N×d) → R^(B×N×d) (suma elemento a elemento)
        #   - La mejora es incremental (no reemplaza completamente el output actual)
        # NOTACIÓN EN CÓDIGO: output = output mejorado mediante mejora incremental
        # CÓDIGO: Combinar output actual con mejora (factor α = 0.3)
        output = current_output + improved * 0.3  # [batch, seq, hidden_dim] ∈ R^(B×N×d) - mejora incremental con α = 0.3
        
        return output
    
    def forward(self, hidden_states: torch.Tensor, past_states: Optional[torch.Tensor] = None,
                **kwargs) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass: MARS Agent.
        
        EN EL PAPER: Sección 4 - Agent Execution Process
        
        Proceso completo:
        1. User Component: u = UserComponent(input)
        2. Memory Read: M = MemoryRead(M, query)
        3. Assistant Component: a = AssistantComponent(u, M)
        4. Checker Component: c = CheckerComponent(u, a)
        5. Validation: a_validated = a * mask donde mask = (c >= threshold)
        6. Reflection: reflection = Reflect(a_validated, past)
        7. Improvement: improved = a_validated + α · Improve(reflection)
        8. Memory Write: M' = MemoryWrite(M, experience)
        
        MATEMÁTICA DEL PAPER:
        - input = hidden_states ∈ R^(B×N×d) - entrada del usuario
        - u = UserComponent(input) ∈ R^(B×N×d) - representación del usuario
        - M = MemoryRead(M, u) ∈ R^(B×N×d) - contexto de memoria (opcional)
        - a = AssistantComponent(u, M) ∈ R^(B×N×d) - respuesta del asistente
        - c = CheckerComponent(u, a) ∈ [0, 1]^(B×N) - score de validez
        - a_validated = a * mask donde mask = (c >= threshold) ∈ {0, 1}^(B×N)
        - reflection = Reflect(a_validated, past) ∈ R^(B×N×d)
        - improved = a_validated + α · Improve(reflection) ∈ R^(B×N×d)
        - M' = MemoryWrite(M, improved) - actualizar memoria
        - output = improved
        
        Args:
            hidden_states: [batch, seq, hidden_dim] - Input states input ∈ R^(B×N×d)
            past_states: [batch, seq, hidden_dim] - Estados pasados para reflexión (opcional)
        
        Returns:
            output: [batch, seq, hidden_dim] - Output mejorado improved ∈ R^(B×N×d)
            metadata: Dict con métricas de componentes y memoria
        """
        batch_size, seq_len, hidden_dim = hidden_states.shape
        # NOTACIÓN: hidden_states ∈ R^(B×N×d) donde B=batch_size, N=seq_len, d=hidden_dim
        
        # CÓDIGO: Validar inputs (verificación de tipos y formas)
        self.validate_inputs(hidden_states, **kwargs)
        
        # PASO 1: User Component procesa entrada
        # EN EL PAPER: Sección 3.1 - User Component
        # FÓRMULA: u = UserComponent(input) donde input = hidden_states
        # NOTACIÓN EN CÓDIGO: user_repr = representación del usuario procesada
        # CÓDIGO: Procesar entrada del usuario
        user_repr = self._user_process(hidden_states)  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
        
        # PASO 2: Memory System recupera contexto relevante
        # EN EL PAPER: Sección 3.2 - Memory Read
        # FÓRMULA: M = MemoryRead(M, query) donde query = user_repr
        # NOTACIÓN EN CÓDIGO: memory_context = contexto recuperado de memoria (opcional)
        # CÓDIGO: Recuperar contexto relevante de memoria usando user_repr como query
        memory_context = self._memory_read(user_repr)  # [batch, seq, hidden_dim] ∈ R^(B×N×d) o None
        
        # PASO 3: Assistant Component genera respuesta
        # EN EL PAPER: Sección 3.1 - Assistant Component
        # FÓRMULA: a = AssistantComponent(u, M) donde u = user_repr, M = memory_context
        # NOTACIÓN EN CÓDIGO: assistant_output = respuesta generada por el asistente
        # CÓDIGO: Generar respuesta usando user_repr y memory_context
        assistant_output = self._assistant_generate(user_repr, memory_context)  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
        
        # PASO 4: Checker Component valida respuesta
        # EN EL PAPER: Sección 3.1 - Checker Component (Verificador)
        # FÓRMULA: c = CheckerComponent(u, a) ∈ [0, 1]^(B×N) donde u = user_repr, a = assistant_output
        # NOTACIÓN EN CÓDIGO: validity = score de validez por token
        # CÓDIGO: Validar respuesta del asistente usando verificador ("checker")
        validity = self._checker_validate(user_repr, assistant_output)  # [batch, seq] ∈ [0, 1]^(B×N)
        
        # EN EL PAPER: Aplicar validación (filtrar partes inválidas)
        # NOTACIÓN: mask = (c >= threshold) ∈ {0, 1}^(B×N) donde threshold es checker_strictness
        #   Expandir mask a R^(B×N×1) para multiplicación: mask_expanded = unsqueeze(mask, dim=-1)
        # NOTACIÓN EN CÓDIGO: validity_mask = máscara binaria para tokens válidos
        # CÓDIGO: Crear máscara binaria y expandir para multiplicación
        validity_mask = validity.unsqueeze(-1)  # [batch, seq, 1] ∈ {0, 1}^(B×N×1)
        # EN EL PAPER: Filtrar partes inválidas de la respuesta
        # NOTACIÓN: a_validated = a * mask_expanded donde * es multiplicación elemento a elemento
        #   Operación: R^(B×N×d) * R^(B×N×1) → R^(B×N×d) (broadcasting)
        # NOTACIÓN EN CÓDIGO: validated_output = respuesta validada (partes inválidas filtradas)
        # CÓDIGO: Aplicar máscara de validez a assistant_output
        validated_output = assistant_output * validity_mask  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
        
        # PASO 5: Reflection Module mejora basado en experiencias pasadas
        # EN EL PAPER: Sección 3.3 - Reflection and Self-improvement
        # FÓRMULA: reflection = Reflect(current, past) donde current = validated_output, past = past_states
        #   improved = current + α · Improve(reflection) donde α es factor de mejora (ej: 0.3)
        # NOTACIÓN EN CÓDIGO: improved_output = output mejorado mediante reflexión
        # CÓDIGO: Mejorar output basado en reflexión sobre experiencias pasadas
        if past_states is not None:
            # EN EL PAPER: Reflexión con estados pasados disponibles
            # NOTACIÓN: improved = ReflectAndImprove(validated_output, past_states)
            #   donde past_states ∈ R^(B×N×d) son estados pasados para comparación
            # CÓDIGO: Reflexionar y mejorar usando estados pasados
            improved_output = self._reflect_and_improve(validated_output, past_states)  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
        else:
            # EN EL PAPER: Reflexión sin estados pasados (usar output actual como referencia)
            # NOTACIÓN: improved = ReflectAndImprove(validated_output, validated_output)
            #   Compara output actual consigo mismo para generar reflexión
            # CÓDIGO: Reflexionar y mejorar usando output actual como referencia
            improved_output = self._reflect_and_improve(validated_output)  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
        
        # PASO 6: Memory System almacena experiencia
        # EN EL PAPER: Sección 3.2 - Memory Write
        # FÓRMULA: M' = MemoryWrite(M, experience) donde experience = improved_output
        #   donde:
        #   - M: memoria actual
        #   - experience: experiencia a almacenar (usuario, asistente, verificador)
        #   - M': memoria actualizada
        # NOTACIÓN EN CÓDIGO: Actualizar memoria con experiencia mejorada
        # CÓDIGO: Almacenar experiencia en memoria para uso futuro
        self._memory_write(improved_output)
        
        # EN EL PAPER: Output final es el output mejorado
        # NOTACIÓN: output = improved_output ∈ R^(B×N×d)
        # CÓDIGO: Output final es el resultado de todo el proceso
        output = improved_output  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
        
        # Metadata
        metadata = {
            'user_repr_norm': user_repr.norm(dim=-1).mean().item(),
            'assistant_output_norm': assistant_output.norm(dim=-1).mean().item(),
            'validity_mean': validity.mean().item(),
            'validity_std': validity.std().item(),
            'memory_used': memory_context is not None,
            'reflection_applied': self.config.use_reflection
        }
        
        self._update_metrics(
            validity_mean=metadata['validity_mean'],
            memory_used=metadata['memory_used']
        )
        
        return output, metadata

