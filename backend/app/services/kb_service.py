"""Knowledge indexing and retrieval backed by Chroma and configurable embeddings."""

import hashlib
import json
import os
import re
import threading
import uuid
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.config import settings
from app.models.equipment import Equipment
from app.models.lab import Lab

_index_lock = threading.RLock()
_active_store = None
_active_collection_name: str | None = None


def _embedding_signature() -> str:
    backend = settings.RAG_EMBEDDING_BACKEND.strip().lower()
    if backend == "api":
        model = settings.RAG_EMBEDDING_MODEL.strip()
        base_url = (
            settings.RAG_EMBEDDING_BASE_URL.strip() or settings.LLM_BASE_URL.strip()
        ).rstrip("/")
        provider = "openai-compatible"
        identity = f"{backend}|{provider}|{model}|{base_url}"
    elif backend == "local":
        identity = f"{backend}|{settings.RAG_LOCAL_EMBEDDING_MODEL.strip()}"
    else:
        raise BusinessException(
            message="RAG_EMBEDDING_BACKEND 只支持 api 或 local", code=503
        )
    identity += f"|chunk={settings.RAG_CHUNK_SIZE}:{settings.RAG_CHUNK_OVERLAP}"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


@lru_cache(maxsize=4)
def _get_embeddings(backend: str, model: str, base_url: str):
    if backend == "api":
        api_key = settings.RAG_EMBEDDING_API_KEY.strip() or settings.LLM_API_KEY.strip()
        if not api_key:
            raise BusinessException(message="Embedding API 密钥未配置", code=503)
        if not model:
            raise BusinessException(
                message="Embedding 模型名未配置；请单独配置 RAG_EMBEDDING_MODEL",
                code=503,
            )
        if not base_url:
            raise BusinessException(message="Embedding API 服务地址未配置", code=503)
        try:
            from langchain_openai import OpenAIEmbeddings
        except ImportError as exc:
            raise BusinessException(
                message="缺少 OpenAI 兼容 Embedding 集成，请安装 langchain-openai",
                code=503,
            ) from exc
        try:
            return OpenAIEmbeddings(
                model=model,
                api_key=api_key,
                base_url=base_url,
                timeout=settings.RAG_EMBEDDING_TIMEOUT_SECONDS,
                max_retries=0,
            )
        except Exception as exc:
            raise BusinessException(
                message="Embedding API 配置无效，请检查模型和服务地址", code=503
            ) from exc

    if backend == "local":
        if not model:
            raise BusinessException(message="本地 Embedding 模型名未配置", code=503)
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
        except ImportError as exc:
            raise BusinessException(
                message="本地 Embedding 依赖未安装，请执行 pip install -r requirements-rag-local.txt",
                code=503,
            ) from exc
        try:
            return HuggingFaceEmbeddings(
                model_name=model,
                model_kwargs={"device": settings.RAG_LOCAL_DEVICE},
                encode_kwargs={"normalize_embeddings": True},
            )
        except Exception as exc:
            raise BusinessException(
                message="本地 Embedding 模型加载失败，请检查模型名称、网络和运行设备",
                code=503,
            ) from exc

    raise BusinessException(message="不支持的 Embedding 后端", code=503)


def _embeddings():
    backend = settings.RAG_EMBEDDING_BACKEND.strip().lower()
    model = (
        settings.RAG_EMBEDDING_MODEL.strip()
        if backend == "api"
        else settings.RAG_LOCAL_EMBEDDING_MODEL.strip()
    )
    base_url = (
        settings.RAG_EMBEDDING_BASE_URL.strip() or settings.LLM_BASE_URL.strip()
        if backend == "api"
        else ""
    )
    return _get_embeddings(backend, model, base_url)


def _read_markdown_documents() -> list[Document]:
    settings.RAG_KB_DIR.mkdir(parents=True, exist_ok=True)
    documents: list[Document] = []
    for path in sorted(settings.RAG_KB_DIR.glob("*.md")):
        try:
            content = path.read_text(encoding="utf-8").strip()
        except (OSError, UnicodeError) as exc:
            raise BusinessException(
                message=f"知识文件读取失败：{path.name}", code=400
            ) from exc
        if content:
            documents.append(
                Document(
                    page_content=content,
                    metadata={
                        "source_id": f"file:{path.name}",
                        "source_name": path.name,
                        "source_type": "policy",
                        "title": path.stem,
                    },
                )
            )
    return documents


