#!/usr/bin/env python3
"""
Constants for Model Data Collection System
==========================================

Constantes utilizadas en el sistema de recolección de datos de modelos.
"""

from pathlib import Path

DEFAULT_CACHE_TTL = 300
DEFAULT_BENCHMARK_WARMUP_RUNS = 3
DEFAULT_BENCHMARK_NUM_RUNS = 5
DEFAULT_TOP_K_MODELS = 10
DEFAULT_MAX_WORKERS = None

DEFAULT_BENCHMARK_SIZES = [
    {'batch_size': 1, 'seq_len': 128},
    {'batch_size': 4, 'seq_len': 256},
    {'batch_size': 8, 'seq_len': 512}
]

DEFAULT_DEVICE = 'cpu'
DEFAULT_PROJECT_NAME = "model-data-collection"

SUPPORTED_EXPORT_FORMATS = {'json', 'csv', 'html', 'markdown'}
DEFAULT_EXPORT_FORMAT = 'json'

DB_FILENAME = 'model_data.db'
EXPORTS_DIR = 'exports'
VISUALIZATIONS_DIR = 'visualizations'
CHECKPOINTS_DIR = 'checkpoints'

MIN_WORKERS = 1
MAX_WORKERS_LIMIT = 100


