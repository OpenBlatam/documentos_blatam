#!/usr/bin/env python3
"""
Documents Routes
================

API routes for document conversion operations.
"""

import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from core.utils import setup_logger

logger = setup_logger(__name__)

router = APIRouter()

# Try to import document converter
try:
    from document_converter_advanced import DocumentConverterAdvanced
    DOCUMENT_CONVERTER_AVAILABLE = True
except ImportError:
    DocumentConverterAdvanced = None
    DOCUMENT_CONVERTER_AVAILABLE = False


# Request Models
class DocumentConvertRequest(BaseModel):
    """Request model for document conversion."""
    data: Union[Dict[str, Any], List[Any], str] = Field(..., description="Datos a convertir")
    format: str = Field(..., description="Formato de salida: pdf, docx, xlsx")
    title: Optional[str] = Field("Documento", description="Título del documento")
    method: Optional[str] = Field("auto", description="Método específico a usar (auto para selección automática)")
    output_filename: Optional[str] = Field(None, description="Nombre del archivo de salida (sin extensión)")


class DocumentConvertMultipleRequest(BaseModel):
    """Request model for multiple format conversion."""
    data: Union[Dict[str, Any], List[Any], str] = Field(..., description="Datos a convertir")
    formats: List[str] = Field(..., description="Lista de formatos: ['pdf', 'docx', 'xlsx']")
    title: Optional[str] = Field("Documento", description="Título del documento")
    output_filename: Optional[str] = Field(None, description="Nombre base del archivo (sin extensión)")


# Helper Functions
def _prepare_data_to_file(data: Union[Dict[str, Any], List[Any], str], suffix: str = ".txt") -> Path:
    """Convierte datos a un archivo temporal."""
    import json
    temp_file = Path(tempfile.gettempdir()) / f"api_doc_{uuid4().hex}{suffix}"
    
    if isinstance(data, str):
        temp_file.write_text(data, encoding="utf-8")
    elif isinstance(data, (dict, list)):
        # Convertir a JSON o texto estructurado
        if suffix == ".json":
            temp_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        else:
            # Convertir a texto legible
            text_content = json.dumps(data, indent=2, ensure_ascii=False) if isinstance(data, dict) else "\n".join(str(item) for item in data)
            temp_file.write_text(text_content, encoding="utf-8")
    else:
        temp_file.write_text(str(data), encoding="utf-8")
    
    return temp_file


def _get_document_converter() -> "DocumentConverterAdvanced":
    """
    Get document converter instance.
    
    Returns:
        DocumentConverterAdvanced instance
    
    Raises:
        HTTPException: If document converter is not available
    """
    if not DOCUMENT_CONVERTER_AVAILABLE or DocumentConverterAdvanced is None:
        raise HTTPException(status_code=503, detail="Document converter not available")
    return DocumentConverterAdvanced(output_dir=tempfile.gettempdir())


def handle_api_error(operation_name: str, error: Exception, req: Optional[Request] = None) -> HTTPException:
    """
    Helper para manejar errores de API de manera consistente.
    
    Args:
        operation_name: Nombre de la operación que falló
        error: Excepción capturada
        req: Optional FastAPI request object para obtener request_id
    
    Returns:
        HTTPException con código 500 y mensaje de error
    """
    request_id = getattr(req.state, 'request_id', None) if req else None
    logger.error(
        f"Error en {operation_name}: {error}",
        exc_info=True,
        request_id=request_id
    )
    return HTTPException(status_code=500, detail=f"Error {operation_name}: {str(error)}")