def _database_documents(db: Session) -> list[Document]:
    documents: list[Document] = []

    labs = db.query(Lab).order_by(Lab.id.asc()).all()
    for lab in labs:
        fields = [f"实验室：{lab.name}"]
        if lab.location:
            fields.append(f"位置：{lab.location}")
        if lab.open_time or lab.close_time:
            fields.append(
                f"预约时段参考：{lab.open_time or '未设置'} 至 {lab.close_time or '未设置'}"
            )
        if lab.description:
            fields.append(f"简介：{lab.description}")
        documents.append(
            Document(
                page_content="\n".join(fields),
                metadata={
                    "source_id": f"lab:{lab.id}",
                    "source_name": f"实验室资料：{lab.name}",
                    "source_type": "lab",
                    "title": lab.name,
                },
            )
        )

    equipment_rows = (
        db.query(Equipment, Lab)
        .join(Lab, Equipment.lab_id == Lab.id)
        .order_by(Equipment.id.asc())
        .all()
    )
    for equipment, lab in equipment_rows:
        fields = [f"设备：{equipment.name}", f"所属实验室：{lab.name}"]
        if equipment.spec:
            fields.append(f"型号规格：{equipment.spec}")
        if equipment.description:
            fields.append(f"设备说明：{equipment.description}")
        documents.append(
            Document(
                page_content="\n".join(fields),
                metadata={
                    "source_id": f"equipment:{equipment.id}",
                    "source_name": f"设备资料：{equipment.name}",
                    "source_type": "equipment",
                    "title": equipment.name,
                },
            )
        )
    return documents


def _load_source_documents(db: Session) -> list[Document]:
    return [*_read_markdown_documents(), *_database_documents(db)]


def _split_documents(documents: list[Document]) -> list[Document]:
    if settings.RAG_CHUNK_SIZE < 100:
        raise BusinessException(message="RAG_CHUNK_SIZE 不能小于 100", code=503)
    if not 0 <= settings.RAG_CHUNK_OVERLAP < settings.RAG_CHUNK_SIZE:
        raise BusinessException(message="RAG_CHUNK_OVERLAP 配置不合法", code=503)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.RAG_CHUNK_SIZE,
        chunk_overlap=settings.RAG_CHUNK_OVERLAP,
        separators=[
            "\n## ",
            "\n# ",
            "\n\n",
            "\n",
            "。",
            "！",
            "？",
            "，",
            "",
        ],
    )
    split_docs = splitter.split_documents(documents)
    for index, document in enumerate(split_docs):
        document.metadata["chunk_index"] = index
    return split_docs


def _manifest_path() -> Path:
    return settings.RAG_CHROMA_DIR / "active_collection.json"


def _read_manifest() -> dict[str, Any] | None:
    path = _manifest_path()
    if not path.exists():
        return None
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BusinessException(
            message="知识库索引状态文件损坏，请管理员重建知识库", code=503
        ) from exc
    return manifest


def _collection_name(signature: str) -> str:
    provider = re.sub(r"[^a-z0-9_-]", "_", settings.RAG_EMBEDDING_BACKEND.lower())
    prefix = re.sub(r"[^a-z0-9_-]", "_", settings.RAG_COLLECTION_PREFIX.lower())
    return f"{prefix[:20]}_{provider}_{signature[:10]}_{uuid.uuid4().hex[:8]}"


def _new_vectorstore(collection_name: str):
    try:
        from langchain_chroma import Chroma
    except ImportError as exc:
        raise BusinessException(
            message="Chroma 依赖未安装，请先安装后端 requirements.txt", code=503
        ) from exc
    return Chroma(
        collection_name=collection_name,
        embedding_function=_embeddings(),
        persist_directory=str(settings.RAG_CHROMA_DIR),
        collection_metadata={"hnsw:space": "cosine"},
    )


