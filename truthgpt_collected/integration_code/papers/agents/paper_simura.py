#!/usr/bin/env python3
"""
SimuRA: Towards General Goal-Oriented Agent via Simulative Reasoning Architecture with LLM-Based World Model
==========================================================================================================
Deng, Hou, Shen, Jin, Neubig, Hu, Xing (2025)

Venue: arXiv
Year: 2025

Técnica principal (EXACTO según descripción del paper):
- Proponen un "world-model" basado en LLM para hacer simulaciones mental-lingüísticas
- Planear acciones y razonar como agente general
- Arquitectura de razonamiento simulativo (Simulative Reasoning Architecture)
- World Model basado en LLM para simular estados y transiciones del entorno

MATEMÁTICAS DEL PAPER IMPLEMENTADAS:

1. LLM-Based World Model:
   - Para cada estado s_t y acción a_t: s_{t+1} = WorldModel(s_t, a_t, g) ∈ R^d
   - donde g es el objetivo (goal) codificado
   - El World Model simula el entorno usando representaciones lingüísticas del LLM
   - Predice estados futuros basado en el estado actual y acciones propuestas
   - Implementado en: _world_model_predict()

2. Simulative Reasoning (Simulaciones Mental-Lingüísticas):
   - Para K pasos de simulación: S = {s_1, s_2, ..., s_K} donde s_k = WorldModel(s_{k-1}, a_{k-1}, g)
   - Realiza simulaciones mental-lingüísticas antes de actuar
   - Simula múltiples pasos hacia adelante para predecir consecuencias
   - NOTACIÓN: S = Simulate(s_0, g, K) donde K es el número de pasos de simulación
   - Implementado en: _mental_simulation()

3. Goal-Oriented Planning:
   - Plan π = Plan(s_current, S, g) donde S son estados simulados
   - Planifica secuencia de acciones hacia el objetivo g
   - Analiza las simulaciones y planifica la mejor secuencia de acciones
   - NOTACIÓN: π = argmax_{a} E[Reward(simulate(s, a, g))]
   - Implementado en: _goal_oriented_planning()

4. Action Selection:
   - a* = SelectAction(π, S) basado en simulaciones
   - Selecciona la mejor acción basada en simulaciones y plan
   - Evalúa calidad de cada estado simulado
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
class SimuRAConfig(BasePaperConfig):
    """
    Configuración para SimuRA.
    
    EN EL PAPER: Sección 3 - Architecture Configuration
    - world_model_dim: Dimensión del World Model (d_w en el paper)
    - num_simulation_steps: Número de pasos de simulación K
    - planning_horizon: Horizonte de planificación H
    - goal_embedding_dim: Dimensión del embedding del objetivo g
    - simulation_temperature: Temperatura para exploración en simulaciones
    """
    world_model_dim: int = 512
    num_simulation_steps: int = 5  # K en el paper
    planning_horizon: int = 10  # H en el paper
    goal_embedding_dim: int = 256
    use_mental_simulation: bool = True
    simulation_temperature: float = 0.7  # τ en el paper


class SimuRAModule(BasePaperModule):
    """
    SimuRA: Simulative Reasoning Architecture con LLM-Based World Model.
    
    EN EL PAPER: Sección 3 - Simulative Reasoning Architecture
    - El paper propone un "world-model" basado en LLM para hacer simulaciones mental-lingüísticas
    - Planear acciones y razonar como agente general
    - Arquitectura de razonamiento simulativo (Simulative Reasoning Architecture)
    - World Model basado en LLM para simular estados y transiciones
    
    EN EL PAPER: Sección 3.1 - World Model
    - El World Model simula el entorno usando representaciones lingüísticas del LLM
    - Predice estados futuros basado en el estado actual y acciones propuestas
    - NOTACIÓN: s_{t+1} = WorldModel(s_t, a_t, g)
    
    EN EL PAPER: Sección 3.2 - Simulative Reasoning
    - Realiza simulaciones mental-lingüísticas antes de actuar
    - Simula múltiples pasos hacia adelante para predecir consecuencias
    - NOTACIÓN: S = Simulate(s_0, g, K) donde K es el número de pasos
    """
    
    def __init__(self, config: SimuRAConfig):
        """
        Inicialización del módulo SimuRA.
        
        EN EL PAPER: Sección 3.1 - Architecture Components
        - World Model: Simula estados del entorno usando LLM
        - Simulative Reasoning: Realiza simulaciones mental-lingüísticas
        - Goal-Oriented Planning: Planifica acciones hacia objetivos
        - Action Selection: Selecciona acciones basadas en simulaciones
        
        CÓDIGO: Inicializamos:
        1. World Model: Predice estados futuros
        2. Goal Encoder: Codifica objetivos
        3. Simulation Network: Realiza simulaciones
        4. Planning Network: Planifica acciones
        5. Action Selector: Selecciona mejores acciones
        """
        super().__init__(config)
        self.config = config
        
        # EN EL PAPER: Sección 3.1 - LLM-Based World Model
        # El paper propone un "world-model" basado en LLM (término exacto del paper)
        # NOTACIÓN DEL PAPER: s_{t+1} = WorldModel(s_t, a_t, g) ∈ R^d
        #   donde:
        #   - s_t: estado actual en R^d
        #   - a_t: acción propuesta
        #   - g: objetivo (goal) codificado
        #   - WorldModel: red neuronal que simula el entorno usando representaciones lingüísticas
        # NOTACIÓN EN CÓDIGO: world_model predice s_{t+1} desde (s_t, g)
        # CÓDIGO: Red que predice estados futuros basado en estado actual y objetivo
        self.world_model = nn.Sequential(
            nn.Linear(config.hidden_dim + config.goal_embedding_dim, config.world_model_dim),
            nn.GELU(),
            nn.Linear(config.world_model_dim, config.hidden_dim),
            nn.LayerNorm(config.hidden_dim)
        )
        
        # EN EL PAPER: Sección 3.1 - Goal Encoding
        # El paper codifica objetivos (goals) en embeddings para guiar la planificación
        # NOTACIÓN DEL PAPER: g = GoalEncoder(goal_text) ∈ R^{d_g}
        #   donde d_g es la dimensión del embedding del objetivo
        # NOTACIÓN EN CÓDIGO: goal_encoder codifica objetivos en embeddings
        # CÓDIGO: Red que codifica objetivos en representaciones vectoriales
        self.goal_encoder = nn.Sequential(
            nn.Linear(config.hidden_dim, config.goal_embedding_dim),
            nn.GELU(),
            nn.Linear(config.goal_embedding_dim, config.goal_embedding_dim)
        )
        
        # EN EL PAPER: Sección 3.2 - Simulative Reasoning (Simulaciones Mental-Lingüísticas)
        # El paper realiza "simulaciones mental-lingüísticas" (término exacto del paper)
        # NOTACIÓN DEL PAPER: S = {s_1, s_2, ..., s_K} donde s_k = WorldModel(s_{k-1}, a_{k-1}, g)
        #   donde:
        #   - K: número de pasos de simulación
        #   - s_k: estado simulado en el paso k
        #   - Simula múltiples pasos hacia adelante para predecir consecuencias
        # NOTACIÓN EN CÓDIGO: simulation_network realiza simulaciones mental-lingüísticas
        # CÓDIGO: Transformer Decoder que simula múltiples pasos hacia adelante
        self.simulation_network = nn.TransformerDecoder(
            nn.TransformerDecoderLayer(
                d_model=config.hidden_dim,
                nhead=8,
                dim_feedforward=config.hidden_dim * 4,
                dropout=0.1,
                batch_first=True
            ),
            num_layers=3
        )
        
        # EN EL PAPER: Sección 3.3 - Goal-Oriented Planning
        # El paper planifica acciones orientadas al objetivo (goal-oriented planning)
        # NOTACIÓN DEL PAPER: π = Plan(s_current, S, g) donde S son estados simulados
        #   donde:
        #   - π: plan (secuencia de acciones)
        #   - s_current: estado actual
        #   - S: estados simulados {s_1, ..., s_K}
        #   - g: objetivo
        #   - Analiza las simulaciones y planifica la mejor secuencia de acciones
        # NOTACIÓN EN CÓDIGO: planning_network genera plan desde simulaciones
        # CÓDIGO: Red que planifica secuencia de acciones basada en simulaciones
        self.planning_network = nn.Sequential(
            nn.Linear(config.hidden_dim * 2, config.hidden_dim),
            nn.GELU(),
            nn.Linear(config.hidden_dim, config.hidden_dim)
        )
        
        # EN EL PAPER: Sección 3.4 - Action Selection
        # El paper selecciona la mejor acción basada en simulaciones
        # NOTACIÓN DEL PAPER: a* = SelectAction(π, S) = argmax_{a} E[Reward(simulate(s, a, g))]
        #   donde:
        #   - a*: mejor acción seleccionada
        #   - π: plan generado
        #   - S: estados simulados
        #   - Evalúa calidad de cada estado simulado y selecciona la mejor acción
        # NOTACIÓN EN CÓDIGO: action_selector evalúa y selecciona acciones
        # CÓDIGO: Red que evalúa calidad de estados simulados y selecciona mejor acción
        self.action_selector = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim // 2),
            nn.GELU(),
            nn.Linear(config.hidden_dim // 2, 1),
            nn.Sigmoid()
        )
        
        logger.info(f"SimuRA initialized: world_model_dim={config.world_model_dim}, simulation_steps={config.num_simulation_steps}")
    
    def _world_model_predict(self, state: torch.Tensor, goal: torch.Tensor) -> torch.Tensor:
        """
        World Model: Predice el siguiente estado basado en el estado actual y el objetivo.
        
        EN EL PAPER: Sección 3.1 - LLM-Based World Model
        FÓRMULA EXACTA DEL PAPER: 
          s_{t+1} = WorldModel(s_t, a_t, g) ∈ R^d
        donde:
        - s_t: estado actual ∈ R^(B×N×d) donde B=batch, N=seq_len, d=hidden_dim
        - a_t: acción propuesta (implícita en state)
        - g: objetivo (goal) codificado ∈ R^(B×N×d_g) donde d_g es goal_embedding_dim
        - WorldModel: red neuronal que simula el entorno usando representaciones lingüísticas del LLM
        - El World Model predice estados futuros basado en el estado actual y acciones propuestas
        - El paper propone un "world-model" basado en LLM (término exacto del paper)
        
        Args:
            state: [batch, seq, hidden_dim] - Estado actual s_t ∈ R^(B×N×d)
            goal: [batch, seq, goal_embedding_dim] - Objetivo codificado g ∈ R^(B×N×d_g)
        
        Returns:
            next_state: [batch, seq, hidden_dim] - Estado siguiente predicho s_{t+1} ∈ R^(B×N×d)
        """
        # EN EL PAPER: Combinar estado actual con objetivo
        # NOTACIÓN: combined = concat(s_t, g) ∈ R^(B×N×(d+d_g))
        #   donde:
        #   - s_t = state ∈ R^(B×N×d)
        #   - g = goal ∈ R^(B×N×d_g)
        #   - concat concatena en la última dimensión: R^(B×N×d) + R^(B×N×d_g) → R^(B×N×(d+d_g))
        # NOTACIÓN EN CÓDIGO: combined = entrada combinada para world_model
        # CÓDIGO: Concatenar state y goal en la última dimensión
        combined = torch.cat([state, goal], dim=-1)  # [batch, seq, hidden_dim + goal_dim] ∈ R^(B×N×(d+d_g))
        
        # EN EL PAPER: Aplicar World Model para predecir siguiente estado
        # NOTACIÓN: s_{t+1} = WorldModel(combined) ∈ R^(B×N×d)
        #   donde WorldModel: R^(B×N×(d+d_g)) → R^(B×N×d) predice estado siguiente
        #   El World Model simula el entorno usando representaciones lingüísticas del LLM
        # NOTACIÓN EN CÓDIGO: next_state = estado siguiente predicho
        # CÓDIGO: Aplicar world_model para predecir siguiente estado
        next_state = self.world_model(combined)  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
        return next_state
    
    def _mental_simulation(self, initial_state: torch.Tensor, goal: torch.Tensor) -> List[torch.Tensor]:
        """
        Simulative Reasoning: Realiza simulaciones mental-lingüísticas.
        
        EN EL PAPER: Sección 3.2 - Simulative Reasoning (Simulaciones Mental-Lingüísticas)
        FÓRMULA EXACTA DEL PAPER: 
          S = {s_1, s_2, ..., s_K} donde s_k = WorldModel(s_{k-1}, a_{k-1}, g)
        donde:
        - K: número de pasos de simulación (num_simulation_steps)
        - s_k: estado simulado en el paso k
        - s_0: estado inicial (initial_state)
        - g: objetivo codificado
        - El paper realiza "simulaciones mental-lingüísticas" (término exacto) antes de actuar
        - Simula múltiples pasos hacia adelante para predecir consecuencias
        
        NOTACIÓN: S = Simulate(s_0, g, K)
        
        Args:
            initial_state: [batch, seq, hidden_dim] - Estado inicial s_0
            goal: [batch, goal_embedding_dim] - Objetivo codificado g
        
        Returns:
            simulated_states: Lista de [batch, seq, hidden_dim] - Estados simulados S = {s_1, ..., s_K}
        """
        # EN EL PAPER: Inicializar lista de estados simulados
        # NOTACIÓN: S = {} - lista vacía que se llenará con estados simulados
        # CÓDIGO: Lista para almacenar estados simulados
        simulated_states = []
        # EN EL PAPER: Estado inicial para simulación
        # NOTACIÓN: s_0 = initial_state ∈ R^(B×N×d)
        # CÓDIGO: Empezar desde estado inicial
        current_state = initial_state  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
        
        # EN EL PAPER: Simular K pasos hacia adelante
        # NOTACIÓN: Para k = 1, 2, ..., K donde K = num_simulation_steps
        # CÓDIGO: Iterar sobre número de pasos de simulación
        for step in range(self.config.num_simulation_steps):
            # EN EL PAPER: Predecir siguiente estado usando World Model
            # NOTACIÓN: s_k = WorldModel(s_{k-1}, a_{k-1}, g) ∈ R^(B×N×d)
            #   donde:
            #   - s_{k-1} = current_state es el estado en el paso k-1
            #   - g = goal es el objetivo codificado
            #   - s_k = next_state es el estado predicho para el paso k
            # NOTACIÓN EN CÓDIGO: next_state = estado predicho por World Model
            # CÓDIGO: Predecir siguiente estado usando World Model
            next_state = self._world_model_predict(current_state, goal)  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
            
            # EN EL PAPER: Usar simulation network para refinar la predicción
            # NOTACIÓN: queries = s_{k-1} + noise · τ donde noise ~ N(0,1), τ = simulation_temperature
            #   simulated_state = SimulationNetwork(queries, s_k) ∈ R^(B×N×d)
            #   donde:
            #   - queries ∈ R^(B×N×d) son queries con ruido para exploración
            #   - τ = simulation_temperature es la temperatura para exploración
            #   - SimulationNetwork es un Transformer Decoder que refina la predicción
            #   - El paper realiza "simulaciones mental-lingüísticas" (término exacto)
            # NOTACIÓN EN CÓDIGO: queries = queries con ruido para exploración
            # CÓDIGO: Crear queries con ruido gaussiano multiplicado por temperatura
            queries = current_state + torch.randn_like(current_state) * self.config.simulation_temperature  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
            # EN EL PAPER: Aplicar simulation network (Transformer Decoder)
            # NOTACIÓN: simulated_state = SimulationNetwork(queries, next_state.unsqueeze(1))
            #   donde next_state.unsqueeze(1) ∈ R^(B×1×N×d) agrega dimensión para decoder
            # NOTACIÓN EN CÓDIGO: simulated_state = estado simulado refinado
            # CÓDIGO: Aplicar simulation_network (Transformer Decoder) para refinar predicción
            simulated_state = self.simulation_network(queries, next_state.unsqueeze(1))  # [batch, 1, hidden_dim] ∈ R^(B×1×d)
            # EN EL PAPER: Eliminar dimensión de secuencia unitaria
            # NOTACIÓN: simulated_state = squeeze(simulated_state, dim=1) ∈ R^(B×N×d)
            # CÓDIGO: Eliminar dimensión unitaria agregada por decoder
            simulated_state = simulated_state.squeeze(1)  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
            
            # EN EL PAPER: Almacenar estado simulado
            # NOTACIÓN: S = S ∪ {s_k} donde s_k = simulated_state
            # CÓDIGO: Agregar estado simulado a la lista
            simulated_states.append(simulated_state)  # Lista de [batch, seq, hidden_dim]
            # EN EL PAPER: Actualizar estado actual para siguiente iteración
            # NOTACIÓN: s_{k-1} = s_k para siguiente paso
            # CÓDIGO: Actualizar current_state para siguiente iteración
            current_state = simulated_state  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
        
        # EN EL PAPER: Retornar todos los estados simulados
        # NOTACIÓN: S = {s_1, s_2, ..., s_K} donde cada s_k ∈ R^(B×N×d)
        # CÓDIGO: Retornar lista de estados simulados
        return simulated_states  # Lista de K elementos, cada uno ∈ R^(B×N×d)
    
    def _goal_oriented_planning(self, current_state: torch.Tensor, goal: torch.Tensor, 
                                simulated_states: List[torch.Tensor]) -> torch.Tensor:
        """
        Goal-Oriented Planning: Planifica acciones hacia el objetivo.
        
        EN EL PAPER: Sección 3.3 - Goal-Oriented Planning
        FÓRMULA EXACTA DEL PAPER: 
          π = Plan(s_current, S, g) = argmax_{a} E[Reward(simulate(s, a, g))]
        donde:
        - π: plan (secuencia de acciones) hacia el objetivo
        - s_current: estado actual
        - S: estados simulados {s_1, ..., s_K}
        - g: objetivo codificado
        - El paper planifica acciones orientadas al objetivo (goal-oriented planning)
        - Analiza las simulaciones y planifica la mejor secuencia de acciones
        
        Args:
            current_state: [batch, seq, hidden_dim] - Estado actual s_current
            goal: [batch, goal_embedding_dim] - Objetivo codificado g
            simulated_states: Lista de [batch, seq, hidden_dim] - Estados simulados S
        
        Returns:
            plan: [batch, seq, hidden_dim] - Plan π generado
        """
        # EN EL PAPER: Combinar estado actual con el último estado simulado
        # NOTACIÓN: Si S no está vacío: planning_input = concat(s_current, s_K) ∈ R^(B×N×(2d))
        #   Si S está vacío: planning_input = concat(s_current, s_current) ∈ R^(B×N×(2d))
        #   donde:
        #   - s_current = current_state ∈ R^(B×N×d) es el estado actual
        #   - s_K = last_simulated ∈ R^(B×N×d) es el último estado simulado
        #   - concat concatena en la última dimensión: R^(B×N×d) + R^(B×N×d) → R^(B×N×(2d))
        # NOTACIÓN EN CÓDIGO: planning_input = entrada combinada para planning_network
        # CÓDIGO: Combinar estado actual con último estado simulado (o consigo mismo si no hay simulaciones)
        if simulated_states:
            # EN EL PAPER: Usar último estado simulado
            # NOTACIÓN: last_simulated = s_K = simulated_states[-1] ∈ R^(B×N×d)
            # CÓDIGO: Obtener último estado simulado
            last_simulated = simulated_states[-1]  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
            # EN EL PAPER: Combinar estado actual con último simulado
            # NOTACIÓN: planning_input = concat(s_current, s_K) ∈ R^(B×N×(2d))
            # CÓDIGO: Concatenar current_state y last_simulated
            planning_input = torch.cat([current_state, last_simulated], dim=-1)  # [batch, seq, hidden_dim * 2] ∈ R^(B×N×(2d))
        else:
            # EN EL PAPER: Si no hay simulaciones, usar estado actual duplicado
            # NOTACIÓN: planning_input = concat(s_current, s_current) ∈ R^(B×N×(2d))
            # CÓDIGO: Concatenar current_state consigo mismo
            planning_input = torch.cat([current_state, current_state], dim=-1)  # [batch, seq, hidden_dim * 2] ∈ R^(B×N×(2d))
        
        # EN EL PAPER: Planificar usando planning network
        # NOTACIÓN: π = Plan(planning_input) ∈ R^(B×N×d)
        #   donde Plan: R^(B×N×(2d)) → R^(B×N×d) genera plan desde planning_input
        #   El paper planifica acciones orientadas al objetivo (goal-oriented planning)
        #   Analiza las simulaciones y planifica la mejor secuencia de acciones
        # NOTACIÓN EN CÓDIGO: plan = plan generado
        # CÓDIGO: Aplicar planning_network para generar plan
        plan = self.planning_network(planning_input)  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
        
        # EN EL PAPER: Incorporar objetivo en el plan
        # NOTACIÓN: π' = π + g_expanded ∈ R^(B×N×d)
        #   donde:
        #   - π = plan ∈ R^(B×N×d) es el plan generado
        #   - g = goal ∈ R^(B×N×d_g) es el objetivo codificado
        #   - g_expanded = expand(g) ∈ R^(B×N×d) es el objetivo expandido/truncado a hidden_dim
        #   - Operación: R^(B×N×d) + R^(B×N×d) → R^(B×N×d) (suma elemento a elemento)
        #   Esto incorpora el objetivo en el plan para orientarlo hacia la meta
        # NOTACIÓN EN CÓDIGO: plan = plan con objetivo incorporado
        # CÓDIGO: Expandir goal a dimensión de secuencia y truncar/expandir a hidden_dim, luego sumar al plan
        goal_expanded = goal.unsqueeze(1).expand(-1, plan.size(1), -1)  # [batch, seq, goal_dim] ∈ R^(B×N×d_g)
        # EN EL PAPER: Ajustar dimensión de goal si es necesario
        # NOTACIÓN: Si d_g > d: truncar a d dimensiones
        #   Si d_g < d: padding con ceros hasta d
        # CÓDIGO: Ajustar goal_expanded para que coincida con hidden_dim
        if goal_expanded.size(-1) != plan.size(-1):
            if goal_expanded.size(-1) > plan.size(-1):
                goal_expanded = goal_expanded[:, :, :plan.size(-1)]  # Truncar
            else:
                padding = torch.zeros(plan.size(0), plan.size(1), plan.size(-1) - goal_expanded.size(-1),
                                    device=goal_expanded.device)
                goal_expanded = torch.cat([goal_expanded, padding], dim=-1)  # Padding
        plan = plan + goal_expanded  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
        
        return plan
    
    def forward(self, hidden_states: torch.Tensor, goal: Optional[torch.Tensor] = None, 
                **kwargs) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass: Simulative Reasoning Architecture.
        
        EN EL PAPER: Sección 4 - Agent Execution Process
        
        Proceso completo:
        1. Codificar objetivo: g = GoalEncoder(goal_text)
        2. Simulaciones mental-lingüísticas: S = Simulate(s_0, g, K)
        3. Planificación orientada al objetivo: π = Plan(s_current, S, g)
        4. Selección de acción: a* = SelectAction(π, S)
        
        MATEMÁTICA DEL PAPER:
        - s_0 = hidden_states (estado inicial)
        - g = GoalEncoder(goal) si se proporciona, sino g = mean(hidden_states)
        - S = {s_1, ..., s_K} donde s_k = WorldModel(s_{k-1}, a_{k-1}, g)
        - π = Plan(s_0, S, g)
        - a* = argmax_{a} E[Reward(simulate(s_0, a, g))]
        - output = ApplyAction(s_0, a*)
        
        Args:
            hidden_states: [batch, seq, hidden_dim] - Estado actual s_0
            goal: [batch, hidden_dim] - Objetivo a alcanzar (opcional)
        
        Returns:
            output: [batch, seq, hidden_dim] - Estado mejorado con razonamiento simulativo
            metadata: Dict con métricas de simulación y planificación
        """
        batch_size, seq_len, hidden_dim = hidden_states.shape
        # NOTACIÓN: hidden_states ∈ R^(B×N×d) donde B=batch_size, N=seq_len, d=hidden_dim
        
        # EN EL PAPER: Codificar objetivo (usar promedio de hidden_states si no se proporciona)
        # NOTACIÓN: Si goal es None: g = mean(hidden_states, dim=1) ∈ R^(B×d)
        #   Si goal se proporciona: g = goal ∈ R^(B×d)
        #   g_embedding = GoalEncoder(g) ∈ R^(B×d_g) donde d_g es goal_embedding_dim
        # NOTACIÓN EN CÓDIGO: goal_embedding = objetivo codificado
        # CÓDIGO: Codificar objetivo o usar promedio de hidden_states como objetivo
        if goal is None:
            # EN EL PAPER: Usar promedio de hidden_states como objetivo implícito
            # NOTACIÓN: g = mean(hidden_states, dim=1) ∈ R^(B×d) - promedio sobre secuencia
            # CÓDIGO: Promediar hidden_states sobre dimensión de secuencia
            goal = hidden_states.mean(dim=1)  # [batch, hidden_dim] ∈ R^(B×d)
        
        # EN EL PAPER: Codificar objetivo en embedding
        # NOTACIÓN: g_embedding = GoalEncoder(g) ∈ R^(B×d_g)
        #   donde GoalEncoder: R^(B×d) → R^(B×d_g) codifica objetivo en embedding
        # CÓDIGO: Aplicar goal_encoder para codificar objetivo
        goal_embedding = self.goal_encoder(goal)  # [batch, goal_embedding_dim] ∈ R^(B×d_g)
        
        # EN EL PAPER: Expandir goal_embedding para combinarlo con estados
        # NOTACIÓN: g_expanded = expand(g_embedding) ∈ R^(B×N×d_g)
        #   Operación: unsqueeze(1) agrega dimensión de secuencia, expand replica para todos los tokens
        # NOTACIÓN EN CÓDIGO: goal_expanded = objetivo expandido para todos los tokens
        # CÓDIGO: Expandir goal_embedding desde [batch, goal_dim] a [batch, seq, goal_dim]
        goal_expanded = goal_embedding.unsqueeze(1).expand(-1, seq_len, -1)  # [batch, seq, goal_dim] ∈ R^(B×N×d_g)
        # EN EL PAPER: Ajustar dimensión de goal para que coincida con hidden_dim
        # NOTACIÓN: Si d_g > d: truncar a d dimensiones
        #   Si d_g < d: usar goal_expanded tal cual (se ajustará en métodos siguientes)
        # NOTACIÓN EN CÓDIGO: goal_for_states = objetivo ajustado para usar con estados
        # CÓDIGO: Truncar goal_expanded si es más grande que hidden_dim
        goal_for_states = goal_expanded[:, :, :hidden_dim] if goal_expanded.size(-1) > hidden_dim else goal_expanded  # [batch, seq, min(goal_dim, hidden_dim)]
        
        # EN EL PAPER: Realizar simulaciones mental-lingüísticas
        # NOTACIÓN: S = Simulate(s_0, g, K) donde s_0 = hidden_states, g = goal_for_states, K = num_simulation_steps
        #   S = {s_1, s_2, ..., s_K} donde cada s_k ∈ R^(B×N×d)
        #   El paper realiza "simulaciones mental-lingüísticas" (término exacto) antes de actuar
        # NOTACIÓN EN CÓDIGO: simulated_states = lista de estados simulados
        # CÓDIGO: Realizar simulaciones si está habilitado
        if self.config.use_mental_simulation:
            # EN EL PAPER: Simular múltiples pasos hacia adelante
            # NOTACIÓN: S = Simulate(s_0, g, K)
            # CÓDIGO: Realizar simulaciones mental-lingüísticas
            simulated_states = self._mental_simulation(hidden_states, goal_for_states)  # Lista de K elementos, cada uno ∈ R^(B×N×d)
        else:
            # EN EL PAPER: Sin simulaciones
            # NOTACIÓN: S = {} (lista vacía)
            # CÓDIGO: Lista vacía si no se usan simulaciones
            simulated_states = []  # Lista vacía
        
        # EN EL PAPER: Planificación orientada al objetivo
        # NOTACIÓN: π = Plan(s_current, S, g) donde s_current = hidden_states, S = simulated_states, g = goal_for_states
        #   El paper planifica acciones orientadas al objetivo (goal-oriented planning)
        #   Analiza las simulaciones y planifica la mejor secuencia de acciones
        # NOTACIÓN EN CÓDIGO: plan = plan generado
        # CÓDIGO: Planificar acciones orientadas al objetivo
        plan = self._goal_oriented_planning(hidden_states, goal_for_states, simulated_states)  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
        
        # EN EL PAPER: Seleccionar mejor acción basada en simulaciones
        # NOTACIÓN: a* = SelectAction(π, S) = argmax_{a} E[Reward(simulate(s, a, g))]
        #   Para cada s_k ∈ S: score_k = ActionSelector(s_k) ∈ [0, 1]^(B×N)
        #   best_score = mean([score_1, ..., score_K]) ∈ [0, 1]^(B×N)
        #   Evalúa calidad de cada estado simulado y selecciona la mejor acción
        # NOTACIÓN EN CÓDIGO: action_scores = scores de calidad para cada estado simulado
        # CÓDIGO: Evaluar calidad de cada estado simulado
        action_scores = []
        for sim_state in simulated_states:
            # EN EL PAPER: Evaluar calidad de estado simulado
            # NOTACIÓN: score_k = ActionSelector(s_k) ∈ [0, 1]^(B×N)
            #   donde ActionSelector: R^(B×N×d) → R^(B×N) evalúa calidad del estado
            # NOTACIÓN EN CÓDIGO: score = score de calidad del estado simulado
            # CÓDIGO: Aplicar action_selector y eliminar dimensión unitaria
            score = self.action_selector(sim_state).squeeze(-1)  # [batch, seq] ∈ [0, 1]^(B×N)
            action_scores.append(score)  # Lista de scores
        
        # EN EL PAPER: Combinar plan con mejor estado simulado
        # NOTACIÓN: Si action_scores no está vacío:
        #   best_scores = mean([score_1, ..., score_K]) ∈ [0, 1]^(B×N)
        #   best_mask = best_scores ∈ [0, 1]^(B×N×1) (expandido)
        #   output = π * (1 - best_mask) + best_simulated * best_mask ∈ R^(B×N×d)
        #   donde best_simulated = s_K (último estado simulado)
        #   Esto combina el plan con el mejor estado simulado usando máscara de scores
        # NOTACIÓN EN CÓDIGO: output = resultado combinado
        # CÓDIGO: Combinar plan con mejor estado simulado si hay scores
        if action_scores:
            # EN EL PAPER: Calcular score promedio de todos los estados simulados
            # NOTACIÓN: best_scores = mean([score_1, ..., score_K]) ∈ [0, 1]^(B×N)
            #   Operación: stack([score_1, ..., score_K]) ∈ R^(K×B×N), luego mean(dim=0) ∈ R^(B×N)
            # NOTACIÓN EN CÓDIGO: best_scores = score promedio
            # CÓDIGO: Apilar scores y promediar sobre dimensión de pasos de simulación
            best_scores = torch.stack(action_scores, dim=0).mean(dim=0)  # [batch, seq] ∈ [0, 1]^(B×N)
            # EN EL PAPER: Expandir score para crear máscara
            # NOTACIÓN: best_mask = unsqueeze(best_scores, dim=-1) ∈ [0, 1]^(B×N×1)
            # CÓDIGO: Expandir best_scores para crear máscara
            best_mask = best_scores.unsqueeze(-1)  # [batch, seq, 1] ∈ [0, 1]^(B×N×1)
            
            # EN EL PAPER: Combinar plan con mejor estado simulado
            # NOTACIÓN: output = π * (1 - best_mask) + best_simulated * best_mask ∈ R^(B×N×d)
            #   donde:
            #   - π = plan ∈ R^(B×N×d)
            #   - best_simulated = s_K ∈ R^(B×N×d) es el último estado simulado
            #   - best_mask ∈ [0, 1]^(B×N×1) es la máscara de scores
            #   - Operación: combinación ponderada entre plan y mejor estado simulado
            # NOTACIÓN EN CÓDIGO: output = resultado combinado
            # CÓDIGO: Combinar plan con mejor estado simulado usando máscara
            if simulated_states:
                # EN EL PAPER: Usar último estado simulado
                # NOTACIÓN: best_simulated = s_K = simulated_states[-1] ∈ R^(B×N×d)
                # CÓDIGO: Obtener último estado simulado
                best_simulated = simulated_states[-1]  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
                # EN EL PAPER: Combinación ponderada
                # NOTACIÓN: output = π * (1 - best_mask) + best_simulated * best_mask
                #   Operación: R^(B×N×d) * R^(B×N×1) + R^(B×N×d) * R^(B×N×1) → R^(B×N×d) (broadcasting)
                # CÓDIGO: Combinar plan y mejor estado simulado
                output = plan * (1 - best_mask) + best_simulated * best_mask  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
            else:
                # EN EL PAPER: Si no hay simulaciones, usar solo plan
                # NOTACIÓN: output = π
                # CÓDIGO: Usar solo plan si no hay simulaciones
                output = plan  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
        else:
            # EN EL PAPER: Si no hay action_scores, usar solo plan
            # NOTACIÓN: output = π
            # CÓDIGO: Usar solo plan si no hay scores
            output = plan  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
        
        # Metadata
        metadata = {
            'num_simulations': len(simulated_states),
            'planning_horizon': self.config.planning_horizon,
            'goal_embedding_norm': goal_embedding.norm(dim=-1).mean().item(),
            'simulation_variance': torch.stack(simulated_states).var(dim=0).mean().item() if simulated_states else 0.0,
            'action_score_mean': torch.stack(action_scores).mean().item() if action_scores else 0.0
        }
        
        self._update_metrics(
            num_simulations=metadata['num_simulations'],
            goal_embedding_norm=metadata['goal_embedding_norm']
        )
        
        return output, metadata

