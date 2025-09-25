
from .extensions import db
from datetime import datetime

class IbovAtivo(db.Model):
    __tablename__ = 'ibov_ativos'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(10), nullable=False)
    nome = db.Column(db.String(120), nullable=False)
    tipo = db.Column(db.String(50), nullable=True)
    participacao = db.Column(db.String(20), nullable=True)  # string para compatibilidade com scraping
    theoricalQty = db.Column(db.String(40), nullable=True)  # novo campo para quantidade teórica
    data = db.Column(db.Date, nullable=False)

