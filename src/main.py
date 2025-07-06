from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
import auth
import schemas
from models import User, Client, Ordem
from datetime import timedelta
from typing import List
from fastapi.middleware.cors import CORSMiddleware


Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:5173", # A porta onde sua aplicação React está rodando
    # Você pode adicionar outras origens aqui se sua aplicação React for rodar em outro domínio/porta
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
 )

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
    username: str = Depends(auth.get_current_user)  
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

@app.get("/my-clients/")
def get_my_clients(
    db: Session = Depends(get_db),
    username: str = Depends(auth.get_current_user)  
):
    """Retorna apenas os clientes do usuário autenticado"""
    db_user = db.query(User).filter(User.username == username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    clients = db.query(Client).filter(Client.user_id == db_user.id).all()
    return clients

@app.post("/ordem/")
def create_ordem(
    ordem: schemas.OrdemCreate,
    db: Session = Depends(get_db),
    username: str = Depends(auth.get_current_user)  
):
    """Cria uma nova ordem de serviço"""
    db_user = db.query(User).filter(User.username == username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Verifica se o cliente existe
    db_client = db.query(Client).filter(
        Client.id == ordem.client_id,
        Client.user_id == db_user.id
    ).first()
    
    if not db_client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    db_ordem = Ordem(
        client_id=ordem.client_id,
        nome_servico=ordem.nome_servico,
        descricao_servico=ordem.descricao_servico,
        valor=ordem.valor,
        status=ordem.status
    )
    db.add(db_ordem)
    db.commit()
    
    return {"msg": "Ordem de serviço criada com sucesso"}

@app.get("/ordens/")
def get_my_ordens(
    db: Session = Depends(get_db),
    username: str = Depends(auth.get_current_user)  
):
    """Retorna todas as ordens do usuário autenticado"""
    db_user = db.query(User).filter(User.username == username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Busca ordens através do relacionamento com clientes
    ordens = db.query(Ordem).join(Client).filter(
        Client.user_id == db_user.id
    ).all()
    
    return ordens

@app.put("/ordem/{ordem_id}/")
def update_ordem_status(
    ordem_id: int,
    status: str,
    db: Session = Depends(get_db),
    username: str = Depends(auth.get_current_user) 
):
    """Atualiza o status de uma ordem de serviço"""
    db_user = db.query(User).filter(User.username == username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Verifica se a ordem existe
    db_ordem = db.query(Ordem).join(Client).filter(
        Ordem.id == ordem_id,
        Client.user_id == db_user.id
    ).first()
    
    if not db_ordem:
        raise HTTPException(status_code=404, detail="Ordem não encontrada")
    
    # Valida status permitidos
    status_validos = ["Pendente", "Em Andamento", "Concluído", "Cancelado"]
    if status not in status_validos:
        raise HTTPException(status_code=400, detail=f"Status inválido. Use: {', '.join(status_validos)}")
    
    db_ordem.status = status
    db.commit()
    
    return {"msg": "Status atualizado com sucesso"}

@app.get("/client/{client_id}/ordens/")
def get_ordens_by_client(
    client_id: int,
    db: Session = Depends(get_db),
    username: str = Depends(auth.get_current_user) 
):
    """Retorna todas as ordens de um cliente específico"""
    db_user = db.query(User).filter(User.username == username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Verifica se o cliente existe
    db_client = db.query(Client).filter(
        Client.id == client_id,
        Client.user_id == db_user.id
    ).first()
    
    if not db_client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    # Busca todas as ordens do cliente
    ordens = db.query(Ordem).filter(Ordem.client_id == client_id).all()
    
    return {
        "cliente": {
            "id": db_client.id,
            "nome": db_client.nome,
            "telefone": db_client.telefone,
            "email": db_client.email
        },
        "ordens": ordens
    }

@app.put("/ordem/{ordem_id}/editar/")
def update_ordem(
    ordem_id: int,
    ordem_update: schemas.OrdemUpdate,
    db: Session = Depends(get_db),
    username: str = Depends(auth.get_current_user)  
):
    """Edita uma ordem de serviço completa"""
    db_user = db.query(User).filter(User.username == username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Verifica se a ordem existe e se pertence ao usuário
    db_ordem = db.query(Ordem).join(Client).filter(
        Ordem.id == ordem_id,
        Client.user_id == db_user.id
    ).first()
    
    if not db_ordem:
        raise HTTPException(status_code=404, detail="Ordem não encontrada")
    
    # Valida status
    if ordem_update.status:
        status_validos = ["Pendente", "Em Andamento", "Concluído", "Cancelado"]
        if ordem_update.status not in status_validos:
            raise HTTPException(status_code=400, detail=f"Status inválido. Use: {', '.join(status_validos)}")
    
    # Atualiza oredem de serviço
    if ordem_update.nome_servico is not None:
        db_ordem.nome_servico = ordem_update.nome_servico
    if ordem_update.descricao_servico is not None:
        db_ordem.descricao_servico = ordem_update.descricao_servico
    if ordem_update.valor is not None:
        db_ordem.valor = ordem_update.valor
    if ordem_update.status is not None:
        db_ordem.status = ordem_update.status
    
    db.commit()
    
    return {"msg": "Ordem de serviço atualizada com sucesso"}

@app.delete("/client/{client_id}/")
def delete_client(
    client_id: int,
    db: Session = Depends(get_db),
    username: str = Depends(auth.get_current_user) 
):
    """Remove um cliente e todas as suas ordens"""
    db_user = db.query(User).filter(User.username == username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Verifica se o cliente existe e pertence ao usuário
    db_client = db.query(Client).filter(
        Client.id == client_id,
        Client.user_id == db_user.id
    ).first()
    
    if not db_client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    # Remove todas as ordens do cliente primeiro
    db.query(Ordem).filter(Ordem.client_id == client_id).delete()
    
    # Remove o cliente
    db.delete(db_client)
    db.commit()
    
    return {"msg": "Cliente excluido com sucesso"}
