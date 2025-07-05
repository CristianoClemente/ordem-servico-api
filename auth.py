import jwt
from datetime import datetime, timedelta, timezone
import bcrypt
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

SECRET_KEY = "meu_top_secret"
ALGORITHM = "HS256"

api_key_header = APIKeyHeader(name="Authorization")

def create_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload  # Retorna os dados decodificados do token
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado, faça login novamente")  # Mensagem mais clara
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

def get_current_user(authorization: str = Security(api_key_header)):
    print(f"🔍 Authorization recebido: {authorization}")
    
    if not authorization:
        print("❌ Nenhuma autorização fornecida")
        raise HTTPException(status_code=401, detail="Token JWT não fornecido")
    
    if not authorization.startswith("Bearer "):
        print(f"❌ Formato incorreto. Recebido: {authorization[:50]}...")
        raise HTTPException(status_code=401, detail="Token deve começar com 'Bearer '")
    
    token = authorization.split(" ")[1]  # Obtém o token JWT
    print(f"🔍 Token extraído: {token[:50]}...")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])  # Verifica o token
        print(f"✅ Token válido. Usuário: {payload.get('sub')}")
        return payload.get("sub")  # 🔹 Retorna o usuário autenticado
    except jwt.ExpiredSignatureError:
        print("❌ Token expirado")
        raise HTTPException(status_code=401, detail="Token expirado, faça login novamente")
    except jwt.InvalidTokenError as e:
        print(f"❌ Token inválido: {e}")
        raise HTTPException(status_code=401, detail="Token inválido")

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode(), salt)
    return hashed.decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())