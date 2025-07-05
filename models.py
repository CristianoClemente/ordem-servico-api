from sqlalchemy import (Column, Integer, String, ForeignKey, 
    Text, DateTime, Float)
from sqlalchemy.orm import relationship
import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    posts = relationship("Client", lazy=True, backref="user")

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    nome = Column(String)
    telefone = Column(String)
    email = Column(String)
    date = Column(DateTime, default=datetime.datetime.now)
    ordens = relationship("Ordem", lazy=True, backref="client")

class Ordem(Base):
    __tablename__ = "ordens"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    nome_servico = Column(String)
    descricao_servico = Column(Text)
    valor = Column(Float, default=0.0)
    status = Column(String, default="Pendente")
    date_created = Column(DateTime, default=datetime.datetime.now)
    date_updated = Column(DateTime, onupdate=datetime.datetime.now)