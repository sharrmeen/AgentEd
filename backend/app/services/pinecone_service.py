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

    @staticmethod
    def _coerce_metadata(metadata: Any) -> Dict[str, Any]:
        """Normalize metadata into a Pinecone-compatible dictionary.

        Pinecone expects metadata to be a dict, not a JSON string.
        Accepted value types are scalar primitives and lists of primitives.
        """
        if metadata is None:
            return {}

        if isinstance(metadata, str):
            try:
                parsed = json.loads(metadata)
            except json.JSONDecodeError as exc:
                raise ValueError("Pinecone metadata must be a dict, got non-JSON string") from exc
            if not isinstance(parsed, dict):
                raise ValueError("Pinecone metadata must be a dict")
            metadata = parsed

        if not isinstance(metadata, dict):
            raise ValueError(f"Pinecone metadata must be a dict, got {type(metadata).__name__}")

        def _normalize_value(value: Any) -> Any:
            if value is None:
                return None
            if isinstance(value, (str, int, float, bool)):
                return value
            if isinstance(value, list):
                normalized_list = []
                for item in value:
                    if isinstance(item, (str, int, float, bool)) or item is None:
                        normalized_list.append(item)
                    else:
                        normalized_list.append(str(item))
                return normalized_list
            return str(value)

        return {str(key): _normalize_value(value) for key, value in metadata.items()}

    def _normalize_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and normalize records before upserting to Pinecone."""
        normalized: List[Dict[str, Any]] = []

        for record in records:
            if not isinstance(record, dict):
                raise ValueError("Each Pinecone record must be a dict")

            record_id = record.get("_id") or record.get("id")
            if not record_id:
                raise ValueError("Each Pinecone record must include '_id' or 'id'")

            text = record.get("text")
            if text is None:
                text = ""

            normalized.append(
                {
                    "_id": str(record_id),
                    "text": str(text),
                    "metadata": self._coerce_metadata(record.get("metadata", {})),
                }
            )

        return normalized

    def upsert_text_records(
        self,
        records: List[Dict[str, Any]],
        namespace: Optional[str] = None,
    ) -> None:
        """Upsert records in Pinecone.

        Expects records in integrated embedding format:
        [{"_id": "...", "text": "...", "metadata": {...}}, ...]
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
        """Search Pinecone and return normalized result objects."""
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
                metadata = hit.get("metadata", {}) or {}
                record_id = hit.get("_id") or hit.get("id")
                score = hit.get("_score")
                if score is None:
                    score = hit.get("score", 0.0)
                text = hit.get("fields", {}).get("text") or metadata.get("text") or ""
            else:
                metadata = getattr(hit, "metadata", {}) or {}
                record_id = getattr(hit, "_id", None) or getattr(hit, "id", None)
                score = getattr(hit, "_score", None)
                if score is None:
                    score = getattr(hit, "score", 0.0)
                fields = getattr(hit, "fields", {}) or {}
                text = fields.get("text") or metadata.get("text") or ""

            normalized.append(
                {
                    "id": record_id,
                    "score": float(score or 0.0),
                    "text": text,
                    "metadata": metadata,
                }
            )

        return normalized
