"""LangChain chat model adapter used by the AI service."""

from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Any

from app.common.exceptions import BusinessException
from app.config import settings


def _raise_config_error(message: str) -> None:
    raise BusinessException(message=message, code=503)


@lru_cache(maxsize=1)
def _get_model():
    if not settings.LLM_API_KEY.strip():
        _raise_config_error("大模型密钥未配置")
    if not settings.LLM_BASE_URL.strip():
        _raise_config_error("大模型服务地址未配置")
    if not settings.LLM_MODEL.strip():
        _raise_config_error("大模型名称未配置")
    if not settings.LLM_MODEL_PROVIDER.strip():
        _raise_config_error("大模型 provider 未配置")

    try:
        from langchain.chat_models import init_chat_model
    except ImportError as exc:
        raise BusinessException(
            message="LangChain 未安装，请安装后端 requirements.txt 中的依赖", code=503
        ) from exc

    try:
        return init_chat_model(
            model=settings.LLM_MODEL,
            model_provider=settings.LLM_MODEL_PROVIDER,
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            timeout=settings.LLM_TIMEOUT_SECONDS,
            max_retries=0,
            temperature=settings.LLM_TEMPERATURE,
        )
    except ImportError as exc:
        raise BusinessException(
            message="未安装当前 provider 对应的 LangChain 集成包，请按 provider 安装适配依赖",
            code=503,
        ) from exc
    except Exception as exc:
        # 不把第三方异常原文返回前端，避免泄露请求地址、密钥或供应商内部信息。
        raise BusinessException(
            message="大模型配置无效，请检查 provider、模型名和服务地址", code=503
        ) from exc


def _message_text(content: Any) -> str:
    """兼容 LangChain 字符串回复和多模态内容块中的文本块。"""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        text_parts = [
            block["text"]
            for block in content
            if isinstance(block, dict)
            and block.get("type") == "text"
            and isinstance(block.get("text"), str)
        ]
        return "".join(text_parts).strip()
    return ""


def _provider_error(exc: Exception) -> BusinessException:
    status_code = getattr(exc, "status_code", None)
    status_code = status_code or getattr(getattr(exc, "response", None), "status_code", None)
    error_name = type(exc).__name__.lower()

    if status_code == 429 or "ratelimit" in error_name:
        return BusinessException(message="大模型请求过于频繁，请稍后重试", code=429)
    if status_code in (401, 403) or "authentication" in error_name or "permission" in error_name:
        return BusinessException(message="大模型密钥无效或无权访问该模型", code=502)
    if isinstance(exc, (TimeoutError,)) or "timeout" in error_name:
        return BusinessException(message="大模型响应超时，请稍后重试", code=504)
    if "connection" in error_name or "network" in error_name:
        return BusinessException(message="无法连接大模型服务，请检查网络或服务地址", code=502)
    if status_code is not None and status_code >= 500:
        return BusinessException(message="大模型服务暂时不可用，请稍后重试", code=502)
    return BusinessException(message="大模型调用失败，请稍后重试", code=502)


class LLMClient:
    async def chat(self, messages: list[dict[str, str]]) -> str:
        try:
            response = await _get_model().ainvoke(messages)
        except BusinessException:
            raise
        except Exception as exc:
            raise _provider_error(exc) from exc

        content = _message_text(getattr(response, "content", None))
        if not content:
            raise BusinessException(message="大模型返回了空内容，请重试", code=502)
        return content

    async def stream_chat(
        self, messages: list[dict[str, str]]
    ) -> AsyncIterator[str]:
        if not settings.LLM_STREAM_ENABLED:
            raise BusinessException(message="流式对话尚未启用", code=400)

        try:
            async for chunk in _get_model().astream(messages):
                text = _message_text(getattr(chunk, "content", None))
                if text:
                    yield text
        except BusinessException:
            raise
        except Exception as exc:
            raise _provider_error(exc) from exc


llm_client = LLMClient()
