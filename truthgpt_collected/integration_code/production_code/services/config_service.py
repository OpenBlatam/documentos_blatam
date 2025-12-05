#!/usr/bin/env python3
"""
Config Service
==============

Business logic for configuration operations.
"""

from typing import Dict, Optional, Any, Union, Tuple, List, TYPE_CHECKING
from core.utils import setup_logger
from core.error_handling import safe_execute

if TYPE_CHECKING:
    from core.config_manager import ConfigManager

logger = setup_logger(__name__)


class ConfigService:
    """Service for configuration operations."""
    
    def __init__(self, config_manager: "ConfigManager") -> None:
        """
        Initialize config service.
        
        Args:
            config_manager: ConfigManager instance
        
        Raises:
            ValueError: If config_manager is None
        """
        if config_manager is None:
            raise ValueError("Config manager cannot be None")
        self.config_manager = config_manager
    
    def get_config(self, module: Optional[str] = None) -> Dict[str, Any]:
        """
        Get configuration.
        
        Args:
            module: Optional module name
        
        Returns:
            Configuration dictionary
        
        Raises:
            ValueError: If config manager is not initialized
            RuntimeError: If getting config fails
        """
        if self.config_manager is None:
            raise ValueError("Config manager not initialized")
        
        return safe_execute(
            lambda: (
                self.config_manager.get_config(module)
                if module
                else self.config_manager.get_all_configs()
            ),
            error_message="Error getting config"
        )
    
    def update_config(self, module: str, config: Dict[str, Any]) -> bool:
        """
        Update configuration.
        
        Args:
            module: Module name
            config: Configuration dictionary
        
        Returns:
            True if successful
        
        Raises:
            ValueError: If config manager is not initialized or module is empty
            RuntimeError: If updating config fails
        """
        if self.config_manager is None:
            raise ValueError("Config manager not initialized")
        
        return safe_execute(
            lambda: self.config_manager.set_config(module, config) or True,
            error_message="Error updating config"
        )
    
    def validate_config(self, module: str) -> Tuple[bool, List[str]]:
        """
        Validate configuration.
        
        Args:
            module: Module name
        
        Returns:
            Tuple of (is_valid, errors)
        
        Raises:
            ValueError: If config manager is not initialized or module is empty
            RuntimeError: If validation fails
        """
        if self.config_manager is None:
            raise ValueError("Config manager not initialized")
        
        return safe_execute(
            lambda: self.config_manager.validate_config(module),
            error_message="Error validating config"
        )
    
    def is_available(self) -> bool:
        """Check if config manager is available."""
        return self.config_manager is not None


