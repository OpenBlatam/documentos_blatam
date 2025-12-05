#!/usr/bin/env python3
"""
Tests para el módulo Sora - Generación de Video
================================================

Suite completa de tests para todos los módulos de generación de video.
"""

import pytest
import torch
import numpy as np
from pathlib import Path
import tempfile
import shutil

from sora import (
    VideoGenerationConfig,
    VideoGenerationModule,
    TextToVideoConfig,
    TextToVideoModule,
    ImageToVideoConfig,
    ImageToVideoModule,
    VideoToVideoConfig,
    VideoToVideoModule,
    DiffusionScheduler,
    SchedulerType,
    normalize_video,
    resize_video,
    video_to_numpy,
)


class TestVideoGenerationConfig:
    """Tests para VideoGenerationConfig."""
    
    def test_config_defaults(self):
        """Test que los valores por defecto sean correctos."""
        config = VideoGenerationConfig()
        assert config.video_length == 16
        assert config.resolution == (512, 512)
        assert config.fps == 24
        assert config.temporal_layers == 4
        assert config.diffusion_steps == 50
    
    def test_config_custom_values(self):
        """Test configuración con valores personalizados."""
        config = VideoGenerationConfig(
            hidden_dim=256,
            video_length=32,
            resolution=(256, 256),
            fps=30,
            temporal_layers=6
        )
        assert config.hidden_dim == 256
        assert config.video_length == 32
        assert config.resolution == (256, 256)
        assert config.fps == 30
        assert config.temporal_layers == 6
    
    def test_config_validation_resolution(self):
        """Test validación de resolución."""
        # Resolución válida
        config = VideoGenerationConfig(resolution=(512, 512))
        assert config.resolution == (512, 512)
        
        # Resolución desde lista
        config = VideoGenerationConfig(resolution=[256, 256])
        assert config.resolution == (256, 256)
    
    def test_config_serialization(self):
        """Test serialización de configuración."""
        config = VideoGenerationConfig(
            hidden_dim=512,
            video_length=16,
            resolution=(256, 256)
        )
        
        # to_dict
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert config_dict['hidden_dim'] == 512
        assert config_dict['video_length'] == 16
        
        # from_dict
        new_config = VideoGenerationConfig.from_dict(config_dict)
        assert new_config.hidden_dim == 512
        assert new_config.video_length == 16


