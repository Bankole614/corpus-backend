from datetime import datetime, timezone
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_token
from app.db.models import RevokedToken


async def is_token_revoked(db: AsyncSession, token: str, jti: str | None = None) -> bool:
    """
    Check whether a token or its jti has been recorded in the revocation table.
    """
    token_h = hash_token(token)
    conditions = [RevokedToken.token_hash == token_h]
    if jti:
        conditions.append(RevokedToken.jti == jti)

    stmt = select(RevokedToken.id).where(
        conditions[0] | conditions[1] if len(conditions) > 1 else conditions[0]
    ).limit(1)
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def revoke_token(
    db: AsyncSession,
    token: str,
    user_id: str | None,
    expires_at: datetime,
    jti: str | None = None,
) -> RevokedToken:
    """
    Revoke an access token by storing its hash (and jti) in the database.
    Also cleans up expired tokens to keep the revocation table compact.
    """
    now = datetime.now(timezone.utc)
    # Prune expired tokens
    await db.execute(delete(RevokedToken).where(RevokedToken.expires_at < now))

    token_h = hash_token(token)
    already_revoked = await is_token_revoked(db, token, jti)
    if already_revoked:
        stmt = select(RevokedToken).where(RevokedToken.token_hash == token_h)
        res = await db.execute(stmt)
        record = res.scalar_one_or_none()
        if record:
            return record

    revoked = RevokedToken(
        token_hash=token_h,
        jti=jti,
        user_id=user_id,
        expires_at=expires_at,
    )
    db.add(revoked)
    await db.commit()
    await db.refresh(revoked)
    return revoked
