from pydantic import BaseModel, EmailStr
import datetime

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class ClientCreate(BaseModel):
    nome: str
    telefone: str
    email: EmailStr
    date: datetime.datetime = datetime.datetime.now

class OrdemCreate(BaseModel):
    client_id: int
    nome_servico: str
    descricao_servico: str
    valor: float = 0.0
    status: str = "Pendente"
    date_created: datetime.datetime = datetime.datetime.now
    date_updated: datetime.datetime = datetime.datetime.now