class TestVideoGenerationModule:
    """Tests para VideoGenerationModule."""
    
    def test_module_initialization(self):
        """Test inicialización del módulo."""
        config = VideoGenerationConfig(hidden_dim=256, video_length=8)
        module = VideoGenerationModule(config)
        
        assert module.config == config
        assert len(module.temporal_layers) == config.temporal_layers
        assert len(module.spatial_blocks) == config.spatial_blocks
    
    def test_forward_pass_basic(self):
        """Test forward pass básico."""
        config = VideoGenerationConfig(
            hidden_dim=128,
            video_length=4,
            resolution=(64, 64)
        )
        module = VideoGenerationModule(config)
        module.eval()
        
        batch_size = 2
        latent = torch.randn(
            batch_size, config.video_length, config.hidden_dim,
            config.resolution[0] // 8, config.resolution[1] // 8
        )
        
        with torch.no_grad():
            video, metadata = module.forward(latent)
        
        assert video.shape == (batch_size, config.video_length, config.channels, *config.resolution)
        assert 'video_shape' in metadata
        assert 'num_frames' in metadata
        assert metadata['num_frames'] == config.video_length
    
    def test_forward_with_condition(self):
        """Test forward pass con condición."""
        config = VideoGenerationConfig(hidden_dim=128, video_length=4)
        module = VideoGenerationModule(config)
        module.eval()
        
        latent = torch.randn(1, config.video_length, config.hidden_dim, 8, 8)
        condition = torch.randn(1, config.hidden_dim)
        
        with torch.no_grad():
            video, metadata = module.forward(latent, condition=condition)
        
        assert video.shape[0] == 1
        assert 'video_shape' in metadata
    
    def test_forward_with_timestep(self):
        """Test forward pass con timestep."""
        config = VideoGenerationConfig(hidden_dim=128, video_length=4)
        module = VideoGenerationModule(config)
        module.eval()
        
        latent = torch.randn(1, config.video_length, config.hidden_dim, 8, 8)
        timestep = torch.tensor([10])
        
        with torch.no_grad():
            video, metadata = module.forward(latent, timestep=timestep)
        
        assert video.shape[0] == 1
    
    def test_save_and_load(self, temp_dir):
        """Test guardar y cargar modelo."""
        config = VideoGenerationConfig(hidden_dim=128, video_length=4)
        module = VideoGenerationModule(config)
        
        save_path = temp_dir / "test_model.pt"
        module.save_model(str(save_path))
        
        assert save_path.exists()
        
        loaded_module = VideoGenerationModule.load_model(str(save_path), config=config)
        assert loaded_module.config.hidden_dim == config.hidden_dim
        assert len(loaded_module.temporal_layers) == len(module.temporal_layers)
    
    def test_model_info(self):
        """Test información del modelo."""
        config = VideoGenerationConfig(hidden_dim=128, video_length=4)
        module = VideoGenerationModule(config)
        
        info = module.get_model_info()
        assert 'total_parameters' in info
        assert 'trainable_parameters' in info
        assert info['total_parameters'] > 0
    
    def test_parameters_count(self):
        """Test conteo de parámetros."""
        config = VideoGenerationConfig(hidden_dim=128, video_length=4)
        module = VideoGenerationModule(config)
        
        total = module.count_parameters()
        trainable = module.count_parameters(trainable_only=True)
        
        assert total > 0
        assert trainable > 0
        assert trainable <= total


class TestTextToVideoModule:
    """Tests para TextToVideoModule."""
    
    def test_module_initialization(self):
        """Test inicialización."""
        config = TextToVideoConfig(hidden_dim=256, video_length=8)
        module = TextToVideoModule(config)
        
        assert module.config == config
        assert module.text_encoder is not None
    
    def test_encode_text(self):
        """Test encoding de texto."""
        config = TextToVideoConfig(hidden_dim=256, max_text_length=64)
        module = TextToVideoModule(config)
        module.eval()
        
        text_tokens = torch.randint(0, config.max_text_length, (1, 32))
        
        with torch.no_grad():
            embedding = module.encode_text(text_tokens)
        
        assert embedding.shape == (1, config.hidden_dim)
    
    def test_forward_pass(self):
        """Test forward pass."""
        config = TextToVideoConfig(
            hidden_dim=128,
            video_length=4,
            resolution=(64, 64),
            max_text_length=32
        )
        module = TextToVideoModule(config)
        module.eval()
        
        text_tokens = torch.randint(0, config.max_text_length, (1, 16))
        
        with torch.no_grad():
            video, metadata = module.forward(text_tokens)
        
        assert video.shape[0] == 1
        assert video.shape[1] == config.video_length
        assert 'text_length' in metadata
    
    def test_generate_from_text(self):
        """Test generación desde texto."""
        config = TextToVideoConfig(
            hidden_dim=128,
            video_length=4,
            resolution=(64, 64),
            max_text_length=32,
            diffusion_steps=5
        )
        module = TextToVideoModule(config)
        module.eval()
        
        prompt = "A beautiful sunset"
        
        with torch.no_grad():
            video, metadata = module.generate_from_text(prompt, num_inference_steps=3, seed=42)
        
        assert video.shape[0] == 1
        assert 'prompt' in metadata
        assert metadata['prompt'] == prompt


