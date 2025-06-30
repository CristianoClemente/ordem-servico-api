from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
import auth
import schemas
from models import User, Client, Ordem
from datetime import timedelta

# Criar tabelas ao iniciar a aplicação
Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/register/")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
     
    #Verifica se o usuário já existe
    existing_user = db.query(User).filter(User.username == user.username).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Usuário já existe")
    
    #Gerando o hash da senha do usuário
    hashed_password = auth.hash_password(user.password)
    
    #Cria novo usuário
    db_user = User(username=user.username,
        email = user.email, password=hashed_password)
    db.add(db_user)
    db.commit()
    
    #Cria o token JWT para o usuário recém criado
    token = auth.create_token({"sub": db_user.username},
                expires_delta=timedelta(hours=2))
        
    return {"msg": "Usuário registrado com sucesso", "access_token": token}

@app.post("/login/")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    
    if not db_user or not auth.verify_password(user.password,
                                db_user.password):
        raise HTTPException(status_code=400, detail="Credenciais inválidas")
        
    #Cria o token JWT para o usuário recém criado
    token = auth.create_token({"sub": db_user.username},
                expires_delta=timedelta(hours=2))
    return {"access_token": token}

@app.post("/client/")
def create_client(
    client: schemas.ClientCreate,
    db: Session = Depends(get_db),
    username: str = Depends(auth.get_current_user)  # Obtém o usuário autenticado
):
    db_user = db.query(User).filter(User.username == username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    db_client = Client(user_id=db_user.id, nome=client.nome, telefone=client.telefone, email=client.email, date=client.date)
    db.add(db_client)
    db.commit()
    
    return {"msg": "Cliente criado com sucesso"}

@app.get("/clients/")
def get_all_clients(db: Session = Depends(get_db)):
    clients = db.query(Client).all()
    return clients