#!/usr/bin/env python3
"""
Data Persistence
================

Persistencia de datos de modelos en base de datos.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import json
import sqlite3
import time
from datetime import datetime
from contextlib import contextmanager

from .data_collector import ModelData
from .constants import DB_FILENAME
from core.utils import setup_logger
from core.error_handling import safe_execute

logger = setup_logger(__name__)


class DataPersistence:
    """
    Persistencia de datos de modelos en base de datos SQLite.
    
    Almacena:
    - Datos de modelos
    - Historial de cambios
    - Benchmarks
    - Métricas temporales
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Inicializa la persistencia.
        
        Args:
            db_path: Ruta de la base de datos (opcional)
        
        Raises:
            IOError: Si no se puede crear el directorio de la base de datos
        """
        if db_path is None:
            db_path = Path(__file__).parent.parent / DB_FILENAME
        
        self.db_path = Path(db_path)
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error("Error creando directorio para base de datos", path=str(self.db_path.parent), error=str(e))
            raise IOError(f"No se pudo crear el directorio para la base de datos: {e}") from e
        
        self._init_database()
    
    def _init_database(self):
        """
        Inicializa las tablas de la base de datos.
        
        Raises:
            sqlite3.Error: Si hay un error al crear las tablas
        """
        def _init():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Tabla de modelos
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS model_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        model_name TEXT NOT NULL,
                        model_class TEXT NOT NULL,
                        paper_id TEXT,
                        category TEXT,
                        model_info TEXT,
                        config TEXT,
                        metrics TEXT,
                        parameters TEXT,
                        metadata TEXT,
                        collected_at REAL NOT NULL,
                        updated_at REAL NOT NULL,
                        UNIQUE(model_name, paper_id, collected_at)
                    )
                """)
                
                # Tabla de benchmarks
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS benchmarks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        model_data_id INTEGER NOT NULL,
                        batch_size INTEGER,
                        seq_len INTEGER,
                        hidden_dim INTEGER,
                        forward_time REAL,
                        backward_time REAL,
                        memory_used REAL,
                        throughput REAL,
                        latency REAL,
                        benchmark_data TEXT,
                        created_at REAL NOT NULL,
                        FOREIGN KEY (model_data_id) REFERENCES model_data(id)
                    )
                """)
                
                # Índices
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_model_data_paper_id 
                    ON model_data(paper_id)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_model_data_category 
                    ON model_data(category)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_model_data_collected_at 
                    ON model_data(collected_at)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_benchmarks_model_data_id 
                    ON benchmarks(model_data_id)
                """)
                
                conn.commit()
        
        result, error = safe_execute(_init, default_value=None, log_errors=True)
        if error:
            logger.error("Error inicializando base de datos", error=str(error))
            raise sqlite3.Error(f"Error al inicializar la base de datos: {error}") from error
    
    @contextmanager
    def _get_connection(self):
        """Context manager para conexiones a la base de datos."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def save_model_data(self, model_data: ModelData) -> int:
        """
        Guarda datos de un modelo.
        
        Args:
            model_data: Datos del modelo
        
        Returns:
            ID del registro guardado
        
        Raises:
            sqlite3.Error: Si hay un error al guardar
        """
        def _save():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                try:
                    cursor.execute("""
                        INSERT INTO model_data (
                            model_name, model_class, paper_id, category,
                            model_info, config, metrics, parameters, metadata,
                            collected_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        model_data.model_name,
                        model_data.model_class,
                        model_data.paper_id,
                        model_data.category,
                        json.dumps(model_data.model_info, default=str),
                        json.dumps(model_data.config, default=str),
                        json.dumps(model_data.metrics, default=str),
                        json.dumps(model_data.parameters, default=str),
                        json.dumps(model_data.metadata, default=str),
                        model_data.collected_at,
                        model_data.updated_at
                    ))
                    
                    model_data_id = cursor.lastrowid
                    
                    if model_data.benchmarks:
                        benchmark_data = [
                            (
                                model_data_id,
                                benchmark.get('batch_size'),
                                benchmark.get('seq_len'),
                                benchmark.get('hidden_dim'),
                                benchmark.get('forward_time'),
                                benchmark.get('backward_time'),
                                benchmark.get('memory_used'),
                                benchmark.get('throughput'),
                                benchmark.get('latency'),
                                json.dumps(benchmark.get('metadata', {}), default=str),
                                time.time()
                            )
                            for benchmark in model_data.benchmarks
                        ]
                        
                        cursor.executemany("""
                            INSERT INTO benchmarks (
                                model_data_id, batch_size, seq_len, hidden_dim,
                                forward_time, backward_time, memory_used,
                                throughput, latency, benchmark_data, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, benchmark_data)
                    
                    conn.commit()
                    logger.info("Datos del modelo guardados", model_name=model_data.model_name, id=model_data_id)
                    return model_data_id
                except sqlite3.Error as e:
                    conn.rollback()
                    raise
        
        result, error = safe_execute(_save, default_value=None, log_errors=True)
        if error:
            logger.error("Error guardando datos del modelo", model_name=model_data.model_name, error=str(error))
            raise sqlite3.Error(f"Error al guardar datos del modelo: {error}") from error
        
        return result
    
    def get_model_history(
        self,
        paper_id: Optional[str] = None,
        model_name: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene historial de un modelo.
        
        Args:
            paper_id: Filtrar por paper_id
            model_name: Filtrar por model_name
            limit: Límite de resultados
        
        Returns:
            Lista de registros históricos
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM model_data WHERE 1=1"
            params = []
            
            if paper_id:
                query += " AND paper_id = ?"
                params.append(paper_id)
            
            if model_name:
                query += " AND model_name = ?"
                params.append(model_name)
            
            query += " ORDER BY collected_at DESC"
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                result = dict(row)
                # Parsear JSON fields
                for field in ['model_info', 'config', 'metrics', 'parameters', 'metadata']:
                    if result[field]:
                        result[field] = json.loads(result[field])
                results.append(result)
            
            return results
    
    def get_latest_model_data(
        self,
        paper_id: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene los datos más recientes de un modelo.
        
        Args:
            paper_id: Filtrar por paper_id
            model_name: Filtrar por model_name
        
        Returns:
            Datos del modelo o None
        """
        history = self.get_model_history(paper_id=paper_id, model_name=model_name, limit=1)
        return history[0] if history else None
    
    def compare_models_over_time(
        self,
        paper_id: str,
        metric: str = 'total_parameters'
    ) -> List[Dict[str, Any]]:
        """
        Compara un modelo a lo largo del tiempo.
        
        Args:
            paper_id: ID del paper
            metric: Métrica a comparar
        
        Returns:
            Lista de valores de la métrica a lo largo del tiempo
        """
        history = self.get_model_history(paper_id=paper_id)
        
        results = []
        for record in history:
            value = None
            if metric == 'total_parameters':
                value = record.get('parameters', {}).get('total_parameters')
            elif metric == 'forward_count':
                value = record.get('metrics', {}).get('forward_count')
            
            if value is not None:
                results.append({
                    'timestamp': record['collected_at'],
                    'value': value,
                    'model_name': record['model_name']
                })
        
        return results
    
    def get_statistics(
        self,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtiene estadísticas de la base de datos.
        
        Args:
            category: Filtrar por categoría (opcional)
        
        Returns:
            Diccionario con estadísticas
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT COUNT(*) as total FROM model_data"
            params = []
            
            if category:
                query += " WHERE category = ?"
                params.append(category)
            
            cursor.execute(query, params)
            total = cursor.fetchone()['total']
            
            # Papers únicos
            query = "SELECT COUNT(DISTINCT paper_id) as unique_papers FROM model_data"
            if category:
                query += " WHERE category = ?"
            cursor.execute(query, params)
            unique_papers = cursor.fetchone()['unique_papers']
            
            # Categorías
            cursor.execute("SELECT category, COUNT(*) as count FROM model_data GROUP BY category")
            categories = {row['category']: row['count'] for row in cursor.fetchall()}
            
            return {
                'total_records': total,
                'unique_papers': unique_papers,
                'categories': categories
            }

