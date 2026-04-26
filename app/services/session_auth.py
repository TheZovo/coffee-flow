import base64
import hashlib
import hmac
import json
import time


def _b64_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _b64_decode(raw: str) -> bytes:
    padding = "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode(raw + padding)


def _sign_payload(payload: dict, secret: str) -> str:
    payload_b64 = _b64_encode(json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode())
    signature = hmac.new(secret.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{signature}"


def _verify_payload(token: str, secret: str) -> dict | None:
    if not token or "." not in token:
        return None
    payload_b64, signature = token.rsplit(".", 1)
    expected_signature = hmac.new(secret.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected_signature):
        return None

    try:
        payload = json.loads(_b64_decode(payload_b64).decode())
    except (json.JSONDecodeError, ValueError, UnicodeDecodeError):
        return None

    exp = payload.get("exp")
    if not isinstance(exp, int):
        return None
    if exp < int(time.time()):
        return None
    return payload


def sign_session_token(telegram_id: int, secret: str, ttl_seconds: int) -> str:
    payload = {
        "tg": int(telegram_id),
        "exp": int(time.time()) + int(ttl_seconds),
    }
    return _sign_payload(payload, secret)


def verify_session_token(token: str, secret: str) -> dict | None:
    payload = _verify_payload(token, secret)
    tg = None if payload is None else payload.get("tg")
    if not isinstance(tg, int):
        return None
    return payload


def sign_role_session_token(role: str, secret: str, ttl_seconds: int) -> str:
    payload = {
        "role": role,
        "exp": int(time.time()) + int(ttl_seconds),
    }
    return _sign_payload(payload, secret)


def verify_role_session_token(token: str, secret: str, expected_role: str) -> dict | None:
    payload = _verify_payload(token, secret)
    role = None if payload is None else payload.get("role")
    if role != expected_role:
        return None
    return payload
