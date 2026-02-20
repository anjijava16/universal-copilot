"""
core/skill_rag.py — Skill RAG Engine (FAISS + OpenAI Embeddings)
=================================================================
Embeds skill file sections into a FAISS vector store.
At query time, retrieves the most relevant chunks by cosine similarity.

This prevents context window overflow when many skills are loaded —
instead of injecting ALL skill content, we only inject the top-k
most relevant sections for the current user query.

Architecture:
  - One FAISS index per user (isolated, no cross-user leakage)
  - Metadata stored in Redis alongside the index
  - Index persisted to disk (FAISS_INDEX_PATH/{user_id}.index)
  - Embedding model: text-embedding-3-small (1536 dims)
"""

import os
import json
import pickle
import asyncio
import numpy as np
from pathlib import Path
from typing import Any

import openai
import structlog

from core.config import settings
from core.redis_client import redis_client

log = structlog.get_logger(__name__)


class SkillRAGEngine:
    """
    Manages per-user FAISS indexes for skill chunk retrieval.

    Each user has:
      - A FAISS FlatIP index (inner product = cosine sim on normalized vectors)
      - A metadata store (Redis) mapping vector index → chunk metadata
    """

    def __init__(self):
        self._indexes: dict[str, Any] = {}    # user_id → faiss.Index
        self._meta: dict[str, list[dict]] = {} # user_id → list of chunk metadata
        self._index_path = Path(settings.FAISS_INDEX_PATH)
        self._index_path.mkdir(parents=True, exist_ok=True)

    # ── Ping (health check) ───────────────────────────────────────────────────

    def ping(self) -> bool:
        """Just verify FAISS can be imported and index dir is writable."""
        import faiss  # noqa
        return self._index_path.exists()

    # ── Embedding ─────────────────────────────────────────────────────────────

    async def _embed_texts(self, texts: list[str]) -> np.ndarray:
        """
        Call OpenAI embeddings API for a list of texts.
        Returns normalized float32 numpy array of shape (N, dims).
        """
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        # Batch in groups of 100 (API limit)
        all_embeddings = []
        batch_size = 100
        for i in range(0, len(texts), batch_size):
            batch = texts[i: i + batch_size]
            response = await client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=batch,
            )
            batch_embeddings = [d.embedding for d in response.data]
            all_embeddings.extend(batch_embeddings)

        arr = np.array(all_embeddings, dtype=np.float32)

        # Normalize for cosine similarity (FAISS IndexFlatIP)
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        arr = arr / (norms + 1e-9)
        return arr

    # ── Index management ──────────────────────────────────────────────────────

    def _get_or_create_index(self, user_id: str):
        """Load index from disk or create a new empty one."""
        import faiss

        if user_id in self._indexes:
            return self._indexes[user_id], self._meta.get(user_id, [])

        index_file = self._index_path / f"{user_id}.index"
        meta_file  = self._index_path / f"{user_id}.meta"

        if index_file.exists() and meta_file.exists():
            index = faiss.read_index(str(index_file))
            with open(meta_file, "rb") as f:
                meta = pickle.load(f)
            log.info("faiss.index_loaded", user_id=user_id, vectors=index.ntotal)
        else:
            # Inner-product index (cosine sim on normalized vectors)
            index = faiss.IndexFlatIP(settings.EMBEDDING_DIMENSIONS)
            meta  = []
            log.info("faiss.index_created", user_id=user_id)

        self._indexes[user_id] = index
        self._meta[user_id]    = meta
        return index, meta

    def _save_index(self, user_id: str):
        import faiss
        index = self._indexes.get(user_id)
        meta  = self._meta.get(user_id, [])
        if index is None:
            return

        index_file = self._index_path / f"{user_id}.index"
        meta_file  = self._index_path / f"{user_id}.meta"
        faiss.write_index(index, str(index_file))
        with open(meta_file, "wb") as f:
            pickle.dump(meta, f)

    # ── Embed a skill into the index ──────────────────────────────────────────

    async def embed_skill(
        self,
        skill_id: str,
        user_id: str,
        sections: list[dict],
        full_content: str,
    ):
        """
        Chunk skill sections, embed them, and add to user's FAISS index.
        Called as a background task after skill upload.
        """
        from core.skill_parser import SkillParser
        parser = SkillParser()

        chunks = parser.chunk_for_embedding(sections, max_chunk_tokens=500)
        if not chunks:
            # Fallback: embed the full content as a single chunk
            chunks = [{"chunk_id": "0_0", "section_index": 0,
                       "title": "Full Content", "content": full_content[:4000]}]

        texts = [c["content"] for c in chunks]

        log.info("faiss.embedding_start", skill_id=skill_id, chunks=len(chunks))
        embeddings = await self._embed_texts(texts)

        index, meta = self._get_or_create_index(user_id)

        # Tag each chunk with skill_id for later filtering/deletion
        for i, chunk in enumerate(chunks):
            meta.append({
                "skill_id": skill_id,
                "chunk_id": chunk["chunk_id"],
                "title":    chunk["title"],
                "content":  chunk["content"],
                "vector_idx": index.ntotal + i,
            })

        index.add(embeddings)
        self._save_index(user_id)

        # Store skill_name in Redis for display in search results
        skill_key = f"skill:{user_id}:{skill_id}:meta"
        raw = await redis_client.get(skill_key)
        skill_name = json.loads(raw).get("name", skill_id) if raw else skill_id

        # Update meta with skill_name
        for m in meta:
            if m["skill_id"] == skill_id and "skill_name" not in m:
                m["skill_name"] = skill_name

        self._meta[user_id] = meta
        self._save_index(user_id)
        log.info("faiss.embedding_done", skill_id=skill_id, chunks=len(chunks))

    # ── Semantic search ───────────────────────────────────────────────────────

    async def search(
        self,
        query: str,
        user_id: str,
        top_k: int = 5,
        min_score: float = 0.5,
    ) -> list[dict]:
        """
        Search for relevant skill chunks by semantic similarity.
        Returns top_k results with score, content, and metadata.
        """
        index, meta = self._get_or_create_index(user_id)

        if index.ntotal == 0:
            return []

        query_embedding = await self._embed_texts([query])
        k = min(top_k, index.ntotal)
        scores, indices = index.search(query_embedding, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(meta):
                continue
            if score < min_score:
                continue

            chunk = meta[idx]
            results.append({
                "skill_id":     chunk["skill_id"],
                "skill_name":   chunk.get("skill_name", chunk["skill_id"]),
                "section_title": chunk["title"],
                "content":      chunk["content"],
                "score":        float(score),
            })

        return results

    # ── Retrieve for context injection ────────────────────────────────────────

    async def retrieve_for_context(
        self,
        query: str,
        user_id: str,
        skill_ids: list[str],          # restrict to these skills only
        max_tokens: int = 3000,
    ) -> tuple[str, list[str], int]:
        """
        High-level retrieval for ContextBuilder.
        Returns (injected_content_string, skill_ids_used, token_count).

        Strategy:
        1. If total token cost of all requested skills fits in budget → inject ALL
        2. Otherwise → RAG retrieve top chunks up to budget
        """
        from core.token_counter import count_tokens
        from core.redis_client import redis_client

        # Load full content of each skill from Redis
        skill_contents: dict[str, str] = {}
        for sid in skill_ids:
            content = await redis_client.get(f"skill:{user_id}:{sid}:content")
            if content:
                skill_contents[sid] = content

        if not skill_contents:
            return "", [], 0

        # Try to fit all skills directly
        all_content = "\n\n---\n\n".join(skill_contents.values())
        all_tokens  = count_tokens(all_content)

        if all_tokens <= max_tokens:
            # All fit — inject everything
            return all_content, list(skill_contents.keys()), all_tokens

        # Doesn't fit → use RAG retrieval
        log.info("skill_rag.overflow_using_rag",
                 total_tokens=all_tokens, budget=max_tokens)

        results = await self.search(query=query, user_id=user_id, top_k=20)
        # Filter to requested skill_ids only
        results = [r for r in results if r["skill_id"] in skill_ids]

        injected_chunks = []
        used_skill_ids  = set()
        total_tokens    = 0

        for r in results:
            chunk_tokens = count_tokens(r["content"])
            if total_tokens + chunk_tokens > max_tokens:
                break
            injected_chunks.append(r["content"])
            used_skill_ids.add(r["skill_id"])
            total_tokens += chunk_tokens

        injected = "\n\n---\n\n".join(injected_chunks)
        return injected, list(used_skill_ids), total_tokens

    # ── Delete skill from index ───────────────────────────────────────────────

    async def delete_skill(self, skill_id: str, user_id: str):
        """
        Remove all chunks for a skill from the FAISS index.
        FAISS IndexFlatIP doesn't support direct deletion, so we
        rebuild the index without the skill's vectors.
        """
        import faiss

        index, meta = self._get_or_create_index(user_id)

        # Filter out this skill's metadata
        remaining_meta = [m for m in meta if m["skill_id"] != skill_id]
        removed_count  = len(meta) - len(remaining_meta)

        if removed_count == 0:
            return  # Skill not in index

        if not remaining_meta:
            # Index is now empty
            new_index = faiss.IndexFlatIP(settings.EMBEDDING_DIMENSIONS)
            self._indexes[user_id] = new_index
            self._meta[user_id]    = []
            self._save_index(user_id)
            return

        # Rebuild index with remaining vectors
        remaining_indices = np.array(
            [m["vector_idx"] for m in remaining_meta], dtype=np.int64
        )
        all_vectors = index.reconstruct_n(0, index.ntotal)
        remaining_vectors = all_vectors[remaining_indices]

        # Re-normalize
        norms = np.linalg.norm(remaining_vectors, axis=1, keepdims=True)
        remaining_vectors = remaining_vectors / (norms + 1e-9)

        new_index = faiss.IndexFlatIP(settings.EMBEDDING_DIMENSIONS)
        new_index.add(remaining_vectors.astype(np.float32))

        # Update vector_idx in metadata
        for i, m in enumerate(remaining_meta):
            m["vector_idx"] = i

        self._indexes[user_id] = new_index
        self._meta[user_id]    = remaining_meta
        self._save_index(user_id)

        log.info("faiss.skill_deleted",
                 skill_id=skill_id, removed_chunks=removed_count)


# Singleton
skill_rag_engine = SkillRAGEngine()
