#!/usr/bin/env python3
"""
Utilidades para manejo de archivos y formatos.

Incluye:
- Procesamiento de imágenes
- Procesamiento de PDFs
- Procesamiento de documentos Word/Excel
- OCR
"""

from typing import Dict, Any, Optional, List, Union, BinaryIO
from pathlib import Path
import io

try:
    from PIL import Image, ImageDraw, ImageFont
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    from PyPDF2 import PdfReader, PdfWriter
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    from openpyxl import load_workbook, Workbook
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

from .utils import setup_logger
from .error_handling import safe_execute, retry, RetryStrategy

logger = setup_logger(__name__)


def load_image(path: Union[str, Path]) -> Optional[Any]:
    """
    Carga una imagen desde un archivo.
    
    Args:
        path: Ruta al archivo de imagen
    
    Returns:
        Imagen PIL o None si hay error
    """
    if not PILLOW_AVAILABLE:
        raise ImportError("Pillow no está instalado. Instala con: pip install Pillow")
    
    def _load_image():
        return Image.open(path)
    
    result, error = safe_execute(_load_image, default_value=None, log_errors=True)
    if error:
        logger.error("Error cargando imagen", path=str(path), error=str(error))
    return result


def resize_image(image: Any, size: tuple, maintain_aspect: bool = True) -> Optional[Any]:
    """
    Redimensiona una imagen.
    
    Args:
        image: Imagen PIL
        size: Tamaño objetivo (width, height)
        maintain_aspect: Si True, mantiene la relación de aspecto
    
    Returns:
        Imagen redimensionada
    """
    if not PILLOW_AVAILABLE:
        raise ImportError("Pillow no está instalado")
    
    if maintain_aspect:
        image.thumbnail(size, Image.Resampling.LANCZOS)
        return image
    else:
        return image.resize(size, Image.Resampling.LANCZOS)


def extract_text_from_image(image_path: Union[str, Path]) -> Optional[str]:
    """
    Extrae texto de una imagen usando OCR.
    
    Args:
        image_path: Ruta a la imagen
    
    Returns:
        Texto extraído o None
    """
    if not TESSERACT_AVAILABLE:
        logger.warning("pytesseract no disponible, no se puede hacer OCR")
        return None
    
    def _extract_text():
        image = load_image(image_path)
        if image is None:
            return None
        return pytesseract.image_to_string(image)
    
    @retry(
        max_attempts=2,
        delay=0.5,
        strategy=RetryStrategy.FIXED_DELAY,
        exceptions=(Exception,)
    )
    def _extract_with_retry():
        return _extract_text()
    
    result, error = safe_execute(_extract_with_retry, default_value=None, log_errors=True)
    if error:
        logger.error("Error en OCR", path=str(image_path), error=str(error))
    return result


def extract_text_from_pdf(pdf_path: Union[str, Path]) -> Optional[str]:
    """
    Extrae texto de un PDF.
    
    Args:
        pdf_path: Ruta al PDF
    
    Returns:
        Texto extraído o None
    """
    if PYMUPDF_AVAILABLE:
        def _extract_pymupdf():
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        
        result, error = safe_execute(_extract_pymupdf, default_value=None, log_errors=True)
        if result:
            return result
        if error:
            logger.error("Error extrayendo texto de PDF (PyMuPDF)", path=str(pdf_path), error=str(error))
    
    if PYPDF2_AVAILABLE:
        def _extract_pypdf2():
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
        
        result, error = safe_execute(_extract_pypdf2, default_value=None, log_errors=True)
        if result:
            return result
        if error:
            logger.error("Error extrayendo texto de PDF (PyPDF2)", path=str(pdf_path), error=str(error))
    
    logger.warning("PyMuPDF o PyPDF2 no disponibles o fallaron")
    return None


def read_excel_file(excel_path: Union[str, Path], sheet_name: Optional[str] = None) -> Optional[Any]:
    """
    Lee un archivo Excel.
    
    Args:
        excel_path: Ruta al archivo Excel
        sheet_name: Nombre de la hoja (opcional)
    
    Returns:
        DataFrame de pandas o None
    """
    if not OPENPYXL_AVAILABLE:
        try:
            import pandas as pd
            return pd.read_excel(excel_path, sheet_name=sheet_name)
        except ImportError:
            raise ImportError("openpyxl o pandas no están instalados")
    
    def _read_excel():
        import pandas as pd
        return pd.read_excel(excel_path, sheet_name=sheet_name, engine='openpyxl')
    
    result, error = safe_execute(_read_excel, default_value=None, log_errors=True)
    if error:
        logger.error("Error leyendo Excel", path=str(excel_path), error=str(error))
    return result


def read_word_file(word_path: Union[str, Path]) -> Optional[str]:
    """
    Lee un archivo Word y extrae el texto.
    
    Args:
        word_path: Ruta al archivo Word
    
    Returns:
        Texto extraído o None
    """
    if not DOCX_AVAILABLE:
        logger.warning("python-docx no disponible")
        return None
    
    def _read_word():
        doc = Document(word_path)
        text = []
        for paragraph in doc.paragraphs:
            text.append(paragraph.text)
        return '\n'.join(text)
    
    result, error = safe_execute(_read_word, default_value=None, log_errors=True)
    if error:
        logger.error("Error leyendo Word", path=str(word_path), error=str(error))
    return result

