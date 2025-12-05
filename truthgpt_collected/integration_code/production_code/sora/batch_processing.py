#!/usr/bin/env python3
"""
Batch Processing - Procesamiento en Lote
=========================================

Utilidades para procesar múltiples videos en batch.
"""

import torch
from typing import List, Dict, Any, Optional, Callable, Union
from pathlib import Path
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from sora import (
    TextToVideoModule,
    TextToVideoConfig,
    ImageToVideoModule,
    ImageToVideoConfig,
    save_video_opencv
)
from core.utils import setup_logger

logger = setup_logger(__name__)


class BatchProcessor:
    """
    Procesador de batch para generación de videos.
    
    Permite procesar múltiples videos en paralelo o secuencialmente.
    """
    
    def __init__(
        self,
        max_workers: int = 4,
        use_parallel: bool = True
    ):
        """
        Inicializa el procesador de batch.
        
        Args:
            max_workers: Número máximo de workers paralelos
            use_parallel: Si usar procesamiento paralelo
        """
        self.max_workers = max_workers
        self.use_parallel = use_parallel
    
    def process_text_to_video_batch(
        self,
        prompts: List[str],
        config: TextToVideoConfig,
        output_dir: Optional[Path] = None,
        num_inference_steps: int = 50,
        seeds: Optional[List[int]] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Procesa un batch de text-to-video.
        
        Args:
            prompts: Lista de prompts
            config: Configuración del modelo
            output_dir: Directorio de salida
            num_inference_steps: Pasos de inferencia
            seeds: Lista de semillas (opcional)
            progress_callback: Callback de progreso (current, total, prompt)
        
        Returns:
            Lista de resultados con video_path y metadata
        """
        model = TextToVideoModule(config)
        model.eval()
        
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
        
        results = []
        
        if self.use_parallel and self.max_workers > 1:
            results = self._process_parallel(
                prompts=prompts,
                model=model,
                config=config,
                output_dir=output_dir,
                num_inference_steps=num_inference_steps,
                seeds=seeds,
                progress_callback=progress_callback,
                generation_func=self._generate_text_to_video
            )
        else:
            results = self._process_sequential(
                prompts=prompts,
                model=model,
                config=config,
                output_dir=output_dir,
                num_inference_steps=num_inference_steps,
                seeds=seeds,
                progress_callback=progress_callback,
                generation_func=self._generate_text_to_video
            )
        
        return results
    
    def process_image_to_video_batch(
        self,
        image_paths: List[Union[str, Path]],
        config: ImageToVideoConfig,
        output_dir: Optional[Path] = None,
        num_inference_steps: int = 50,
        motion_strengths: Optional[List[float]] = None,
        seeds: Optional[List[int]] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Procesa un batch de image-to-video.
        
        Args:
            image_paths: Lista de paths a imágenes
            config: Configuración del modelo
            output_dir: Directorio de salida
            num_inference_steps: Pasos de inferencia
            motion_strengths: Lista de motion strengths
            seeds: Lista de semillas
            progress_callback: Callback de progreso
        
        Returns:
            Lista de resultados
        """
        from PIL import Image
        import torchvision.transforms as transforms
        
        model = ImageToVideoModule(config)
        model.eval()
        
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # Cargar imágenes
        images = []
        for img_path in image_paths:
            image = Image.open(img_path)
            transform = transforms.Compose([
                transforms.Resize(config.resolution),
                transforms.ToTensor()
            ])
            images.append(transform(image).unsqueeze(0))
        
        if self.use_parallel and self.max_workers > 1:
            results = self._process_parallel(
                prompts=image_paths,
                model=model,
                config=config,
                output_dir=output_dir,
                num_inference_steps=num_inference_steps,
                seeds=seeds,
                progress_callback=progress_callback,
                generation_func=lambda m, p, c, s, o, n: self._generate_image_to_video(
                    m, images[image_paths.index(p)], c, s, o, n, 
                    motion_strengths[image_paths.index(p)] if motion_strengths else 0.5
                )
            )
        else:
            results = []
            for i, (img_path, image_tensor) in enumerate(zip(image_paths, images)):
                if progress_callback:
                    progress_callback(i + 1, len(image_paths), str(img_path))
                
                result = self._generate_image_to_video(
                    model, image_tensor, config,
                    seeds[i] if seeds else None,
                    output_dir, num_inference_steps,
                    motion_strengths[i] if motion_strengths else 0.5
                )
                results.append(result)
        
        return results
    
    def _generate_text_to_video(
        self,
        model: TextToVideoModule,
        prompt: str,
        config: TextToVideoConfig,
        seed: Optional[int],
        output_dir: Optional[Path],
        num_inference_steps: int
    ) -> Dict[str, Any]:
        """Genera un video desde texto."""
        with torch.no_grad():
            video, metadata = model.generate_from_text(
                prompt,
                num_inference_steps=num_inference_steps,
                seed=seed
            )
        
        video_path = None
        if output_dir:
            video_filename = f"video_{hash(prompt) % 1000000}.mp4"
            video_path = output_dir / video_filename
            save_video_opencv(video, str(video_path), fps=config.fps)
        
        return {
            'prompt': prompt,
            'video_path': video_path,
            'video': video,
            'metadata': metadata
        }
    
    def _generate_image_to_video(
        self,
        model: ImageToVideoModule,
        image: torch.Tensor,
        config: ImageToVideoConfig,
        seed: Optional[int],
        output_dir: Optional[Path],
        num_inference_steps: int,
        motion_strength: float = 0.5
    ) -> Dict[str, Any]:
        """Genera video desde imagen."""
        with torch.no_grad():
            video, metadata = model.animate_image(
                image,
                num_inference_steps=num_inference_steps,
                motion_strength=motion_strength,
                seed=seed
            )
        
        video_path = None
        if output_dir:
            video_filename = f"video_{hash(str(image.shape)) % 1000000}.mp4"
            video_path = output_dir / video_filename
            save_video_opencv(video, str(video_path), fps=config.fps)
        
        return {
            'video_path': video_path,
            'video': video,
            'metadata': metadata
        }
    
    def _process_parallel(
        self,
        prompts: List[Any],
        model: Any,
        config: Any,
        output_dir: Optional[Path],
        num_inference_steps: int,
        seeds: Optional[List[int]],
        progress_callback: Optional[Callable],
        generation_func: Callable
    ) -> List[Dict[str, Any]]:
        """Procesa en paralelo."""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            
            for i, prompt in enumerate(prompts):
                future = executor.submit(
                    generation_func,
                    model,
                    prompt,
                    config,
                    seeds[i] if seeds else None,
                    output_dir,
                    num_inference_steps
                )
                futures[future] = (i, prompt)
            
            for future in as_completed(futures):
                i, prompt = futures[future]
                try:
                    result = future.result()
                    results.append((i, result))
                    
                    if progress_callback:
                        progress_callback(i + 1, len(prompts), str(prompt))
                except Exception as e:
                    logger.error(f"Error procesando {prompt}: {e}")
                    results.append((i, {'error': str(e)}))
        
        # Ordenar por índice original
        results.sort(key=lambda x: x[0])
        return [r[1] for r in results]
    
    def _process_sequential(
        self,
        prompts: List[Any],
        model: Any,
        config: Any,
        output_dir: Optional[Path],
        num_inference_steps: int,
        seeds: Optional[List[int]],
        progress_callback: Optional[Callable],
        generation_func: Callable
    ) -> List[Dict[str, Any]]:
        """Procesa secuencialmente."""
        results = []
        
        for i, prompt in enumerate(prompts):
            if progress_callback:
                progress_callback(i + 1, len(prompts), str(prompt))
            
            try:
                result = generation_func(
                    model,
                    prompt,
                    config,
                    seeds[i] if seeds else None,
                    output_dir,
                    num_inference_steps
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Error procesando {prompt}: {e}")
                results.append({'error': str(e)})
        
        return results


