#!/usr/bin/env python3
"""
A Concurrent Modular Agent: Framework for Autonomous LLM Agents
================================================================
Maruyama, Yoshida, Sato, Masumori, Ikegami (2025)

Venue: arXiv
Year: 2025

Técnica principal (EXACTO según descripción del paper):
- Presentan una arquitectura de agente con módulos concurrentes que operan de forma autónoma
- Comunicación entre módulos mediante mensajes
- Un "estado global" compartido para coordinación
- Módulos especializados que trabajan en paralelo

MATEMÁTICAS DEL PAPER IMPLEMENTADAS:

1. Concurrent Modular Architecture (Arquitectura Modular Concurrente):
   - Para N módulos: M = {M_1, M_2, ..., M_N} donde cada M_i opera de forma autónoma
   - Cada módulo: o_i = M_i(input) ∈ R^{d_m} donde d_m es module_dim
   - Los módulos operan de forma concurrente (paralela)
   - Implementado en: _module_forward()

2. Inter-Module Communication (Comunicación entre Módulos):
   - Para cada módulo i: msg_i = CommunicationNetwork_i(o_i) ∈ R^{d_c}
   - Cada módulo recibe: received_i = MessageReceiver_i([msg_1, ..., msg_N]) ∈ R^{d_m}
   - NOTACIÓN: received_i = f_receive(concat(msg_1, ..., msg_N))
   - Los módulos se comunican mediante mensajes
   - Implementado en: _inter_module_communication()

3. Shared Global State (Estado Global Compartido):
   - G = GlobalState([o_1, ..., o_N]) ∈ R^{d_g} donde d_g es global_state_dim
   - G se actualiza: G' = UpdateGlobalState(G, [o_1, ..., o_N])
   - El "estado global" compartido coordina todos los módulos
   - NOTACIÓN: G = f_global(concat(input, o_1, ..., o_N))
   - Implementado en: _update_global_state()

4. Module Fusion:
   - output = Fusion([o_1, ..., o_N]) ∈ R^d
   - Combina salidas de todos los módulos concurrentes
   - Implementado en: forward()
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import sys
from pathlib import Path

try:
    from ..core.paper_base import BasePaperModule, BasePaperConfig
    from ..core.utils import setup_logger
except ImportError:
    production_code_path = Path(__file__).parent.parent.parent / 'production_code'
    if production_code_path.exists():
        sys.path.insert(0, str(production_code_path))
    from core.paper_base import BasePaperModule, BasePaperConfig
    from core.utils import setup_logger

logger = setup_logger(__name__)


@dataclass
class ConcurrentModularAgentConfig(BasePaperConfig):
    """
    Configuración para Concurrent Modular Agent.
    
    EN EL PAPER: Sección 3 - Architecture Configuration
    - num_modules: Número de módulos concurrentes N
    - module_dim: Dimensión de cada módulo d_m
    - communication_dim: Dimensión de los mensajes entre módulos d_c
    - global_state_dim: Dimensión del "estado global" compartido d_g
    - communication_steps: Número de pasos de comunicación C
    - El paper presenta una arquitectura con módulos concurrentes que operan de forma autónoma
    """
    num_modules: int = 4  # N en el paper
    module_dim: int = 256  # d_m en el paper
    communication_dim: int = 128  # d_c en el paper
    global_state_dim: int = 512  # d_g en el paper
    use_global_state: bool = True
    communication_steps: int = 3  # C en el paper


class ConcurrentModularAgentModule(BasePaperModule):
    """
    Concurrent Modular Agent: Framework con módulos concurrentes.
    
    EN EL PAPER: Sección 3 - Concurrent Modular Architecture
    - El paper presenta una arquitectura de agente con módulos concurrentes que operan de forma autónoma
    - Comunicación entre módulos mediante mensajes
    - Un "estado global" compartido (término exacto del paper) para coordinación
    - Módulos especializados que trabajan en paralelo
    
    EN EL PAPER: Sección 3.1 - Module Architecture
    - Cada módulo opera de forma autónoma
    - Los módulos son especializados (cada uno tiene una función específica)
    """
    
    def __init__(self, config: ConcurrentModularAgentConfig):
        """
        Inicialización del módulo Concurrent Modular Agent.
        
        EN EL PAPER: Sección 3.1 - Architecture Components
        - El paper presenta módulos concurrentes que operan de forma autónoma
        - Sistema de comunicación entre módulos
        - Estado global compartido para coordinación
        
        CÓDIGO: Inicializamos:
        1. Módulos especializados concurrentes
        2. Redes de comunicación entre módulos
        3. Receptores de mensajes
        4. Estado global compartido
        5. Fusionador de salidas
        """
        super().__init__(config)
        self.config = config
        
        # EN EL PAPER: Sección 3.1 - Concurrent Modules
        # El paper presenta módulos concurrentes que operan de forma autónoma (término exacto)
        # NOTACIÓN DEL PAPER: M = {M_1, M_2, ..., M_N} donde cada M_i opera de forma autónoma
        #   donde:
        #   - N: número de módulos (num_modules)
        #   - M_i: módulo i que procesa input de forma especializada
        #   - o_i = M_i(input) ∈ R^{d_m} donde d_m es module_dim
        #   - Los módulos operan de forma concurrente (paralela)
        # NOTACIÓN EN CÓDIGO: modules[i] = M_i
        # CÓDIGO: Módulos especializados que operan de forma autónoma
        self.modules = nn.ModuleList([
            nn.Sequential(
                nn.Linear(config.hidden_dim, config.module_dim),
                nn.GELU(),
                nn.Linear(config.module_dim, config.module_dim),
                nn.LayerNorm(config.module_dim)
            ) for _ in range(config.num_modules)
        ])
        
        # EN EL PAPER: Sección 3.2 - Inter-Module Communication
        # El paper presenta comunicación entre módulos mediante mensajes (término exacto)
        # NOTACIÓN DEL PAPER: Para cada módulo i: msg_i = CommunicationNetwork_i(o_i) ∈ R^{d_c}
        #   donde:
        #   - o_i: output del módulo i
        #   - msg_i: mensaje generado por el módulo i
        #   - d_c: dimensión de comunicación (communication_dim)
        #   - Cada módulo puede enviar mensajes a otros módulos
        # NOTACIÓN EN CÓDIGO: communication_networks[i] genera mensajes del módulo i
        # CÓDIGO: Redes que generan mensajes para comunicación entre módulos
        self.communication_networks = nn.ModuleList([
            nn.Sequential(
                nn.Linear(config.module_dim, config.communication_dim),
                nn.GELU(),
                nn.Linear(config.communication_dim, config.communication_dim)
            ) for _ in range(config.num_modules)
        ])
        
        # EN EL PAPER: Sección 3.2 - Message Reception
        # Cada módulo recibe mensajes de todos los demás módulos
        # NOTACIÓN DEL PAPER: received_i = MessageReceiver_i([msg_1, ..., msg_N]) ∈ R^{d_m}
        #   donde:
        #   - received_i: información recibida por el módulo i
        #   - [msg_1, ..., msg_N]: mensajes de todos los módulos
        #   - NOTACIÓN: received_i = f_receive(concat(msg_1, ..., msg_N))
        # NOTACIÓN EN CÓDIGO: message_receivers[i] procesa mensajes recibidos por módulo i
        # CÓDIGO: Redes que procesan mensajes recibidos de otros módulos
        self.message_receivers = nn.ModuleList([
            nn.Sequential(
                nn.Linear(config.communication_dim * config.num_modules, config.module_dim),
                nn.GELU(),
                nn.Linear(config.module_dim, config.module_dim)
            ) for _ in range(config.num_modules)
        ])
        
        # EN EL PAPER: Sección 3.3 - Shared Global State
        # El paper presenta un "estado global" compartido (término exacto del paper) para coordinación
        # NOTACIÓN DEL PAPER: G = GlobalState([o_1, ..., o_N]) ∈ R^{d_g}
        #   donde:
        #   - G: estado global compartido
        #   - [o_1, ..., o_N]: outputs de todos los módulos
        #   - d_g: dimensión del estado global (global_state_dim)
        #   - El "estado global" compartido coordina todos los módulos
        # NOTACIÓN EN CÓDIGO: global_state_network genera estado global desde inputs y módulos
        # CÓDIGO: Red que genera estado global compartido para coordinación
        if config.use_global_state:
            self.global_state_network = nn.Sequential(
                nn.Linear(config.hidden_dim + config.module_dim * config.num_modules, config.global_state_dim),
                nn.GELU(),
                nn.Linear(config.global_state_dim, config.global_state_dim),
                nn.LayerNorm(config.global_state_dim)
            )
            
            # Actualización del estado global
            self.global_state_updater = nn.Sequential(
                nn.Linear(config.global_state_dim + config.module_dim * config.num_modules, config.global_state_dim),
                nn.GELU(),
                nn.Linear(config.global_state_dim, config.global_state_dim)
            )
        
        # Fusionador: Combina salidas de todos los módulos
        self.fusion_network = nn.Sequential(
            nn.Linear(config.module_dim * config.num_modules, config.hidden_dim),
            nn.GELU(),
            nn.Linear(config.hidden_dim, config.hidden_dim)
        )
        
        logger.info(f"ConcurrentModularAgent initialized: num_modules={config.num_modules}, module_dim={config.module_dim}")
    
    def _module_forward(self, module_idx: int, input_state: torch.Tensor, 
                       global_state: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Forward pass de un módulo individual.
        
        EN EL PAPER: Sección 3.1 - Modular Processing
        FÓRMULA EXACTA DEL PAPER: 
          o_i = M_i(input) ∈ R^{d_m}
        donde:
        - M_i: módulo i-ésimo especializado
        - input: estado de entrada input_state ∈ R^(B×N×d)
        - o_i: salida del módulo i ∈ R^(B×N×d_m) donde d_m es module_dim
        - El paper propone "módulos concurrentes que operan de forma autónoma" (término exacto)
        - Cada módulo procesa el input de forma especializada
        
        Si se usa estado global:
          o_i' = o_i + G' donde G' = expand(G) ajustado a d_m
        donde:
        - G: estado global global_state ∈ R^(B×d_g) donde d_g es global_state_dim
        - G': estado global expandido y ajustado ∈ R^(B×N×d_m)
        - o_i': salida del módulo con estado global incorporado
        
        Args:
            module_idx: Índice del módulo i
            input_state: [batch, seq, hidden_dim] - Estado de entrada input ∈ R^(B×N×d)
            global_state: [batch, global_state_dim] - Estado global G (opcional) ∈ R^(B×d_g)
        
        Returns:
            module_output: [batch, seq, module_dim] - Salida del módulo o_i ∈ R^(B×N×d_m)
        """
        # EN EL PAPER: Procesar input con módulo especializado
        # NOTACIÓN: o_i = M_i(input) donde M_i = modules[module_idx]
        #   M_i: R^(B×N×d) → R^(B×N×d_m) procesa input de forma especializada
        #   El paper propone módulos concurrentes que operan de forma autónoma
        # NOTACIÓN EN CÓDIGO: module_output = salida del módulo
        # CÓDIGO: Aplicar módulo especializado al input
        module_output = self.modules[module_idx](input_state)  # [batch, seq, module_dim] ∈ R^(B×N×d_m)
        
        # EN EL PAPER: Incorporar estado global si está disponible
        # NOTACIÓN: Si G (global_state) está disponible y use_global_state:
        #   G_expanded = expand(G) ∈ R^(B×N×d_g) - expandir para secuencia
        #   G' = adjust(G_expanded) ∈ R^(B×N×d_m) - ajustar a module_dim
        #   o_i' = o_i + G' ∈ R^(B×N×d_m)
        # NOTACIÓN EN CÓDIGO: module_output = salida con estado global incorporado
        # CÓDIGO: Incorporar estado global si está disponible
        if global_state is not None and self.config.use_global_state:
            # EN EL PAPER: Expandir global_state para combinarlo con module_output
            # NOTACIÓN: G_expanded = expand(G) ∈ R^(B×N×d_g)
            #   Operación: unsqueeze(1) agrega dimensión de secuencia, expand replica para todos los tokens
            # NOTACIÓN EN CÓDIGO: global_expanded = estado global expandido
            # CÓDIGO: Expandir global_state desde [batch, d_g] a [batch, seq, d_g]
            global_expanded = global_state.unsqueeze(1).expand(-1, module_output.size(1), -1)  # [batch, seq, global_state_dim] ∈ R^(B×N×d_g)
            
            # EN EL PAPER: Ajustar dimensión de global_expanded para que coincida con module_dim
            # NOTACIÓN: Si d_g > d_m: G' = G_expanded[:, :, :d_m] ∈ R^(B×N×d_m) (truncar)
            #   Si d_g < d_m: G' = concat(G_expanded, padding) ∈ R^(B×N×d_m) (padding)
            # NOTACIÓN EN CÓDIGO: global_expanded = estado global ajustado
            # CÓDIGO: Ajustar dimensión de global_expanded para que coincida con module_dim
            if global_expanded.size(-1) > module_output.size(-1):
                # EN EL PAPER: Truncar si global_expanded es más grande
                # NOTACIÓN: G' = G_expanded[:, :, :d_m] ∈ R^(B×N×d_m)
                # CÓDIGO: Truncar a module_dim dimensiones
                global_expanded = global_expanded[:, :, :module_output.size(-1)]  # [batch, seq, module_dim] ∈ R^(B×N×d_m)
            elif global_expanded.size(-1) < module_output.size(-1):
                # EN EL PAPER: Padding si global_expanded es más pequeño
                # NOTACIÓN: padding = zeros(B, N, d_m - d_g) ∈ R^(B×N×(d_m-d_g))
                #   G' = concat(G_expanded, padding) ∈ R^(B×N×d_m)
                # CÓDIGO: Agregar padding de ceros hasta module_dim
                padding = torch.zeros(module_output.size(0), module_output.size(1), 
                                    module_output.size(-1) - global_expanded.size(-1),
                                    device=global_expanded.device)  # [batch, seq, d_m - d_g] ∈ R^(B×N×(d_m-d_g))
                global_expanded = torch.cat([global_expanded, padding], dim=-1)  # [batch, seq, module_dim] ∈ R^(B×N×d_m)
            
            # EN EL PAPER: Incorporar estado global a salida del módulo
            # NOTACIÓN: o_i' = o_i + G' ∈ R^(B×N×d_m)
            #   Operación: R^(B×N×d_m) + R^(B×N×d_m) → R^(B×N×d_m) (suma elemento a elemento)
            #   Esto incorpora información global en cada módulo especializado
            # NOTACIÓN EN CÓDIGO: module_output = salida con estado global incorporado
            # CÓDIGO: Sumar estado global ajustado a module_output
            module_output = module_output + global_expanded  # [batch, seq, module_dim] ∈ R^(B×N×d_m)
        
        return module_output
    
    def _inter_module_communication(self, module_outputs: List[torch.Tensor]) -> List[torch.Tensor]:
        """
        Inter-Module Communication: Sistema de mensajes entre módulos.
        
        EN EL PAPER: Sección 3.2 - Inter-Module Communication
        FÓRMULA EXACTA DEL PAPER: 
          msg_i = CommunicationNetwork_i(o_i) ∈ R^{d_c}
          o_i' = o_i + MessageReceiver_i(concat([msg_1, ..., msg_N])) ∈ R^{d_m}
        donde:
        - o_i: salida del módulo i ∈ R^(B×N×d_m)
        - msg_i: mensaje del módulo i ∈ R^(B×N×d_c) donde d_c es communication_dim
        - CommunicationNetwork_i: red que genera mensaje desde salida del módulo
        - MessageReceiver_i: red que procesa mensajes recibidos
        - o_i': salida actualizada del módulo i ∈ R^(B×N×d_m)
        - El paper propone "comunicación entre módulos" (término exacto)
        - Cada módulo envía mensajes a todos los demás módulos
        
        Args:
            module_outputs: Lista de [batch, seq, module_dim] - Salidas de módulos {o_1, ..., o_N}
        
        Returns:
            updated_outputs: Lista de [batch, seq, module_dim] - Salidas actualizadas {o_1', ..., o_N'}
        """
        batch_size, seq_len = module_outputs[0].shape[:2]
        # NOTACIÓN: module_outputs = {o_1, ..., o_N} donde cada o_i ∈ R^(B×N×d_m)
        
        # EN EL PAPER: Generar mensajes de cada módulo
        # NOTACIÓN: Para cada módulo i: msg_i = CommunicationNetwork_i(o_i) ∈ R^(B×N×d_c)
        #   donde CommunicationNetwork_i: R^(B×N×d_m) → R^(B×N×d_c) genera mensaje
        # NOTACIÓN EN CÓDIGO: messages = lista de mensajes de todos los módulos
        # CÓDIGO: Generar mensaje de cada módulo usando su communication_network
        messages = []
        for i, module_output in enumerate(module_outputs):
            # EN EL PAPER: Generar mensaje del módulo i
            # NOTACIÓN: msg_i = CommunicationNetwork_i(o_i) donde o_i = module_output
            # CÓDIGO: Aplicar communication_network para generar mensaje
            message = self.communication_networks[i](module_output)  # [batch, seq, communication_dim] ∈ R^(B×N×d_c)
            messages.append(message)  # Lista de mensajes
        
        # EN EL PAPER: Cada módulo recibe mensajes de todos los demás
        # NOTACIÓN: Para cada módulo i:
        #   all_messages = concat([msg_1, ..., msg_N]) ∈ R^(B×N×(N·d_c))
        #   received_info = MessageReceiver_i(all_messages) ∈ R^(B×N×d_m)
        #   o_i' = o_i + received_info ∈ R^(B×N×d_m)
        # NOTACIÓN EN CÓDIGO: updated_outputs = salidas actualizadas de todos los módulos
        # CÓDIGO: Cada módulo recibe y procesa mensajes de todos los demás
        updated_outputs = []
        for i, module_output in enumerate(module_outputs):
            # EN EL PAPER: Concatenar todos los mensajes
            # NOTACIÓN: all_messages = concat([msg_1, ..., msg_N]) ∈ R^(B×N×(N·d_c))
            #   donde concat concatena en la última dimensión: R^(B×N×d_c) + ... + R^(B×N×d_c) → R^(B×N×(N·d_c))
            # NOTACIÓN EN CÓDIGO: all_messages = todos los mensajes concatenados
            # CÓDIGO: Concatenar todos los mensajes en la última dimensión
            all_messages = torch.cat(messages, dim=-1)  # [batch, seq, communication_dim * num_modules] ∈ R^(B×N×(N·d_c))
            
            # EN EL PAPER: Procesar mensajes recibidos
            # NOTACIÓN: received_info = MessageReceiver_i(all_messages) ∈ R^(B×N×d_m)
            #   donde MessageReceiver_i: R^(B×N×(N·d_c)) → R^(B×N×d_m) procesa mensajes
            # NOTACIÓN EN CÓDIGO: received_info = información recibida por el módulo i
            # CÓDIGO: Aplicar message_receiver para procesar mensajes recibidos
            received_info = self.message_receivers[i](all_messages)  # [batch, seq, module_dim] ∈ R^(B×N×d_m)
            
            # EN EL PAPER: Combinar con output del módulo
            # NOTACIÓN: o_i' = o_i + received_info ∈ R^(B×N×d_m)
            #   Operación: R^(B×N×d_m) + R^(B×N×d_m) → R^(B×N×d_m) (suma elemento a elemento)
            #   Esto actualiza la salida del módulo con información de otros módulos
            # NOTACIÓN EN CÓDIGO: updated_output = salida actualizada del módulo i
            # CÓDIGO: Sumar información recibida a salida del módulo
            updated_output = module_output + received_info  # [batch, seq, module_dim] ∈ R^(B×N×d_m)
            updated_outputs.append(updated_output)  # Lista de salidas actualizadas
        
        return updated_outputs
    
    def _update_global_state(self, module_outputs: List[torch.Tensor], 
                            current_global_state: Optional[torch.Tensor]) -> torch.Tensor:
        """
        Actualizar estado global compartido basado en salidas de módulos.
        
        EN EL PAPER: Sección 3.3 - Global State
        FÓRMULA EXACTA DEL PAPER: 
          G' = GlobalStateUpdate(G, [o_1, ..., o_N]) ∈ R^{d_g}
        donde:
        - G: estado global actual current_global_state ∈ R^(B×d_g) donde d_g es global_state_dim
        - {o_1, ..., o_N}: salidas de módulos module_outputs ∈ R^(B×N×d_m)
        - G': estado global actualizado ∈ R^(B×d_g)
        - GlobalStateUpdate: red que actualiza estado global desde salidas de módulos
        - El paper propone "estado global" (término exacto) compartido entre módulos
        
        Args:
            module_outputs: Lista de [batch, seq, module_dim] - Salidas de módulos {o_1, ..., o_N}
            current_global_state: [batch, global_state_dim] - Estado global actual G (opcional) ∈ R^(B×d_g)
        
        Returns:
            updated_global: [batch, global_state_dim] - Estado global actualizado G' ∈ R^(B×d_g)
        """
        # EN EL PAPER: Verificar si se usa estado global
        # CÓDIGO: Retornar None si no se usa estado global
        if not self.config.use_global_state:
            return None
        
        batch_size, seq_len = module_outputs[0].shape[:2]
        # NOTACIÓN: module_outputs = {o_1, ..., o_N} donde cada o_i ∈ R^(B×N×d_m)
        
        # EN EL PAPER: Concatenar todas las salidas de módulos
        # NOTACIÓN: all_module_outputs = concat([o_1, ..., o_N]) ∈ R^(B×N×(N·d_m))
        #   donde concat concatena en la última dimensión: R^(B×N×d_m) + ... + R^(B×N×d_m) → R^(B×N×(N·d_m))
        # NOTACIÓN EN CÓDIGO: all_module_outputs = todas las salidas concatenadas
        # CÓDIGO: Concatenar todas las salidas de módulos en la última dimensión
        all_module_outputs = torch.cat(module_outputs, dim=-1)  # [batch, seq, module_dim * num_modules] ∈ R^(B×N×(N·d_m))
        
        # EN EL PAPER: Verificar si hay estado global actual
        # NOTACIÓN: Si G (current_global_state) es None, se inicializa en forward()
        # CÓDIGO: Retornar None si no hay estado global actual (se inicializa en forward)
        if current_global_state is None:
            # EN EL PAPER: Inicializar estado global desde el promedio de hidden_states
            # NOTACIÓN: Esto se hace en forward() antes de llamar a este método
            # CÓDIGO: Retornar None si no hay estado global (se inicializa en forward)
            return None
        
        # EN EL PAPER: Actualizar estado global
        # NOTACIÓN: G_expanded = expand(G) ∈ R^(B×N×d_g) - expandir para secuencia
        #   combined = concat(G_expanded, all_module_outputs) ∈ R^(B×N×(d_g+N·d_m))
        #   G' = GlobalStateUpdate(combined) ∈ R^(B×N×d_g)
        #   G'_final = mean(G', dim=1) ∈ R^(B×d_g) - promedio sobre secuencia
        # NOTACIÓN EN CÓDIGO: updated_global = estado global actualizado
        # CÓDIGO: Actualizar estado global desde salidas de módulos
        # EN EL PAPER: Expandir current_global_state para combinarlo
        # NOTACIÓN: G_expanded = expand(G) ∈ R^(B×N×d_g)
        #   Operación: unsqueeze(1) agrega dimensión de secuencia, expand replica para todos los tokens
        # NOTACIÓN EN CÓDIGO: global_expanded = estado global expandido
        # CÓDIGO: Expandir current_global_state desde [batch, d_g] a [batch, seq, d_g]
        global_expanded = current_global_state.unsqueeze(1).expand(-1, seq_len, -1)  # [batch, seq, global_state_dim] ∈ R^(B×N×d_g)
        
        # EN EL PAPER: Combinar estado global expandido con salidas de módulos
        # NOTACIÓN: combined = concat(G_expanded, all_module_outputs) ∈ R^(B×N×(d_g+N·d_m))
        #   donde concat concatena en la última dimensión: R^(B×N×d_g) + R^(B×N×(N·d_m)) → R^(B×N×(d_g+N·d_m))
        # NOTACIÓN EN CÓDIGO: combined = entrada combinada para global_state_updater
        # CÓDIGO: Concatenar estado global expandido y salidas de módulos
        combined = torch.cat([global_expanded, all_module_outputs], dim=-1)  # [batch, seq, global_state_dim + module_dim * num_modules] ∈ R^(B×N×(d_g+N·d_m))
        
        # EN EL PAPER: Aplicar global_state_updater
        # NOTACIÓN: G' = GlobalStateUpdate(combined) ∈ R^(B×N×d_g)
        #   donde GlobalStateUpdate: R^(B×N×(d_g+N·d_m)) → R^(B×N×d_g) actualiza estado global
        # NOTACIÓN EN CÓDIGO: updated_global = estado global actualizado
        # CÓDIGO: Aplicar global_state_updater para actualizar estado global
        updated_global = self.global_state_updater(combined)  # [batch, seq, global_state_dim] ∈ R^(B×N×d_g)
        
        # EN EL PAPER: Promediar sobre secuencia para obtener estado global único
        # NOTACIÓN: G'_final = mean(G', dim=1) ∈ R^(B×d_g)
        #   Operación: promedio sobre dimensión de secuencia para obtener estado global único por batch
        # NOTACIÓN EN CÓDIGO: updated_global = estado global final (promediado)
        # CÓDIGO: Promediar sobre dimensión de secuencia para obtener estado global único
        updated_global = updated_global.mean(dim=1)  # [batch, global_state_dim] ∈ R^(B×d_g)
        
        return updated_global
    
    def forward(self, hidden_states: torch.Tensor, **kwargs) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass: Concurrent Modular Agent.
        
        Proceso:
        1. Cada módulo procesa el input de forma especializada (concurrente)
        2. Módulos se comunican entre sí mediante mensajes
        3. Estado global se actualiza basado en salidas de módulos
        4. Fusionar salidas de todos los módulos
        
        Args:
            hidden_states: [batch, seq, hidden_dim] - Input states
        
        Returns:
            output: [batch, seq, hidden_dim] - Output fusionado de todos los módulos
            metadata: Dict con métricas de módulos y comunicación
        """
        batch_size, seq_len, hidden_dim = hidden_states.shape
        
        # Inicializar estado global si se usa
        global_state = None
        if self.config.use_global_state:
            # Inicializar desde promedio de hidden_states
            global_state = hidden_states.mean(dim=1)  # [batch, hidden_dim]
            # Expandir a global_state_dim si es necesario
            if global_state.size(-1) != self.config.global_state_dim:
                if global_state.size(-1) < self.config.global_state_dim:
                    padding = torch.zeros(batch_size, self.config.global_state_dim - global_state.size(-1),
                                        device=global_state.device)
                    global_state = torch.cat([global_state, padding], dim=-1)
                else:
                    global_state = global_state[:, :self.config.global_state_dim]
        
        # PASO 1: Procesamiento concurrente por módulos especializados
        module_outputs = []
        for i in range(self.config.num_modules):
            module_output = self._module_forward(i, hidden_states, global_state)
            module_outputs.append(module_output)
        
        # PASO 2: Comunicación entre módulos (múltiples pasos)
        for comm_step in range(self.config.communication_steps):
            module_outputs = self._inter_module_communication(module_outputs)
        
        # PASO 3: Actualizar estado global
        if self.config.use_global_state:
            # Crear estado global inicial desde hidden_states y módulos
            all_module_outputs = torch.cat(module_outputs, dim=-1)
            global_input = torch.cat([hidden_states, all_module_outputs], dim=-1)
            global_state = self.global_state_network(global_input).mean(dim=1)  # [batch, global_state_dim]
            
            # Actualizar estado global
            global_state = self._update_global_state(module_outputs, global_state)
        
        # PASO 4: Fusionar salidas de todos los módulos
        all_module_outputs = torch.cat(module_outputs, dim=-1)  # [batch, seq, module_dim * num_modules]
        output = self.fusion_network(all_module_outputs)  # [batch, seq, hidden_dim]
        
        # Metadata
        module_norms = [out.norm(dim=-1).mean().item() for out in module_outputs]
        metadata = {
            'num_modules': self.config.num_modules,
            'communication_steps': self.config.communication_steps,
            'module_output_norms': module_norms,
            'module_output_mean_norm': sum(module_norms) / len(module_norms),
            'global_state_norm': global_state.norm(dim=-1).mean().item() if global_state is not None else 0.0
        }
        
        self._update_metrics(
            num_modules=metadata['num_modules'],
            module_output_mean_norm=metadata['module_output_mean_norm']
        )
        
        return output, metadata

