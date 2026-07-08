"""Authentication utilities: password hashing, JWT, current user dependency, RBAC."""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext

from database import users_col

JWT_SECRET = os.environ.get('JWT_SECRET', 'change-me-please')
JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
JWT_EXPIRE_MINUTES = int(os.environ.get('JWT_EXPIRE_MINUTES', '1440'))

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/login', auto_error=False)


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=JWT_EXPIRE_MINUTES))
    to_encode.update({'exp': expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(request: Request, token: Optional[str] = Depends(oauth2_scheme)):
    # Support both Authorization: Bearer and 'token' cookie
    if not token:
        auth = request.headers.get('Authorization', '')
        if auth.lower().startswith('bearer '):
            token = auth.split(' ', 1)[1]
    if not token:
        raise HTTPException(status_code=401, detail='Not authenticated')
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get('sub')
        if not user_id:
            raise HTTPException(status_code=401, detail='Invalid token')
    except JWTError:
        raise HTTPException(status_code=401, detail='Invalid token')

    user = await users_col.find_one({'id': user_id}, {'_id': 0})
    if not user or user.get('status') != 'active':
        raise HTTPException(status_code=401, detail='User not found or inactive')
    return user


def require_roles(*allowed_roles: str):
    async def _dep(current_user=Depends(get_current_user)):
        if current_user['role'] not in allowed_roles:
            raise HTTPException(status_code=403, detail=f"Requires role: {', '.join(allowed_roles)}")
        return current_user
    return _dep


def resolve_school_id(current_user: dict, requested_school_id: Optional[str], x_school_id: Optional[str] = None) -> str:
    """Resolve which school to scope the operation to.
    - super_admin can specify any school via requested_school_id or X-School-Id header.
    - Others are locked to their assigned school.
    """
    if current_user['role'] == 'super_admin':
        sid = requested_school_id or x_school_id
        if not sid:
            raise HTTPException(status_code=400, detail='school_id required for super admin (send X-School-Id header or in body)')
        return sid
    if not current_user.get('school_id'):
        raise HTTPException(status_code=403, detail='User has no assigned school')
    return current_user['school_id']


async def current_school_id(request: Request, current_user=Depends(get_current_user)) -> str:
    """FastAPI dependency to get the currently-active school scope.
    Reads X-School-Id header for super admins, else uses user's school.
    """
    x = request.headers.get('X-School-Id')
    return resolve_school_id(current_user, None, x)
