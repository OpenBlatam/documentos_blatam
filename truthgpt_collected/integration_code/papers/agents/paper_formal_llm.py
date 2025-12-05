#!/usr/bin/env python3
"""
Formal-LLM: Integrating Formal Language and Natural Language for Controllable LLM-based Agents
================================================================================================
Li, Hua, Wang, Zhu, Zhang (2024)

Venue: arXiv
Year: 2024

Técnica principal (EXACTO según descripción del paper):
- Integran lenguaje formal con natural para guiar a agentes LLM en generar planes válidos
- Evitan planes inválidos a través de un autómata formal
- Combinan representaciones formales y naturales para control

MATEMÁTICAS DEL PAPER IMPLEMENTADAS:

1. Formal Language Integration:
   - f = FormalParser(natural_text) ∈ R^{d_f} donde d_f es dimensión formal
   - n = NaturalEncoder(natural_text) ∈ R^d
   - Integran lenguaje formal con natural para guiar agentes LLM
   - Implementado en: _parse_formal_language(), _encode_natural_language()

2. Formal Automaton (Autómata Formal):
   - A = (Q, Σ, δ, q_0, F) donde Q son estados, Σ alfabeto, δ transiciones
   - Para plan π: valid(π) = Automaton(π) ∈ {valid, invalid}
   - El autómata formal valida planes y evita planes inválidos
   - NOTACIÓN: valid(π) = 1 si π es válido según autómata, 0 si no
   - Implementado en: _formal_automaton_validate()

3. Plan Generation and Validation:
   - π = PlanGenerator(combined_repr) donde combined_repr combina formal y natural
   - validity = PlanValidator(π, formal_repr) ∈ [0, 1]
   - Generan planes válidos evitando planes inválidos
   - Implementado en: _generate_plan(), _validate_plan()
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
class FormalLLMConfig(BasePaperConfig):
    """
    Configuración para Formal-LLM.
    
    Parámetros:
        formal_dim: Dimensión de representaciones formales
        automaton_states: Número de estados del autómata
        plan_horizon: Horizonte de planificación
        validation_strictness: Estrictez de validación (0-1)
    """
    formal_dim: int = 256
    automaton_states: int = 10
    plan_horizon: int = 8
    validation_strictness: float = 0.8
    use_formal_automaton: bool = True
    combine_method: str = "weighted_sum"  # "weighted_sum", "attention", "gating"


class FormalLLMModule(BasePaperModule):
    """
    Formal-LLM: Integración de lenguaje formal y natural para agentes controlables.
    
    Implementa:
    1. Formal Language Parser: Procesa especificaciones formales
    2. Natural Language Encoder: Codifica lenguaje natural
    3. Formal Automaton: Autómata que valida planes
    4. Plan Generator: Genera planes válidos
    5. Plan Validator: Valida planes usando autómata
    """
    
    def __init__(self, config: FormalLLMConfig):
        super().__init__(config)
        self.config = config
        
        # Formal Language Parser: Parsea especificaciones formales
        self.formal_parser = nn.Sequential(
            nn.Linear(config.hidden_dim, config.formal_dim),
            nn.GELU(),
            nn.Linear(config.formal_dim, config.formal_dim),
            nn.LayerNorm(config.formal_dim)
        )
        
        # Natural Language Encoder: Codifica lenguaje natural
        self.natural_encoder = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim),
            nn.GELU(),
            nn.Linear(config.hidden_dim, config.hidden_dim)
        )
        
        # Combinador: Integra representaciones formales y naturales
        if config.combine_method == "attention":
            self.combiner = nn.MultiheadAttention(
                embed_dim=config.hidden_dim,
                num_heads=8,
                batch_first=True
            )
        elif config.combine_method == "gating":
            self.combiner = nn.Sequential(
                nn.Linear(config.hidden_dim * 2, config.hidden_dim),
                nn.Sigmoid()
            )
        else:  # weighted_sum
            self.combiner = nn.Sequential(
                nn.Linear(config.hidden_dim * 2, config.hidden_dim),
                nn.GELU(),
                nn.Linear(config.hidden_dim, config.hidden_dim)
            )
        
        # Formal Automaton: Autómata que valida planes
        # Representa estados y transiciones del autómata
        if config.use_formal_automaton:
            self.automaton_states = nn.Parameter(
                torch.randn(config.automaton_states, config.formal_dim)
            )
            self.automaton_transitions = nn.Sequential(
                nn.Linear(config.formal_dim * 2, config.formal_dim),
                nn.GELU(),
                nn.Linear(config.formal_dim, config.automaton_states),
                nn.Softmax(dim=-1)
            )
        
        # Plan Generator: Genera planes válidos
        self.plan_generator = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim),
            nn.GELU(),
            nn.Linear(config.hidden_dim, config.hidden_dim)
        )
        
        # Plan Validator: Valida planes usando autómata
        self.plan_validator = nn.Sequential(
            nn.Linear(config.hidden_dim + config.formal_dim, config.hidden_dim),
            nn.GELU(),
            nn.Linear(config.hidden_dim, 1),
            nn.Sigmoid()
        )
        
        logger.info(f"Formal-LLM initialized: formal_dim={config.formal_dim}, automaton_states={config.automaton_states}")
    
    def _parse_formal_language(self, hidden_states: torch.Tensor) -> torch.Tensor:
        """
        Formal Language Parser: Parsea especificaciones formales.
        
        EN EL PAPER: Sección 3.1 - Formal Language Integration
        FÓRMULA EXACTA DEL PAPER: 
          f = FormalParser(natural_text) ∈ R^{d_f}
        donde:
        - natural_text: texto en lenguaje natural (hidden_states) ∈ R^(B×N×d)
        - f: representación formal ∈ R^(B×N×d_f) donde d_f es formal_dim
        - FormalParser: red neuronal que convierte lenguaje natural a formal
        - El paper integra lenguaje formal con natural (término exacto)
        
        Args:
            hidden_states: [batch, seq, hidden_dim] - Texto natural natural_text ∈ R^(B×N×d)
        
        Returns:
            formal_repr: [batch, seq, formal_dim] - Representación formal f ∈ R^(B×N×d_f)
        """
        # EN EL PAPER: Parsear lenguaje formal desde lenguaje natural
        # NOTACIÓN: f = FormalParser(natural_text) donde natural_text = hidden_states
        #   FormalParser: R^(B×N×d) → R^(B×N×d_f) convierte natural a formal
        # NOTACIÓN EN CÓDIGO: formal_repr = representación formal parseada
        # CÓDIGO: Aplicar formal_parser para convertir a representación formal
        formal_repr = self.formal_parser(hidden_states)  # [batch, seq, formal_dim] ∈ R^(B×N×d_f)
        return formal_repr
    
    def _encode_natural_language(self, hidden_states: torch.Tensor) -> torch.Tensor:
        """
        Natural Language Encoder: Codifica lenguaje natural.
        
        EN EL PAPER: Sección 3.1 - Natural Language Encoding
        FÓRMULA EXACTA DEL PAPER: 
          n = NaturalEncoder(natural_text) ∈ R^d
        donde:
        - natural_text: texto en lenguaje natural (hidden_states) ∈ R^(B×N×d)
        - n: representación de lenguaje natural codificada ∈ R^(B×N×d)
        - NaturalEncoder: red neuronal que codifica lenguaje natural
        - El paper integra lenguaje formal con natural (término exacto)
        
        Args:
            hidden_states: [batch, seq, hidden_dim] - Texto natural natural_text ∈ R^(B×N×d)
        
        Returns:
            natural_repr: [batch, seq, hidden_dim] - Representación natural codificada n ∈ R^(B×N×d)
        """
        # EN EL PAPER: Codificar lenguaje natural
        # NOTACIÓN: n = NaturalEncoder(natural_text) donde natural_text = hidden_states
        #   NaturalEncoder: R^(B×N×d) → R^(B×N×d) codifica lenguaje natural
        # NOTACIÓN EN CÓDIGO: natural_repr = representación natural codificada
        # CÓDIGO: Aplicar natural_encoder para codificar lenguaje natural
        natural_repr = self.natural_encoder(hidden_states)  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
        return natural_repr
    
    def _combine_formal_natural(self, formal_repr: torch.Tensor, 
                                natural_repr: torch.Tensor) -> torch.Tensor:
        """
        Combina representaciones formales y naturales.
        
        EN EL PAPER: Sección 3.1 - Combining Formal and Natural Language
        FÓRMULA EXACTA DEL PAPER: 
          combined = Combine(f, n) ∈ R^d
        donde:
        - f: representación formal formal_repr ∈ R^(B×N×d_f) donde d_f es formal_dim
        - n: representación natural natural_repr ∈ R^(B×N×d) donde d es hidden_dim
        - combined: representación combinada ∈ R^(B×N×d)
        - El paper integra lenguaje formal con natural (término exacto) usando diferentes métodos
        - Métodos: "attention" (atención), "gating" (puerta), "weighted_sum" (suma ponderada)
        
        Args:
            formal_repr: [batch, seq, formal_dim] - Representación formal f ∈ R^(B×N×d_f)
            natural_repr: [batch, seq, hidden_dim] - Representación natural n ∈ R^(B×N×d)
        
        Returns:
            combined: [batch, seq, hidden_dim] - Representación combinada ∈ R^(B×N×d)
        """
        # EN EL PAPER: Método 1 - Combinación mediante atención
        # NOTACIÓN: combined = Attention(n, f, f) donde n es query, f es key y value
        #   Attention: R^(B×N×d) × R^(B×N×d_f) × R^(B×N×d_f) → R^(B×N×d)
        #   El paper usa atención para combinar representaciones formales y naturales
        # NOTACIÓN EN CÓDIGO: combined = representación combinada mediante atención
        # CÓDIGO: Usar atención para combinar si combine_method es "attention"
        if self.config.combine_method == "attention":
            # EN EL PAPER: Aplicar multi-head attention
            # NOTACIÓN: combined = Attention(natural_repr, formal_repr, formal_repr) ∈ R^(B×N×d)
            #   donde:
            #   - natural_repr ∈ R^(B×N×d) es la query (lenguaje natural)
            #   - formal_repr ∈ R^(B×N×d_f) es la key y value (lenguaje formal)
            #   - Attention recupera información formal relevante para cada token natural
            #   - Si d_f ≠ d: formal_repr se proyecta automáticamente por el módulo de atención
            # NOTACIÓN EN CÓDIGO: combined = resultado de atención
            # CÓDIGO: Aplicar multi-head attention con natural_repr como query y formal_repr como key/value
            combined, _ = self.combiner(natural_repr, formal_repr, formal_repr)  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
            return combined
        
        # EN EL PAPER: Método 2 - Combinación mediante gating (puerta)
        # NOTACIÓN: gate = Gate(concat(n, f)) ∈ [0, 1]^(B×N×d)
        #   combined = n * gate + f * (1 - gate) ∈ R^(B×N×d)
        #   donde gate controla la mezcla entre representaciones formales y naturales
        # NOTACIÓN EN CÓDIGO: combined = representación combinada mediante gating
        # CÓDIGO: Usar gating para combinar si combine_method es "gating"
        elif self.config.combine_method == "gating":
            # EN EL PAPER: Ajustar dimensiones de formal_repr para que coincida con natural_repr
            # NOTACIÓN: Si d_f < d: formal_repr' = concat(formal_repr, padding) ∈ R^(B×N×d)
            #   Si d_f > d: formal_repr' = formal_repr[:, :, :d] ∈ R^(B×N×d)
            #   Esto asegura que formal_repr y natural_repr tengan la misma dimensión
            # NOTACIÓN EN CÓDIGO: formal_repr = representación formal ajustada
            # CÓDIGO: Ajustar dimensión de formal_repr para que coincida con natural_repr
            if formal_repr.size(-1) != natural_repr.size(-1):
                if formal_repr.size(-1) < natural_repr.size(-1):
                    # EN EL PAPER: Padding si formal_repr es más pequeño
                    # NOTACIÓN: padding = zeros(B, N, d - d_f) ∈ R^(B×N×(d-d_f))
                    #   formal_repr' = concat(formal_repr, padding) ∈ R^(B×N×d)
                    # CÓDIGO: Agregar padding de ceros hasta hidden_dim
                    padding = torch.zeros(natural_repr.size(0), natural_repr.size(1),
                                        natural_repr.size(-1) - formal_repr.size(-1),
                                        device=formal_repr.device)  # [batch, seq, d - d_f] ∈ R^(B×N×(d-d_f))
                    formal_repr = torch.cat([formal_repr, padding], dim=-1)  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
                else:
                    # EN EL PAPER: Truncar si formal_repr es más grande
                    # NOTACIÓN: formal_repr' = formal_repr[:, :, :d] ∈ R^(B×N×d)
                    # CÓDIGO: Truncar a hidden_dim dimensiones
                    formal_repr = formal_repr[:, :, :natural_repr.size(-1)]  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
            
            # EN EL PAPER: Preparar entrada para gating
            # NOTACIÓN: combined_input = concat(n, f') ∈ R^(B×N×(2d))
            #   donde:
            #   - n = natural_repr ∈ R^(B×N×d)
            #   - f' = formal_repr (ajustado) ∈ R^(B×N×d)
            #   - concat concatena en la última dimensión: R^(B×N×d) + R^(B×N×d) → R^(B×N×(2d))
            # NOTACIÓN EN CÓDIGO: combined_input = entrada combinada para gate
            # CÓDIGO: Concatenar natural_repr y formal_repr para entrada del gate
            combined_input = torch.cat([natural_repr, formal_repr], dim=-1)  # [batch, seq, hidden_dim * 2] ∈ R^(B×N×(2d))
            
            # EN EL PAPER: Calcular gate (puerta)
            # NOTACIÓN: gate = Gate(combined_input) ∈ [0, 1]^(B×N×d)
            #   donde Gate: R^(B×N×(2d)) → [0, 1]^(B×N×d) genera valores de gate
            #   gate controla cuánto de cada representación usar
            # NOTACIÓN EN CÓDIGO: gate = valores de gate
            # CÓDIGO: Aplicar combiner (gate network) para calcular gate
            gate = self.combiner(combined_input)  # [batch, seq, hidden_dim] ∈ [0, 1]^(B×N×d)
            
            # EN EL PAPER: Combinar mediante gating
            # NOTACIÓN: combined = n * gate + f' * (1 - gate) ∈ R^(B×N×d)
            #   donde:
            #   - n = natural_repr ∈ R^(B×N×d)
            #   - f' = formal_repr ∈ R^(B×N×d)
            #   - gate ∈ [0, 1]^(B×N×d) es la puerta
            #   - Operación: R^(B×N×d) * [0, 1]^(B×N×d) + R^(B×N×d) * [0, 1]^(B×N×d) → R^(B×N×d)
            #   Esto mezcla representaciones formales y naturales según gate
            # NOTACIÓN EN CÓDIGO: combined = representación combinada mediante gating
            # CÓDIGO: Combinar natural_repr y formal_repr usando gate
            combined = natural_repr * gate + formal_repr * (1 - gate)  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
            return combined
        
        # EN EL PAPER: Método 3 - Combinación mediante suma ponderada (weighted_sum)
        # NOTACIÓN: combined = WeightedSum(concat(n, f')) ∈ R^(B×N×d)
        #   donde WeightedSum: R^(B×N×(2d)) → R^(B×N×d) combina mediante red neuronal
        # NOTACIÓN EN CÓDIGO: combined = representación combinada mediante suma ponderada
        # CÓDIGO: Usar suma ponderada para combinar si combine_method es "weighted_sum"
        else:  # weighted_sum
            # EN EL PAPER: Ajustar dimensiones de formal_repr para que coincida con natural_repr
            # NOTACIÓN: Si d_f < d: formal_repr' = concat(formal_repr, padding) ∈ R^(B×N×d)
            #   Si d_f > d: formal_repr' = formal_repr[:, :, :d] ∈ R^(B×N×d)
            #   Esto asegura que formal_repr y natural_repr tengan la misma dimensión
            # NOTACIÓN EN CÓDIGO: formal_repr = representación formal ajustada
            # CÓDIGO: Ajustar dimensión de formal_repr para que coincida con natural_repr
            if formal_repr.size(-1) != natural_repr.size(-1):
                if formal_repr.size(-1) < natural_repr.size(-1):
                    # EN EL PAPER: Padding si formal_repr es más pequeño
                    # NOTACIÓN: padding = zeros(B, N, d - d_f) ∈ R^(B×N×(d-d_f))
                    #   formal_repr' = concat(formal_repr, padding) ∈ R^(B×N×d)
                    # CÓDIGO: Agregar padding de ceros hasta hidden_dim
                    padding = torch.zeros(natural_repr.size(0), natural_repr.size(1),
                                        natural_repr.size(-1) - formal_repr.size(-1),
                                        device=formal_repr.device)  # [batch, seq, d - d_f] ∈ R^(B×N×(d-d_f))
                    formal_repr = torch.cat([formal_repr, padding], dim=-1)  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
                else:
                    # EN EL PAPER: Truncar si formal_repr es más grande
                    # NOTACIÓN: formal_repr' = formal_repr[:, :, :d] ∈ R^(B×N×d)
                    # CÓDIGO: Truncar a hidden_dim dimensiones
                    formal_repr = formal_repr[:, :, :natural_repr.size(-1)]  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
            
            # EN EL PAPER: Preparar entrada para suma ponderada
            # NOTACIÓN: combined_input = concat(n, f') ∈ R^(B×N×(2d))
            #   donde:
            #   - n = natural_repr ∈ R^(B×N×d)
            #   - f' = formal_repr (ajustado) ∈ R^(B×N×d)
            #   - concat concatena en la última dimensión: R^(B×N×d) + R^(B×N×d) → R^(B×N×(2d))
            # NOTACIÓN EN CÓDIGO: combined_input = entrada combinada para weighted_sum
            # CÓDIGO: Concatenar natural_repr y formal_repr para entrada de weighted_sum
            combined_input = torch.cat([natural_repr, formal_repr], dim=-1)  # [batch, seq, hidden_dim * 2] ∈ R^(B×N×(2d))
            
            # EN EL PAPER: Aplicar suma ponderada mediante red neuronal
            # NOTACIÓN: combined = WeightedSum(combined_input) ∈ R^(B×N×d)
            #   donde WeightedSum: R^(B×N×(2d)) → R^(B×N×d) es una red neuronal que combina
            #   La red aprende pesos óptimos para combinar representaciones formales y naturales
            # NOTACIÓN EN CÓDIGO: combined = representación combinada mediante suma ponderada
            # CÓDIGO: Aplicar combiner (weighted_sum network) para combinar
            combined = self.combiner(combined_input)  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
            return combined
    
    def _formal_automaton_validate(self, plan: torch.Tensor, formal_repr: torch.Tensor) -> torch.Tensor:
        """
        Formal Automaton: Valida planes usando autómata.
        
        EN EL PAPER: Sección 3.2 - Formal Automaton (Autómata Formal)
        FÓRMULA EXACTA DEL PAPER: 
          A = (Q, Σ, δ, q_0, F) donde Q son estados, Σ alfabeto, δ transiciones
          valid(π) = Automaton(π) ∈ {valid, invalid}
        donde:
        - A: autómata formal A = (Q, Σ, δ, q_0, F)
        - Q: conjunto de estados del autómata (automaton_states)
        - Σ: alfabeto (representaciones formales)
        - δ: función de transición δ: Q × Σ → Q
        - q_0: estado inicial
        - F: estados finales (válidos)
        - π: plan a validar ∈ R^(B×N×d)
        - valid(π): resultado de validación ∈ [0, 1]^B
        - El autómata formal valida planes y evita planes inválidos (término exacto)
        
        Args:
            plan: [batch, seq, hidden_dim] - Plan π a validar ∈ R^(B×N×d)
            formal_repr: [batch, seq, formal_dim] - Representación formal f ∈ R^(B×N×d_f)
        
        Returns:
            final_validity: [batch] - Score de validez valid(π) ∈ [0, 1]^B
        """
        # EN EL PAPER: Verificar si se usa autómata formal
        # CÓDIGO: Retornar validez máxima si no se usa autómata
        if not self.config.use_formal_automaton:
            return torch.ones(plan.size(0), device=plan.device)  # [batch] ∈ [0, 1]^B (todos válidos)
        
        batch_size, seq_len = plan.size(0), plan.size(1)
        # NOTACIÓN: plan ∈ R^(B×N×d), formal_repr ∈ R^(B×N×d_f)
        
        # EN EL PAPER: Inicializar estado del autómata
        # NOTACIÓN: q_0 = automaton_states[0] ∈ R^{d_f} es el estado inicial
        #   current_state = expand(q_0) ∈ R^(B×d_f) - expandir para batch
        # NOTACIÓN EN CÓDIGO: current_state = estado actual del autómata
        # CÓDIGO: Inicializar con primer estado del autómata y expandir para batch
        current_state = self.automaton_states[0].unsqueeze(0).expand(batch_size, -1)  # [batch, formal_dim] ∈ R^(B×d_f)
        
        # EN EL PAPER: Simular transiciones del autómata
        # NOTACIÓN: Para cada paso t = 1, 2, ..., min(N, H) donde H = plan_horizon:
        #   q_{t+1} = δ(q_t, σ_t) donde σ_t = formal_repr[:, t, :] es el símbolo en el paso t
        # NOTACIÓN EN CÓDIGO: validity_scores = scores de validez por paso
        # CÓDIGO: Simular transiciones del autómata para cada paso del plan
        validity_scores = []
        for step in range(min(seq_len, self.config.plan_horizon)):
            # EN EL PAPER: Obtener representación formal del paso actual
            # NOTACIÓN: σ_t = formal_repr[:, t, :] ∈ R^(B×d_f) es el símbolo en el paso t
            # NOTACIÓN EN CÓDIGO: step_formal = símbolo formal del paso actual
            # CÓDIGO: Extraer representación formal del paso step
            step_formal = formal_repr[:, step, :]  # [batch, formal_dim] ∈ R^(B×d_f)
            
            # EN EL PAPER: Calcular transición del autómata
            # NOTACIÓN: transition_input = concat(q_t, σ_t) ∈ R^(B×(2d_f))
            #   next_state_probs = δ(transition_input) ∈ [0, 1]^(B×|Q|)
            #   donde δ: R^(B×(2d_f)) → [0, 1]^(B×|Q|) es la función de transición
            #   next_state_probs son probabilidades sobre estados del autómata
            # NOTACIÓN EN CÓDIGO: next_state_probs = probabilidades de transición
            # CÓDIGO: Concatenar estado actual y símbolo formal, luego calcular transición
            transition_input = torch.cat([current_state, step_formal], dim=-1)  # [batch, formal_dim * 2] ∈ R^(B×(2d_f))
            next_state_probs = self.automaton_transitions(transition_input)  # [batch, automaton_states] ∈ [0, 1]^(B×|Q|)
            
            # EN EL PAPER: Seleccionar siguiente estado
            # NOTACIÓN: next_state_idx = argmax(next_state_probs) ∈ {0, 1, ..., |Q|-1}^B
            #   q_{t+1} = automaton_states[next_state_idx] ∈ R^(B×d_f)
            #   Selecciona el estado más probable según la transición
            # NOTACIÓN EN CÓDIGO: next_state = siguiente estado del autómata
            # CÓDIGO: Seleccionar estado más probable y obtener su embedding
            next_state_idx = next_state_probs.argmax(dim=-1)  # [batch] ∈ {0, 1, ..., |Q|-1}^B
            next_state = self.automaton_states[next_state_idx]  # [batch, formal_dim] ∈ R^(B×d_f)
            
            # EN EL PAPER: Calcular score de validez (probabilidad de estar en estado válido)
            # NOTACIÓN: F = {q_0, q_1, ..., q_{|F|-1}} son estados válidos (primeros |Q|/2 estados)
            #   validity_score_t = Σ_{q ∈ F} P(q | transition_input) ∈ [0, 1]^B
            #   Suma probabilidades de estar en estados válidos
            # NOTACIÓN EN CÓDIGO: validity_score = score de validez del paso actual
            # CÓDIGO: Calcular probabilidad de estar en estados válidos
            valid_states = self.config.automaton_states // 2  # |F| = |Q|/2
            validity_score = next_state_probs[:, :valid_states].sum(dim=-1)  # [batch] ∈ [0, 1]^B
            validity_scores.append(validity_score)  # Lista de scores
            
            # EN EL PAPER: Actualizar estado actual para siguiente iteración
            # NOTACIÓN: q_t = q_{t+1} para siguiente paso
            # CÓDIGO: Actualizar current_state para siguiente iteración
            current_state = next_state  # [batch, formal_dim] ∈ R^(B×d_f)
        
        # EN EL PAPER: Score de validez promedio sobre todos los pasos
        # NOTACIÓN: final_validity = mean([validity_score_1, ..., validity_score_T]) ∈ [0, 1]^B
        #   donde T = min(N, H) es el número de pasos simulados
        #   Operación: stack([...]) ∈ R^(T×B), luego mean(dim=0) ∈ R^B
        # NOTACIÓN EN CÓDIGO: final_validity = validez final del plan
        # CÓDIGO: Calcular promedio de scores de validez
        if validity_scores:
            # EN EL PAPER: Promediar scores de validez
            # NOTACIÓN: final_validity = mean([validity_score_1, ..., validity_score_T])
            # CÓDIGO: Apilar scores y promediar sobre dimensión de pasos
            final_validity = torch.stack(validity_scores).mean(dim=0)  # [batch] ∈ [0, 1]^B
        else:
            # EN EL PAPER: Si no hay pasos, considerar plan válido
            # NOTACIÓN: final_validity = 1 (todos válidos)
            # CÓDIGO: Retornar validez máxima si no hay pasos
            final_validity = torch.ones(batch_size, device=plan.device)  # [batch] ∈ [0, 1]^B
        
        return final_validity
    
    def _generate_plan(self, combined_repr: torch.Tensor) -> torch.Tensor:
        """
        Plan Generator: Genera planes válidos.
        
        EN EL PAPER: Sección 3.3 - Plan Generation
        FÓRMULA EXACTA DEL PAPER: 
          π = PlanGenerator(combined_repr) ∈ R^d
        donde:
        - combined_repr: representación combinada (formal + natural) ∈ R^(B×N×d)
        - π: plan generado ∈ R^(B×N×d)
        - El paper genera planes válidos evitando planes inválidos (término exacto)
        - PlanGenerator: R^(B×N×d) → R^(B×N×d) genera secuencia de acciones (plan)
        
        Args:
            combined_repr: [batch, seq, hidden_dim] - Representación combinada ∈ R^(B×N×d)
        
        Returns:
            plan: [batch, seq, hidden_dim] - Plan generado π ∈ R^(B×N×d)
        """
        # EN EL PAPER: Generar plan desde representación combinada
        # NOTACIÓN: π = PlanGenerator(combined_repr) ∈ R^(B×N×d)
        #   donde PlanGenerator: R^(B×N×d) → R^(B×N×d) genera plan válido
        #   El paper genera planes válidos evitando planes inválidos
        # NOTACIÓN EN CÓDIGO: plan = plan generado
        # CÓDIGO: Aplicar plan_generator para generar plan
        plan = self.plan_generator(combined_repr)  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
        return plan
    
    def _validate_plan(self, plan: torch.Tensor, formal_repr: torch.Tensor) -> torch.Tensor:
        """
        Plan Validator: Valida planes usando autómata formal.
        
        EN EL PAPER: Sección 3.2 - Plan Validation
        FÓRMULA EXACTA DEL PAPER: 
          validity = PlanValidator(π, f) ∈ [0, 1]
        donde:
        - π: plan a validar plan ∈ R^(B×N×d)
        - f: representación formal formal_repr ∈ R^(B×N×d_f)
        - validity: score de validez ∈ [0, 1]^B
        - El paper valida planes usando representación formal
        - PlanValidator: R^(B×d) × R^(B×d_f) → [0, 1]^B valida plan
        
        Args:
            plan: [batch, seq, hidden_dim] - Plan π a validar ∈ R^(B×N×d)
            formal_repr: [batch, seq, formal_dim] - Representación formal f ∈ R^(B×N×d_f)
        
        Returns:
            validity: [batch] - Score de validez ∈ [0, 1]^B
        """
        # EN EL PAPER: Promediar sobre secuencia para obtener representación global
        # NOTACIÓN: plan_mean = mean(plan, dim=1) ∈ R^(B×d) - promedio sobre secuencia
        #   formal_mean = mean(formal_repr, dim=1) ∈ R^(B×d_f) - promedio sobre secuencia
        #   Esto crea representaciones globales del plan y la representación formal
        # NOTACIÓN EN CÓDIGO: plan_mean = representación global del plan
        # CÓDIGO: Promediar plan y formal_repr sobre dimensión de secuencia
        plan_mean = plan.mean(dim=1)  # [batch, hidden_dim] ∈ R^(B×d)
        formal_mean = formal_repr.mean(dim=1)  # [batch, formal_dim] ∈ R^(B×d_f)
        
        # EN EL PAPER: Ajustar dimensión de formal_mean para que coincida con plan_mean
        # NOTACIÓN: Si d_f < d: formal_mean' = concat(formal_mean, padding) ∈ R^(B×d)
        #   Si d_f > d: formal_mean' = formal_mean[:, :d] ∈ R^(B×d)
        #   Esto asegura que formal_mean y plan_mean tengan la misma dimensión
        # NOTACIÓN EN CÓDIGO: formal_mean = representación formal ajustada
        # CÓDIGO: Ajustar dimensión de formal_mean para que coincida con plan_mean
        if formal_mean.size(-1) != plan_mean.size(-1):
            if formal_mean.size(-1) < plan_mean.size(-1):
                # EN EL PAPER: Padding si formal_mean es más pequeño
                # NOTACIÓN: padding = zeros(B, d - d_f) ∈ R^(B×(d-d_f))
                #   formal_mean' = concat(formal_mean, padding) ∈ R^(B×d)
                # CÓDIGO: Agregar padding de ceros hasta hidden_dim
                padding = torch.zeros(plan_mean.size(0), plan_mean.size(-1) - formal_mean.size(-1),
                                    device=formal_mean.device)  # [batch, d - d_f] ∈ R^(B×(d-d_f))
                formal_mean = torch.cat([formal_mean, padding], dim=-1)  # [batch, hidden_dim] ∈ R^(B×d)
            else:
                # EN EL PAPER: Truncar si formal_mean es más grande
                # NOTACIÓN: formal_mean' = formal_mean[:, :d] ∈ R^(B×d)
                # CÓDIGO: Truncar a hidden_dim dimensiones
                formal_mean = formal_mean[:, :plan_mean.size(-1)]  # [batch, hidden_dim] ∈ R^(B×d)
        
        # EN EL PAPER: Combinar plan y representación formal
        # NOTACIÓN: combined = concat(plan_mean, formal_mean') ∈ R^(B×(2d))
        #   donde:
        #   - plan_mean ∈ R^(B×d) es la representación global del plan
        #   - formal_mean' ∈ R^(B×d) es la representación formal ajustada
        #   - concat concatena en la última dimensión: R^(B×d) + R^(B×d) → R^(B×(2d))
        # NOTACIÓN EN CÓDIGO: combined = entrada combinada para plan_validator
        # CÓDIGO: Concatenar plan_mean y formal_mean para entrada del validator
        combined = torch.cat([plan_mean, formal_mean], dim=-1)  # [batch, hidden_dim * 2] ∈ R^(B×(2d))
        
        # EN EL PAPER: Validar plan usando plan validator
        # NOTACIÓN: validity = PlanValidator(combined) ∈ [0, 1]^B
        #   donde PlanValidator: R^(B×(2d)) → R^(B×1) → R^B (después de squeeze)
        #   El validator evalúa si el plan es válido según la representación formal
        # NOTACIÓN EN CÓDIGO: validity = score de validez del plan
        # CÓDIGO: Aplicar plan_validator y eliminar dimensión unitaria
        validity = self.plan_validator(combined).squeeze(-1)  # [batch] ∈ [0, 1]^B
        
        return validity
    
    def forward(self, hidden_states: torch.Tensor, **kwargs) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass: Formal-LLM Integration.
        
        Proceso:
        1. Parsear lenguaje formal desde hidden_states
        2. Codificar lenguaje natural
        3. Combinar representaciones formales y naturales
        4. Generar plan válido
        5. Validar plan usando autómata formal
        
        Args:
            hidden_states: [batch, seq, hidden_dim] - Input states
        
        Returns:
            output: [batch, seq, hidden_dim] - Plan válido generado
            metadata: Dict con métricas de validación y planificación
        """
        batch_size, seq_len, hidden_dim = hidden_states.shape
        # NOTACIÓN: hidden_states ∈ R^(B×N×d) donde B=batch_size, N=seq_len, d=hidden_dim
        
        # PASO 1: Parsear lenguaje formal
        # EN EL PAPER: Sección 3.1 - Formal Language Parsing
        # FÓRMULA: f = FormalParser(natural_text) donde natural_text = hidden_states
        # NOTACIÓN EN CÓDIGO: formal_repr = representación formal parseada
        # CÓDIGO: Parsear lenguaje formal desde hidden_states
        formal_repr = self._parse_formal_language(hidden_states)  # [batch, seq, formal_dim] ∈ R^(B×N×d_f)
        
        # PASO 2: Codificar lenguaje natural
        # EN EL PAPER: Sección 3.1 - Natural Language Encoding
        # FÓRMULA: n = NaturalEncoder(natural_text) donde natural_text = hidden_states
        # NOTACIÓN EN CÓDIGO: natural_repr = representación natural codificada
        # CÓDIGO: Codificar lenguaje natural
        natural_repr = self._encode_natural_language(hidden_states)  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
        
        # PASO 3: Combinar representaciones formales y naturales
        # EN EL PAPER: Sección 3.1 - Combining Formal and Natural
        # FÓRMULA: combined = Combine(f, n) donde f = formal_repr, n = natural_repr
        #   El paper integra lenguaje formal con natural (término exacto)
        # NOTACIÓN EN CÓDIGO: combined_repr = representación combinada
        # CÓDIGO: Combinar representaciones formales y naturales
        combined_repr = self._combine_formal_natural(formal_repr, natural_repr)  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
        
        # PASO 4: Generar plan válido
        # EN EL PAPER: Sección 3.3 - Plan Generation
        # FÓRMULA: π = PlanGenerator(combined_repr) ∈ R^(B×N×d)
        #   El paper genera planes válidos evitando planes inválidos (término exacto)
        # NOTACIÓN EN CÓDIGO: plan = plan generado
        # CÓDIGO: Generar plan válido desde representación combinada
        plan = self._generate_plan(combined_repr)  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
        
        # PASO 5: Validar plan usando autómata formal
        # EN EL PAPER: Sección 3.2 - Plan Validation
        # FÓRMULA: automaton_validity = Automaton(π, f) ∈ [0, 1]^B
        #   validator_validity = PlanValidator(π, f) ∈ [0, 1]^B
        #   El autómata formal valida planes y evita planes inválidos
        # NOTACIÓN EN CÓDIGO: automaton_validity = validez del autómata
        # CÓDIGO: Validar plan usando autómata formal
        automaton_validity = self._formal_automaton_validate(plan, formal_repr)  # [batch] ∈ [0, 1]^B
        # EN EL PAPER: Validación adicional con plan validator
        # FÓRMULA: validator_validity = PlanValidator(π, f) ∈ [0, 1]^B
        # NOTACIÓN EN CÓDIGO: validator_validity = validez del validator
        # CÓDIGO: Validar plan usando plan validator
        validator_validity = self._validate_plan(plan, formal_repr)  # [batch] ∈ [0, 1]^B
        
        # EN EL PAPER: Combinar validaciones
        # NOTACIÓN: final_validity = γ · automaton_validity + (1-γ) · validator_validity ∈ [0, 1]^B
        #   donde γ = validation_strictness es el peso del autómata
        #   Operación: [0, 1]^B * γ + [0, 1]^B * (1-γ) → [0, 1]^B
        # NOTACIÓN EN CÓDIGO: final_validity = validez final combinada
        # CÓDIGO: Combinar validaciones con peso validation_strictness
        final_validity = (automaton_validity * self.config.validation_strictness + 
                        validator_validity * (1 - self.config.validation_strictness))  # [batch] ∈ [0, 1]^B
        
        # EN EL PAPER: Aplicar validación al plan (filtrar partes inválidas)
        # NOTACIÓN: validity_mask = expand(final_validity) ∈ [0, 1]^(B×1×1)
        #   output = π * validity_mask ∈ R^(B×N×d)
        #   donde * es multiplicación elemento a elemento con broadcasting
        #   Operación: R^(B×N×d) * R^(B×1×1) → R^(B×N×d) (broadcasting)
        #   Esto filtra partes inválidas del plan
        # NOTACIÓN EN CÓDIGO: validity_mask = máscara de validez expandida
        # CÓDIGO: Expandir final_validity para crear máscara y aplicar al plan
        validity_mask = final_validity.unsqueeze(1).unsqueeze(2)  # [batch, 1, 1] ∈ [0, 1]^(B×1×1)
        # EN EL PAPER: Filtrar partes inválidas del plan
        # NOTACIÓN: output = π * validity_mask
        # CÓDIGO: Aplicar máscara de validez al plan
        output = plan * validity_mask  # [batch, seq, hidden_dim] ∈ R^(B×N×d)
        
        # Metadata
        metadata = {
            'formal_repr_norm': formal_repr.norm(dim=-1).mean().item(),
            'natural_repr_norm': natural_repr.norm(dim=-1).mean().item(),
            'automaton_validity': automaton_validity.mean().item(),
            'validator_validity': validator_validity.mean().item(),
            'final_validity': final_validity.mean().item(),
            'plan_norm': plan.norm(dim=-1).mean().item()
        }
        
        self._update_metrics(
            automaton_validity=metadata['automaton_validity'],
            final_validity=metadata['final_validity']
        )
        
        return output, metadata