class TestImageToVideoModule:
    """Tests para ImageToVideoModule."""
    
    def test_module_initialization(self):
        """Test inicialización."""
        config = ImageToVideoConfig(hidden_dim=256, video_length=8)
        module = ImageToVideoModule(config)
        
        assert module.config == config
        assert module.image_encoder is not None
    
    def test_encode_image(self):
        """Test encoding de imagen."""
        config = ImageToVideoConfig(hidden_dim=256, resolution=(128, 128))
        module = ImageToVideoModule(config)
        module.eval()
        
        image = torch.randn(1, 3, 128, 128)
        
        with torch.no_grad():
            global_features, spatial_features = module.encode_image(image)
        
        assert global_features.shape == (1, config.hidden_dim)
        assert len(spatial_features.shape) == 4
    
    def test_forward_pass(self):
        """Test forward pass."""
        config = ImageToVideoConfig(
            hidden_dim=128,
            video_length=4,
            resolution=(64, 64)
        )
        module = ImageToVideoModule(config)
        module.eval()
        
        image = torch.randn(1, 3, 64, 64)
        
        with torch.no_grad():
            video, metadata = module.forward(image)
        
        assert video.shape[0] == 1
        assert video.shape[1] == config.video_length
        assert 'image_shape' in metadata
    
    def test_animate_image(self):
        """Test animación de imagen."""
        config = ImageToVideoConfig(
            hidden_dim=128,
            video_length=4,
            resolution=(64, 64),
            diffusion_steps=5
        )
        module = ImageToVideoModule(config)
        module.eval()
        
        image = torch.randn(1, 3, 64, 64)
        
        with torch.no_grad():
            video, metadata = module.animate_image(
                image,
                num_inference_steps=3,
                motion_strength=0.5,
                seed=42
            )
        
        assert video.shape[0] == 1
        assert 'motion_strength' in metadata


class TestVideoToVideoModule:
    """Tests para VideoToVideoModule."""
    
    def test_module_initialization(self):
        """Test inicialización."""
        config = VideoToVideoConfig(hidden_dim=256, video_length=8)
        module = VideoToVideoModule(config)
        
        assert module.config == config
        assert module.style_transfer is not None
        assert module.enhancement is not None
    
    def test_forward_pass(self):
        """Test forward pass."""
        config = VideoToVideoConfig(
            hidden_dim=128,
            video_length=4,
            resolution=(64, 64)
        )
        module = VideoToVideoModule(config)
        module.eval()
        
        input_video = torch.randn(1, 4, 3, 64, 64)
        
        with torch.no_grad():
            video, metadata = module.forward(input_video)
        
        assert video.shape[0] == 1
        assert 'style_strength' in metadata
    
    def test_transform_video(self):
        """Test transformación de video."""
        config = VideoToVideoConfig(
            hidden_dim=128,
            video_length=4,
            resolution=(64, 64),
            diffusion_steps=5
        )
        module = VideoToVideoModule(config)
        module.eval()
        
        input_video = torch.randn(1, 4, 3, 64, 64)
        style_reference = torch.randn(1, 3, 64, 64)
        
        with torch.no_grad():
            video, metadata = module.transform_video(
                input_video,
                style_reference=style_reference,
                num_inference_steps=3,
                seed=42
            )
        
        assert video.shape[0] == 1
        assert metadata['has_style_reference'] is True