# Routes
@router.post("/convert")
async def convert_document(
    request: DocumentConvertRequest,
    req: Request
):
    """
    Convert data to PDF, Word, or Excel format.
    
    Converts various input data formats (text, JSON, HTML, Markdown) to
    professional document formats. Supports multiple conversion methods
    and automatic format detection.
    
    Args:
        request: DocumentConvertRequest containing:
            - data: Data to convert (dict, list, or string)
            - format: Output format ("pdf", "docx", "xlsx", "word", "excel")
            - title: Optional document title (default: "Documento")
            - method: Optional conversion method ("auto" for automatic selection)
            - output_filename: Optional output filename without extension
        req: FastAPI request object for accessing request state
    
    Returns:
        FileResponse with converted document
    
    Raises:
        HTTPException:
            - 400: If format is invalid or data is empty
            - 503: If document converter is not available
            - 500: If conversion fails
    
    Example:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/v1/documents/convert",
        ...     json={
        ...         "data": {"title": "Test", "content": "Hello World"},
        ...         "format": "pdf",
        ...         "title": "Test Document"
        ...     }
        ... )
        >>> response.headers["content-type"]
        "application/pdf"
    """
    temp_input_file = None
    try:
        # Validar formato
        valid_formats = ['pdf', 'docx', 'xlsx', 'word', 'excel']
        format_lower = request.format.lower()
        if format_lower == 'word':
            format_lower = 'docx'
        elif format_lower == 'excel':
            format_lower = 'xlsx'
        
        if format_lower not in ['pdf', 'docx', 'xlsx']:
            raise HTTPException(
                status_code=400,
                detail=f"Formato inválido: {request.format}. Formatos válidos: pdf, docx, xlsx"
            )
        
        # Preparar archivo temporal de entrada
        input_suffix = ".txt"  # Por defecto texto plano
        if isinstance(request.data, dict):
            input_suffix = ".json"
        elif isinstance(request.data, str) and request.data.strip().startswith('<'):
            input_suffix = ".html"
        elif isinstance(request.data, str) and request.data.strip().startswith('#'):
            input_suffix = ".md"
        
        temp_input_file = _prepare_data_to_file(request.data, input_suffix)
        
        # Generar nombre de archivo de salida
        if request.output_filename:
            base_filename = request.output_filename
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"document_{timestamp}"
        
        temp_dir = tempfile.mkdtemp()
        output_path = str(Path(temp_dir) / f"{base_filename}.{format_lower}")
        
        # Obtener convertidor
        converter = _get_document_converter()
        
        # Convertir según formato
        result = None
        if format_lower == 'pdf':
            result = converter.convert_to_pdf(
                str(temp_input_file),
                output_path,
                method=request.method if request.method != "auto" else None
            )
        elif format_lower == 'docx':
            result = converter.convert_to_word(
                str(temp_input_file),
                output_path,
                style='professional'
            )
        elif format_lower == 'xlsx':
            result = converter.convert_to_excel(
                str(temp_input_file),
                output_path,
                style='professional'
            )
        
        if result and Path(result).exists():
            media_types = {
                'pdf': 'application/pdf',
                'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
            return FileResponse(
                result,
                media_type=media_types.get(format_lower, 'application/octet-stream'),
                filename=f"{base_filename}.{format_lower}"
            )
        else:
            raise HTTPException(status_code=500, detail="Error en la conversión: no se generó el archivo")
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        # Validation errors - return 400 with clear message
        logger.warning(f"Validation error in convert_document: {e}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        # Unexpected errors - log and return 500
        raise handle_api_error("convirtiendo documento", e, req)
    finally:
        # Limpiar archivo temporal de entrada
        if temp_input_file and temp_input_file.exists():
            try:
                temp_input_file.unlink()
            except Exception:
                pass


@router.post("/convert-multiple")
async def convert_document_multiple(
    request: DocumentConvertMultipleRequest,
    req: Request
):
    """
    Convert data to multiple formats simultaneously.
    
    Converts input data to multiple output formats in a single request,
    returning all converted files as a ZIP archive. Useful for generating
    documents in multiple formats at once.
    
    Args:
        request: DocumentConvertMultipleRequest containing:
            - data: Data to convert (dict, list, or string)
            - formats: List of output formats (e.g., ["pdf", "docx", "xlsx"])
            - title: Optional document title (default: "Documento")
            - output_filename: Optional base filename without extension
        req: FastAPI request object for accessing request state
    
    Returns:
        FileResponse with ZIP archive containing all converted documents
    
    Raises:
        HTTPException:
            - 400: If formats are invalid, empty, or data is invalid
            - 503: If document converter is not available
            - 500: If conversion fails for all formats
    
    Example:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/v1/documents/convert-multiple",
        ...     json={
        ...         "data": "Hello World",
        ...         "formats": ["pdf", "docx", "xlsx"]
        ...     }
        ... )
        >>> response.headers["content-type"]
        "application/zip"
    """
    temp_input_file = None
    try:
        # Normalizar formatos
        normalized_formats = []
        format_map = {'word': 'docx', 'excel': 'xlsx'}
        valid_formats = ['pdf', 'docx', 'xlsx']
        
        for fmt in request.formats:
            fmt_lower = fmt.lower()
            if fmt_lower in format_map:
                fmt_lower = format_map[fmt_lower]
            if fmt_lower not in valid_formats:
                raise HTTPException(
                    status_code=400,
                    detail=f"Formato inválido: {fmt}. Formatos válidos: {valid_formats}"
                )
            if fmt_lower not in normalized_formats:
                normalized_formats.append(fmt_lower)
        
        if not normalized_formats:
            raise HTTPException(status_code=400, detail="Debe especificar al menos un formato")
        
        # Preparar archivo temporal de entrada
        input_suffix = ".txt"
        if isinstance(request.data, dict):
            input_suffix = ".json"
        elif isinstance(request.data, str) and request.data.strip().startswith('<'):
            input_suffix = ".html"
        elif isinstance(request.data, str) and request.data.strip().startswith('#'):
            input_suffix = ".md"
        
        temp_input_file = _prepare_data_to_file(request.data, input_suffix)
        
        # Generar nombre base
        if request.output_filename:
            base_filename = request.output_filename
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"document_{timestamp}"
        
        # Crear directorio temporal
        temp_dir = Path(tempfile.mkdtemp())
        results = {}
        
        # Obtener convertidor
        converter = _get_document_converter()
        
        # Convertir a cada formato
        for fmt in normalized_formats:
            try:
                output_path = str(temp_dir / f"{base_filename}.{fmt}")
                result = None
                
                if fmt == 'pdf':
                    result = converter.convert_to_pdf(str(temp_input_file), output_path)
                elif fmt == 'docx':
                    result = converter.convert_to_word(str(temp_input_file), output_path, style='professional')
                elif fmt == 'xlsx':
                    result = converter.convert_to_excel(str(temp_input_file), output_path, style='professional')
                
                if result and Path(result).exists():
                    results[fmt] = result
            except Exception as e:
                logger.warning(f"Error convirtiendo a {fmt}: {e}")
                results[fmt] = None
        
        if not any(results.values()):
            raise HTTPException(status_code=500, detail="No se pudo convertir a ningún formato")
        
        # Crear ZIP con todos los archivos
        zip_path = str(temp_dir / f"{base_filename}.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for fmt, file_path in results.items():
                if file_path and Path(file_path).exists():
                    zipf.write(file_path, f"{base_filename}.{fmt}")
        
        return FileResponse(
            zip_path,
            media_type="application/zip",
            filename=f"{base_filename}.zip"
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        # Validation errors - return 400 with clear message
        logger.warning(f"Validation error in convert_document_multiple: {e}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        # Unexpected errors - log and return 500
        raise handle_api_error("convirtiendo documentos múltiples", e, req)
    finally:
        if temp_input_file and temp_input_file.exists():
            try:
                temp_input_file.unlink()
            except Exception:
                pass


@router.post("/convert-file")
async def convert_file(
    file: UploadFile = File(...),
    format: str = Form(...),
    method: Optional[str] = Form("auto"),
    req: Request = None
):
    """
    Convert an uploaded file to another format.
    
    Accepts a file upload and converts it to the specified output format.
    Supports conversion from various input formats to PDF, Word, or Excel.
    
    Args:
        file: Uploaded file to convert
        format: Output format ("pdf", "docx", "xlsx", "word", "excel")
        method: Optional conversion method ("auto" for automatic selection)
        req: FastAPI request object for accessing request state
    
    Returns:
        FileResponse with converted document
    
    Raises:
        HTTPException:
            - 400: If format is invalid or file is empty
            - 413: If file is too large
            - 503: If document converter is not available
            - 500: If conversion fails
    
    Example:
        >>> import requests
        >>> with open("document.txt", "rb") as f:
        ...     response = requests.post(
        ...         "http://localhost:8000/api/v1/documents/convert-file",
        ...         files={"file": f},
        ...         data={"format": "pdf"}
        ...     )
        >>> response.headers["content-type"]
        "application/pdf"
    """
    temp_input_file = None
    try:
        # Validar formato de salida
        format_lower = format.lower()
        format_map = {'word': 'docx', 'excel': 'xlsx'}
        if format_lower in format_map:
            format_lower = format_map[format_lower]
        
        if format_lower not in ['pdf', 'docx', 'xlsx']:
            raise HTTPException(
                status_code=400,
                detail=f"Formato inválido: {format}. Formatos válidos: pdf, docx, xlsx"
            )
        
        # Guardar archivo subido temporalmente
        file_ext = Path(file.filename).suffix if file.filename else ".txt"
        temp_input_file = Path(tempfile.gettempdir()) / f"upload_{uuid4().hex}{file_ext}"
        with open(temp_input_file, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        # Generar nombre de salida
        base_filename = Path(file.filename).stem if file.filename else f"converted_{uuid4().hex}"
        temp_dir = Path(tempfile.mkdtemp())
        output_path = str(temp_dir / f"{base_filename}.{format_lower}")
        
        # Obtener convertidor
        converter = _get_document_converter()
        
        # Convertir
        result = None
        if format_lower == 'pdf':
            result = converter.convert_to_pdf(
                str(temp_input_file),
                output_path,
                method=method if method != "auto" else None
            )
        elif format_lower == 'docx':
            result = converter.convert_to_word(
                str(temp_input_file),
                output_path,
                style='professional'
            )
        elif format_lower == 'xlsx':
            result = converter.convert_to_excel(
                str(temp_input_file),
                output_path,
                style='professional'
            )
        
        if result and Path(result).exists():
            media_types = {
                'pdf': 'application/pdf',
                'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
            return FileResponse(
                result,
                media_type=media_types.get(format_lower, 'application/octet-stream'),
                filename=f"{base_filename}.{format_lower}"
            )
        else:
            raise HTTPException(status_code=500, detail="Error en la conversión")
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        # Validation errors - return 400 with clear message
        logger.warning(f"Validation error in convert_file: {e}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        # Unexpected errors - log and return 500
        raise handle_api_error("convirtiendo archivo", e, req)
    finally:
        if temp_input_file and temp_input_file.exists():
            try:
                temp_input_file.unlink()
            except Exception:
                pass


@router.get("/libraries")
async def get_available_libraries(req: Optional[Request] = None) -> Dict[str, Any]:
    """
    Get information about available document conversion libraries.
    
    Args:
        req: Optional FastAPI request object
    
    Returns:
        Dictionary with available libraries organized by category (PDF, Word, Excel)
        and summary information
    
    Raises:
        HTTPException: If document converter is not available or an error occurs
    """
    try:
        converter = _get_document_converter()
        libraries = converter.available_libraries
        
        # Organizar por categoría
        pdf_libs = {k: v for k, v in libraries.items() if k in [
            'reportlab', 'fpdf', 'weasyprint', 'pdfkit', 'pypdf', 'PyMuPDF', 
            'xhtml2pdf', 'docx2pdf'
        ]}
        word_libs = {k: v for k, v in libraries.items() if k in [
            'python-docx', 'mammoth'
        ]}
        excel_libs = {k: v for k, v in libraries.items() if k in [
            'openpyxl', 'xlsxwriter', 'pandas', 'xlrd', 'xlwt', 'pyexcel'
        ]}
        
        return {
            "pdf": pdf_libs,
            "word": word_libs,
            "excel": excel_libs,
            "summary": {
                "pdf_available": sum(1 for v in pdf_libs.values() if v),
                "word_available": sum(1 for v in word_libs.values() if v),
                "excel_available": sum(1 for v in excel_libs.values() if v),
                "total_available": sum(1 for v in libraries.values() if v)
            },
            "requirements": converter.get_requirements() if hasattr(converter, 'get_requirements') else []
        }
    except HTTPException:
        raise
    except Exception as e:
        raise handle_api_error("obteniendo librerías", e)


@router.get("/formats")
async def get_supported_formats(req: Optional[Request] = None) -> Dict[str, Any]:
    """
    Get information about supported input and output formats.
    
    Returns comprehensive information about all supported file formats,
    conversion methods, and conversion matrix showing which conversions
    are possible.
    
    Args:
        req: Optional FastAPI request object
    
    Returns:
        Dictionary containing:
            - input_formats: Supported input formats organized by type
            - output_formats: Supported output formats with methods and descriptions
            - conversion_matrix: Matrix showing possible conversions
    
    Example:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/v1/documents/formats")
        >>> formats = response.json()
        >>> formats["output_formats"]["pdf"]["methods"]
        ["reportlab", "fpdf", "weasyprint", ...]
    """
    return {
        "input_formats": {
            "text": [".txt", ".md", ".html"],
            "structured": [".json"],
            "documents": [".docx", ".pdf", ".xlsx", ".xls"]
        },
        "output_formats": {
            "pdf": {
                "extensions": [".pdf"],
                "methods": ["reportlab", "fpdf", "weasyprint", "pdfkit", "pypdf", "PyMuPDF", "xhtml2pdf", "docx2pdf", "libreoffice"],
                "description": "Portable Document Format"
            },
            "docx": {
                "extensions": [".docx"],
                "methods": ["python-docx"],
                "description": "Microsoft Word Document",
                "styles": ["simple", "professional", "premium"]
            },
            "xlsx": {
                "extensions": [".xlsx"],
                "methods": ["openpyxl", "xlsxwriter", "pandas"],
                "description": "Microsoft Excel Spreadsheet",
                "styles": ["simple", "professional", "premium"]
            }
        },
        "conversion_matrix": {
            "text -> pdf": True,
            "text -> docx": True,
            "text -> xlsx": True,
            "json -> pdf": True,
            "json -> docx": True,
            "json -> xlsx": True,
            "html -> pdf": True,
            "html -> docx": True,
            "markdown -> pdf": True,
            "markdown -> docx": True,
            "docx -> pdf": True,
            "xlsx -> pdf": True
        }
    }

