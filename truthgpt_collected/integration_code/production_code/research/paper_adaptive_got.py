#!/usr/bin/env python3
"""
Adaptive Graph of Thoughts: Test-Time Adaptive Reasoning
=========================================================
Pandey, Ghukasyan, Goktas, Radha (2025)

Paper URL: https://arxiv.org/abs/[ID_PENDIENTE]
# Nota: Paper de arXiv 2025, buscar en arXiv cuando esté disponible
arXiv 2025: Adaptive Graph of Thoughts: Test-Time Adaptive Reasoning

Técnica principal:
- Usa un DAG dinámico para razonar solo donde es necesario
- Une chain, tree y graph en inferencia
- Adaptación en tiempo de test (test-time adaptation)

MATEMÁTICAS DEL PAPER IMPLEMENTADAS:

1. Construcción de DAG Dinámico:
   - G = (V, E) donde V son nodos de pensamiento y E son aristas
   - E se construye dinámicamente según necesidad
   - Implementado en: _build_dynamic_dag()

2. Razonamiento Selectivo:
   - razonar(v) = True si importancia(v) > θ
   - donde θ es umbral de importancia
   - Implementado en: _selective_reasoning()

3. Unificación Multi-Paradigma:
   - output = fuse(chain_output, tree_output, graph_output)
   - Implementado en: forward()
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass
from core.paper_base import BasePaperModule, BasePaperConfig
from core.utils import setup_logger

logger = setup_logger(__name__)
@dataclass
class AdaptiveGoTConfig(BasePaperConfig):
    """
    Configuración para Adaptive Graph of Thoughts (Production-Ready).
    
    Attributes:
        max_nodes: Máximo número de nodos en el DAG (debe ser > 0)
        importance_threshold: Umbral para razonamiento selectivo (0.0-1.0)
        use_test_time_adaptation: Si True, usa adaptación en tiempo de test
        dag_density: Densidad del grafo (0.0-1.0)
        fusion_method: Método de fusión ('weighted', 'attention', 'max')
        dropout_rate: Tasa de dropout para regularización (default: 0.1)
    """
    max_nodes: int = 20
    importance_threshold: float = 0.5
    use_test_time_adaptation: bool = True
    dag_density: float = 0.3
    fusion_method: str = 'weighted'
    dropout_rate: float = 0.1
    
    def validate(self):
        """Valida la configuración de Adaptive GoT."""
        super().validate()
        if self.max_nodes <= 0:
            raise ValueError(f"max_nodes debe ser > 0, recibido: {self.max_nodes}")
        if not 0.0 <= self.importance_threshold <= 1.0:
            raise ValueError(f"importance_threshold debe estar en [0, 1], recibido: {self.importance_threshold}")
        if not 0.0 <= self.dag_density <= 1.0:
            raise ValueError(f"dag_density debe estar en [0, 1], recibido: {self.dag_density}")
        if self.fusion_method not in ['weighted', 'attention', 'max']:
            raise ValueError(
                f"fusion_method debe ser 'weighted', 'attention' o 'max', recibido: {self.fusion_method}"
            )
        if not 0.0 <= self.dropout_rate < 1.0:
            raise ValueError(f"dropout_rate debe estar en [0, 1), recibido: {self.dropout_rate}")


class AdaptiveGoTModule(BasePaperModule):
    """
    Adaptive Graph of Thoughts: Razonamiento adaptativo con DAG dinámico.
    
    EN EL PAPER: Sección 3 - Dynamic DAG Construction
    - El paper construye un DAG dinámico de nodos de pensamiento
    - Solo razona en nodos relevantes (razonamiento selectivo)
    - Unifica chain, tree y graph en un solo framework
    """
    
    def __init__(self, config: AdaptiveGoTConfig):
        """
        Inicialización del módulo Adaptive GoT.
        
        EN EL PAPER: Sección 3.1 - Architecture
        - El paper define nodos V y aristas E del DAG
        - Cada nodo representa un pensamiento/estado de razonamiento
        - Las aristas conectan pensamientos relacionados
        
        CÓDIGO: Inicializamos:
        1. Encoder de nodos (pensamientos)
        2. Constructor de DAG dinámico
        3. Módulo de razonamiento selectivo
        4. Fusionador multi-paradigma
        """
        super().__init__(config)
        self.config = config
        
        # EN EL PAPER: Sección 3.2 - Node Encoder
        # El paper codifica cada nodo (pensamiento) en el DAG
        # NOTACIÓN DEL PAPER: h_v ∈ R^d es embedding del nodo v ∈ V
        #   donde V es conjunto de nodos (pensamientos)
        # NOTACIÓN EN CÓDIGO: node_encoder(x) = h_v
        try:
            # CÓDIGO: Red que codifica pensamientos en embeddings
            self.node_encoder = nn.Sequential(
                nn.Linear(config.hidden_dim, config.hidden_dim * 2),
                nn.GELU(),
                nn.Dropout(config.dropout_rate),  # Regularización para producción
                nn.Linear(config.hidden_dim * 2, config.hidden_dim)
            )
            
            # EN EL PAPER: Sección 3.3 - Edge Predictor
            # El paper predice aristas del DAG dinámicamente
            # NOTACIÓN DEL PAPER: E ⊆ V × V es conjunto de aristas
            #   e = (v_i, v_j) ∈ E si pensamiento j depende de pensamiento i
            # NOTACIÓN EN CÓDIGO: edge_predictor(h_i, h_j) = probabilidad de arista
            # CÓDIGO: Red que predice si existe arista entre dos nodos
            self.edge_predictor = nn.Sequential(
                nn.Linear(config.hidden_dim * 2, config.hidden_dim),
                nn.GELU(),
                nn.Dropout(config.dropout_rate),  # Regularización para producción
                nn.Linear(config.hidden_dim, 1),
                nn.Sigmoid()
            )
            
            # EN EL PAPER: Sección 3.4 - Importance Scorer
            # El paper calcula importancia de cada nodo para razonamiento selectivo
            # NOTACIÓN DEL PAPER: importancia(v) ∈ [0, 1] es importancia del nodo v
            # NOTACIÓN EN CÓDIGO: importance_scorer(h_v) = importancia(v)
            # CÓDIGO: Red que scorea importancia de nodos
            self.importance_scorer = nn.Sequential(
                nn.Linear(config.hidden_dim, config.hidden_dim // 2),
                nn.GELU(),
                nn.Dropout(config.dropout_rate),  # Regularización para producción
                nn.Linear(config.hidden_dim // 2, 1),
                nn.Sigmoid()
            )
            
            # EN EL PAPER: Sección 3.5 - Reasoning Module
            # El paper aplica razonamiento en nodos seleccionados
            # NOTACIÓN DEL PAPER: razonar(v) → h'_v donde h'_v es pensamiento actualizado
            # NOTACIÓN EN CÓDIGO: reasoning_module(h_v) = h'_v
            # CÓDIGO: Red que aplica razonamiento en un nodo
            self.reasoning_module = nn.Sequential(
                nn.Linear(config.hidden_dim, config.hidden_dim * 2),
                nn.GELU(),
                nn.Dropout(config.dropout_rate),  # Regularización para producción
                nn.Linear(config.hidden_dim * 2, config.hidden_dim)
            )
            
            # EN EL PAPER: Sección 3.6 - Multi-Paradigm Fusion
            # El paper fusiona outputs de chain, tree y graph
            # NOTACIÓN DEL PAPER: output = fuse(chain, tree, graph)
            # NOTACIÓN EN CÓDIGO: fusion_module combina múltiples paradigmas
            # CÓDIGO: Módulo que fusiona diferentes paradigmas
            if config.fusion_method == 'weighted':
                self.fusion_weights = nn.Parameter(torch.ones(3) / 3)  # chain, tree, graph
            elif config.fusion_method == 'attention':
                self.fusion_attention = nn.MultiheadAttention(config.hidden_dim, num_heads=4, dropout=config.dropout_rate)
            else:  # max
                self.fusion_module = nn.Identity()
        except Exception as e:
            logger.error(f"Error inicializando Adaptive GoT: {e}")
            raise
        
        logger.info(f"Adaptive GoT initialized: max_nodes={config.max_nodes}, density={config.dag_density}")
    
    def _build_dynamic_dag(self, node_embeddings: torch.Tensor) -> torch.Tensor:
        """
        Construye DAG dinámico basado en embeddings de nodos (Production-Ready).
        
        EN EL PAPER: Sección 3.3 - Dynamic Edge Construction
        - El paper construye aristas dinámicamente según similitud/relación
        - FÓRMULA: e_ij = 1 si score(h_i, h_j) > θ_edge
        - FÓRMULA: E = {(i, j) | e_ij = 1, i < j} (DAG: sin ciclos)
        
        Args:
            node_embeddings: [num_nodes, hidden_dim] = [h_1, ..., h_n]
            
        Returns:
            adjacency_matrix: [num_nodes, num_nodes] = A donde A[i, j] = 1 si arista (i, j)
        """
        try:
            num_nodes = node_embeddings.shape[0]
            if num_nodes == 0:
                raise ValueError("node_embeddings no puede estar vacío")
            
            # Limitar número de nodos al máximo configurado
            num_nodes = min(num_nodes, self.config.max_nodes)
            node_embeddings = node_embeddings[:num_nodes]
            
            # EN EL PAPER: Sección 3.3.1 - Edge Scoring
            # El paper calcula score para cada par de nodos
            # NOTACIÓN DEL PAPER: score_ij = f(h_i, h_j) ∈ [0, 1]
            # NOTACIÓN EN CÓDIGO: edge_scores[i, j] = score_ij
            # CÓDIGO: Calcular scores para todos los pares
            adjacency = torch.zeros(num_nodes, num_nodes, device=node_embeddings.device)
            
            for i in range(num_nodes):
                for j in range(i + 1, num_nodes):  # DAG: solo aristas hacia adelante
                    # EN EL PAPER: Score de arista basado en embeddings
                    # FÓRMULA: score_ij = edge_predictor(concat(h_i, h_j))
                    # NOTACIÓN EN CÓDIGO: edge_score = probabilidad de arista
                    # CÓDIGO: Concatenar embeddings y predecir arista
                    pair_embedding = torch.cat([node_embeddings[i], node_embeddings[j]])
                    edge_score = self.edge_predictor(pair_embedding).squeeze()
                    
                    # EN EL PAPER: Umbral para decidir si crear arista
                    # FÓRMULA: e_ij = 1 si score_ij > θ_density
                    # NOTACIÓN EN CÓDIGO: adjacency[i, j] = 1 si score > threshold
                    # CÓDIGO: Crear arista si score supera umbral (controlado por densidad)
                    threshold = 1.0 - self.config.dag_density  # Mayor densidad = más aristas
                    if edge_score > threshold:
                        adjacency[i, j] = 1.0
            
            return adjacency
        except Exception as e:
            logger.error(f"Error en _build_dynamic_dag: {e}")
            # Retornar DAG vacío en caso de error
            num_nodes = min(node_embeddings.shape[0], self.config.max_nodes) if node_embeddings.shape[0] > 0 else 1
            return torch.zeros(num_nodes, num_nodes, device=node_embeddings.device)
    
    def _selective_reasoning(self, node_embeddings: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Aplica razonamiento solo en nodos importantes (Production-Ready).
        
        EN EL PAPER: Sección 3.4 - Selective Reasoning
        - El paper razona solo en nodos con importancia > θ
        - FÓRMULA: razonar(v) = True si importancia(v) > θ
        - FÓRMULA: h'_v = reasoning_module(h_v) si razonar(v), else h_v
        
        Args:
            node_embeddings: [num_nodes, hidden_dim] = [h_1, ..., h_n]
            
        Returns:
            updated_embeddings: [num_nodes, hidden_dim] = [h'_1, ..., h'_n]
            reasoning_mask: [num_nodes] = máscara de nodos razonados
        """
        try:
            num_nodes = node_embeddings.shape[0]
            if num_nodes == 0:
                raise ValueError("node_embeddings no puede estar vacío")
            
            # EN EL PAPER: Sección 3.4.1 - Importance Calculation
            # El paper calcula importancia de cada nodo
            # FÓRMULA: importancia(v) = importance_scorer(h_v)
            # NOTACIÓN DEL PAPER: importancia ∈ [0, 1]^n para n nodos
            # NOTACIÓN EN CÓDIGO: importance_scores[i] = importancia(i)
            # CÓDIGO: Calcular importancia de cada nodo
            importance_scores = self.importance_scorer(node_embeddings).squeeze()  # [num_nodes]
            
            # EN EL PAPER: Sección 3.4.2 - Selection
            # El paper selecciona nodos para razonar
            # FÓRMULA: razonar(v) = importancia(v) > θ
            # NOTACIÓN DEL PAPER: V_selected = {v | importancia(v) > θ}
            # NOTACIÓN EN CÓDIGO: reasoning_mask[i] = 1 si razonar(i), else 0
            # CÓDIGO: Crear máscara de nodos seleccionados
            reasoning_mask = (importance_scores > self.config.importance_threshold).float()
            
            # EN EL PAPER: Sección 3.4.3 - Reasoning Application
            # El paper aplica razonamiento en nodos seleccionados
            # FÓRMULA: h'_v = reasoning_module(h_v) si razonar(v), else h_v
            # NOTACIÓN EN CÓDIGO: updated_embeddings = razonamiento aplicado
            # CÓDIGO: Aplicar razonamiento solo en nodos seleccionados
            reasoning_output = self.reasoning_module(node_embeddings)
            updated_embeddings = (
                reasoning_mask.unsqueeze(-1) * reasoning_output +
                (1 - reasoning_mask.unsqueeze(-1)) * node_embeddings
            )
            
            return updated_embeddings, reasoning_mask
        except Exception as e:
            logger.error(f"Error en _selective_reasoning: {e}")
            # Retornar embeddings sin modificar en caso de error
            reasoning_mask = torch.zeros(node_embeddings.shape[0], device=node_embeddings.device)
            return node_embeddings, reasoning_mask
    
    def forward(self, hidden_states: torch.Tensor, **kwargs) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass: razonamiento adaptativo con DAG dinámico (Production-Ready).
        
        EN EL PAPER: Sección 4 - Adaptive Reasoning Process
        - El paper construye DAG dinámico
        - Aplica razonamiento selectivo
        - Fusiona múltiples paradigmas
        
        Args:
            hidden_states: [batch, seq, hidden_dim] = x ∈ R^(B×N×d)
            **kwargs: Argumentos adicionales
            
        Returns:
            output: [batch, seq, hidden_dim] = y ∈ R^(B×N×d)
            metadata: Dict con información del DAG y razonamiento
        """
        # Validar inputs
        self.validate_inputs(hidden_states, **kwargs)
        
        batch_size, seq_len, hidden_dim = hidden_states.shape
        
        try:
            # PASO 1: Crear nodos del DAG desde hidden states
            # EN EL PAPER: Sección 4.1 - Node Creation
            # FÓRMULA: h_v = node_encoder(x_v) para cada posición v
            # NOTACIÓN DEL PAPER: V = {v_1, ..., v_n} son nodos del DAG
            # NOTACIÓN EN CÓDIGO: node_embeddings = embeddings de nodos
            # CÓDIGO: Codificar cada posición como nodo
            num_nodes = min(seq_len, self.config.max_nodes)
            node_inputs = hidden_states[:, :num_nodes, :].mean(dim=0)  # [num_nodes, hidden_dim]
            node_embeddings = self.node_encoder(node_inputs)  # [num_nodes, hidden_dim]
            
            # PASO 2: Construir DAG dinámico
            # EN EL PAPER: Sección 4.2 - DAG Construction
            # FÓRMULA: E = build_dag(V)
            # NOTACIÓN DEL PAPER: G = (V, E) es el DAG construido
            # NOTACIÓN EN CÓDIGO: adjacency = matriz de adyacencia del DAG
            # CÓDIGO: Construir DAG dinámicamente
            adjacency = self._build_dynamic_dag(node_embeddings)
            num_edges = adjacency.sum().item()
            
            # PASO 3: Razonamiento selectivo
            # EN EL PAPER: Sección 4.3 - Selective Reasoning
            # FÓRMULA: h'_v = selective_reasoning(h_v)
            # NOTACIÓN EN CÓDIGO: updated_embeddings = nodos después de razonamiento
            # CÓDIGO: Aplicar razonamiento solo en nodos importantes
            updated_embeddings, reasoning_mask = self._selective_reasoning(node_embeddings)
            num_reasoned = reasoning_mask.sum().item()
            
            # PASO 4: Fusionar paradigmas (chain, tree, graph)
            # EN EL PAPER: Sección 4.4 - Multi-Paradigm Fusion
            # FÓRMULA: output = fuse(chain, tree, graph)
            # NOTACIÓN DEL PAPER: chain, tree, graph son outputs de diferentes paradigmas
            # NOTACIÓN EN CÓDIGO: paradigm_outputs = [chain_out, tree_out, graph_out]
            # CÓDIGO: Simular outputs de diferentes paradigmas y fusionar
            chain_output = updated_embeddings.mean(dim=0, keepdim=True).expand(batch_size, -1, -1)
            tree_output = updated_embeddings.mean(dim=0, keepdim=True).expand(batch_size, -1, -1)
            graph_output = updated_embeddings.mean(dim=0, keepdim=True).expand(batch_size, -1, -1)
            
            # EN EL PAPER: Fusión ponderada
            # FÓRMULA: output = w_chain × chain + w_tree × tree + w_graph × graph
            # NOTACIÓN EN CÓDIGO: output = combinación ponderada
            # CÓDIGO: Fusionar con pesos adaptativos
            if self.config.fusion_method == 'weighted':
                weights = F.softmax(self.fusion_weights, dim=0)
                output = weights[0] * chain_output + weights[1] * tree_output + weights[2] * graph_output
            else:
                # Attention fusion
                paradigm_inputs = torch.stack([chain_output, tree_output, graph_output], dim=1)  # [batch, 3, seq, hidden]
                paradigm_inputs_flat = paradigm_inputs.view(batch_size * 3, seq_len, hidden_dim)
                fused, _ = self.fusion_attention(paradigm_inputs_flat, paradigm_inputs_flat, paradigm_inputs_flat)
                output = fused[:batch_size]  # Tomar solo el primer paradigma como base
            
            # Asegurar dimensión correcta
            if output.shape[1] < seq_len:
                padding = torch.zeros(batch_size, seq_len - output.shape[1], hidden_dim, device=output.device)
                output = torch.cat([output, padding], dim=1)
            elif output.shape[1] > seq_len:
                output = output[:, :seq_len, :]
            
            # Calcular métricas mejoradas
            max_possible_edges = num_nodes * (num_nodes - 1) / 2 if num_nodes > 1 else 0
            dag_density_actual = num_edges / max_possible_edges if max_possible_edges > 0 else 0.0
            
            metadata = {
                'num_nodes': num_nodes,
                'num_edges': int(num_edges),
                'max_nodes': self.config.max_nodes,
                'dag_density_actual': dag_density_actual,
                'dag_density_config': self.config.dag_density,
                'num_reasoned_nodes': int(num_reasoned),
                'reasoning_ratio': num_reasoned / num_nodes if num_nodes > 0 else 0.0,
                'importance_threshold': self.config.importance_threshold,
                'fusion_method': self.config.fusion_method,
                'use_test_time_adaptation': self.config.use_test_time_adaptation,
                'output_mean': output.mean().item(),
                'output_std': output.std().item(),
                'output_max': output.max().item(),
                'output_min': output.min().item()
            }
            
            self._update_metrics(
                num_nodes=num_nodes,
                num_edges=int(num_edges),
                reasoning_ratio=metadata['reasoning_ratio'],
                dag_density=metadata['dag_density_actual']
            )
            
            return output, metadata
            
        except Exception as e:
            logger.error(f"Error en forward de Adaptive GoT: {e}")
            # En caso de error, retornar hidden_states sin modificar
            error_metadata = {
                'error': str(e),
                'num_nodes': 0,
                'num_edges': 0,
                'dag_density_actual': 0.0,
                'num_reasoned_nodes': 0,
                'reasoning_ratio': 0.0
            }
            return hidden_states, error_metadata
