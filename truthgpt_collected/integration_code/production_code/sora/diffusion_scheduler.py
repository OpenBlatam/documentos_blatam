#!/usr/bin/env python3
"""
Diffusion Scheduler - Programadores para Proceso de Difusión
============================================================

Implementa diferentes schedulers para el proceso de difusión en generación de video.
"""

import torch
import numpy as np
from typing import Optional, Union, List
from enum import Enum


class SchedulerType(str, Enum):
    """Tipos de schedulers disponibles."""
    LINEAR = "linear"
    COSINE = "cosine"
    QUADRATIC = "quadratic"
    SIGMOID = "sigmoid"
    DDPM = "ddpm"
    DDIM = "ddim"


class DiffusionScheduler:
    """
    Scheduler para proceso de difusión.
    
    Maneja la programación de noise schedule y sampling steps.
    """
    
    def __init__(
        self,
        num_train_timesteps: int = 1000,
        beta_start: float = 0.0001,
        beta_end: float = 0.02,
        scheduler_type: SchedulerType = SchedulerType.LINEAR,
        device: Optional[torch.device] = None
    ):
        self.num_train_timesteps = num_train_timesteps
        self.beta_start = beta_start
        self.beta_end = beta_end
        self.scheduler_type = scheduler_type
        self.device = device or torch.device("cpu")
        
        # Calcular betas según el tipo de scheduler
        self.betas = self._compute_betas()
        self.alphas = 1.0 - self.betas
        self.alphas_cumprod = torch.cumprod(self.alphas, dim=0)
        self.alphas_cumprod_prev = torch.cat([torch.tensor([1.0]), self.alphas_cumprod[:-1]])
        
        # Pre-calcular valores útiles
        self.sqrt_alphas_cumprod = torch.sqrt(self.alphas_cumprod)
        self.sqrt_one_minus_alphas_cumprod = torch.sqrt(1.0 - self.alphas_cumprod)
        self.posterior_variance = self.betas * (1.0 - self.alphas_cumprod_prev) / (1.0 - self.alphas_cumprod)
    
    def _compute_betas(self) -> torch.Tensor:
        """Calcula betas según el tipo de scheduler."""
        if self.scheduler_type == SchedulerType.LINEAR:
            return torch.linspace(self.beta_start, self.beta_end, self.num_train_timesteps)
        elif self.scheduler_type == SchedulerType.COSINE:
            s = 0.008
            steps = torch.arange(self.num_train_timesteps + 1, dtype=torch.float32)
            alphas_cumprod = torch.cos(((steps / self.num_train_timesteps) + s) / (1 + s) * np.pi / 2) ** 2
            alphas_cumprod = alphas_cumprod / alphas_cumprod[0]
            betas = 1 - (alphas_cumprod[1:] / alphas_cumprod[:-1])
            return torch.clip(betas, 0.0001, 0.9999)
        elif self.scheduler_type == SchedulerType.QUADRATIC:
            betas = torch.linspace(self.beta_start ** 0.5, self.beta_end ** 0.5, self.num_train_timesteps) ** 2
            return betas
        elif self.scheduler_type == SchedulerType.SIGMOID:
            betas = torch.linspace(-6, 6, self.num_train_timesteps)
            betas = torch.sigmoid(betas) * (self.beta_end - self.beta_start) + self.beta_start
            return betas
        else:
            # DDPM/DDIM - usar linear por defecto
            return torch.linspace(self.beta_start, self.beta_end, self.num_train_timesteps)
    
    def add_noise(
        self,
        original_samples: torch.Tensor,
        noise: torch.Tensor,
        timesteps: torch.Tensor
    ) -> torch.Tensor:
        """
        Agrega ruido a las muestras originales.
        
        Args:
            original_samples: Muestras originales
            noise: Ruido a agregar
            timesteps: Timesteps para cada muestra
        
        Returns:
            Muestras con ruido agregado
        """
        sqrt_alpha_prod = self.sqrt_alphas_cumprod[timesteps].to(original_samples.device)
        sqrt_one_minus_alpha_prod = self.sqrt_one_minus_alphas_cumprod[timesteps].to(original_samples.device)
        
        # Expandir para broadcasting
        while len(sqrt_alpha_prod.shape) < len(original_samples.shape):
            sqrt_alpha_prod = sqrt_alpha_prod.unsqueeze(-1)
        while len(sqrt_one_minus_alpha_prod.shape) < len(original_samples.shape):
            sqrt_one_minus_alpha_prod = sqrt_one_minus_alpha_prod.unsqueeze(-1)
        
        noisy_samples = sqrt_alpha_prod * original_samples + sqrt_one_minus_alpha_prod * noise
        return noisy_samples
    
    def scale_model_input(self, sample: torch.Tensor, timestep: Union[int, torch.Tensor]) -> torch.Tensor:
        """Escala el input del modelo según el timestep."""
        return sample
    
    def step(
        self,
        model_output: torch.Tensor,
        timestep: Union[int, torch.Tensor],
        sample: torch.Tensor,
        eta: float = 0.0,
        generator: Optional[torch.Generator] = None
    ) -> torch.Tensor:
        """
        Predice la muestra del timestep anterior.
        
        Args:
            model_output: Output del modelo (predicción de ruido)
            timestep: Timestep actual
            sample: Muestra actual
            eta: Parámetro eta para DDIM (0 = DDPM, 1 = DDIM determinístico)
            generator: Generator para ruido aleatorio
        
        Returns:
            Muestra previa
        """
        if isinstance(timestep, int):
            timestep = torch.tensor([timestep])
        
        timestep = timestep.to(sample.device)
        
        # Predicción de x_0
        pred_original_sample = (
            sample - self.sqrt_one_minus_alphas_cumprod[timestep] * model_output
        ) / self.sqrt_alphas_cumprod[timestep]
        
        # Predicción de dirección
        pred_epsilon_direction = model_output
        
        # Varianza
        variance = (1 - eta) * self.posterior_variance[timestep]
        std_dev_t = eta * torch.sqrt(self.posterior_variance[timestep])
        
        # Generar ruido si es necesario
        if generator is None:
            generator = torch.Generator(device=sample.device)
        
        noise = torch.randn(
            sample.shape,
            generator=generator,
            device=sample.device,
            dtype=sample.dtype
        )
        
        # Calcular muestra previa
        prev_sample = (
            self.sqrt_alphas_cumprod[timestep - 1] * pred_original_sample +
            torch.sqrt(variance) * noise +
            std_dev_t * pred_epsilon_direction
        )
        
        return prev_sample
    
    def set_timesteps(self, num_inference_steps: int) -> torch.Tensor:
        """
        Configura los timesteps para inferencia.
        
        Args:
            num_inference_steps: Número de pasos de inferencia
        
        Returns:
            Tensor con timesteps
        """
        step_ratio = self.num_train_timesteps // num_inference_steps
        timesteps = (np.arange(0, num_inference_steps) * step_ratio).round()
        timesteps = np.flip(timesteps).copy()
        return torch.from_numpy(timesteps).long()


class NoiseScheduler:
    """Scheduler simplificado para generación rápida."""
    
    def __init__(self, num_steps: int = 50):
        self.num_steps = num_steps
        self.timesteps = torch.linspace(1.0, 0.0, num_steps)
    
    def get_timestep(self, step: int) -> float:
        """Obtiene el valor del timestep para un paso dado."""
        if step < 0 or step >= self.num_steps:
            raise ValueError(f"step debe estar en [0, {self.num_steps})")
        return self.timesteps[step].item()
    
    def get_noise_schedule(self, step: int) -> float:
        """Obtiene el nivel de ruido para un paso dado."""
        return 1.0 - self.get_timestep(step)


