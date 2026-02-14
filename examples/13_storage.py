#!/usr/bin/env python3
"""Example 13: Storage Interfaces

This example demonstrates the **Storage** interfaces in Personaut PDK.

Personaut provides two storage backends:
    • FileStorage   — JSON files on disk (default, human-readable)
    • SQLiteStorage — SQLite database (better for large datasets)

Both implement the same Storage protocol, so you can swap them freely.

Key operations:
    save_individual / get_individual / list_individuals / delete_individual
    save_situation  / get_situation  / list_situations  / delete_situation
    save_relationship / get_relationship
"""

import tempfile
from pathlib import Path

# ── PDK imports ────────────────────────────────────────────────────────────
from personaut import create_individual, create_situation
from personaut.interfaces import FileStorage, SQLiteStorage
from personaut.relationships import create_relationship
from personaut.types import Modality


def _adapt_relationship(rel_dict: dict) -> dict:
    """Adapt relationship dict for storage backends.

    The SQLite backend expects individual_a/individual_b columns,
    while Relationship.to_dict() uses individual_ids list.
    """
    d = rel_dict.copy()
    ids = d.get("individual_ids", [])
    if len(ids) >= 2:
        d["individual_a"] = ids[0]
        d["individual_b"] = ids[1]
    # Map trust dict → trust_levels for SQLite
    if "trust" in d and "trust_levels" not in d:
        d["trust_levels"] = d["trust"]
    return d


