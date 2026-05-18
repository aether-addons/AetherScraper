from __future__ import annotations

import importlib
import inspect
import json
import os
import pkgutil
from collections.abc import Iterable
from dataclasses import dataclass
from types import ModuleType

from .config import ProviderConfig
from .kodi.settings import KodiSettings
from .provider import BaseProvider


@dataclass(frozen=True)
class ProviderLoadError:
    module: str
    message: str


def load_provider_configs(directory):
    configs = {}
    if not directory or not os.path.isdir(directory):
        return configs
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".json"):
            continue
        path = os.path.join(directory, name)
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        config = ProviderConfig(**data)
        configs[config.id] = config
    return configs


def merge_provider_config(base, override=None):
    if override is None:
        return base
    data = base.__dict__.copy()
    data.update(
        {key: value for key, value in override.__dict__.items() if value is not None}
    )
    return ProviderConfig(**data)


def iter_provider_module_names(package: str = "aetherscraper.providers") -> list[str]:
    """Return importable provider module names in a provider package."""

    module = importlib.import_module(package)
    paths = getattr(module, "__path__", None)
    if paths is None:
        return []
    names = []
    for item in pkgutil.iter_modules(paths, module.__name__ + "."):
        if item.name.rsplit(".", 1)[-1].startswith("_"):
            continue
        names.append(item.name)
    return sorted(names)


def provider_classes_from_module(module: ModuleType) -> list[type[BaseProvider]]:
    """Find concrete BaseProvider subclasses declared by one module."""

    classes = []
    for _, candidate in inspect.getmembers(module, inspect.isclass):
        if candidate is BaseProvider:
            continue
        if not issubclass(candidate, BaseProvider):
            continue
        if candidate.__module__ != module.__name__:
            continue
        if inspect.isabstract(candidate):
            continue
        classes.append(candidate)
    return classes


def load_provider_classes(
    package: str = "aetherscraper.providers",
) -> tuple[list[type[BaseProvider]], list[ProviderLoadError]]:
    """Import provider modules safely and return provider classes plus errors."""

    classes: list[type[BaseProvider]] = []
    errors: list[ProviderLoadError] = []
    try:
        module_names = iter_provider_module_names(package)
    except Exception as exc:
        return [], [ProviderLoadError(package, str(exc))]

    for module_name in module_names:
        try:
            module = importlib.import_module(module_name)
            classes.extend(provider_classes_from_module(module))
        except Exception as exc:
            errors.append(ProviderLoadError(module_name, str(exc)))
    classes.sort(key=lambda cls: cls.config.priority)
    return classes, errors


def instantiate_provider(
    provider_class: type[BaseProvider],
    config_overrides: dict[str, ProviderConfig] | None = None,
    settings: KodiSettings | None = None,
) -> BaseProvider:
    """Create provider with merged config and optional settings mirror."""

    config = merge_provider_config(
        provider_class.config, (config_overrides or {}).get(provider_class.config.id)
    )
    try:
        return provider_class(config=config, settings=settings)
    except TypeError:
        provider = provider_class()
        provider.config = config
        provider.settings = settings
        return provider


def load_providers(
    package: str = "aetherscraper.providers",
    config_overrides: dict[str, ProviderConfig] | None = None,
    settings: KodiSettings | None = None,
) -> tuple[list[BaseProvider], list[ProviderLoadError]]:
    """Discover, import, instantiate, and sort available providers."""

    classes, errors = load_provider_classes(package)
    providers = []
    for provider_class in classes:
        try:
            providers.append(
                instantiate_provider(
                    provider_class, config_overrides=config_overrides, settings=settings
                )
            )
        except Exception as exc:
            errors.append(ProviderLoadError(provider_class.__module__, str(exc)))
    providers.sort(key=lambda provider: provider.config.priority)
    return providers, errors


def filter_provider_configs(
    configs: Iterable[ProviderConfig],
    *,
    provider_type: str | None = None,
    pack_capable: bool | None = None,
) -> list[ProviderConfig]:
    selected = []
    for config in configs:
        if provider_type is not None and config.provider_type != provider_type:
            continue
        if pack_capable is not None and config.pack_capable != pack_capable:
            continue
        selected.append(config)
    return selected
