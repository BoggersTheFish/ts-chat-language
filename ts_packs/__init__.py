"""TSLC language packs."""

from ts_packs.loader import PackRegistry, active_registry, load_packs, reset_registry_cache

__all__ = ["PackRegistry", "active_registry", "load_packs", "reset_registry_cache"]