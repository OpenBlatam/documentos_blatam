#!/usr/bin/env python3
"""
DriveAgent: LLM-Driven Multi-Agent Autonomous Driving
======================================================
Hou, Wang, Yang, Lin, Feng, Min, Zhao (2025)

Venue: LXL Sword
Year: 2025

Técnica principal (EXACTO según descripción del paper):
- Un framework de agente modular para conducción autónoma
- Sensores: cámaras, LiDAR, GPS (términos exactos del paper)
- Agentes de razonamiento especializados
- Agente decisor para maniobras urgentes (término exacto)

MATEMÁTICAS DEL PAPER IMPLEMENTADAS:

1. Sensor Integration (Integración de Sensores):
   - Para S sensores: sensor_i = SensorProcessor_i(input) ∈ R^{d_s} donde i ∈ {camera, LiDAR, GPS}
   - El paper integra sensores: cámaras, LiDAR, GPS (términos exactos)
   - NOTACIÓN: sensors = [sensor_camera, sensor_lidar, sensor_gps]
   - Implementado en: _process_sensors()

2. Sensor Fusion (Fusión de Sensores):
   - fused = SensorFusion([sensor_1, ..., sensor_S]) ∈ R^d
   - Integra datos de múltiples sensores en una representación unificada
   - NOTACIÓN: fused = f_fusion(concat(sensor_1, ..., sensor_S))
   - Implementado en: _fuse_sensors()

3. Reasoning Agents (Agentes de Razonamiento):
   - Para R agentes: reasoning_i = ReasoningAgent_i(fused) ∈ R^{d_r}
   - Múltiples agentes de razonamiento especializados
   - NOTACIÓN: reasonings = [reasoning_1, ..., reasoning_R]
   - Implementado en: _reasoning_agents_process()

4. Urgent Maneuver Detection (Detección de Maniobras Urgentes):
   - urgent_score = UrgentDetector(reasoning) ∈ [0, 1]
   - El paper propone un agente decisor para maniobras urgentes (término exacto)
   - Detecta situaciones que requieren acción urgente
   - Implementado en: _detect_urgent_maneuvers()

5. Decision Agent (Agente Decisor):
   - decision = DecisionAgent(reasoning, sensor_fused) ∈ R^d
   - Agente decisor para maniobras urgentes
   - Implementado en: _decision_agent_process()

6. Action Execution:
   - action = ActionExecutor(decision, urgent_score) ∈ R^d
   - Ejecuta acciones finales priorizando maniobras urgentes
   - Implementado en: _execute_actions()
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
class DriveAgentConfig(BasePaperConfig):
    """
    Configuración para DriveAgent.
    
    EN EL PAPER: Sección 3 - Multi-Agent Framework Configuration
    - num_sensors: Número de sensores S (cámaras, LiDAR, GPS - términos exactos del paper)
    - sensor_dim: Dimensión de cada sensor d_s
    - num_reasoning_agents: Número de agentes de razonamiento R
    - reasoning_dim: Dimensión de cada agente de razonamiento d_r
    - urgent_threshold: Umbral para maniobras urgentes τ_u ∈ [0, 1]
    - El paper propone un framework de agente modular para conducción autónoma
    """
    num_sensors: int = 3  # S en el paper: camera, LiDAR, GPS (términos exactos)
    sensor_dim: int = 256  # d_s en el paper
    num_reasoning_agents: int = 4  # R en el paper
    reasoning_dim: int = 256  # d_r en el paper
    urgent_threshold: float = 0.7  # τ_u en el paper
    use_sensor_fusion: bool = True
    use_reasoning_agents: bool = True


class DriveAgentModule(BasePaperModule):
    """
    DriveAgent: LLM-Driven Multi-Agent Autonomous Driving.
    
    EN EL PAPER: Sección 3 - Multi-Agent Framework
    - Un framework de agente modular para conducción autónoma (término exacto)
    - Sensores: cámaras, LiDAR, GPS (términos exactos del paper)
    - Agentes de razonamiento especializados
    - Agente decisor para maniobras urgentes (término exacto del paper)
    
    EN EL PAPER: Sección 3.1 - Architecture Components
    - Sensor Integration: Integra datos de múltiples sensores
    - Reasoning Agents: Múltiples agentes de razonamiento
    - Decision Agent: Agente decisor para maniobras urgentes
    - Action Executor: Ejecuta acciones finales
    """
    
    def __init__(self, config: DriveAgentConfig):
        """
        Inicialización del módulo DriveAgent.
        
        EN EL PAPER: Sección 3.1 - Architecture Components
        - El paper propone un framework de agente modular
        - Sensores: cámaras, LiDAR, GPS (términos exactos)
        - Agentes de razonamiento especializados
        - Agente decisor para maniobras urgentes
        
        CÓDIGO: Inicializamos:
        1. Sensor Processors: Procesan datos de cada sensor (cámaras, LiDAR, GPS)
        2. Sensor Fusion: Integra datos de múltiples sensores
        3. Reasoning Agents: Múltiples agentes de razonamiento
        4. Urgent Detector: Detecta maniobras urgentes
        5. Decision Agent: Agente decisor
        6. Action Executor: Ejecuta acciones
        """
        super().__init__(config)
        self.config = config
        
        # EN EL PAPER: Sección 3.1 - Sensor Integration
        # El paper integra sensores: cámaras, LiDAR, GPS (términos exactos del paper)
        # NOTACIÓN DEL PAPER: sensor_i = SensorProcessor_i(input) ∈ R^{d_s} donde i ∈ {camera, LiDAR, GPS}
        #   donde:
        #   - S: número de sensores (num_sensors = 3: camera, LiDAR, GPS)
        #   - sensor_i: datos procesados del sensor i
        #   - d_s: dimensión del sensor (sensor_dim)
        # NOTACIÓN EN CÓDIGO: sensor_processors[i] procesa datos del sensor i
        # CÓDIGO: Procesadores para cada sensor (cámaras, LiDAR, GPS)
        self.sensor_processors = nn.ModuleList([
            nn.Sequential(
                nn.Linear(config.hidden_dim, config.sensor_dim),
                nn.GELU(),
                nn.Linear(config.sensor_dim, config.sensor_dim),
                nn.LayerNorm(config.sensor_dim)
            ) for _ in range(config.num_sensors)
        ])
        
        # Sensor Fusion: Integra datos de múltiples sensores
        if config.use_sensor_fusion:
            self.sensor_fusion = nn.Sequential(
                nn.Linear(config.sensor_dim * config.num_sensors, config.hidden_dim),
                nn.GELU(),
                nn.Linear(config.hidden_dim, config.hidden_dim)
            )
        
        # Reasoning Agents: Múltiples agentes de razonamiento especializados
        if config.use_reasoning_agents:
            self.reasoning_agents = nn.ModuleList([
                nn.Sequential(
                    nn.Linear(config.hidden_dim, config.reasoning_dim),
                    nn.GELU(),
                    nn.Linear(config.reasoning_dim, config.reasoning_dim)
                ) for _ in range(config.num_reasoning_agents)
            ])
            
            # Fusionador de agentes de razonamiento
            self.reasoning_fusion = nn.Sequential(
                nn.Linear(config.reasoning_dim * config.num_reasoning_agents, config.hidden_dim),
                nn.GELU(),
                nn.Linear(config.hidden_dim, config.hidden_dim)
            )
        
        # Decision Agent: Agente decisor para maniobras urgentes
        self.decision_agent = nn.Sequential(
            nn.Linear(config.hidden_dim * 2, config.hidden_dim),  # reasoning + sensor
            nn.GELU(),
            nn.Linear(config.hidden_dim, config.hidden_dim)
        )
        
        # Urgent Maneuver Detector: Detecta situaciones urgentes
        self.urgent_detector = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim // 2),
            nn.GELU(),
            nn.Linear(config.hidden_dim // 2, 1),
            nn.Sigmoid()
        )
        
        # Action Executor: Ejecuta acciones finales
        self.action_executor = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim),
            nn.GELU(),
            nn.Linear(config.hidden_dim, config.hidden_dim)
        )
        
        logger.info(f"DriveAgent initialized: num_sensors={config.num_sensors}, num_reasoning_agents={config.num_reasoning_agents}")
    
    def _process_sensors(self, hidden_states: torch.Tensor) -> List[torch.Tensor]:
        """
        Sensor Processors: Procesan datos de cada sensor.
        
        Returns:
            sensor_outputs: Lista de [batch, seq, sensor_dim] para cada sensor
        """
        sensor_outputs = []
        for sensor_processor in self.sensor_processors:
            sensor_output = sensor_processor(hidden_states)  # [batch, seq, sensor_dim]
            sensor_outputs.append(sensor_output)
        
        return sensor_outputs
    
    def _fuse_sensors(self, sensor_outputs: List[torch.Tensor]) -> torch.Tensor:
        """
        Sensor Fusion: Integra datos de múltiples sensores.
        """
        if not self.config.use_sensor_fusion:
            # Usar solo el primer sensor
            return sensor_outputs[0]
        
        # Concatenar todas las salidas de sensores
        fused = torch.cat(sensor_outputs, dim=-1)  # [batch, seq, sensor_dim * num_sensors]
        fused_output = self.sensor_fusion(fused)  # [batch, seq, hidden_dim]
        
        return fused_output
    
    def _reasoning_agents_process(self, sensor_fused: torch.Tensor) -> torch.Tensor:
        """
        Reasoning Agents: Múltiples agentes de razonamiento especializados.
        """
        if not self.config.use_reasoning_agents:
            return sensor_fused
        
        # Procesar con cada agente de razonamiento
        reasoning_outputs = []
        for reasoning_agent in self.reasoning_agents:
            reasoning_output = reasoning_agent(sensor_fused)  # [batch, seq, reasoning_dim]
            reasoning_outputs.append(reasoning_output)
        
        # Fusionar salidas de agentes de razonamiento
        reasoning_fused = torch.cat(reasoning_outputs, dim=-1)  # [batch, seq, reasoning_dim * num_agents]
        reasoning_output = self.reasoning_fusion(reasoning_fused)  # [batch, seq, hidden_dim]
        
        return reasoning_output
    
    def _detect_urgent_maneuvers(self, hidden_states: torch.Tensor) -> torch.Tensor:
        """
        Urgent Maneuver Detector: Detecta situaciones urgentes.
        
        Returns:
            urgent_scores: [batch, seq] - Scores de urgencia
        """
        urgent_scores = self.urgent_detector(hidden_states).squeeze(-1)  # [batch, seq]
        return urgent_scores
    
    def _decision_agent_process(self, reasoning_output: torch.Tensor, 
                                sensor_fused: torch.Tensor) -> torch.Tensor:
        """
        Decision Agent: Agente decisor para maniobras urgentes.
        """
        # Combinar reasoning y sensor fusion
        combined = torch.cat([reasoning_output, sensor_fused], dim=-1)  # [batch, seq, hidden_dim * 2]
        decision = self.decision_agent(combined)  # [batch, seq, hidden_dim]
        
        return decision
    
    def _execute_actions(self, decision: torch.Tensor, urgent_scores: torch.Tensor) -> torch.Tensor:
        """
        Action Executor: Ejecuta acciones finales.
        
        Prioriza acciones urgentes.
        """
        # Aplicar pesos de urgencia
        urgent_mask = (urgent_scores >= self.config.urgent_threshold).float().unsqueeze(-1)  # [batch, seq, 1]
        
        # Ejecutar acciones
        actions = self.action_executor(decision)  # [batch, seq, hidden_dim]
        
        # Priorizar acciones urgentes
        output = actions * (1 + urgent_mask * 0.5)  # Aumentar 50% acciones urgentes
        
        return output
    
    def forward(self, hidden_states: torch.Tensor, **kwargs) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass: DriveAgent Multi-Agent System.
        
        Proceso:
        1. Procesar datos de múltiples sensores
        2. Fusionar datos de sensores
        3. Procesar con agentes de razonamiento
        4. Detectar maniobras urgentes
        5. Decisión del agente decisor
        6. Ejecutar acciones
        
        Args:
            hidden_states: [batch, seq, hidden_dim] - Input states (pueden representar datos de sensores)
        
        Returns:
            output: [batch, seq, hidden_dim] - Acciones ejecutadas
            metadata: Dict con métricas de sensores, razonamiento y urgencia
        """
        # PASO 1: Procesar datos de múltiples sensores
        sensor_outputs = self._process_sensors(hidden_states)  # Lista de [batch, seq, sensor_dim]
        
        # PASO 2: Fusionar datos de sensores
        sensor_fused = self._fuse_sensors(sensor_outputs)  # [batch, seq, hidden_dim]
        
        # PASO 3: Procesar con agentes de razonamiento
        reasoning_output = self._reasoning_agents_process(sensor_fused)  # [batch, seq, hidden_dim]
        
        # PASO 4: Detectar maniobras urgentes
        urgent_scores = self._detect_urgent_maneuvers(reasoning_output)  # [batch, seq]
        
        # PASO 5: Decisión del agente decisor
        decision = self._decision_agent_process(reasoning_output, sensor_fused)  # [batch, seq, hidden_dim]
        
        # PASO 6: Ejecutar acciones
        output = self._execute_actions(decision, urgent_scores)  # [batch, seq, hidden_dim]
        
        # Metadata
        sensor_norms = [out.norm(dim=-1).mean().item() for out in sensor_outputs]
        metadata = {
            'num_sensors': self.config.num_sensors,
            'num_reasoning_agents': self.config.num_reasoning_agents,
            'sensor_output_norms': sensor_norms,
            'sensor_fused_norm': sensor_fused.norm(dim=-1).mean().item(),
            'reasoning_output_norm': reasoning_output.norm(dim=-1).mean().item(),
            'urgent_score_mean': urgent_scores.mean().item(),
            'urgent_score_std': urgent_scores.std().item(),
            'urgent_ratio': (urgent_scores >= self.config.urgent_threshold).float().mean().item(),
            'decision_norm': decision.norm(dim=-1).mean().item()
        }
        
        self._update_metrics(
            urgent_score_mean=metadata['urgent_score_mean'],
            urgent_ratio=metadata['urgent_ratio']
        )
        
        return output, metadata

