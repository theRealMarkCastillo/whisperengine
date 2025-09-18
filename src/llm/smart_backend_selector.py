#!/usr/bin/env python3
"""
Smart LLM Backend Selector for WhisperEngine
Automatically detects and selects the optimal LLM backend based on platform capabilities
"""

import logging
import os
import platform
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class BackendInfo:
    """Information about an available backend"""

    name: str
    priority: int  # Lower = higher priority
    url_scheme: str
    description: str
    requirements: list[str]
    platform_optimized: bool = False
    gpu_accelerated: bool = False
    apple_silicon_optimized: bool = False


class SmartBackendSelector:
    """Intelligent LLM backend selection based on platform and availability"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.available_backends = self._detect_available_backends()

    def _detect_available_backends(self) -> list[BackendInfo]:
        """Detect all available LLM backends on the current system

        Desktop App Priority Order:
        1. Search for existing Ollama or LM Studio server on localhost
        2. Use Python-based API for Ollama or MLX for Apple Silicon
        """
        backends = []

        # Priority 1: LM Studio (Local HTTP server) - Check first
        if self._is_lm_studio_available():
            backends.append(
                BackendInfo(
                    name="LM Studio",
                    priority=1,
                    url_scheme="http://localhost:1234/v1",
                    description="User-friendly local LLM server with GUI",
                    requirements=["LM Studio running"],
                    platform_optimized=False,
                    gpu_accelerated=True,
                )
            )

        # Priority 2: Ollama (Local HTTP server) - Check second
        if self._is_ollama_available():
            backends.append(
                BackendInfo(
                    name="Ollama",
                    priority=2,
                    url_scheme="http://localhost:11434/v1",
                    description="Production-ready local LLM server",
                    requirements=["Ollama installed and running"],
                    platform_optimized=False,
                    gpu_accelerated=True,
                )
            )

        # Priority 3: MLX Backend (Apple Silicon only) - DISABLED - No backend implementation
        # TODO: Re-enable when MLX backend is implemented
        # if self._is_mlx_available():
        #     backends.append(
        #         BackendInfo(
        #             name="MLX",
        #             priority=3,  # Fallback to Python-based API for Apple Silicon
        #             url_scheme="mlx://",
        #             description="Apple Silicon optimized inference with unified memory",
        #             requirements=["mlx-lm", "Apple Silicon"],
        #             platform_optimized=True,
        #             gpu_accelerated=True,
        #             apple_silicon_optimized=True,
        #         )
        #     )

        # Priority 4: llama-cpp-python (Direct Python integration) - General Python fallback
        if self._is_llamacpp_available():
            backends.append(
                BackendInfo(
                    name="llama-cpp-python",
                    priority=4,
                    url_scheme="llamacpp://",
                    description="Direct Python LLM inference with GGUF models",
                    requirements=["llama-cpp-python", "GGUF models"],
                    platform_optimized=True,
                    gpu_accelerated=True,
                )
            )

        # Priority 5: Local transformers (Direct Python integration) - Last resort
        if self._is_transformers_available():
            backends.append(
                BackendInfo(
                    name="Transformers",
                    priority=5,
                    url_scheme="local://",
                    description="HuggingFace transformers with PyTorch",
                    requirements=["transformers", "torch", "Local models"],
                    platform_optimized=True,
                    gpu_accelerated=True,
                )
            )

        return sorted(backends, key=lambda x: x.priority)

    def _is_mlx_available(self) -> bool:
        """Check if MLX is available (Apple Silicon only)"""
        # DISABLED: MLX backend not implemented
        # TODO: Re-enable when MLX backend is implemented
        return False
        # try:
        #     if platform.system() != "Darwin" or platform.machine() != "arm64":
        #         return False
        # 
        #     import mlx.core  # type: ignore
        #     from mlx_lm import load  # type: ignore
        # 
        #     return True
        # except ImportError:
        #     return False

    def _is_lm_studio_available(self) -> bool:
        """Check if LM Studio is running"""
        try:
            import requests

            response = requests.get("http://localhost:1234/v1/models", timeout=2)
            return response.status_code == 200
        except Exception:
            return False

    def _is_ollama_available(self) -> bool:
        """Check if Ollama is running"""
        try:
            import requests

            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            return response.status_code == 200
        except Exception:
            return False

    def _is_llamacpp_available(self) -> bool:
        """Check if llama-cpp-python is available with models"""
        try:
            from llama_cpp import Llama  # type: ignore

            # Check for GGUF models
            models_dir = os.getenv("LOCAL_MODELS_DIR", "./models")
            gguf_files = []
            if os.path.exists(models_dir):
                for file in os.listdir(models_dir):
                    if file.endswith(".gguf"):
                        gguf_files.append(file)

            return len(gguf_files) > 0 or bool(os.getenv("LLAMACPP_MODEL_PATH"))
        except ImportError:
            return False

    def _is_transformers_available(self) -> bool:
        """Check if transformers is available with local models"""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore

            # Check for local models
            models_dir = os.getenv("LOCAL_MODELS_DIR", "./models")
            local_model_name = os.getenv("LOCAL_LLM_MODEL", "microsoft_Phi-3-mini-4k-instruct")
            model_path = os.path.join(models_dir, local_model_name)

            return os.path.exists(model_path)
        except ImportError:
            return False

    def get_optimal_backend(
        self, prefer_local: bool = True, require_gpu: bool = False
    ) -> BackendInfo | None:
        """Get the optimal backend based on preferences and system capabilities

        Desktop App Priority:
        1. Existing local servers (LM Studio, Ollama) - always preferred
        2. Python-based APIs (MLX for Apple Silicon, llama-cpp-python for others)
        """
        if not self.available_backends:
            self.logger.warning("No LLM backends available")
            return None

        # Filter backends based on requirements
        candidates = self.available_backends.copy()

        if require_gpu:
            candidates = [b for b in candidates if b.gpu_accelerated]

        # Desktop app: Always prefer local servers first, then Python APIs
        if prefer_local:
            # Check for running local servers first (LM Studio, Ollama)
            local_servers = [b for b in candidates if b.name in ["LM Studio", "Ollama"]]
            if local_servers:
                optimal = local_servers[0]  # Already sorted by priority
                self.logger.info(f"🌐 Selected local server: {optimal.name}")
                return optimal

            # Fallback to Python-based APIs
            # MLX disabled until backend implementation is complete
            python_apis = [
                b for b in candidates if b.name in ["llama-cpp-python", "Transformers"]
            ]
            if python_apis:
                # Apple Silicon preference - MLX disabled, use llama-cpp-python or Transformers
                # TODO: Re-enable MLX preference when backend is implemented
                # if platform.system() == "Darwin" and platform.machine() == "arm64":
                #     mlx_backends = [b for b in python_apis if b.name == "MLX"]
                #     if mlx_backends:
                #         optimal = mlx_backends[0]
                #         self.logger.info(f"🍎 Selected Apple Silicon Python API: {optimal.name}")
                #         return optimal

                # Default to first available Python API
                optimal = python_apis[0]
                self.logger.info(f"🐍 Selected Python API: {optimal.name}")
                return optimal

        # Default to highest priority available backend
        if candidates:
            optimal = candidates[0]
            self.logger.info(f"Selected optimal backend: {optimal.name}")
            return optimal

        return None

    def get_fallback_chain(self) -> list[BackendInfo]:
        """Get a prioritized list of backends for fallback purposes"""
        return self.available_backends

    def get_backend_config(self, backend: BackendInfo) -> dict[str, Any]:
        """Get configuration for a specific backend"""
        config = {
            "LLM_CHAT_API_URL": backend.url_scheme,
            "backend_name": backend.name,
            "description": backend.description,
            "platform_optimized": backend.platform_optimized,
            "gpu_accelerated": backend.gpu_accelerated,
        }

        # Backend-specific configurations
        if backend.name == "MLX":
            config.update(
                {
                    "MLX_MODEL_NAME": os.getenv("MLX_MODEL_NAME", "llama-3.1-8b-instruct"),
                    "MLX_MAX_TOKENS": int(os.getenv("MLX_MAX_TOKENS", "2048")),
                    "MLX_TEMPERATURE": float(os.getenv("MLX_TEMPERATURE", "0.7")),
                }
            )
        elif backend.name == "llama-cpp-python":
            config.update(
                {
                    "LLAMACPP_MODEL_PATH": os.getenv("LLAMACPP_MODEL_PATH"),
                    "LLAMACPP_CONTEXT_SIZE": int(os.getenv("LLAMACPP_CONTEXT_SIZE", "4096")),
                    "LLAMACPP_USE_GPU": os.getenv("LLAMACPP_USE_GPU", "auto"),
                }
            )
        elif backend.name == "Transformers":
            config.update(
                {
                    "LOCAL_LLM_MODEL": os.getenv(
                        "LOCAL_LLM_MODEL", "microsoft_Phi-3-mini-4k-instruct"
                    ),
                    "LOCAL_MODELS_DIR": os.getenv("LOCAL_MODELS_DIR", "./models"),
                }
            )

        return config

    def auto_configure_environment(self, respect_user_overrides: bool = True) -> bool:
        """Automatically configure environment for optimal backend

        Args:
            respect_user_overrides: If True, don't override user-configured settings
        """
        # Always respect explicit user configuration
        if respect_user_overrides:
            user_url = os.getenv("LLM_CHAT_API_URL")
            user_key = os.getenv("LLM_CHAT_API_KEY")
            user_model = os.getenv("LLM_CHAT_MODEL")

            if user_url or user_key or user_model:
                self.logger.info("🔧 User configuration detected - respecting user overrides")
                if user_url:
                    self.logger.info(f"   API URL: {user_url}")
                if user_model:
                    self.logger.info(f"   Model: {user_model}")
                # Don't log API key for security
                if user_key:
                    self.logger.info("   API Key: [CONFIGURED]")
                return True

        optimal_backend = self.get_optimal_backend()
        if not optimal_backend:
            self.logger.error("No suitable LLM backend found")
            return False

        # Set environment variables for optimal backend
        config = self.get_backend_config(optimal_backend)

        # Only set if not already configured by user
        if not os.getenv("LLM_CHAT_API_URL"):
            os.environ["LLM_CHAT_API_URL"] = config["LLM_CHAT_API_URL"]
            self.logger.info(f"Auto-configured LLM_CHAT_API_URL: {config['LLM_CHAT_API_URL']}")

        # Set backend-specific environment variables (only if not user-configured)
        for key, value in config.items():
            if key.startswith(("MLX_", "LLAMACPP_", "LOCAL_")) and not os.getenv(key):
                os.environ[key] = str(value)
                self.logger.debug(f"Auto-configured {key}: {value}")

        self.logger.info(f"✅ Auto-configured for {optimal_backend.name} backend")
        return True

    def get_setup_recommendations(self) -> list[str]:
        """Get setup recommendations for improving LLM backend availability"""
        recommendations = []

        # Check platform-specific recommendations
        if platform.system() == "Darwin" and platform.machine() == "arm64":
            # MLX disabled until backend implementation is complete
            # TODO: Re-enable when MLX backend is implemented
            # if not self._is_mlx_available():
            #     recommendations.append(
            #         "🍎 Install MLX for optimal Apple Silicon performance: pip install mlx-lm"
            #     )
            recommendations.append(
                "🍎 Apple Silicon detected - using PyTorch with Metal acceleration"
            )

        if not self._is_lm_studio_available():
            recommendations.append(
                "💻 Install LM Studio for user-friendly local LLM: https://lmstudio.ai/"
            )

        if not self._is_ollama_available():
            recommendations.append(
                "🦙 Install Ollama for production-ready local LLM: https://ollama.ai/"
            )

        if not self._is_llamacpp_available():
            recommendations.append(
                "⚡ Install llama-cpp-python for optimized inference: pip install llama-cpp-python"
            )

        return recommendations

    def has_user_configuration(self) -> dict[str, bool]:
        """Check which configuration settings have been explicitly set by user"""
        return {
            "api_url": bool(os.getenv("LLM_CHAT_API_URL")),
            "api_key": bool(os.getenv("LLM_CHAT_API_KEY")),
            "model": bool(os.getenv("LLM_CHAT_MODEL")),
            "base_url": bool(os.getenv("LLM_BASE_URL")),  # Alternative URL setting
        }

    def get_effective_configuration(self) -> dict[str, Any]:
        """Get the effective configuration combining user overrides with auto-detection"""
        user_config = self.has_user_configuration()
        config = {
            "source": "user_override" if any(user_config.values()) else "auto_detected",
            "user_overrides": user_config,
        }

        # Use user settings if available
        if user_config["api_url"]:
            config["LLM_CHAT_API_URL"] = os.getenv("LLM_CHAT_API_URL")
            config["backend_name"] = "User Configured"
            config["description"] = "User-configured API endpoint"
        elif user_config["base_url"]:
            config["LLM_CHAT_API_URL"] = os.getenv("LLM_BASE_URL")
            config["backend_name"] = "User Configured"
            config["description"] = "User-configured base URL"
        else:
            # Fall back to auto-detection
            optimal_backend = self.get_optimal_backend()
            if optimal_backend:
                backend_config = self.get_backend_config(optimal_backend)
                config.update(backend_config)
            else:
                config.update(
                    {
                        "LLM_CHAT_API_URL": None,
                        "backend_name": "None Available",
                        "description": "No suitable backend found",
                    }
                )

        # Always include user-configured model and key if available
        if user_config["model"]:
            config["LLM_CHAT_MODEL"] = os.getenv("LLM_CHAT_MODEL")

        if user_config["api_key"]:
            config["has_api_key"] = True
            # Don't include the actual key for security

        return config


def get_smart_backend_selector() -> SmartBackendSelector:
    """Factory function to get backend selector instance"""
    return SmartBackendSelector()


def auto_detect_optimal_llm_url() -> str | None:
    """Automatically detect and return the optimal LLM URL for current system

    Respects user overrides:
    - LLM_CHAT_API_URL (primary)
    - LLM_BASE_URL (alternative)

    Falls back to auto-detection if no user configuration found.
    """
    # Check for user overrides first
    user_url = os.getenv("LLM_CHAT_API_URL")
    if user_url:
        return user_url

    user_base_url = os.getenv("LLM_BASE_URL")
    if user_base_url:
        return user_base_url

    # Fall back to auto-detection
    selector = get_smart_backend_selector()
    optimal_backend = selector.get_optimal_backend()

    if optimal_backend:
        config = selector.get_backend_config(optimal_backend)
        return config.get("LLM_CHAT_API_URL")

    return None


if __name__ == "__main__":
    # Test the backend selector
    selector = get_smart_backend_selector()

    for _i, backend in enumerate(selector.available_backends, 1):
        if backend.apple_silicon_optimized:
            pass
        if backend.gpu_accelerated:
            pass

    # Check for user configuration
    user_config = selector.has_user_configuration()
    for _setting, configured in user_config.items():
        status = "✅ Configured" if configured else "❌ Not set"

    # Show effective configuration
    effective_config = selector.get_effective_configuration()
    for key, value in effective_config.items():
        if key not in ["source", "user_overrides"] and value is not None:
            pass

    optimal = selector.get_optimal_backend()
    if optimal:
        if not any(user_config.values()):
            pass
        else:
            pass
    else:
        for _rec in selector.get_setup_recommendations():
            pass
