import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, _patch, patch

import pytest

from memory import vector as vector_module


class FakeSession:
    def __init__(self) -> None:
        self.added = None
        self.add = MagicMock(side_effect=lambda entry: setattr(self, "added", entry))
        self.commit = AsyncMock()
        self.execute = AsyncMock(return_value=MagicMock(all=MagicMock(return_value=[])))

    async def __aenter__(self) -> "FakeSession":
        return self

    async def __aexit__(self, *args: Any) -> bool:
        return False


@pytest.mark.asyncio
async def test_store_embeds_and_saves_embedding() -> None:
    session = FakeSession()
    with (
        patch.object(vector_module, "embed_text", AsyncMock(return_value=[0.1, 0.2, 0.3])),
        patch.object(vector_module, "get_session", AsyncMock(return_value=session)),
    ):
        await vector_module.store_vector_memory("content here", {"key": "value"})

    assert session.added is not None
    assert session.added.content == "content here"
    assert json.loads(session.added.embedding) == [0.1, 0.2, 0.3]
    assert json.loads(session.added.metadata_json) == {"key": "value"}
    session.commit.assert_awaited_once()


def _embedding_failure() -> _patch[Any]:
    return patch.object(
        vector_module, "embed_text", AsyncMock(side_effect=RuntimeError("no api key"))
    )


def _semantic_mock(**kwargs: Any) -> _patch[Any]:
    return patch.object(vector_module, "_semantic_search", AsyncMock(**kwargs))


def _chronological_mock(**kwargs: Any) -> _patch[Any]:
    return patch.object(vector_module, "_chronological_search", AsyncMock(**kwargs))


@pytest.mark.asyncio
async def test_store_saves_without_embedding_when_embedding_fails() -> None:
    session = FakeSession()
    with (
        _embedding_failure(),
        patch.object(vector_module, "get_session", AsyncMock(return_value=session)),
    ):
        await vector_module.store_vector_memory("content here")

    assert session.added is not None
    assert session.added.embedding is None
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_search_uses_semantic_path_when_embedding_succeeds() -> None:
    with (
        patch.object(vector_module, "embed_text", AsyncMock(return_value=[0.1] * 8)),
        _semantic_mock(return_value=[{"id": 1}]) as semantic,
        _chronological_mock(return_value=[]) as chronological,
    ):
        result = await vector_module.search_vector_memory("find the relevant thing")

    assert result == [{"id": 1}]
    semantic.assert_awaited_once()
    chronological.assert_not_awaited()


@pytest.mark.asyncio
async def test_search_falls_back_to_chronological_when_embedding_fails() -> None:
    with (
        _embedding_failure(),
        _semantic_mock(return_value=[]) as semantic,
        _chronological_mock(return_value=[{"id": 2}]) as chronological,
    ):
        result = await vector_module.search_vector_memory("find the relevant thing")

    assert result == [{"id": 2}]
    semantic.assert_not_awaited()
    chronological.assert_awaited_once()


@pytest.mark.asyncio
async def test_search_falls_back_when_semantic_search_fails() -> None:
    with (
        patch.object(vector_module, "embed_text", AsyncMock(return_value=[0.1] * 8)),
        _semantic_mock(side_effect=RuntimeError("pgvector missing")),
        _chronological_mock(return_value=[{"id": 3}]) as chronological,
    ):
        result = await vector_module.search_vector_memory("find the relevant thing")

    assert result == [{"id": 3}]
    chronological.assert_awaited_once()
