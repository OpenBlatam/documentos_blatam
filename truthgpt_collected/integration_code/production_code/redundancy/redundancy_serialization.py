#!/usr/bin/env python3
"""
Sistema de Serialización para Redundancy
=========================================

Sistema avanzado de serialización y deserialización para el módulo de redundancia,
incluyendo versionado, compresión y validación.
"""

from typing import Dict, Any, Optional, Union, List
import json
import pickle
import gzip
import base64
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
import hashlib

from core.utils import setup_logger
from core.error_handling import safe_execute

logger = setup_logger(__name__)


@dataclass
class SerializationMetadata:
    """Metadatos de serialización."""
    version: str
    timestamp: str
    format: str
    compressed: bool
    checksum: Optional[str] = None
    metadata: Dict[str, Any] = None


class RedundancySerializer:
    """
    Serializador avanzado para el módulo de redundancia.
    """
    
    CURRENT_VERSION = "1.0.0"
    SUPPORTED_FORMATS = ["json", "pickle", "binary"]
    
    def __init__(
        self,
        compress: bool = True,
        include_metadata: bool = True,
        validate_on_load: bool = True
    ):
        """
        Inicializa el serializador.
        
        Args:
            compress: Si se debe comprimir los datos
            include_metadata: Si se debe incluir metadatos
            validate_on_load: Si se debe validar al cargar
        """
        self.compress = compress
        self.include_metadata = include_metadata
        self.validate_on_load = validate_on_load
    
    def serialize(
        self,
        data: Any,
        format: str = "json",
        include_state: bool = True
    ) -> bytes:
        """
        Serializa datos.
        
        Args:
            data: Datos a serializar
            format: Formato de serialización
            include_state: Si se debe incluir el estado completo
        
        Returns:
            Datos serializados como bytes
        """
        def _serialize():
            if format not in self.SUPPORTED_FORMATS:
                raise ValueError(f"Formato no soportado: {format}")
            
            if format == "json":
                serialized = json.dumps(data, default=self._json_default).encode('utf-8')
            elif format == "pickle":
                serialized = pickle.dumps(data)
            else:  # binary
                serialized = self._serialize_binary(data)
            
            if self.compress:
                serialized = gzip.compress(serialized)
            
            if self.include_metadata:
                metadata = self._create_metadata(format, serialized)
                return self._add_metadata(serialized, metadata)
            
            return serialized
        
        result, error = safe_execute(
            _serialize,
            default_value=b'',
            log_errors=True
        )
        
        if error:
            logger.error(f"Error serializando datos: {error}")
            return b''
        
        return result
    
    def deserialize(
        self,
        data: bytes,
        format: Optional[str] = None
    ) -> Any:
        """
        Deserializa datos.
        
        Args:
            data: Datos serializados
            format: Formato (se detecta automáticamente si es None)
        
        Returns:
            Datos deserializados
        """
        def _deserialize():
            metadata = None
            actual_data = data
            
            if self.include_metadata:
                actual_data, metadata = self._extract_metadata(data)
                if metadata:
                    format = metadata.get('format', 'json')
                    if metadata.get('compressed', False):
                        actual_data = gzip.decompress(actual_data)
            
            if format is None:
                format = self._detect_format(actual_data)
            
            if format == "json":
                result = json.loads(actual_data.decode('utf-8'))
            elif format == "pickle":
                result = pickle.loads(actual_data)
            else:  # binary
                result = self._deserialize_binary(actual_data)
            
            if self.validate_on_load:
                self._validate_data(result)
            
            return result
        
        result, error = safe_execute(
            _deserialize,
            default_value=None,
            log_errors=True
        )
        
        if error:
            logger.error(f"Error deserializando datos: {error}")
            return None
        
        return result
    
    def save_to_file(
        self,
        data: Any,
        filepath: Union[str, Path],
        format: str = "json"
    ) -> bool:
        """
        Guarda datos serializados en un archivo.
        
        Args:
            data: Datos a guardar
            filepath: Ruta del archivo
            format: Formato de serialización
        
        Returns:
            True si se guardó exitosamente
        """
        def _save():
            serialized = self.serialize(data, format)
            filepath_obj = Path(filepath)
            filepath_obj.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath_obj, 'wb') as f:
                f.write(serialized)
            
            logger.info(f"Datos guardados en {filepath}")
            return True
        
        result, error = safe_execute(_save, default_value=False, log_errors=True)
        return result
    
    def load_from_file(
        self,
        filepath: Union[str, Path],
        format: Optional[str] = None
    ) -> Any:
        """
        Carga datos desde un archivo.
        
        Args:
            filepath: Ruta del archivo
            format: Formato (se detecta automáticamente si es None)
        
        Returns:
            Datos deserializados
        """
        def _load():
            filepath_obj = Path(filepath)
            if not filepath_obj.exists():
                raise FileNotFoundError(f"Archivo no encontrado: {filepath}")
            
            with open(filepath_obj, 'rb') as f:
                data = f.read()
            
            return self.deserialize(data, format)
        
        result, error = safe_execute(_load, default_value=None, log_errors=True)
        return result
    
    def _create_metadata(
        self,
        format: str,
        data: bytes
    ) -> Dict[str, Any]:
        """Crea metadatos de serialización."""
        checksum = hashlib.sha256(data).hexdigest()
        
        return {
            'version': self.CURRENT_VERSION,
            'timestamp': datetime.now().isoformat(),
            'format': format,
            'compressed': self.compress,
            'checksum': checksum
        }
    
    def _add_metadata(
        self,
        data: bytes,
        metadata: Dict[str, Any]
    ) -> bytes:
        """Añade metadatos a los datos serializados."""
        metadata_json = json.dumps(metadata).encode('utf-8')
        metadata_b64 = base64.b64encode(metadata_json).decode('utf-8')
        
        header = f"REDUNDANCY_SERIALIZED:{metadata_b64}:".encode('utf-8')
        return header + data
    
    def _extract_metadata(
        self,
        data: bytes
    ) -> Tuple[bytes, Optional[Dict[str, Any]]]:
        """Extrae metadatos de los datos serializados."""
        try:
            header_prefix = b"REDUNDANCY_SERIALIZED:"
            if not data.startswith(header_prefix):
                return data, None
            
            header_end = data.find(b":", len(header_prefix))
            if header_end == -1:
                return data, None
            
            metadata_b64 = data[len(header_prefix):header_end].decode('utf-8')
            metadata_json = base64.b64decode(metadata_b64).decode('utf-8')
            metadata = json.loads(metadata_json)
            
            actual_data = data[header_end + 1:]
            return actual_data, metadata
        except Exception:
            return data, None
    
    def _detect_format(self, data: bytes) -> str:
        """Detecta el formato de los datos."""
        try:
            json.loads(data.decode('utf-8'))
            return "json"
        except:
            try:
                pickle.loads(data)
                return "pickle"
            except:
                return "binary"
    
    def _serialize_binary(self, data: Any) -> bytes:
        """Serializa a formato binario personalizado."""
        return pickle.dumps(data)
    
    def _deserialize_binary(self, data: bytes) -> Any:
        """Deserializa desde formato binario."""
        return pickle.loads(data)
    
    def _json_default(self, obj: Any) -> Any:
        """Función para serializar objetos no serializables por defecto en JSON."""
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        elif hasattr(obj, 'tolist'):  # numpy/torch arrays
            return obj.tolist()
        else:
            return str(obj)
    
    def _validate_data(self, data: Any) -> bool:
        """Valida datos deserializados."""
        if data is None:
            raise ValueError("Datos deserializados son None")
        return True


def create_serializer(
    compress: bool = True,
    include_metadata: bool = True
) -> RedundancySerializer:
    """
    Crea un serializador con configuración personalizada.
    
    Args:
        compress: Si se debe comprimir
        include_metadata: Si se debe incluir metadatos
    
    Returns:
        Instancia del serializador
    """
    return RedundancySerializer(
        compress=compress,
        include_metadata=include_metadata
    )


