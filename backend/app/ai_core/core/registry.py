"""AI Core registry for providers and adapters."""
from typing import Dict, Optional, Type

from app.ai_core.core.config import ai_settings
from app.ai_core.providers.base import ModelProvider, EmbeddingProvider, VectorStore


class Registry:
    """Central registry for AI Core providers and adapters."""

    def __init__(self):
        self._llm_providers: Dict[str, Type[ModelProvider]] = {}
        self._embedding_providers: Dict[str, Type[EmbeddingProvider]] = {}
        self._vector_stores: Dict[str, Type[VectorStore]] = {}
        self._instances: Dict[str, object] = {}

    # --- LLM providers ---
    def register_llm_provider(self, name: str, provider_cls: Type[ModelProvider]) -> None:
        self._llm_providers[name] = provider_cls

    def get_llm_provider(self, name: Optional[str] = None) -> Optional[Type[ModelProvider]]:
        name = name or ai_settings.default_llm_provider
        return self._llm_providers.get(name) if name else None

    # --- Embedding providers ---
    def register_embedding_provider(self, name: str, provider_cls: Type[EmbeddingProvider]) -> None:
        self._embedding_providers[name] = provider_cls

    def get_embedding_provider(self, name: Optional[str] = None) -> Optional[Type[EmbeddingProvider]]:
        name = name or ai_settings.default_embedding_provider
        return self._embedding_providers.get(name) if name else None

    # --- Vector stores ---
    def register_vector_store(self, name: str, store_cls: Type[VectorStore]) -> None:
        self._vector_stores[name] = store_cls

    def get_vector_store(self, name: Optional[str] = None) -> Optional[Type[VectorStore]]:
        return self._vector_stores.get(name) if name else None

    # --- Instance caching ---
    def get_instance(self, key: str) -> Optional[object]:
        return self._instances.get(key)

    def set_instance(self, key: str, instance: object) -> None:
        self._instances[key] = instance


registry = Registry()