def _embedding_error(exc: Exception) -> BusinessException:
    status_code = getattr(exc, "status_code", None)
    status_code = status_code or getattr(
        getattr(exc, "response", None), "status_code", None
    )
    name = type(exc).__name__.lower()
    if status_code == 429 or "ratelimit" in name:
        return BusinessException(
            message="Embedding API 请求过于频繁，请稍后重试", code=429
        )
    if status_code in (401, 403) or "authentication" in name:
        return BusinessException(
            message="Embedding API 密钥无效或无权使用该模型", code=502
        )
    if isinstance(exc, TimeoutError) or "timeout" in name:
        return BusinessException(message="Embedding 请求超时，请稍后重试", code=504)
    if "connection" in name or "network" in name:
        return BusinessException(
            message="无法连接 Embedding 服务，请检查网络和服务地址", code=502
        )
    return BusinessException(
        message="知识库向量处理失败，请检查 Embedding 配置", code=502
    )


def rebuild(db: Session) -> dict[str, Any]:
    """以新 collection 构建索引，构建成功后原子切换活动索引清单。"""
    global _active_store, _active_collection_name

    with _index_lock:
        settings.RAG_CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        documents = _load_source_documents(db)
        if not documents:
            raise BusinessException(
                message="知识库没有可索引资料，请添加 Markdown 或维护实验室/设备资料",
                code=400,
            )
        chunks = _split_documents(documents)
        if not chunks:
            raise BusinessException(message="知识库切分后没有可索引内容", code=400)

        signature = _embedding_signature()
        collection_name = _collection_name(signature)
        try:
            store = _new_vectorstore(collection_name)
            ids = [
                hashlib.sha256(
                    f"{doc.metadata['source_id']}:{doc.metadata['chunk_index']}:{doc.page_content}".encode(
                        "utf-8"
                    )
                ).hexdigest()
                for doc in chunks
            ]
            store.add_documents(chunks, ids=ids)
        except BusinessException:
            raise
        except Exception as exc:
            raise _embedding_error(exc) from exc

        manifest = {
            "collection_name": collection_name,
            "embedding_signature": signature,
            "document_count": len(documents),
            "chunk_count": len(chunks),
            "indexed_at": datetime.now().isoformat(timespec="seconds"),
        }
        manifest_path = _manifest_path()
        temporary_path = manifest_path.with_suffix(".tmp")
        temporary_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        os.replace(temporary_path, manifest_path)
        _active_store = store
        _active_collection_name = collection_name
        return manifest


def search(query: str) -> list[dict[str, Any]]:
    """Return relevant text chunks plus source metadata for answer citations."""
    global _active_store, _active_collection_name

    with _index_lock:
        manifest = _read_manifest()
        if not manifest:
            raise BusinessException(
                message="知识库尚未建立，请管理员先重建知识库", code=503
            )
        signature = _embedding_signature()
        if manifest.get("embedding_signature") != signature:
            raise BusinessException(
                message="Embedding 配置已变化，请管理员重建知识库后再提问", code=503
            )
        collection_name = manifest.get("collection_name")
        if not isinstance(collection_name, str) or not collection_name:
            raise BusinessException(
                message="知识库索引状态无效，请管理员重建知识库", code=503
            )

        try:
            if _active_store is None or _active_collection_name != collection_name:
                from langchain_chroma import Chroma

                _active_store = Chroma(
                    collection_name=collection_name,
                    embedding_function=_embeddings(),
                    persist_directory=str(settings.RAG_CHROMA_DIR),
                )
                _active_collection_name = collection_name
            results = _active_store.similarity_search_with_relevance_scores(
                query, k=max(1, settings.RAG_TOP_K)
            )
        except BusinessException:
            raise
        except Exception as exc:
            raise _embedding_error(exc) from exc

        citations: list[dict[str, Any]] = []
        for document, score in results:
            if score < settings.RAG_MIN_RELEVANCE_SCORE:
                continue
            citations.append(
                {
                    "content": document.page_content,
                    "source": str(document.metadata.get("source_name", "知识库资料")),
                    "kind": str(document.metadata.get("source_type", "document")),
                    "score": round(float(score), 4),
                }
            )
        return citations
