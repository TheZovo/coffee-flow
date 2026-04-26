import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from fastapi import HTTPException, status


def verify_telegram_webapp_init_data(
    init_data: str,
    bot_token: str,
    ttl_seconds: int,
) -> dict:
    if not init_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Telegram init data",
        )

    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    recv_hash = parsed.pop("hash", None)

    if not recv_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Telegram init data",
        )

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calc_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calc_hash, recv_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Telegram auth check failed",
        )

    auth_date_raw = parsed.get("auth_date")
    if auth_date_raw:
        try:
            auth_date = int(auth_date_raw)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Telegram auth timestamp",
            ) from exc
        if int(time.time()) - auth_date > ttl_seconds:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Telegram init data expired",
            )

    user_raw = parsed.get("user")
    if not user_raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Telegram user payload missing",
        )

    try:
        user = json.loads(user_raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to parse Telegram user payload",
        ) from exc

    if "id" not in user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Telegram user id missing",
        )

    return user
