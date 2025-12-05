#!/usr/bin/env python3
"""
Core modules for production code.
================================

Módulos centrales que proporcionan funcionalidades base para todo el sistema:
- BasePaperModule y BasePaperConfig para módulos de papers
- PaperRegistry para gestión de papers
- Benchmarking, testing y profiling
- Monitoring y health checks
- Validation y error handling
- Optimization y export
- Analysis y visualization
- Performance optimization
- Checkpointing y quality checking
"""

__version__ = '2.0.0'

from .paper_base import (
    BasePaperModule,
    BasePaperConfig,
    ModelError,
    ValidationError,
    ConfigurationError
)

from .paper_registry import (
    PaperRegistry,
    PaperInfo,
    LoadedModule,
    get_registry
)

from .benchmark import (
    BenchmarkRunner,
    BenchmarkResult,
    compare_results
)

from .testing import (
    ModuleTester,
    TestResult,
    run_tests
)

from .profiling import (
    Profiler,
    ProfileResult,
    profile_module
)

from .monitoring import (
    MetricsCollector,
    HealthMonitor,
    Metric,
    HealthCheck,
    create_default_health_checks
)

from .utils import setup_logger
from .validation_utils import (
    validate_range,
    validate_positive,
    validate_non_negative,
    validate_integer,
    validate_boolean
)
from .error_handling import (
    retry,
    async_retry,
    RetryStrategy,
    safe_execute,
    ErrorHandler,
    CoreError
)

from .optimization import (
    ModuleOptimizer,
    OptimizationResult,
    auto_optimize_module
)

from .validation import (
    ModuleValidator,
    ValidationResult,
    create_default_validators
)

from .export import (
    export_to_onnx,
    export_to_torchscript,
    export_model_info,
    export_complete
)

from .helpers import (
    timing_decorator,
    device_decorator,
    count_parameters,
    get_model_size_mb,
    freeze_module,
    get_gradient_norm,
    clip_gradients,
    create_summary,
    compare_modules,
    get_gpu_memory_stats,
    clear_gpu_cache,
    auto_select_device,
    move_to_device,
    batch_tensor,
    concatenate_tensors,
    get_tensor_info,
    ensure_tensor_on_device,
    profile_function,
    validate_tensor_device
)

from .migration import (
    migrate_logging,
    migrate_validate_method,
    migrate_validate_inputs,
    migrate_file,
    migrate_directory
)

from .analysis import (
    ModuleAnalyzer,
    LayerAnalysis,
    ModuleAnalysis,
    analyze_forward_pass,
    compute_flops
)

from .visualization import (
    generate_module_report,
    generate_comparison_report,
    visualize_architecture
)

from .performance import (
    PerformanceMonitor,
    optimize_for_inference,
    fuse_modules,
    compile_module,
    profile_memory
)

from .checkpointing import (
    CheckpointManager,
    CheckpointMetadata,
    save_checkpoint,
    load_checkpoint
)

from .quality import (
    QualityChecker,
    QualityIssue,
    QualityReport,
    check_module_quality
)

try:
    from .advanced_utils import (
        serialize_json,
        deserialize_json,
        serialize_msgpack,
        deserialize_msgpack,
        CacheManager,
        get_console,
        print_table,
        print_panel,
        AdvancedConfigManager,
        PrometheusMetricsCollector,
        get_system_metrics,
        parallel_process,
        setup_structured_logging,
        get_structured_logger,
        parse_datetime,
        validate_json_schema,
        validate_with_cerberus
    )
    ADVANCED_UTILS_AVAILABLE = True
except ImportError:
    ADVANCED_UTILS_AVAILABLE = False

try:
    from .llm_advanced import (
        AdvancedLLMClient,
        TokenCounter,
        AdvancedVectorStore,
        PromptEngineer
    )
    LLM_ADVANCED_AVAILABLE = True
except ImportError:
    LLM_ADVANCED_AVAILABLE = False

try:
    from .visualization_advanced import (
        AdvancedVisualizer,
        create_metrics_dashboard
    )
    VISUALIZATION_ADVANCED_AVAILABLE = True
except ImportError:
    VISUALIZATION_ADVANCED_AVAILABLE = False

__all__ = [
    'BasePaperModule',
    'BasePaperConfig',
    'ModelError',
    'ValidationError',
    'ConfigurationError',
    'PaperRegistry',
    'PaperInfo',
    'LoadedModule',
    'get_registry',
    'BenchmarkRunner',
    'BenchmarkResult',
    'compare_results',
    'ModuleTester',
    'TestResult',
    'run_tests',
    'Profiler',
    'ProfileResult',
    'profile_module',
    'MetricsCollector',
    'HealthMonitor',
    'Metric',
    'HealthCheck',
    'create_default_health_checks',
    'setup_logger',
    'validate_range',
    'validate_positive',
    'validate_non_negative',
    'validate_integer',
    'validate_boolean',
    'retry',
    'async_retry',
    'RetryStrategy',
    'safe_execute',
    'ErrorHandler',
    'CoreError',
    'ModuleOptimizer',
    'OptimizationResult',
    'auto_optimize_module',
    'ModuleValidator',
    'ValidationResult',
    'create_default_validators',
    'export_to_onnx',
    'export_to_torchscript',
    'export_model_info',
    'export_complete',
    'timing_decorator',
    'device_decorator',
    'count_parameters',
    'get_model_size_mb',
    'freeze_module',
    'get_gradient_norm',
    'clip_gradients',
    'create_summary',
    'compare_modules',
    'get_gpu_memory_stats',
    'clear_gpu_cache',
    'auto_select_device',
    'move_to_device',
    'batch_tensor',
    'concatenate_tensors',
    'get_tensor_info',
    'ensure_tensor_on_device',
    'profile_function',
    'validate_tensor_device',
    'migrate_logging',
    'migrate_validate_method',
    'migrate_validate_inputs',
    'migrate_file',
    'migrate_directory',
    'ModuleAnalyzer',
    'LayerAnalysis',
    'ModuleAnalysis',
    'analyze_forward_pass',
    'compute_flops',
    'generate_module_report',
    'generate_comparison_report',
    'visualize_architecture',
    'PerformanceMonitor',
    'optimize_for_inference',
    'fuse_modules',
    'compile_module',
    'profile_memory',
    'CheckpointManager',
    'CheckpointMetadata',
    'save_checkpoint',
    'load_checkpoint',
    'QualityChecker',
    'QualityIssue',
    'QualityReport',
    'check_module_quality',
    'ADVANCED_UTILS_AVAILABLE',
    'LLM_ADVANCED_AVAILABLE',
    'VISUALIZATION_ADVANCED_AVAILABLE'
]

if ADVANCED_UTILS_AVAILABLE:
    __all__.extend([
        'serialize_json',
        'deserialize_json',
        'serialize_msgpack',
        'deserialize_msgpack',
        'CacheManager',
        'get_console',
        'print_table',
        'print_panel',
        'AdvancedConfigManager',
        'PrometheusMetricsCollector',
        'get_system_metrics',
        'parallel_process',
        'setup_structured_logging',
        'get_structured_logger',
        'parse_datetime',
        'validate_json_schema',
        'validate_with_cerberus'
    ])

if LLM_ADVANCED_AVAILABLE:
    __all__.extend([
        'AdvancedLLMClient',
        'TokenCounter',
        'AdvancedVectorStore',
        'PromptEngineer'
    ])

if VISUALIZATION_ADVANCED_AVAILABLE:
    __all__.extend([
        'AdvancedVisualizer',
        'create_metrics_dashboard'
    ])