class TestDiffusionScheduler:
    """Tests para DiffusionScheduler."""
    
    def test_linear_scheduler(self):
        """Test scheduler lineal."""
        scheduler = DiffusionScheduler(
            num_train_timesteps=1000,
            scheduler_type=SchedulerType.LINEAR
        )
        
        assert len(scheduler.betas) == 1000
        assert scheduler.betas[0] == pytest.approx(0.0001, abs=1e-6)
        assert scheduler.betas[-1] == pytest.approx(0.02, abs=1e-6)
    
    def test_cosine_scheduler(self):
        """Test scheduler coseno."""
        scheduler = DiffusionScheduler(
            num_train_timesteps=1000,
            scheduler_type=SchedulerType.COSINE
        )
        
        assert len(scheduler.betas) == 1000
        assert scheduler.betas.min() >= 0.0001
        assert scheduler.betas.max() <= 0.9999
    
    def test_set_timesteps(self):
        """Test configuración de timesteps."""
        scheduler = DiffusionScheduler(num_train_timesteps=1000)
        timesteps = scheduler.set_timesteps(50)
        
        assert len(timesteps) == 50
        assert timesteps[0] > timesteps[-1]  # Decreciente
    
    def test_add_noise(self):
        """Test agregar ruido."""
        scheduler = DiffusionScheduler(num_train_timesteps=1000)
        
        original = torch.randn(1, 3, 64, 64)
        noise = torch.randn(1, 3, 64, 64)
        timesteps = torch.tensor([500])
        
        noisy = scheduler.add_noise(original, noise, timesteps)
        
        assert noisy.shape == original.shape
        assert not torch.equal(noisy, original)
    
    def test_step(self):
        """Test paso de difusión."""
        scheduler = DiffusionScheduler(num_train_timesteps=1000)
        
        sample = torch.randn(1, 3, 64, 64)
        model_output = torch.randn(1, 3, 64, 64)
        timestep = torch.tensor([500])
        
        prev_sample = scheduler.step(model_output, timestep, sample)
        
        assert prev_sample.shape == sample.shape


class TestVideoUtils:
    """Tests para utilidades de video."""
    
    def test_normalize_video(self):
        """Test normalización de video."""
        video = torch.randn(1, 4, 3, 64, 64) * 2 - 1  # Rango [-1, 1]
        
        normalized = normalize_video(video, method="tanh")
        
        assert normalized.min() >= 0
        assert normalized.max() <= 1
    
    def test_resize_video(self):
        """Test redimensionamiento de video."""
        video = torch.randn(1, 4, 3, 64, 64)
        
        resized = resize_video(video, size=(32, 32))
        
        assert resized.shape == (1, 4, 3, 32, 32)
    
    def test_video_to_numpy(self):
        """Test conversión a numpy."""
        video = torch.randn(1, 4, 3, 64, 64)
        
        video_np = video_to_numpy(video)
        
        assert isinstance(video_np, np.ndarray)
        assert video_np.dtype == np.uint8
        assert video_np.shape == (1, 4, 64, 64, 3)


class TestIntegration:
    """Tests de integración."""
    
    def test_workflow_text_to_video(self):
        """Test workflow completo text-to-video."""
        config = TextToVideoConfig(
            hidden_dim=128,
            video_length=4,
            resolution=(64, 64),
            max_text_length=32,
            diffusion_steps=5
        )
        model = TextToVideoModule(config)
        model.eval()
        
        # Generar
        with torch.no_grad():
            video, metadata = model.generate_from_text("test prompt", num_inference_steps=3)
        
        # Procesar
        video_norm = normalize_video(video)
        video_resized = resize_video(video_norm, size=(32, 32))
        
        assert video_resized.shape == (1, 4, 3, 32, 32)
    
    def test_workflow_image_to_video(self):
        """Test workflow completo image-to-video."""
        config = ImageToVideoConfig(
            hidden_dim=128,
            video_length=4,
            resolution=(64, 64),
            diffusion_steps=5
        )
        model = ImageToVideoModule(config)
        model.eval()
        
        image = torch.randn(1, 3, 64, 64)
        
        # Animar
        with torch.no_grad():
            video, metadata = model.animate_image(image, num_inference_steps=3)
        
        # Procesar
        video_np = video_to_numpy(video)
        
        assert video_np.shape == (1, 4, 64, 64, 3)
    
    def test_multiple_configs(self):
        """Test múltiples configuraciones."""
        configs = [
            VideoGenerationConfig(hidden_dim=128, video_length=4),
            VideoGenerationConfig(hidden_dim=256, video_length=8),
            VideoGenerationConfig(hidden_dim=512, video_length=16),
        ]
        
        for config in configs:
            module = VideoGenerationModule(config)
            assert module.config == config


@pytest.fixture
def temp_dir():
    """Fixture para directorio temporal."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