def main() -> None:
    print("=" * 60)
    print("Example 13: Storage Interfaces")
    print("=" * 60)

    # We'll use a temp directory so nothing is permanently written
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # ── PART A — FileStorage ──────────────────────────────────────

        print("\n── FileStorage ──────────────────────────────────────")

        # ── 1. Create FileStorage ─────────────────────────────────────
        print("\n1. Creating FileStorage:")
        fs = FileStorage(data_dir=tmppath / "filestore")
        print(f"   Data dir: {tmppath / 'filestore'}")

        # ── 2. Create and persist individuals ─────────────────────────
        print("\n2. Saving individuals:")
        sarah = create_individual(
            name="Sarah",
            traits={"warmth": 0.9, "liveliness": 0.8},
            emotional_state={"cheerful": 0.7},
            metadata={"occupation": "barista"},
        )
        mike = create_individual(
            name="Mike",
            traits={"reasoning": 0.9},
            emotional_state={"content": 0.5},
            metadata={"occupation": "architect"},
        )

        # Storage uses dict format
        fs.save_individual(sarah.to_dict())
        fs.save_individual(mike.to_dict())
        print(f"   Saved: Sarah (ID: {sarah.id[:8]}...)")
        print(f"   Saved: Mike (ID: {mike.id[:8]}...)")

        # ── 3. List individuals ───────────────────────────────────────
        print("\n3. Listing individuals:")
        all_inds = fs.list_individuals()
        print(f"   Total stored: {len(all_inds)}")
        for ind in all_inds:
            print(f"   • {ind.get('name', 'unnamed')} ({ind.get('id', 'no-id')[:8]}...)")

        # ── 4. Get an individual ──────────────────────────────────────
        print("\n4. Get individual by ID:")
        loaded = fs.get_individual(sarah.id)
        if loaded:
            print(f"   Name: {loaded.get('name')}")
            print(f"   Occupation: {loaded.get('metadata', {}).get('occupation')}")
            traits = loaded.get("traits", {})
            print(f"   Warmth: {traits.get('warmth')}")

        # ── 5. Update an individual ───────────────────────────────────
        print("\n5. Updating an individual:")
        fs.update_individual(sarah.id, {"metadata": {"occupation": "head barista"}})
        updated = fs.get_individual(sarah.id)
        if updated:
            print(f"   Updated occupation: {updated.get('metadata', {}).get('occupation')}")

        # ── 6. Save and load situations ───────────────────────────────
        print("\n6. Situations:")
        situation = create_situation(
            modality=Modality.IN_PERSON,
            description="Morning at the coffee shop",
            location="Sunrise Cafe, Miami FL",
        )
        fs.save_situation(situation.to_dict())
        loaded_sit = fs.get_situation(situation.id)
        if loaded_sit:
            print(f"   Saved and loaded: {loaded_sit.get('description')}")
            print(f"   Location: {loaded_sit.get('location')}")

        # ── 7. Save and load relationships ────────────────────────────
        print("\n7. Relationships:")
        rel = create_relationship(
            individual_ids=[sarah.id, mike.id],
            trust={sarah.id: 0.8, mike.id: 0.5},
            relationship_type="friends",
        )
        fs.save_relationship(_adapt_relationship(rel.to_dict()))
        loaded_rel = fs.get_relationship(rel.id)
        if loaded_rel:
            print(f"   Type: {loaded_rel.get('relationship_type')}")
            print(f"   Individual count: {len(loaded_rel.get('individual_ids', []))}")

        # ── 8. Delete ─────────────────────────────────────────────────
        print("\n8. Deleting:")
        fs.delete_individual(mike.id)
        remaining = fs.list_individuals()
        print(f"   Deleted Mike. Remaining: {len(remaining)}")

        # ── 9. Files on disk ──────────────────────────────────────────
        print("\n9. FileStorage directory structure:")
        filestore = tmppath / "filestore"
        if filestore.exists():
            for p in sorted(filestore.rglob("*")):
                if p.is_file():
                    rel_path = p.relative_to(filestore)
                    print(f"   {rel_path}  ({p.stat().st_size} bytes)")

        # ── PART B — SQLiteStorage ────────────────────────────────────

        print("\n── SQLiteStorage ────────────────────────────────────")

        # ── 10. Create SQLiteStorage ──────────────────────────────────
        print("\n10. Creating SQLiteStorage:")
        db_path = tmppath / "personaut.db"
        sq = SQLiteStorage(db_path=str(db_path))
        print(f"   Database: {db_path.name}")

        # ── 11. Same API, different backend ───────────────────────────
        print("\n11. Same API, different backend:")
        sq.save_individual(sarah.to_dict())
        sq.save_individual(mike.to_dict())
        all_sq = sq.list_individuals()
        print(f"   Stored individuals: {len(all_sq)}")

        loaded = sq.get_individual(sarah.id)
        if loaded:
            print(f"   Loaded Sarah: name={loaded.get('name')}")

        sq.save_situation(situation.to_dict())
        sit_list = sq.list_situations()
        print(f"   Stored situations: {len(sit_list)}")

        sq.save_relationship(_adapt_relationship(rel.to_dict()))
        loaded_rel = sq.get_relationship(rel.id)
        if loaded_rel:
            print(f"   Loaded relationship: type={loaded_rel.get('relationship_type')}")

        # ── 12. SQLite file size ──────────────────────────────────────
        print(f"\n12. Database file size: {db_path.stat().st_size:,} bytes")

        # ── 13. Context manager usage ─────────────────────────────────
        print("\n13. Context manager usage:")
        with SQLiteStorage(db_path=str(tmppath / "ctx_test.db")) as ctx_store:
            ctx_store.save_individual(sarah.to_dict())
            loaded = ctx_store.get_individual(sarah.id)
            print(f"   Within context: {loaded.get('name') if loaded else 'N/A'}")
        print("   Connection closed cleanly on context exit")

        # ── 14. Backend swap ──────────────────────────────────────────
        print("\n14. Backend swap demonstration:")
        print("   Both FileStorage and SQLiteStorage implement the")
        print("   same Storage protocol — you can swap backends without")
        print("   changing any application code!")

    print("\n" + "=" * 60)
    print("✅ Example 13 completed successfully!")
    print("=" * 60)
    print("\nKey Insight: FileStorage writes human-readable JSON files;")
    print("SQLiteStorage uses a single database file. Both backends")
    print("share the same API, making them interchangeable.")


if __name__ == "__main__":
    main()
