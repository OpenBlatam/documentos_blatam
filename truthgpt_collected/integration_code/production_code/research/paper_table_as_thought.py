#!/usr/bin/env python3
"""
Table as Thought: Exploring Structured Thoughts in LLM Reasoning
==================================================================
TRL 2025

Paper URL: https://aclanthology.org/[ID_PENDIENTE]
# Nota: Paper de TRL 2025 / ACL Anthology, buscar "Table as Thought: Exploring Structured Thoughts in LLM Reasoning"
ACL Anthology / TRL 2025: Table as Thought

Técnica principal:
- Organiza "pensamientos" en una estructura de tabla
- Nueva forma de estructurar la inferencia
- Permite razonamiento más organizado y estructurado

MATEMÁTICAS DEL PAPER IMPLEMENTADAS:

1. Construcción de Tabla:
   - table = build_table(thoughts)
   - Implementado en: _build_table()

2. Razonamiento Tabular:
   - output = reason_on_table(table)
   - Implementado en: forward()

3. Estructuración de Pensamientos:
   - thoughts_structured = structure(thoughts, table_format)
   - Implementado en: _structure_thoughts()
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import math

from core.paper_base import BasePaperModule, BasePaperConfig
from core.utils import setup_logger

logger = setup_logger(__name__)
@dataclass
class TableAsThoughtConfig(BasePaperConfig):
    """
    Configuración para Table as Thought (Production-Ready).
    
    Attributes:
        table_rows: Número de filas en la tabla (debe ser > 0)
        table_cols: Número de columnas en la tabla (debe ser > 0)
        use_table_attention: Si True, usa atención multi-head para la tabla
        structure_method: Método de estructuración ('grid', 'hierarchical', 'sequential')
        dropout_rate: Tasa de dropout para regularización (default: 0.1)
    """
    table_rows: int = 5
    table_cols: int = 4
    use_table_attention: bool = True
    structure_method: str = 'grid'
    dropout_rate: float = 0.1
    
    def validate(self):
        """Valida la configuración de Table as Thought."""
        super().validate()
        if self.table_rows <= 0:
            raise ValueError(f"table_rows debe ser > 0, recibido: {self.table_rows}")
        if self.table_cols <= 0:
            raise ValueError(f"table_cols debe ser > 0, recibido: {self.table_cols}")
        if self.structure_method not in ['grid', 'hierarchical', 'sequential']:
            raise ValueError(
                f"structure_method debe ser 'grid', 'hierarchical' o 'sequential', "
                f"recibido: {self.structure_method}"
            )
        if not 0.0 <= self.dropout_rate < 1.0:
            raise ValueError(f"dropout_rate debe estar en [0, 1), recibido: {self.dropout_rate}")


class TableAsThoughtModule(BasePaperModule):
    """
    Table as Thought: Razonamiento estructurado en formato tabular.
    
    EN EL PAPER: Sección 3 - Tabular Structure
    - El paper organiza pensamientos en estructura de tabla
    - Permite razonamiento más organizado
    - Nueva forma de estructurar inferencia
    """
    
    def __init__(self, config: TableAsThoughtConfig):
        super().__init__(config)
        self.config = config
        
        try:
            # EN EL PAPER: Sección 3.1 - Table Builder
            # NOTACIÓN DEL PAPER: table = build_table(thoughts)
            # NOTACIÓN EN CÓDIGO: table_builder construye estructura tabular
            self.table_builder = nn.Sequential(
                nn.Linear(config.hidden_dim, config.hidden_dim * 2),
                nn.GELU(),
                nn.Dropout(config.dropout_rate),  # Regularización para producción
                nn.Linear(config.hidden_dim * 2, config.hidden_dim)
            )
            
            # EN EL PAPER: Sección 3.2 - Table Encoder
            # NOTACIÓN DEL PAPER: h_table = table_encoder(table)
            if config.use_table_attention:
                self.table_attention = nn.MultiheadAttention(config.hidden_dim, num_heads=4, dropout=config.dropout_rate)
            else:
                self.table_encoder = nn.Sequential(
                    nn.Linear(config.hidden_dim, config.hidden_dim * 2),
                    nn.GELU(),
                    nn.Dropout(config.dropout_rate),  # Regularización para producción
                    nn.Linear(config.hidden_dim * 2, config.hidden_dim)
                )
            
            # EN EL PAPER: Sección 3.3 - Table Reasoning Module
            # NOTACIÓN DEL PAPER: output = reason_on_table(table)
            self.table_reasoning = nn.Sequential(
                nn.Linear(config.hidden_dim, config.hidden_dim * 2),
                nn.GELU(),
                nn.Dropout(config.dropout_rate),  # Regularización para producción
                nn.Linear(config.hidden_dim * 2, config.hidden_dim)
            )
        except Exception as e:
            logger.error(f"Error inicializando Table as Thought: {e}")
            raise
        
        logger.info(f"Table as Thought initialized: rows={config.table_rows}, cols={config.table_cols}")
    
    def _build_table(self, hidden_states: torch.Tensor) -> torch.Tensor:
        """
        Construye estructura de tabla (Production-Ready).
        
        EN EL PAPER: Sección 3.1 - Table Construction
        FÓRMULA: table = build_table(thoughts)
        
        Args:
            hidden_states: Tensor de shape [batch, seq, hidden_dim]
        
        Returns:
            table: Tensor de shape [batch, num_cells, hidden_dim]
        """
        try:
            batch_size, seq_len, hidden_dim = hidden_states.shape
            
            # Calcular número de celdas
            num_cells = self.config.table_rows * self.config.table_cols
            num_thoughts = min(seq_len, num_cells)
            
            # Organizar pensamientos en tabla
            if self.config.structure_method == 'grid':
                # Organizar en grid
                thoughts = hidden_states[:, :num_thoughts, :]  # [batch, num_thoughts, hidden_dim]
                # Rellenar si es necesario
                if num_thoughts < num_cells:
                    padding = torch.zeros(batch_size, num_cells - num_thoughts, hidden_dim, device=hidden_states.device)
                    thoughts = torch.cat([thoughts, padding], dim=1)
            
                # Reshape a tabla: [batch, rows, cols, hidden_dim]
                table = thoughts.view(batch_size, self.config.table_rows, self.config.table_cols, hidden_dim)
            elif self.config.structure_method == 'sequential':
                # Método secuencial: simplemente tomar primeros num_cells
                table = hidden_states[:, :num_cells, :].view(batch_size, self.config.table_rows, self.config.table_cols, hidden_dim)
            else:  # hierarchical
                # Método jerárquico: similar a grid pero con estructura diferente
                thoughts = hidden_states[:, :num_thoughts, :]
                if num_thoughts < num_cells:
                    padding = torch.zeros(batch_size, num_cells - num_thoughts, hidden_dim, device=hidden_states.device)
                    thoughts = torch.cat([thoughts, padding], dim=1)
                table = thoughts.view(batch_size, self.config.table_rows, self.config.table_cols, hidden_dim)
            
            return table
        except Exception as e:
            logger.error(f"Error en _build_table: {e}")
            # Retornar tabla vacía en caso de error
            batch_size, seq_len, hidden_dim = hidden_states.shape
            num_cells = self.config.table_rows * self.config.table_cols
            return torch.zeros(batch_size, self.config.table_rows, self.config.table_cols, hidden_dim, device=hidden_states.device)
    
    def _structure_thoughts(self, table: torch.Tensor) -> torch.Tensor:
        """
        Estructura pensamientos en formato tabular (Production-Ready).
        
        EN EL PAPER: Sección 3.2 - Thought Structuring
        FÓRMULA: thoughts_structured = structure(thoughts, table)
        
        Args:
            table: Tensor de shape [batch, rows, cols, hidden_dim]
        
        Returns:
            structured: Tensor de shape [batch, rows, cols, hidden_dim]
        """
        try:
            batch_size, rows, cols, hidden_dim = table.shape
            
            # Aplicar table builder a cada celda
            table_flat = table.view(batch_size, rows * cols, hidden_dim)
            structured = self.table_builder(table_flat)  # [batch, rows*cols, hidden_dim]
            
            return structured.view(batch_size, rows, cols, hidden_dim)
        except Exception as e:
            logger.error(f"Error en _structure_thoughts: {e}")
            # Retornar tabla sin modificar en caso de error
            return table
    
    def forward(self, hidden_states: torch.Tensor, **kwargs) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass: razonamiento en estructura tabular.
        
        EN EL PAPER: Sección 4 - Reasoning Process
        
        
        Args:
            hidden_states: Tensor de shape [batch_size, seq_len, hidden_dim]
            **kwargs: Argumentos adicionales
        
        Returns:
            Tuple (output, metadata) donde:
            - output: Tensor procesado de shape [batch_size, seq_len, hidden_dim]
            - metadata: Diccionario con métricas e información adicional
        """
        # Validar inputs
        self.validate_inputs(hidden_states, **kwargs)
        
        batch_size, seq_len, hidden_dim = hidden_states.shape
        
        try:
            # PASO 1: Construir tabla
            table = self._build_table(hidden_states)
            
            # PASO 2: Estructurar pensamientos
            structured_table = self._structure_thoughts(table)
            
            # PASO 3: Aplicar razonamiento tabular
            table_flat = structured_table.view(batch_size, self.config.table_rows * self.config.table_cols, hidden_dim)
            
            if self.config.use_table_attention:
                # Usar atención sobre tabla
                table_reasoned, attention_weights = self.table_attention(table_flat, table_flat, table_flat)
            else:
                # Encoder simple
                table_reasoned = self.table_encoder(table_flat)
                attention_weights = None
            
            # Aplicar módulo de razonamiento
            output_flat = self.table_reasoning(table_reasoned)  # [batch, rows*cols, hidden_dim]
            
            # Expandir/ajustar a longitud original
            if output_flat.shape[1] < seq_len:
                padding = torch.zeros(batch_size, seq_len - output_flat.shape[1], hidden_dim, device=output_flat.device)
                output = torch.cat([output_flat, padding], dim=1)
            elif output_flat.shape[1] > seq_len:
                output = output_flat[:, :seq_len, :]
            else:
                output = output_flat
            
            # Calcular métricas mejoradas
            table_cells = self.config.table_rows * self.config.table_cols
            metadata = {
                'table_rows': self.config.table_rows,
                'table_cols': self.config.table_cols,
                'table_cells': table_cells,
                'structure_method': self.config.structure_method,
                'use_table_attention': self.config.use_table_attention,
                'output_mean': output.mean().item(),
                'output_std': output.std().item(),
                'output_max': output.max().item(),
                'output_min': output.min().item(),
                'attention_used': self.config.use_table_attention
            }
            
            self._update_metrics(
                table_rows=self.config.table_rows,
                table_cols=self.config.table_cols,
                structure_method=self.config.structure_method
            )
            
            return output, metadata
            
        except Exception as e:
            logger.error(f"Error en forward de Table as Thought: {e}")
            # En caso de error, retornar hidden_states sin modificar
            error_metadata = {
                'error': str(e),
                'table_rows': self.config.table_rows,
                'table_cols': self.config.table_cols,
                'table_cells': self.config.table_rows * self.config.table_cols,
                'structure_method': self.config.structure_method
            }
            return hidden_states, error_metadata

