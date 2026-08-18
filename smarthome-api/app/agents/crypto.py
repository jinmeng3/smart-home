import base64
import hashlib
from functools import lru_cache

from app.core.config import get_settings
from cryptography.fernet import Fernet, InvalidToken

_ENVELOPE_PREFIX = "enc:v1:"
_FERNET_PREFIX = "gAAAA"
_MAX_PLAINTEXT_LENGTH = 4096
_MAX_CIPHERTEXT_LENGTH = 16384


class ApiKeyCryptoError(ValueError):
    """API Key 加解密失败，异常信息不得包含密钥原文或密文。"""


@lru_cache(maxsize=1)
def _derive_key() -> bytes:
    """派生当前写入密钥；生产环境强制使用独立密钥。"""
    settings = get_settings()
    secret = (settings.api_key_encryption_secret or "").strip()
    if not secret:
        if settings.production_mode:
            raise ApiKeyCryptoError("生产环境必须配置 API_KEY_ENCRYPTION_SECRET")
        secret = settings.jwt_secret_key
    if settings.production_mode and len(secret) < 32:
        raise ApiKeyCryptoError("API_KEY_ENCRYPTION_SECRET 长度不能少于 32 个字符")
    return _derive_fernet_key(secret)


def _derive_fernet_key(secret: str) -> bytes:
    """将高熵配置密钥稳定派生为 Fernet 所需的 urlsafe base64 key。"""
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def _fernet() -> Fernet:
    """返回用于新数据写入的 Fernet 实例。"""
    return Fernet(_derive_key())


def _decryption_fernets() -> list[Fernet]:
    """返回解密候选密钥，兼容从 JWT 派生密钥迁移到独立密钥。"""
    settings = get_settings()
    candidates = [_fernet()]

    jwt_key = _derive_fernet_key(settings.jwt_secret_key)
    if jwt_key != _derive_key():
        candidates.append(Fernet(jwt_key))
    return candidates


def encrypt_api_key(plaintext: str | None) -> str | None:
    """加密 API Key。

    新密文使用 ``enc:v1:`` 版本化封装。已经加密且能正确解密的值不会
    被重复加密；格式类似密文但无法解密的输入会失败关闭。
    """
    if plaintext is None:
        return None

    value = plaintext.strip()
    if not value:
        return None
    if len(value) > _MAX_CIPHERTEXT_LENGTH:
        raise ApiKeyCryptoError("API Key 内容过长")

    if value.startswith(_ENVELOPE_PREFIX):
        decrypt_api_key(value)  # 验证完整性，防止损坏密文继续入库
        return value
    if is_encrypted(value):
        # 保存配置时顺带把历史裸 Fernet 密文迁移到当前版本和密钥。
        value = decrypt_api_key(value) or ""
        if not value:
            return None
    if len(value) > _MAX_PLAINTEXT_LENGTH:
        raise ApiKeyCryptoError("API Key 内容过长")

    token = _fernet().encrypt(value.encode("utf-8")).decode("ascii")
    return f"{_ENVELOPE_PREFIX}{token}"


def decrypt_api_key(ciphertext: str | None) -> str | None:
    """解密 API Key。

    支持当前 ``enc:v1:`` 与历史裸 Fernet token。
    开发环境暂时兼容迁移前明文；生产环境遇到明文时拒绝使用。
    """
    if ciphertext is None:
        return None

    value = ciphertext.strip()
    if not value:
        return None
    if len(value) > _MAX_CIPHERTEXT_LENGTH:
        raise ApiKeyCryptoError("API Key 密文过长")

    if value.startswith(_ENVELOPE_PREFIX):
        token = value.removeprefix(_ENVELOPE_PREFIX)
        return _decrypt_fernet_token(token)

    if value.startswith(_FERNET_PREFIX):
        return _decrypt_fernet_token(value)

    if get_settings().production_mode:
        raise ApiKeyCryptoError("检测到未加密的 API Key，请重新保存模型配置")
    return value


def is_encrypted(value: str | None) -> bool:
    """按版本标记识别受支持的密文格式，不接触或记录密钥内容。"""
    if not value:
        return False
    candidate = value.strip()
    return candidate.startswith((_ENVELOPE_PREFIX, _FERNET_PREFIX))


def _decrypt_fernet_token(token: str) -> str:
    if not token:
        raise ApiKeyCryptoError("API Key 密文为空")

    try:
        encoded = token.encode("ascii", errors="strict")
    except UnicodeEncodeError as exc:
        raise ApiKeyCryptoError("API Key 密文格式无效") from exc
    for fernet in _decryption_fernets():
        try:
            return fernet.decrypt(encoded).decode("utf-8")
        except InvalidToken:
            continue
        except UnicodeDecodeError as exc:
            raise ApiKeyCryptoError("API Key 密文内容不是有效文本") from exc

    raise ApiKeyCryptoError("API Key 密文无法解密，请重新保存模型配置")


def clear_crypto_cache() -> None:
    """配置或密钥轮换后清除派生密钥缓存。"""
    _derive_key.cache_clear()
