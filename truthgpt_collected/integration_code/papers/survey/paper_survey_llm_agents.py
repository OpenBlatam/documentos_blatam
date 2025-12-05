#!/usr/bin/env python3
"""
A Survey on Large Language Model Based Autonomous Agents
========================================================
Tang, Chen, Yue, Fan, Zhou, Li, Zhang, Zhao (2024)

Venue: SpringerLink
Year: 2024

Técnica principal:
- Revisión sistemática del estado de agentes LLMs
- Análisis de: memoria, planificación, uso de herramientas, evaluación y desafíos
- Integración de técnicas principales de agentes LLM

Arquitectura:
- Memory Module: Integra técnicas de memoria revisadas
- Planning Module: Integra técnicas de planificación
- Tool Usage Module: Integra uso de herramientas
- Evaluation Module: Métricas de evaluación
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import logging

from ..core.paper_base import BasePaperModule, BasePaperConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SurveyLLMAgentsConfig(BasePaperConfig):
    """
    Configuración para Survey on LLM-Based Autonomous Agents.
    
    Parámetros:
        memory_dim: Dimensión del módulo de memoria
        planning_dim: Dimensión del módulo de planificación
        tool_dim: Dimensión del módulo de herramientas
        use_memory: Usar técnicas de memoria
        use_planning: Usar técnicas de planificación
        use_tools: Usar técnicas de herramientas
    """
    memory_dim: int = 256
    planning_dim: int = 256
    tool_dim: int = 256
    use_memory: bool = True
    use_planning: bool = True
    use_tools: bool = True


class SurveyLLMAgentsModule(BasePaperModule):
    """
    Survey on LLM-Based Autonomous Agents: Integración de técnicas principales.
    
    Integra técnicas revisadas en el survey:
    1. Memory: Técnicas de memoria para agentes
    2. Planning: Técnicas de planificación
    3. Tool Usage: Uso de herramientas externas
    4. Evaluation: Métricas de evaluación
    """
    
    def __init__(self, config: SurveyLLMAgentsConfig):
        super().__init__(config)
        self.config = config
        
        # Memory Module: Integra técnicas de memoria revisadas
        if config.use_memory:
            self.memory_module = nn.Sequential(
                nn.Linear(config.hidden_dim, config.memory_dim),
                nn.GELU(),
                nn.Linear(config.memory_dim, config.memory_dim),
                nn.LayerNorm(config.memory_dim)
            )
            # Memoria episódica y semántica
            self.memory_retrieval = nn.MultiheadAttention(
                embed_dim=config.memory_dim,
                num_heads=8,
                batch_first=True
            )
        
        # Planning Module: Integra técnicas de planificación
        if config.use_planning:
            self.planning_module = nn.Sequential(
                nn.Linear(config.hidden_dim, config.planning_dim),
                nn.GELU(),
                nn.Linear(config.planning_dim, config.planning_dim)
            )
            # Planificador jerárquico
            self.hierarchical_planner = nn.TransformerEncoder(
                nn.TransformerEncoderLayer(
                    d_model=config.planning_dim,
                    nhead=8,
                    dim_feedforward=config.planning_dim * 4,
                    dropout=0.1,
                    batch_first=True
                ),
                num_layers=2
            )
        
        # Tool Usage Module: Integra uso de herramientas
        if config.use_tools:
            self.tool_module = nn.Sequential(
                nn.Linear(config.hidden_dim, config.tool_dim),
                nn.GELU(),
                nn.Linear(config.tool_dim, config.tool_dim)
            )
            # Selector de herramientas
            self.tool_selector = nn.Sequential(
                nn.Linear(config.tool_dim, config.tool_dim // 2),
                nn.GELU(),
                nn.Linear(config.tool_dim // 2, 1),
                nn.Sigmoid()
            )
        
        # Fusionador: Combina memoria, planificación y herramientas
        fusion_input_dim = config.hidden_dim
        if config.use_memory:
            fusion_input_dim += config.memory_dim
        if config.use_planning:
            fusion_input_dim += config.planning_dim
        if config.use_tools:
            fusion_input_dim += config.tool_dim
        
        self.fusion_module = nn.Sequential(
            nn.Linear(fusion_input_dim, config.hidden_dim),
            nn.GELU(),
            nn.Linear(config.hidden_dim, config.hidden_dim)
        )
        
        logger.info(f"SurveyLLMAgents initialized: memory={config.use_memory}, planning={config.use_planning}, tools={config.use_tools}")
    
    def _memory_process(self, hidden_states: torch.Tensor) -> torch.Tensor:
        """
        Memory Module: Procesa usando técnicas de memoria.
        """
        if not self.config.use_memory:
            return None
        
        # Procesar con módulo de memoria
        memory_repr = self.memory_module(hidden_states)  # [batch, seq, memory_dim]
        
        # Recuperación de memoria usando atención
        memory_retrieved, _ = self.memory_retrieval(memory_repr, memory_repr, memory_repr)
        
        return memory_retrieved
    
    def _planning_process(self, hidden_states: torch.Tensor) -> torch.Tensor:
        """
        Planning Module: Procesa usando técnicas de planificación.
        """
        if not self.config.use_planning:
            return None
        
        # Procesar con módulo de planificación
        planning_repr = self.planning_module(hidden_states)  # [batch, seq, planning_dim]
        
        # Planificación jerárquica
        planned = self.hierarchical_planner(planning_repr)  # [batch, seq, planning_dim]
        
        return planned
    
    def _tool_process(self, hidden_states: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Tool Usage Module: Procesa usando técnicas de herramientas.
        
        Returns:
            tool_repr: [batch, seq, tool_dim] - Representación de herramientas
            tool_scores: [batch, seq] - Scores de uso de herramientas
        """
        if not self.config.use_tools:
            return None, None
        
        # Procesar con módulo de herramientas
        tool_repr = self.tool_module(hidden_states)  # [batch, seq, tool_dim]
        
        # Seleccionar herramientas
        tool_scores = self.tool_selector(tool_repr).squeeze(-1)  # [batch, seq]
        
        return tool_repr, tool_scores
    
    def forward(self, hidden_states: torch.Tensor, **kwargs) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass: Survey on LLM-Based Autonomous Agents.
        
        Integra técnicas principales revisadas en el survey:
        1. Memory: Técnicas de memoria
        2. Planning: Técnicas de planificación
        3. Tool Usage: Uso de herramientas
        
        Args:
            hidden_states: [batch, seq, hidden_dim] - Input states
        
        Returns:
            output: [batch, seq, hidden_dim] - Output integrado
            metadata: Dict con métricas de memoria, planificación y herramientas
        """
        # PASO 1: Memory Module
        memory_output = self._memory_process(hidden_states)  # [batch, seq, memory_dim] o None
        
        # PASO 2: Planning Module
        planning_output = self._planning_process(hidden_states)  # [batch, seq, planning_dim] o None
        
        # PASO 3: Tool Usage Module
        tool_output, tool_scores = self._tool_process(hidden_states)  # [batch, seq, tool_dim] o None
        
        # PASO 4: Fusionar todos los módulos
        fusion_inputs = [hidden_states]
        
        if memory_output is not None:
            # Expandir memory_output si es necesario
            if memory_output.size(-1) != self.config.hidden_dim:
                if memory_output.size(-1) < self.config.hidden_dim:
                    padding = torch.zeros(memory_output.size(0), memory_output.size(1),
                                        self.config.hidden_dim - memory_output.size(-1),
                                        device=memory_output.device)
                    memory_expanded = torch.cat([memory_output, padding], dim=-1)
                else:
                    memory_expanded = memory_output[:, :, :self.config.hidden_dim]
            else:
                memory_expanded = memory_output
            fusion_inputs.append(memory_expanded)
        
        if planning_output is not None:
            # Expandir planning_output si es necesario
            if planning_output.size(-1) != self.config.hidden_dim:
                if planning_output.size(-1) < self.config.hidden_dim:
                    padding = torch.zeros(planning_output.size(0), planning_output.size(1),
                                        self.config.hidden_dim - planning_output.size(-1),
                                        device=planning_output.device)
                    planning_expanded = torch.cat([planning_output, padding], dim=-1)
                else:
                    planning_expanded = planning_output[:, :, :self.config.hidden_dim]
            else:
                planning_expanded = planning_output
            fusion_inputs.append(planning_expanded)
        
        if tool_output is not None:
            # Expandir tool_output si es necesario
            if tool_output.size(-1) != self.config.hidden_dim:
                if tool_output.size(-1) < self.config.hidden_dim:
                    padding = torch.zeros(tool_output.size(0), tool_output.size(1),
                                        self.config.hidden_dim - tool_output.size(-1),
                                        device=tool_output.device)
                    tool_expanded = torch.cat([tool_output, padding], dim=-1)
                else:
                    tool_expanded = tool_output[:, :, :self.config.hidden_dim]
            else:
                tool_expanded = tool_output
            fusion_inputs.append(tool_expanded)
        
        # Concatenar y fusionar
        fused = torch.cat(fusion_inputs, dim=-1)  # [batch, seq, hidden_dim * num_modules]
        output = self.fusion_module(fused)  # [batch, seq, hidden_dim]
        
        # Metadata
        metadata = {
            'memory_used': memory_output is not None,
            'planning_used': planning_output is not None,
            'tools_used': tool_output is not None
        }
        
        if memory_output is not None:
            metadata['memory_norm'] = memory_output.norm(dim=-1).mean().item()
        
        if planning_output is not None:
            metadata['planning_norm'] = planning_output.norm(dim=-1).mean().item()
        
        if tool_output is not None:
            metadata['tool_norm'] = tool_output.norm(dim=-1).mean().item()
            metadata['tool_score_mean'] = tool_scores.mean().item()
        
        metadata['output_norm'] = output.norm(dim=-1).mean().item()
        
        self._update_metrics(
            memory_used=metadata['memory_used'],
            planning_used=metadata['planning_used'],
            tools_used=metadata['tools_used']
        )
        
        return output, metadata



