from datetime import datetime, timedelta
from fastapi import HTTPException, status
from jose import JWTError, jwt

SECRET_KEY = "THIS_IS_SUPER_SECRET_KEY"
ALGORITHM = "HS256"