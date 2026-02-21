"""Persistence layer bridging AppState ↔ SQLiteStorage.

This module adapts the in-memory dict format used by API routes into
the column-oriented format expected by SQLiteStorage, packing extra
fields (portrait_url, physical_features, video_url, individual_ids,
sender_name, etc.) into the JSON ``metadata`` column.

Usage::

    from personaut.server.api.persistence import Persistence

    db = Persistence("personaut.db")
    db.save_individual(individual_dict)     # persist one
    individuals = db.load_individuals()      # load all → list[dict]
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from personaut.interfaces.sqlite import SQLiteStorage


logger = logging.getLogger(__name__)


class Persistence:
    """Thin adapter between in-memory dicts and SQLiteStorage."""

    def __init__(self, db_path: str | Path = "personaut.db") -> None:
        self.db = SQLiteStorage(db_path)
        logger.info("Persistence layer opened: %s", db_path)

    def close(self) -> None:
        self.db.close()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _dt_to_str(val: Any) -> str | None:
        """Convert datetime to ISO-8601 string, pass through strings."""
        if val is None:
            return None
        if isinstance(val, datetime):
            return val.isoformat()
        return str(val)

    @staticmethod
    def _str_to_dt(val: Any) -> datetime | None:
        """Parse ISO-8601 string back to datetime."""
        if val is None:
            return None
        if isinstance(val, datetime):
            return val
        try:
            return datetime.fromisoformat(str(val))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _parse_json_field(raw: Any, default: Any = None) -> Any:
        """Deserialise a JSON TEXT column.

        If *raw* is already the expected Python type (dict / list) it is
        returned as-is.  If it is a JSON string it is parsed.  On any
        failure the *default* is returned.
        """
        if raw is None:
            return default if default is not None else {}
        if isinstance(raw, (dict, list)):
            return raw
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                pass
        return default if default is not None else {}

    # ==================================================================
    # Individuals
    # ==================================================================

    def save_individual(self, ind: dict[str, Any]) -> str:
        """Persist an individual dict to SQLite.

        Extra fields not in the SQL schema (physical_features,
        portrait_url, etc.) are packed into the ``metadata`` column.
        """
        # Pack extra fields into metadata
        meta = dict(ind.get("metadata") or {})
        for extra_key in (
            "physical_features",
            "portrait_url",
        ):
            if extra_key in ind and ind[extra_key] is not None:
                meta[extra_key] = ind[extra_key]

        row: dict[str, Any] = {
            "id": ind["id"],
            "name": ind.get("name", "Unknown"),
            "individual_type": ind.get("individual_type", "simulated"),
            "description": ind.get("description"),
            "trait_profile": ind.get("trait_profile") or {},
            "emotional_state": ind.get("emotional_state") or {},
            "triggers": ind.get("triggers") or [],
            "masks": ind.get("masks") or [],
            "metadata": meta,
            "created_at": self._dt_to_str(ind.get("created_at")),
        }
        return self.db.save_individual(row)

    def load_individuals(self) -> list[dict[str, Any]]:
        """Load all individuals and unpack metadata back to dict fields."""
        rows = self.db.list_individuals(limit=10_000)
        result = []
        for r in rows:
            meta = self._parse_json_field(r.get("metadata"), default={})
            triggers = self._parse_json_field(r.get("triggers"), default=[])
            masks = self._parse_json_field(r.get("masks"), default=[])

            ind: dict[str, Any] = {
                "id": r["id"],
                "name": r.get("name", "Unknown"),
                "individual_type": r.get("individual_type", "simulated"),
                "description": r.get("description"),
                "trait_profile": r.get("trait_profile") or {},
                "emotional_state": r.get("emotional_state") or {},
                "triggers": triggers,
                "masks": masks,
                "physical_features": meta.pop("physical_features", {}),
                "portrait_url": meta.pop("portrait_url", None),
                "metadata": meta,
                "created_at": self._str_to_dt(r.get("created_at")) or datetime.now(),
                "updated_at": self._str_to_dt(r.get("updated_at")),
            }
            result.append(ind)
        return result

    def delete_individual(self, ind_id: str) -> bool:
        return self.db.delete_individual(ind_id)

    # ==================================================================
    # Memories
    # ==================================================================

    def save_memory(self, ind_id: str, mem: dict[str, Any]) -> str:
        """Persist a single memory to the memories table.

        The memory dict uses ``description`` for the content and
        ``salience`` for importance, matching the in-memory API
        schema.  We adapt to the SQL column names here.
        """
        row: dict[str, Any] = {
            "id": mem.get("id", ""),
            "content": mem.get("description") or mem.get("content", ""),
            "memory_type": mem.get("memory_type", "individual"),
            "importance": mem.get("salience", mem.get("importance", 0.5)),
            "metadata": {
                "emotional_state": mem.get("emotional_state"),
                "owner_id": ind_id,
            },
        }
        return self.db.save_memory(ind_id, row)

    def load_memories(self, ind_id: str) -> list[dict[str, Any]]:
        """Load all memories for an individual from the DB.

        Returns them in the in-memory API format (``description``,
        ``salience``, ``emotional_state``, etc.).
        """
        rows = self.db.list_memories(ind_id, limit=10_000)
        result: list[dict[str, Any]] = []
        for r in rows:
            meta = self._parse_json_field(r.get("metadata"), default={})
            mem: dict[str, Any] = {
                "id": r["id"],
                "description": r.get("content", ""),
                "owner_id": ind_id,
                "salience": r.get("importance", 0.5),
                "memory_type": r.get("memory_type", "individual"),
                "emotional_state": meta.get("emotional_state"),
                "metadata": {k: v for k, v in meta.items() if k not in ("emotional_state", "owner_id")},
            }
            result.append(mem)
        return result

    # ==================================================================
    # Situations
    # ==================================================================

    def save_situation(self, sit: dict[str, Any]) -> str:
        row: dict[str, Any] = {
            "id": sit["id"],
            "description": sit.get("description", ""),
            "modality": sit.get("modality", "text_message"),
            "location": sit.get("location"),
            "context": sit.get("context") or {},
            "created_at": self._dt_to_str(sit.get("created_at")),
        }
        return self.db.save_situation(row)

    def load_situations(self) -> list[dict[str, Any]]:
        rows = self.db.list_situations(limit=10_000)
        result = []
        for r in rows:
            sit: dict[str, Any] = {
                "id": r["id"],
                "description": r.get("description", ""),
                "modality": r.get("modality", "text_message"),
                "location": r.get("location"),
                "context": r.get("context") or {},
                "created_at": self._str_to_dt(r.get("created_at")) or datetime.now(),
                "updated_at": self._str_to_dt(r.get("updated_at")),
            }
            result.append(sit)
        return result

    def delete_situation(self, sit_id: str) -> bool:
        return self.db.delete_situation(sit_id)

    # ==================================================================
    # Sessions  (many-to-many individual_ids stored in metadata)
    # ==================================================================

    def save_session(self, sess: dict[str, Any]) -> str:
        """Persist a session.  ``individual_ids`` list and ``video_url``
        are packed into the metadata JSON column since the SQL schema
        only has a single ``individual_id`` TEXT column.
        """
        ind_ids: list[str] = sess.get("individual_ids") or []
        meta = dict(sess.get("metadata") or {})
        meta["individual_ids"] = ind_ids
        if sess.get("video_url"):
            meta["video_url"] = sess["video_url"]
        if sess.get("human_id"):
            meta["human_id"] = sess["human_id"]

        row: dict[str, Any] = {
            "id": sess["id"],
            "individual_id": ind_ids[0] if ind_ids else "",
            "situation_id": sess.get("situation_id"),
            "active": sess.get("active", True),
            "metadata": meta,
            "created_at": self._dt_to_str(sess.get("created_at")),
            "ended_at": self._dt_to_str(sess.get("ended_at")),
        }
        return self.db.save_session(row)

    def load_sessions(self) -> list[dict[str, Any]]:
        """Load all sessions and reconstruct in-memory format.

        Messages are loaded separately and attached.
        """
        rows = self.db.list_sessions(limit=10_000)
        result = []
        for r in rows:
            meta = r.get("metadata") or {}
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except (json.JSONDecodeError, TypeError):
                    meta = {}

            ind_ids = meta.pop("individual_ids", [])
            if not ind_ids and r.get("individual_id"):
                ind_ids = [r["individual_id"]]

            video_url = meta.pop("video_url", None)
            human_id = meta.pop("human_id", None)

            sess: dict[str, Any] = {
                "id": r["id"],
                "situation_id": r.get("situation_id"),
                "individual_ids": ind_ids,
                "human_id": human_id,
                "active": bool(r.get("active", True)),
                "messages": [],  # populated below
                "metadata": meta,
                "video_url": video_url,
                "created_at": self._str_to_dt(r.get("created_at")) or datetime.now(),
                "updated_at": self._str_to_dt(r.get("ended_at")),
            }

            # Load messages for this session
            db_msgs = self.db.list_messages(r["id"], limit=10_000)
            for m in db_msgs:
                m_meta = m.get("metadata") or {}
                if isinstance(m_meta, str):
                    try:
                        m_meta = json.loads(m_meta)
                    except (json.JSONDecodeError, TypeError):
                        m_meta = {}
                msg: dict[str, Any] = {
                    "id": m["id"],
                    "session_id": m.get("session_id", r["id"]),
                    "sender_id": m_meta.get("sender_id"),
                    "sender_name": m.get("sender", "Human"),
                    "content": m.get("content", ""),
                    "action": m_meta.get("action"),
                    "timestamp": self._str_to_dt(m.get("created_at")) or datetime.now(),
                    "emotional_state": m_meta.get("emotional_state"),
                }
                sess["messages"].append(msg)

            result.append(sess)
        return result

    def delete_session(self, sess_id: str) -> None:
        self.db.end_session(sess_id)

    # ==================================================================
    # Messages
    # ==================================================================

    def save_message(self, session_id: str, msg: dict[str, Any]) -> str:
        """Persist a message.  Extra fields go into metadata."""
        meta: dict[str, Any] = {}
        if msg.get("sender_id"):
            meta["sender_id"] = msg["sender_id"]
        if msg.get("action"):
            meta["action"] = msg["action"]
        if msg.get("emotional_state"):
            meta["emotional_state"] = msg["emotional_state"]

        row: dict[str, Any] = {
            "id": msg.get("id") or "",
            "sender": msg.get("sender_name", "Human"),
            "content": msg.get("content", ""),
            "metadata": meta,
            "created_at": self._dt_to_str(msg.get("timestamp") or msg.get("created_at")),
        }
        return self.db.save_message(session_id, row)

    # ==================================================================
    # Relationships
    # ==================================================================

    def save_relationship(self, rel: dict[str, Any]) -> str:
        row: dict[str, Any] = {
            "id": rel["id"],
            "individual_a": rel.get("individual_a"),
            "individual_b": rel.get("individual_b"),
            "relationship_type": rel.get("relationship_type"),
            "trust_levels": rel.get("trust_levels") or {},
            "shared_memories": rel.get("shared_memories") or [],
            "metadata": rel.get("metadata") or {},
            "created_at": self._dt_to_str(rel.get("created_at")),
        }
        return self.db.save_relationship(row)

    def load_relationships(self) -> list[dict[str, Any]]:
        rows = self.db.list_relationships(limit=10_000)
        result = []
        for r in rows:
            meta = r.get("metadata") or {}
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except (json.JSONDecodeError, TypeError):
                    meta = {}

            ind_a = r.get("individual_a", "")
            ind_b = r.get("individual_b", "")

            rel: dict[str, Any] = {
                "id": r["id"],
                # Routes use individual_ids list + trust dict
                "individual_ids": [ind_a, ind_b],
                "individual_a": ind_a,
                "individual_b": ind_b,
                "relationship_type": r.get("relationship_type"),
                "trust": r.get("trust_levels") or {},
                "trust_levels": r.get("trust_levels") or {},
                "history": meta.get("history"),
                "shared_memories": r.get("shared_memories") or [],
                "shared_memory_ids": [],
                "metadata": meta,
                "created_at": self._str_to_dt(r.get("created_at")) or datetime.now(),
                "updated_at": self._str_to_dt(r.get("updated_at")),
            }
            result.append(rel)
        return result

    def delete_relationship(self, rel_id: str) -> bool:
        return self.db.delete_relationship(rel_id)


__all__ = ["Persistence"]
