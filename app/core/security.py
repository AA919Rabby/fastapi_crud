from passlib.context import CryptContext
from datetime import timedelta,datetime,timezone
import jwt
from app.core.config import settings



pwd_context=CryptContext(schemes=["bcrypt"],
deprecated="auto")

def get_password_hash(password:str)->str:
    return pwd_context.hash(password)

def verify_password(plain_password:str,hashed_password:str)->bool:
    return pwd_context.verify(plain_password,hashed_password)

def create_access_token(subject:str | int,expires_delta:timedelta=None)->str:
    if expires_delta:
        expire=datetime.now(timezone.utc)+expires_delta
    else:
        expire=datetime.now(timezone.utc)+timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode={
            "exp":int(expire.timestamp()),
            "sub":str(subject)
        }
        encoded_jwt=jwt.encode(to_encode,settings.SECRET_KEY,algorithm=settings.ALGORITHM)
        return encoded_jwt

def create_password_reset_token(email:str)->str:
    expire=datetime.now(timezone.utc)+timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    to_encode={
        "exp":int(expire.timestamp()),
        "sub":email,
        "type":"reset"
    }
    return jwt.encode(to_encode,settings.SECRET_KEY,algorithm=settings.ALGORITHM)


def verify_password_reset_token(token:str)->str|None:
    try:
        decoded_token=jwt.decode(token,settings.SECRET_KEY,algorithms=settings.ALGORITHM)
        if decoded_token.get("type")!="reset":
            return None
        return decoded_token.get("sub")
    except jwt.PyJWTError:
        return None

