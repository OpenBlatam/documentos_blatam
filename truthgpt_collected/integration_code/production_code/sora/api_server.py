#!/usr/bin/env python3
"""
Sora API Server - REST API para Generación de Video
====================================================

API REST completa para el módulo Sora usando FastAPI.
"""

import torch
import base64
import io
from typing import Optional, Dict, Any, List
from pathlib import Path
import tempfile
import shutil

try:
    from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse, FileResponse
    from pydantic import BaseModel, Field
    import uvicorn
    from contextlib import asynccontextmanager
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

from sora import (
    TextToVideoConfig,
    TextToVideoModule,
    ImageToVideoConfig,
    ImageToVideoModule,
    VideoToVideoConfig,
    VideoToVideoModule,
    save_video_opencv,
    create_video_gif,
    video_to_numpy,
    normalize_video,
)
from sora.rate_limiter import RateLimiter, APIMetrics
from core.api_utils import create_fastapi_app
from core.utils import setup_logger

logger = setup_logger(__name__)

try:
    from sora.video_cache import VideoCache
    VIDEO_CACHE_AVAILABLE = True
except ImportError:
    VIDEO_CACHE_AVAILABLE = False
    VideoCache = None

try:
    from sora.batch_processing import BatchProcessor
    BATCH_PROCESSING_AVAILABLE = True
except ImportError:
    BATCH_PROCESSING_AVAILABLE = False
    BatchProcessor = None

try:
    from sora.async_queue import AsyncVideoQueue, TaskStatus
    ASYNC_QUEUE_AVAILABLE = True
except ImportError:
    ASYNC_QUEUE_AVAILABLE = False
    AsyncVideoQueue = None
    TaskStatus = None


if FASTAPI_AVAILABLE:
    class TextToVideoRequest(BaseModel):
        """Request para generación de video desde texto."""
        prompt: str = Field(..., description="Descripción del video a generar")
        num_inference_steps: Optional[int] = Field(50, ge=1, le=1000, description="Pasos de inferencia")
        seed: Optional[int] = Field(None, description="Semilla para reproducibilidad")
        hidden_dim: Optional[int] = Field(512, ge=64, le=2048)
        video_length: Optional[int] = Field(16, ge=1, le=1024)
        resolution: Optional[List[int]] = Field([256, 256], description="[height, width]")
        fps: Optional[int] = Field(24, ge=1, le=120)
    
    class ImageToVideoRequest(BaseModel):
        """Request para animación de imagen."""
        motion_strength: Optional[float] = Field(0.5, ge=0.0, le=1.0)
        num_inference_steps: Optional[int] = Field(50, ge=1, le=1000)
        seed: Optional[int] = None
        hidden_dim: Optional[int] = Field(512, ge=64, le=2048)
        video_length: Optional[int] = Field(16, ge=1, le=1024)
        resolution: Optional[List[int]] = Field([256, 256])
        fps: Optional[int] = Field(24, ge=1, le=120)
    
    class VideoToVideoRequest(BaseModel):
        """Request para transformación de video."""
        style_strength: Optional[float] = Field(0.5, ge=0.0, le=1.0)
        enhancement_mode: Optional[str] = Field("denoise", description="denoise, upscale, colorize")
        temporal_consistency: Optional[float] = Field(0.8, ge=0.0, le=1.0)
        num_inference_steps: Optional[int] = Field(50, ge=1, le=1000)
        seed: Optional[int] = None
    
    class VideoResponse(BaseModel):
        """Response con información del video generado."""
        video_id: str
        status: str
        metadata: Dict[str, Any]
        download_url: Optional[str] = None


