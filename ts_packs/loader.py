"""Load and merge language packs for TSLC."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

PACKS_DIR = Path(__file__).resolve().parent
DEFAULT_PACKS = ("base_dialogue", "ts_architecture")
ENV_PACKS = "TSLC_PACKS"


@dataclass(frozen=True)
class PackManifest:
    id: str
    version: str
    priority: int
    description: str
    provides: tuple[str, ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any], pack_dir: Path) -> PackManifest:
        pack_id = data.get("id") or pack_dir.name
        return cls(
            id=str(pack_id),
            version=str(data.get("version", "0.0.0")),
            priority=int(data.get("priority", 0)),
            description=str(data.get("description", "")),
            provides=tuple(data.get("provides", [])),
        )


@dataclass
class PackRegistry:
    active_packs: list[str]
    manifests: list[PackManifest]
    dialogue_acts: list[dict[str, Any]] = field(default_factory=list)
    phrase_patterns: list[dict[str, Any]] = field(default_factory=list)
    semantic_rules: list[dict[str, Any]] = field(default_factory=list)
    graph_rules: list[dict[str, Any]] = field(default_factory=list)
    topic_rules: list[dict[str, Any]] = field(default_factory=list)
    frame_schemas: dict[str, Any] = field(default_factory=dict)
    templates: list[dict[str, Any]] = field(default_factory=list)
    lexicon: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "active_packs": self.active_packs,
            "manifests": [
                {
                    "id": m.id,
                    "version": m.version,
                    "priority": m.priority,
                    "description": m.description,
                }
                for m in self.manifests
            ],
            "dialogue_act_count": len(self.dialogue_acts),
            "phrase_pattern_count": len(self.phrase_patterns),
            "semantic_rule_count": len(self.semantic_rules),
            "graph_rule_count": len(self.graph_rules),
            "topic_rule_count": len(self.topic_rules),
            "template_count": len(self.templates),
        }


def _active_pack_names() -> tuple[str, ...]:
    env_value = os.environ.get(ENV_PACKS, "").strip()
    if env_value:
        return tuple(name.strip() for name in env_value.split(",") if name.strip())
    return DEFAULT_PACKS


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _validate_regex(pattern: str, *, context: str) -> None:
    try:
        re.compile(pattern, re.IGNORECASE)
    except re.error as exc:
        raise ValueError(f"Invalid regex in {context}: {pattern}") from exc


def _validate_pack_dir(pack_dir: Path) -> PackManifest:
    manifest_path = pack_dir / "pack.json"
    if not manifest_path.exists():
        raise ValueError(f"Pack missing pack.json: {pack_dir}")
    manifest = PackManifest.from_dict(_load_json(manifest_path), pack_dir)

    for name, key in (
        ("dialogue_acts.json", "acts"),
        ("phrase_patterns.json", "phrases"),
        ("semantic_rules.json", "rules"),
        ("graph_rules.json", "rules"),
        ("topic_rules.json", "rules"),
        ("templates.json", "templates"),
    ):
        path = pack_dir / name
        if not path.exists():
            continue
        data = _load_json(path)
        if key not in data:
            raise ValueError(f"{path}: missing '{key}' array")

    for rules_name in ("semantic_rules.json", "graph_rules.json", "topic_rules.json"):
        rules_path = pack_dir / rules_name
        if not rules_path.exists():
            continue
        rules = _load_json(rules_path).get("rules", [])
        seen: set[str] = set()
        for rule in rules:
            rule_id = rule.get("id")
            if not rule_id:
                raise ValueError(f"{rules_path}: rule missing id")
            if rule_id in seen:
                raise ValueError(f"{rules_path}: duplicate rule id {rule_id}")
            seen.add(rule_id)
            when = rule.get("when", {})
            _validate_rule_conditions(when, context=f"{rules_path}:{rule_id}")

    phrases_path = pack_dir / "phrase_patterns.json"
    if phrases_path.exists():
        for entry in _load_json(phrases_path).get("phrases", []):
            pattern = entry.get("pattern") or entry.get("phrase", "")
            if pattern:
                _validate_regex(pattern, context=f"{phrases_path}:{entry.get('phrase', pattern)}")

    acts_path = pack_dir / "dialogue_acts.json"
    if acts_path.exists():
        for act in _load_json(acts_path).get("acts", []):
            for pattern in act.get("patterns", []):
                _validate_regex(pattern, context=f"{acts_path}:{act.get('id', 'act')}")

    return manifest


def _validate_rule_conditions(when: dict[str, Any], *, context: str) -> None:
    if "all" in when:
        for item in when["all"]:
            _validate_rule_conditions(item, context=context)
    if "any" in when:
        for item in when["any"]:
            _validate_rule_conditions(item, context=context)
    if "text_regex" in when:
        _validate_regex(str(when["text_regex"]), context=context)


def _merge_list_by_id(
    items: list[dict[str, Any]],
    new_items: list[dict[str, Any]],
    id_key: str,
) -> list[dict[str, Any]]:
    index = {str(item[id_key]): i for i, item in enumerate(items) if id_key in item}
    merged = list(items)
    for item in new_items:
        item_id = str(item.get(id_key, ""))
        if item_id and item_id in index:
            merged[index[item_id]] = item
        else:
            merged.append(item)
    return merged


def _merge_dict(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge_dict(result[key], value)
        else:
            result[key] = value
    return result


def _load_pack_contents(pack_dir: Path) -> dict[str, Any]:
    contents: dict[str, Any] = {}
    mapping = {
        "dialogue_acts.json": ("dialogue_acts", "acts"),
        "phrase_patterns.json": ("phrase_patterns", "phrases"),
        "semantic_rules.json": ("semantic_rules", "rules"),
        "graph_rules.json": ("graph_rules", "rules"),
        "topic_rules.json": ("topic_rules", "rules"),
        "templates.json": ("templates", "templates"),
        "frame_schemas.json": ("frame_schemas", "schemas"),
        "lexicon.json": ("lexicon", None),
    }
    for filename, (key, subkey) in mapping.items():
        path = pack_dir / filename
        if not path.exists():
            continue
        data = _load_json(path)
        if subkey:
            contents[key] = data.get(subkey, [])
        else:
            contents[key] = data
    return contents


def load_packs(pack_names: tuple[str, ...] | None = None) -> PackRegistry:
    names = pack_names or _active_pack_names()
    pack_entries: list[tuple[int, str, Path, PackManifest]] = []

    for name in names:
        pack_dir = PACKS_DIR / name
        if not pack_dir.is_dir():
            raise ValueError(f"Pack not found: {name} ({pack_dir})")
        manifest = _validate_pack_dir(pack_dir)
        pack_entries.append((manifest.priority, name, pack_dir, manifest))

    pack_entries.sort(key=lambda item: (item[0], item[1]))

    registry = PackRegistry(
        active_packs=[name for _, name, _, _ in pack_entries],
        manifests=[manifest for _, _, _, manifest in pack_entries],
    )

    for _, _, pack_dir, _ in pack_entries:
        contents = _load_pack_contents(pack_dir)
        registry.dialogue_acts = _merge_list_by_id(
            registry.dialogue_acts,
            contents.get("dialogue_acts", []),
            "id",
        )
        registry.phrase_patterns.extend(contents.get("phrase_patterns", []))
        registry.semantic_rules = _merge_list_by_id(
            registry.semantic_rules,
            contents.get("semantic_rules", []),
            "id",
        )
        registry.graph_rules = _merge_list_by_id(
            registry.graph_rules,
            contents.get("graph_rules", []),
            "id",
        )
        registry.topic_rules = _merge_list_by_id(
            registry.topic_rules,
            contents.get("topic_rules", []),
            "id",
        )
        registry.templates = _merge_list_by_id(
            registry.templates,
            contents.get("templates", []),
            "template_id",
        )
        registry.frame_schemas = _merge_dict(
            registry.frame_schemas,
            contents.get("frame_schemas", {}),
        )
        registry.lexicon = _merge_dict(registry.lexicon, contents.get("lexicon", {}))

    return registry


@lru_cache(maxsize=4)
def get_registry(pack_key: str) -> PackRegistry:
    names = tuple(name.strip() for name in pack_key.split(",") if name.strip())
    return load_packs(names)


def active_registry() -> PackRegistry:
    return get_registry(",".join(_active_pack_names()))


def reset_registry_cache() -> None:
    get_registry.cache_clear()