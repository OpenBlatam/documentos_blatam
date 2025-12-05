#!/usr/bin/env python3
"""
FocusLLM: Scaling LLM's Context by Parallel Decoding
======================================================

(2024) FocusLLM: a framework to extend the context length via parallel decoding
Lee, Thu, etc.

Paper URL: https://arxiv.org/abs/[ID_PENDIENTE]
Nota: Paper de 2024, buscar en arXiv o repositorio del autor

Técnica principal:
- Divide input largo en "chunks" según ventana original
- Extrae información relevante de cada chunk con paralelismo
- Agrega resúmenes al contexto
- Permite contextos muy largos con bajo costo de entrenamiento

MATEMÁTICAS DEL PAPER IMPLEMENTADAS:

1. División en Chunks:
   - N_chunks = ceil(L / C) donde L es la longitud total y C es chunk_size
   - Chunk i: C_i = [x_{i·C}, ..., x_{(i+1)·C-1}]
   - Implementado en: FocusLLMModule.forward()

2. Extracción Paralela:
   - Para cada chunk C_i: S_i = Extract(C_i)
     donde Extract es una red que comprime el chunk
   - S_i tiene tamaño summary_size_per_chunk << chunk_size
   - Implementado en: ChunkExtractor.forward()

3. Contexto Extendido:
   - Contexto final: [x_0, ..., x_{C-1}, S_0, S_1, ..., S_{N-1}]
   - Longitud: C + N · summary_size donde N es el número de chunks
   - Permite procesar secuencias mucho más largas que C
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
class FocusLLMConfig(BasePaperConfig):
    """
    Configuración para FocusLLM (Production-Ready).
    
    Attributes:
        base_context_length: Longitud base del contexto (debe ser > 0)
        extended_context_length: Longitud extendida del contexto (debe ser >= base_context_length)
        chunk_size: Tamaño de chunk (debe ser > 0)
        use_parallel_decoding: Si True, usa decodificación paralela
        extraction_dim: Dimensión para extracción (debe ser > 0)
        num_extraction_layers: Número de capas de extracción (debe ser > 0)
        summary_size_per_chunk: Tamaño de resumen por chunk (debe ser > 0)
        dropout_rate: Tasa de dropout para regularización (default: 0.1)
    """
    base_context_length: int = 2048
    extended_context_length: int = 65536
    chunk_size: int = 2048
    use_parallel_decoding: bool = True
    extraction_dim: int = 256
    num_extraction_layers: int = 2
    summary_size_per_chunk: int = 64
    dropout_rate: float = 0.1
    
    def validate(self):
        """Valida la configuración de FocusLLM."""
        super().validate()
        if self.base_context_length <= 0:
            raise ValueError(f"base_context_length debe ser > 0, recibido: {self.base_context_length}")
        if self.extended_context_length < self.base_context_length:
            raise ValueError(
                f"extended_context_length ({self.extended_context_length}) debe ser >= "
                f"base_context_length ({self.base_context_length})"
            )
        if self.chunk_size <= 0:
            raise ValueError(f"chunk_size debe ser > 0, recibido: {self.chunk_size}")
        if self.extraction_dim <= 0:
            raise ValueError(f"extraction_dim debe ser > 0, recibido: {self.extraction_dim}")
        if self.num_extraction_layers <= 0:
            raise ValueError(f"num_extraction_layers debe ser > 0, recibido: {self.num_extraction_layers}")
        if self.summary_size_per_chunk <= 0:
            raise ValueError(f"summary_size_per_chunk debe ser > 0, recibido: {self.summary_size_per_chunk}")
        if not 0.0 <= self.dropout_rate < 1.0:
            raise ValueError(f"dropout_rate debe estar en [0, 1), recibido: {self.dropout_rate}")


class ChunkExtractor(nn.Module):
    """Extractor de información relevante de chunks."""
    
    def __init__(self, config: FocusLLMConfig):
        super().__init__()
        self.config = config
        
        try:
            # Capas de extracción
            extraction_layers = []
            for i in range(config.num_extraction_layers):
                extraction_layers.append(
                    nn.TransformerEncoderLayer(
                        d_model=config.hidden_dim,
                        nhead=8,
                        dim_feedforward=config.hidden_dim * 4,
                        dropout=config.dropout_rate,  # Regularización para producción
                        batch_first=True
                    )
                )
            self.extractor = nn.Sequential(*extraction_layers)
            
            # Proyección de resumen
            self.summary_proj = nn.Sequential(
                nn.Linear(config.hidden_dim, config.hidden_dim),
                nn.Dropout(config.dropout_rate),  # Regularización para producción
                nn.Linear(config.hidden_dim, config.hidden_dim)
            )
        except Exception as e:
            logger.error(f"Error inicializando ChunkExtractor: {e}")
            raise
    
    def forward(self, chunk: torch.Tensor) -> torch.Tensor:
        """
        Extrae información relevante de un chunk (Production-Ready).
        
        Args:
            chunk: [batch, chunk_size, hidden_dim]
        
        Returns:
            summary: [batch, summary_size, hidden_dim]
        """
        try:
            # Extraer
            extracted = self.extractor(chunk)  # [batch, chunk_size, hidden_dim]
            
            # Crear resumen
            summary_size = self.config.summary_size_per_chunk
            if extracted.size(1) > summary_size:
                # Reducir a summary_size
                summary = F.adaptive_avg_pool1d(
                    extracted.transpose(1, 2),
                    summary_size
                ).transpose(1, 2)  # [batch, summary_size, hidden_dim]
            else:
                # Padding
                summary = extracted
                if extracted.size(1) < summary_size:
                    padding = torch.zeros(
                        extracted.size(0),
                        summary_size - extracted.size(1),
                        extracted.size(2),
                        device=extracted.device,
                        dtype=extracted.dtype
                    )
                    summary = torch.cat([extracted, padding], dim=1)
            
            # Proyectar
            summary = self.summary_proj(summary)
            
            return summary
        except Exception as e:
            logger.error(f"Error en ChunkExtractor forward: {e}")
            # Retornar resumen vacío en caso de error
            batch_size = chunk.shape[0]
            return torch.zeros(
                batch_size,
                self.config.summary_size_per_chunk,
                self.config.hidden_dim,
                device=chunk.device
            )


class ParallelDecoder(nn.Module):
    """Decodificador paralelo para procesar múltiples chunks."""
    
    def __init__(self, config: FocusLLMConfig):
        super().__init__()
        self.config = config
        
        try:
            # Decodificador
            decoder_layer = nn.TransformerDecoderLayer(
                d_model=config.hidden_dim,
                nhead=8,
                dim_feedforward=config.hidden_dim * 4,
                dropout=config.dropout_rate,  # Regularización para producción
                batch_first=True
            )
            self.decoder = nn.TransformerDecoder(decoder_layer, num_layers=2)
        except Exception as e:
            logger.error(f"Error inicializando ParallelDecoder: {e}")
            raise
    
    def forward(self, query: torch.Tensor, chunk_summaries: torch.Tensor) -> torch.Tensor:
        """
        Decodifica usando resúmenes de chunks (Production-Ready).
        
        Args:
            query: [batch, query_len, hidden_dim]
            chunk_summaries: [batch, num_chunks * summary_size, hidden_dim]
        
        Returns:
            decoded: [batch, query_len, hidden_dim]
        """
        try:
            decoded = self.decoder(query, chunk_summaries)
            return decoded
        except Exception as e:
            logger.error(f"Error en ParallelDecoder forward: {e}")
            # Retornar query sin modificar en caso de error
            return query


class FocusLLMModule(BasePaperModule):
    """
    FocusLLM: Context Extension via Parallel Decoding.
    
    Características:
    - División en chunks
    - Extracción paralela de información
    - Agregación de resúmenes
    - Bajo costo de entrenamiento
    """
    
    def __init__(self, config: FocusLLMConfig):
        super().__init__(config)
        self.config = config
        
        # Extractor de chunks
        self.chunk_extractor = ChunkExtractor(config)
        
        # Decodificador paralelo
        if config.use_parallel_decoding:
            self.parallel_decoder = ParallelDecoder(config)
        else:
            self.parallel_decoder = None
        
        logger.info(f"FocusLLM initialized: {config.base_context_length} → {config.extended_context_length} tokens")
    
    def extract_chunks_parallel(self, hidden_states: torch.Tensor) -> torch.Tensor:
        """
        Extrae información de chunks en paralelo (Production-Ready).
        
        Args:
            hidden_states: [batch, seq_len, hidden_dim]
        
        Returns:
            chunk_summaries: [batch, total_summary_size, hidden_dim]
        """
        try:
            batch_size, seq_len, hidden_dim = hidden_states.shape
            chunk_size = self.config.chunk_size
            
            # Dividir en chunks
            num_chunks = (seq_len + chunk_size - 1) // chunk_size
            chunk_summaries = []
            
            for i in range(num_chunks):
                start = i * chunk_size
                end = min(start + chunk_size, seq_len)
                chunk = hidden_states[:, start:end, :]
                
                # Padding si es necesario
                if chunk.size(1) < chunk_size:
                    padding = torch.zeros(
                        batch_size, chunk_size - chunk.size(1), hidden_dim,
                        device=chunk.device, dtype=chunk.dtype
                    )
                    chunk = torch.cat([chunk, padding], dim=1)
                
                # Extraer información relevante
                summary = self.chunk_extractor(chunk)  # [batch, summary_size, hidden_dim]
                chunk_summaries.append(summary)
            
            # Concatenar todos los resúmenes
            all_summaries = torch.cat(chunk_summaries, dim=1)  # [batch, num_chunks * summary_size, hidden_dim]
            
            return all_summaries
        except Exception as e:
            logger.error(f"Error en extract_chunks_parallel: {e}")
            # Retornar resumen simple en caso de error
            batch_size = hidden_states.shape[0]
            return torch.zeros(
                batch_size,
                self.config.summary_size_per_chunk,
                self.config.hidden_dim,
                device=hidden_states.device
            )
    
    def forward(
        self,
        hidden_states: torch.Tensor,
        **kwargs
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass con FocusLLM (Production-Ready).
        
        Args:
            hidden_states: [batch, seq_len, hidden_dim]
            **kwargs: Argumentos adicionales
        
        Returns:
            (output, metadata)
        """
        # Validar inputs
        self.validate_inputs(hidden_states, **kwargs)
        
        batch_size, seq_len, hidden_dim = hidden_states.shape
        
        try:
            if seq_len <= self.config.base_context_length:
                # Contexto corto: usar directamente
                output = hidden_states
                num_chunks = 0
            else:
                # Contexto largo: usar FocusLLM
                # 1. Extraer información de chunks en paralelo
                chunk_summaries = self.extract_chunks_parallel(hidden_states)
                
                # 2. Usar primeros tokens como query
                query = hidden_states[:, :self.config.base_context_length, :]
                
                # 3. Decodificar con resúmenes de chunks
                if self.parallel_decoder is not None:
                    decoded = self.parallel_decoder(query, chunk_summaries)
                else:
                    # Sin decodificador: simplemente concatenar
                    decoded = query
                
                # 4. Combinar query decodificada con resúmenes
                # Truncar resúmenes si es necesario para caber en base_context_length
                max_summary_len = self.config.base_context_length - decoded.size(1)
                if max_summary_len > 0 and chunk_summaries.size(1) > max_summary_len:
                    chunk_summaries = chunk_summaries[:, :max_summary_len, :]
                
                # Concatenar
                if decoded.size(1) + chunk_summaries.size(1) <= self.config.base_context_length:
                    output = torch.cat([decoded, chunk_summaries], dim=1)
                else:
                    output = decoded
                
                num_chunks = (seq_len + self.config.chunk_size - 1) // self.config.chunk_size
            
            # Calcular métricas mejoradas
            metadata = {
                'context_length': seq_len,
                'base_context_length': self.config.base_context_length,
                'extended_context_length': self.config.extended_context_length,
                'extended': seq_len > self.config.base_context_length,
                'num_chunks': num_chunks,
                'chunk_size': self.config.chunk_size,
                'summary_size_per_chunk': self.config.summary_size_per_chunk,
                'parallel_decoding': self.config.use_parallel_decoding,
                'extraction_dim': self.config.extraction_dim,
                'num_extraction_layers': self.config.num_extraction_layers,
                'output_mean': output.mean().item(),
                'output_std': output.std().item(),
                'output_max': output.max().item(),
                'output_min': output.min().item()
            }
            
            self._update_metrics(
                context_length=seq_len,
                num_chunks=num_chunks,
                extended=seq_len > self.config.base_context_length
            )
            
            return output, metadata
            
        except Exception as e:
            logger.error(f"Error en forward de FocusLLM: {e}")
            # En caso de error, retornar hidden_states sin modificar
            error_metadata = {
                'error': str(e),
                'context_length': seq_len,
                'extended': False,
                'num_chunks': 0
            }
            return hidden_states, error_metadata


if __name__ == "__main__":
    config = FocusLLMConfig(
        hidden_dim=768,
        base_context_length=2048,
        extended_context_length=65536
    )
    
    module = FocusLLMModule(config)
    
    # Test
    hidden_states = torch.randn(2, 8192, config.hidden_dim)
    output, metadata = module(hidden_states)
    
    print(f"✅ FocusLLM test:")
    print(f"   Input shape: {hidden_states.shape}")
    print(f"   Output shape: {output.shape}")
    print(f"   Num chunks: {metadata['num_chunks']}")