class SoraAPIServer:
    """Servidor API para módulo Sora."""
    
    def __init__(self, models_dir: Optional[Path] = None):
        """
        Inicializa el servidor API.
        
        Args:
            models_dir: Directorio para guardar modelos y videos generados
        """
        if not FASTAPI_AVAILABLE:
            raise ImportError("FastAPI requerido. Instala con: pip install fastapi uvicorn")
        
        self.models_dir = models_dir or Path(tempfile.mkdtemp(prefix="sora_api_"))
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        self.videos_dir = self.models_dir / "videos"
        self.videos_dir.mkdir(exist_ok=True)
        
        self.models: Dict[str, Any] = {}
        self.rate_limiter = RateLimiter(
            requests_per_minute=60,
            requests_per_hour=1000,
            requests_per_day=10000
        )
        self.metrics = APIMetrics()
        
        if VIDEO_CACHE_AVAILABLE:
            self.video_cache = VideoCache(
                max_size=100,
                ttl_seconds=3600,
                cache_dir=self.models_dir / "cache"
            )
        else:
            self.video_cache = None
        
        if BATCH_PROCESSING_AVAILABLE:
            self.batch_processor = BatchProcessor(max_workers=4, use_parallel=True)
        else:
            self.batch_processor = None
        
        if ASYNC_QUEUE_AVAILABLE:
            self.async_queue = AsyncVideoQueue(max_workers=2, max_queue_size=100)
            self._setup_async_queue_processors()
        else:
            self.async_queue = None
        
        self.app = create_fastapi_app(
            title="Sora Video Generation API",
            version="1.6.0",
            enable_cors=True
        )
        
        self._setup_routes()
    
    def _setup_async_queue_processors(self):
        """Configura procesadores para la cola asíncrona."""
        if not self.async_queue:
            return
        
        async def text_to_video_processor(payload: Dict[str, Any]) -> Dict[str, Any]:
            """Procesador async para text-to-video."""
            import torch
            from sora import TextToVideoConfig, TextToVideoModule, save_video_opencv
            
            prompt = payload['prompt']
            config_dict = payload.get('config', {})
            num_inference_steps = payload.get('num_inference_steps', 50)
            seed = payload.get('seed')
            
            config = TextToVideoConfig(**config_dict)
            model_key = f"text2video_{config.hidden_dim}_{config.video_length}"
            
            if model_key not in self.models:
                self.models[model_key] = TextToVideoModule(config)
                self.models[model_key].eval()
            
            model = self.models[model_key]
            
            with torch.no_grad():
                video, metadata = model.generate_from_text(
                    prompt,
                    num_inference_steps=num_inference_steps,
                    seed=seed
                )
            
            video_id = f"text2video_{torch.randint(0, 1000000, (1,)).item()}"
            video_path = self.videos_dir / f"{video_id}.mp4"
            save_video_opencv(video, str(video_path), fps=config.fps)
            
            return {
                'video_id': video_id,
                'video_path': str(video_path),
                'metadata': metadata,
                'download_url': f"/api/v1/videos/{video_id}"
            }
        
        self.async_queue.register_processor("text_to_video", text_to_video_processor)
    
    def _setup_routes(self):
        """Configura las rutas de la API."""
        
        @self.app.get("/")
        async def root():
            """Endpoint raíz."""
            return {
                "name": "Sora Video Generation API",
                "version": "1.3.0",
                "endpoints": {
                    "text_to_video": "/api/v1/text-to-video",
                    "text_to_video_batch": "/api/v1/text-to-video/batch",
                    "text_to_video_async": "/api/v1/text-to-video/async",
                    "image_to_video": "/api/v1/image-to-video",
                    "video_to_video": "/api/v1/video-to-video",
                    "health": "/health",
                    "models": "/api/v1/models",
                    "tasks": "/api/v1/tasks/{task_id}",
                    "cache_stats": "/api/v1/cache/stats",
                    "queue_stats": "/api/v1/queue/stats"
                }
            }
        
        @self.app.get("/health")
        async def health():
            """Health check."""
            return {"status": "healthy", "models_loaded": len(self.models)}
        
        @self.app.post("/api/v1/text-to-video", response_model=VideoResponse)
        async def text_to_video(request: TextToVideoRequest):
            """Genera video desde texto."""
            import time
            start_time = time.time()
            
            # Rate limiting
            allowed, error_msg = self.rate_limiter.is_allowed()
            if not allowed:
                self.metrics.record_request(success=False)
                raise HTTPException(status_code=429, detail=error_msg)
            
            # Verificar caché
            if self.video_cache:
                cache_key_data = {
                    'prompt': request.prompt,
                    'config': {
                        'hidden_dim': request.hidden_dim,
                        'video_length': request.video_length,
                        'resolution': request.resolution,
                        'fps': request.fps
                    },
                    'seed': request.seed
                }
                cached_result = self.video_cache.get(**cache_key_data)
                if cached_result:
                    video_path, metadata = cached_result
                    video_id = video_path.stem
                    self.metrics.record_request(success=True)
                    return VideoResponse(
                        video_id=video_id,
                        status="completed",
                        metadata={**metadata, 'cached': True},
                        download_url=f"/api/v1/videos/{video_id}"
                    )
            
            try:
                config = TextToVideoConfig(
                    hidden_dim=request.hidden_dim,
                    video_length=request.video_length,
                    resolution=tuple(request.resolution),
                    fps=request.fps
                )
                
                model_key = f"text2video_{config.hidden_dim}_{config.video_length}"
                if model_key not in self.models:
                    self.models[model_key] = TextToVideoModule(config)
                    self.models[model_key].eval()
                
                model = self.models[model_key]
                
                with torch.no_grad():
                    video, metadata = model.generate_from_text(
                        request.prompt,
                        num_inference_steps=request.num_inference_steps,
                        seed=request.seed
                    )
                
                video_id = f"text2video_{torch.randint(0, 1000000, (1,)).item()}"
                video_path = self.videos_dir / f"{video_id}.mp4"
                
                save_video_opencv(video, str(video_path), fps=config.fps)
                
                # Guardar en caché
                if self.video_cache:
                    self.video_cache.set(
                        video_path=video_path,
                        metadata=metadata,
                        prompt=request.prompt,
                        config={
                            'hidden_dim': config.hidden_dim,
                            'video_length': config.video_length,
                            'resolution': config.resolution,
                            'fps': config.fps
                        },
                        seed=request.seed
                    )
                
                generation_time = time.time() - start_time
                self.metrics.record_request(generation_time=generation_time, success=True)
                
                return VideoResponse(
                    video_id=video_id,
                    status="completed",
                    metadata=metadata,
                    download_url=f"/api/v1/videos/{video_id}"
                )
            except HTTPException:
                raise
            except Exception as e:
                generation_time = time.time() - start_time
                self.metrics.record_request(generation_time=generation_time, success=False)
                logger.error(f"Error en text-to-video: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/image-to-video", response_model=VideoResponse)
        async def image_to_video(
            file: UploadFile = File(...),
            motion_strength: float = 0.5,
            num_inference_steps: int = 50,
            seed: Optional[int] = None,
            hidden_dim: int = 512,
            video_length: int = 16,
            resolution: str = "[256, 256]",
            fps: int = 24
        ):
            """Anima imagen estática."""
            import time
            start_time = time.time()
            
            # Rate limiting
            allowed, error_msg = self.rate_limiter.is_allowed()
            if not allowed:
                self.metrics.record_request(success=False)
                raise HTTPException(status_code=429, detail=error_msg)
            
            try:
                import ast
                from PIL import Image
                import torchvision.transforms as transforms
                
                resolution_tuple = tuple(ast.literal_eval(resolution))
                
                config = ImageToVideoConfig(
                    hidden_dim=hidden_dim,
                    video_length=video_length,
                    resolution=resolution_tuple,
                    fps=fps,
                    motion_strength=motion_strength
                )
                
                model_key = f"image2video_{config.hidden_dim}_{config.video_length}"
                if model_key not in self.models:
                    self.models[model_key] = ImageToVideoModule(config)
                    self.models[model_key].eval()
                
                model = self.models[model_key]
                
                image_bytes = await file.read()
                image = Image.open(io.BytesIO(image_bytes))
                transform = transforms.Compose([
                    transforms.Resize(resolution_tuple),
                    transforms.ToTensor()
                ])
                image_tensor = transform(image).unsqueeze(0)
                
                with torch.no_grad():
                    video, metadata = model.animate_image(
                        image_tensor,
                        num_inference_steps=num_inference_steps,
                        motion_strength=motion_strength,
                        seed=seed
                    )
                
                video_id = f"image2video_{torch.randint(0, 1000000, (1,)).item()}"
                video_path = self.videos_dir / f"{video_id}.mp4"
                
                save_video_opencv(video, str(video_path), fps=config.fps)
                
                generation_time = time.time() - start_time
                self.metrics.record_request(generation_time=generation_time, success=True)
                
                return VideoResponse(
                    video_id=video_id,
                    status="completed",
                    metadata=metadata,
                    download_url=f"/api/v1/videos/{video_id}"
                )
            except HTTPException:
                raise
            except Exception as e:
                generation_time = time.time() - start_time
                self.metrics.record_request(generation_time=generation_time, success=False)
                logger.error(f"Error en image-to-video: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/videos/{video_id}")
        async def get_video(video_id: str):
            """Descarga video generado."""
            video_path = self.videos_dir / f"{video_id}.mp4"
            if not video_path.exists():
                raise HTTPException(status_code=404, detail="Video no encontrado")
            return FileResponse(str(video_path), media_type="video/mp4")
        
        @self.app.get("/api/v1/models")
        async def list_models():
            """Lista modelos cargados."""
            return {
                "models": list(self.models.keys()),
                "count": len(self.models)
            }
        
        @self.app.get("/api/v1/metrics")
        async def get_metrics():
            """Obtiene métricas de la API."""
            return {
                "api_metrics": self.metrics.get_stats(),
                "rate_limits": {
                    "per_minute": self.rate_limiter.requests_per_minute,
                    "per_hour": self.rate_limiter.requests_per_hour,
                    "per_day": self.rate_limiter.requests_per_day,
                },
                "remaining": self.rate_limiter.get_remaining()
            }
        
        @self.app.get("/api/v1/rate-limit")
        async def get_rate_limit():
            """Obtiene información de rate limiting."""
            return {
                "limits": {
                    "per_minute": self.rate_limiter.requests_per_minute,
                    "per_hour": self.rate_limiter.requests_per_hour,
                    "per_day": self.rate_limiter.requests_per_day,
                },
                "remaining": self.rate_limiter.get_remaining()
            }
        
        @self.app.post("/api/v1/text-to-video/batch")
        async def text_to_video_batch(prompts: List[str], request: Optional[TextToVideoRequest] = None):
            """Procesa batch de text-to-video."""
            if not self.batch_processor:
                raise HTTPException(status_code=501, detail="Batch processing no disponible")
            
            try:
                config = TextToVideoConfig(
                    hidden_dim=request.hidden_dim if request else 512,
                    video_length=request.video_length if request else 16,
                    resolution=tuple(request.resolution) if request else (256, 256),
                    fps=request.fps if request else 24
                )
                
                results = self.batch_processor.process_text_to_video_batch(
                    prompts=prompts,
                    config=config,
                    output_dir=self.videos_dir,
                    num_inference_steps=request.num_inference_steps if request else 50
                )
                
                return {
                    "total": len(results),
                    "successful": len([r for r in results if 'error' not in r]),
                    "failed": len([r for r in results if 'error' in r]),
                    "results": results
                }
            except Exception as e:
                logger.error(f"Error en batch processing: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/text-to-video/async")
        async def text_to_video_async(request: TextToVideoRequest):
            """Encola tarea de text-to-video de forma asíncrona."""
            if not self.async_queue:
                raise HTTPException(status_code=501, detail="Async queue no disponible")
            
            try:
                task_id = await self.async_queue.enqueue(
                    "text_to_video",
                    {
                        "prompt": request.prompt,
                        "config": {
                            "hidden_dim": request.hidden_dim,
                            "video_length": request.video_length,
                            "resolution": request.resolution,
                            "fps": request.fps
                        },
                        "num_inference_steps": request.num_inference_steps,
                        "seed": request.seed
                    },
                    priority=0
                )
                
                return {
                    "task_id": task_id,
                    "status": "pending",
                    "message": "Tarea encolada para procesamiento asíncrono"
                }
            except Exception as e:
                logger.error(f"Error encolando tarea: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/tasks/{task_id}")
        async def get_task_status(task_id: str):
            """Obtiene estado de una tarea."""
            if not self.async_queue:
                raise HTTPException(status_code=501, detail="Async queue no disponible")
            
            status = await self.async_queue.get_status(task_id)
            if not status:
                raise HTTPException(status_code=404, detail="Tarea no encontrada")
            
            return status
        
        @self.app.get("/api/v1/tasks/{task_id}/result")
        async def get_task_result(task_id: str):
            """Obtiene resultado de una tarea completada."""
            if not self.async_queue:
                raise HTTPException(status_code=501, detail="Async queue no disponible")
            
            result = await self.async_queue.get_result(task_id)
            if result is None:
                status = await self.async_queue.get_status(task_id)
                if not status:
                    raise HTTPException(status_code=404, detail="Tarea no encontrada")
                raise HTTPException(status_code=202, detail="Tarea aún en procesamiento")
            
            return result
        
        @self.app.get("/api/v1/cache/stats")
        async def get_cache_stats():
            """Obtiene estadísticas del caché."""
            if not self.video_cache:
                raise HTTPException(status_code=501, detail="Video cache no disponible")
            
            return self.video_cache.get_stats()
        
        @self.app.delete("/api/v1/cache")
        async def clear_cache():
            """Limpia el caché."""
            if not self.video_cache:
                raise HTTPException(status_code=501, detail="Video cache no disponible")
            
            self.video_cache.clear()
            return {"message": "Caché limpiado exitosamente"}
        
        @self.app.get("/api/v1/queue/stats")
        async def get_queue_stats():
            """Obtiene estadísticas de la cola."""
            if not self.async_queue:
                raise HTTPException(status_code=501, detail="Async queue no disponible")
            
            return self.async_queue.get_stats()
        
        @self.app.delete("/api/v1/models/{model_key}")
        async def unload_model(model_key: str):
            """Descarga un modelo."""
            if model_key in self.models:
                del self.models[model_key]
                return {"status": "unloaded", "model_key": model_key}
            raise HTTPException(status_code=404, detail="Modelo no encontrado")
    
    async def startup(self):
        """Inicializa recursos al iniciar el servidor."""
        if self.async_queue:
            await self.async_queue.start_async()
            logger.info("Async queue iniciada")
    
    async def shutdown(self):
        """Limpia recursos al detener el servidor."""
        if self.async_queue:
            await self.async_queue.stop()
            logger.info("Async queue detenida")
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Ejecuta el servidor."""
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            await self.startup()
            yield
            await self.shutdown()
        
        self.app.router.lifespan_context = lifespan
        uvicorn.run(self.app, host=host, port=port)


def create_app(models_dir: Optional[Path] = None) -> FastAPI:
    """
    Factory function para crear la app FastAPI.
    
    Args:
        models_dir: Directorio para modelos y videos
    
    Returns:
        Aplicación FastAPI
    """
    server = SoraAPIServer(models_dir)
    return server.app


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Sora API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host")
    parser.add_argument("--port", type=int, default=8000, help="Port")
    parser.add_argument("--models-dir", type=Path, help="Directorio para modelos")
    
    args = parser.parse_args()
    
    server = SoraAPIServer(models_dir=args.models_dir)
    server.run(host=args.host, port=args.port)

