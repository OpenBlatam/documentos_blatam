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
import logging
import math

from ..core.paper_base import BasePaperModule, BasePaperConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TableAsThoughtConfig(BasePaperConfig):
    """Configuración para Table as Thought."""
    table_rows: int = 5  # Número de filas en la tabla
    table_cols: int = 4  # Número de columnas
    use_table_attention: bool = True
    structure_method: str = 'grid'  # 'grid', 'hierarchical', 'sequential'


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
        
        # EN EL PAPER: Sección 3.1 - Table Builder
        # NOTACIÓN DEL PAPER: table = build_table(thoughts)
        # NOTACIÓN EN CÓDIGO: table_builder construye estructura tabular
        self.table_builder = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim * 2),
            nn.GELU(),
            nn.Linear(config.hidden_dim * 2, config.hidden_dim)
        )
        
        # EN EL PAPER: Sección 3.2 - Table Encoder
        # NOTACIÓN DEL PAPER: h_table = table_encoder(table)
        if config.use_table_attention:
            self.table_attention = nn.MultiheadAttention(config.hidden_dim, num_heads=4)
        else:
            self.table_encoder = nn.Sequential(
                nn.Linear(config.hidden_dim, config.hidden_dim * 2),
                nn.GELU(),
                nn.Linear(config.hidden_dim * 2, config.hidden_dim)
            )
        
        # EN EL PAPER: Sección 3.3 - Table Reasoning Module
        # NOTACIÓN DEL PAPER: output = reason_on_table(table)
        self.table_reasoning = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim * 2),
            nn.GELU(),
            nn.Linear(config.hidden_dim * 2, config.hidden_dim)
        )
        
        logger.info(f"Table as Thought initialized: rows={config.table_rows}, cols={config.table_cols}")
    
    def _build_table(self, hidden_states: torch.Tensor) -> torch.Tensor:
        """
        Construye estructura de tabla.
        
        EN EL PAPER: Sección 3.1 - Table Construction
        FÓRMULA: table = build_table(thoughts)
        """
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
        else:
            # Método secuencial: simplemente tomar primeros num_cells
            table = hidden_states[:, :num_cells, :].view(batch_size, self.config.table_rows, self.config.table_cols, hidden_dim)
        
        return table
    
    def _structure_thoughts(self, table: torch.Tensor) -> torch.Tensor:
        """
        Estructura pensamientos en formato tabular.
        
        EN EL PAPER: Sección 3.2 - Thought Structuring
        FÓRMULA: thoughts_structured = structure(thoughts, table)
        """
        batch_size, rows, cols, hidden_dim = table.shape
        
        # Aplicar table builder a cada celda
        table_flat = table.view(batch_size, rows * cols, hidden_dim)
        structured = self.table_builder(table_flat)  # [batch, rows*cols, hidden_dim]
        
        return structured.view(batch_size, rows, cols, hidden_dim)
    
    def forward(self, hidden_states: torch.Tensor, **kwargs) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass: razonamiento en estructura tabular.
        
        EN EL PAPER: Sección 4 - Reasoning Process
        """
        batch_size, seq_len, hidden_dim = hidden_states.shape
        
        # PASO 1: Construir tabla
        table = self._build_table(hidden_states)
        
        # PASO 2: Estructurar pensamientos
        structured_table = self._structure_thoughts(table)
        
        # PASO 3: Aplicar razonamiento tabular
        table_flat = structured_table.view(batch_size, self.config.table_rows * self.config.table_cols, hidden_dim)
        
        if self.config.use_table_attention:
            # Usar atención sobre tabla
            table_reasoned, _ = self.table_attention(table_flat, table_flat, table_flat)
        else:
            # Encoder simple
            table_reasoned = self.table_encoder(table_flat)
        
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
        
        metadata = {
            'table_rows': self.config.table_rows,
            'table_cols': self.config.table_cols,
            'table_cells': self.config.table_rows * self.config.table_cols,
            'structure_method': self.config.structure_method
        }
        
        self._update_metrics(
            table_rows=self.config.table_rows,
            table_cols=self.config.table_cols
        )
        
        return output, metadata

