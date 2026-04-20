"""Pinecone integration helpers.

This module is optional at runtime. It is only used when
VECTOR_DB_PROVIDER=pinecone.
"""

from typing import Any, Dict, List, Optional
import json

from app.core.config import settings


class PineconeService:
    def __init__(self):
        self.api_key = settings.PINECONE_API_KEY
        self.index_name = settings.PINECONE_INDEX
        self.namespace = settings.PINECONE_NAMESPACE

    def _get_index(self):
        if not self.api_key:
            raise ValueError("PINECONE_API_KEY is required when VECTOR_DB_PROVIDER=pinecone")
        if not self.index_name:
            raise ValueError("PINECONE_INDEX is required when VECTOR_DB_PROVIDER=pinecone")

        try:
            from pinecone import Pinecone
        except ImportError as exc:
            raise ImportError("pinecone package is not installed") from exc

        pc = Pinecone(api_key=self.api_key)
        return pc.Index(self.index_name)

    def _coerce_metadata(self, metadata: Any) -> Dict[str, Any]:
        """Normalize metadata into a Pinecone-compatible flat dictionary.
        
        Pinecone upsert_records only accepts scalar values (str, int, float, bool)
        or lists of scalars. Nested dicts are skipped.
        """
        if metadata is None:
            return {}

        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except json.JSONDecodeError as exc:
                raise ValueError("Metadata must be a dict, got non-JSON string") from exc

        if not isinstance(metadata, dict):
            raise ValueError(f"Pinecone metadata must be dict, got {type(metadata).__name__}")

        cleaned = {}

        for key, value in metadata.items():
            if value is None:
                continue

            if isinstance(value, (str, int, float, bool)):
                cleaned[str(key)] = value

            elif isinstance(value, list):
                valid_list = []
                for item in value:
                    if isinstance(item, (str, int, float, bool)):
                        valid_list.append(item)
                    else:
                        valid_list.append(str(item))
                cleaned[str(key)] = valid_list

            elif isinstance(value, dict):
                # Skip nested dicts — not supported by Pinecone integrated embedding API
                continue

            else:
                continue

        return cleaned

    def _normalize_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and normalize records before upserting to Pinecone.
        
        Pinecone upsert_records (integrated embedding API) does NOT accept a nested
        'metadata' key. All fields must be flat top-level scalars or lists.
        Metadata fields are merged directly into the top-level record.
        """
        normalized: List[Dict[str, Any]] = []

        for record in records:
            if not isinstance(record, dict):
                raise ValueError("Each Pinecone record must be a dict")

            record_id = record.get("_id") or record.get("id")
            if not record_id:
                raise ValueError("Each Pinecone record must include '_id' or 'id'")

            text = record.get("chunk_text") or record.get("text") or ""

            # Build flat record — Pinecone upsert_records does NOT accept a nested
            # "metadata" key. Every field must be a top-level scalar or list.
            normalized_record: Dict[str, Any] = {
                "_id": str(record_id),
                "text": str(text),
            }

            # Merge coerced metadata fields directly into the top-level record
            coerced = self._coerce_metadata(record.get("metadata", {}))
            normalized_record.update(coerced)

            normalized.append(normalized_record)

        return normalized

    def upsert_text_records(
        self,
        records: List[Dict[str, Any]],
        namespace: Optional[str] = None,
    ) -> None:
        """Upsert records in Pinecone using the integrated embedding API.

        Expects records in the format:
        [{"_id": "...", "chunk_text": "...", "metadata": {...}}, ...]

        Metadata fields are flattened to top-level before sending to Pinecone.
        """
        if not records:
            return

        normalized_records = self._normalize_records(records)
        index = self._get_index()
        ns = namespace or self.namespace

        try:
            index.upsert_records(namespace=ns, records=normalized_records)
        except TypeError:
            # Backward compatibility with SDK variants.
            index.upsert_records(ns, normalized_records)

    def search_text(
        self,
        query: str,
        top_k: int,
        metadata_filter: Optional[Dict[str, Any]] = None,
        namespace: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search Pinecone and return normalized result objects.
        
        Since records are stored with flat top-level fields, metadata fields
        are read back from hit['fields'] (excluding the reserved 'text' key)
        and re-wrapped under 'metadata' for the application layer.
        """
        index = self._get_index()
        ns = namespace or self.namespace

        query_payload: Dict[str, Any] = {
            "inputs": {"text": query},
            "top_k": top_k,
        }
        if metadata_filter:
            query_payload["filter"] = metadata_filter

        response = index.search(namespace=ns, query=query_payload)

        # Normalize SDK response shapes.
        hits = []
        if isinstance(response, dict):
            hits = (
                response.get("result", {}).get("hits")
                or response.get("matches")
                or []
            )
        else:
            result = getattr(response, "result", None)
            if result is not None:
                hits = getattr(result, "hits", []) or []
            if not hits:
                hits = getattr(response, "matches", []) or []

        normalized = []
        for hit in hits:
            if isinstance(hit, dict):
                record_id = hit.get("_id") or hit.get("id")
                score = hit.get("_score")
                if score is None:
                    score = hit.get("score", 0.0)
                # All stored fields (including metadata) come back under "fields"
                fields = hit.get("fields", {}) or {}
                text = fields.get("text", "")
                # Re-wrap non-text fields as metadata for the application layer
                metadata = {k: v for k, v in fields.items() if k != "text"}
            else:
                record_id = getattr(hit, "_id", None) or getattr(hit, "id", None)
                score = getattr(hit, "_score", None)
                if score is None:
                    score = getattr(hit, "score", 0.0)
                fields = getattr(hit, "fields", {}) or {}
                text = fields.get("text", "")
                metadata = {k: v for k, v in fields.items() if k != "text"}

            normalized.append(
                {
                    "id": record_id,
                    "score": float(score or 0.0),
                    "text": text,
                    "metadata": metadata,
                }
            )

        return normalized