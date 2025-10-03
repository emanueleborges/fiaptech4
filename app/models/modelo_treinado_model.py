"""
Model para armazenar informações sobre modelos treinados
"""
from app.utils.extensions import db
from datetime import datetime


class ModeloTreinado(db.Model):
    """
    Tabela com informações sobre modelos de ML treinados
    """
    __tablename__ = 'modelos_treinados'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    versao = db.Column(db.String(20), nullable=False)
    algoritmo = db.Column(db.String(50), nullable=False)  # RandomForest, XGBoost, etc
    
    # Métricas de performance
    acuracia = db.Column(db.Float, nullable=True)
    precision = db.Column(db.Float, nullable=True)
    recall = db.Column(db.Float, nullable=True)
    f1_score = db.Column(db.Float, nullable=True)
    
    # Metadados
    total_amostras_treino = db.Column(db.Integer, nullable=True)
    total_amostras_teste = db.Column(db.Integer, nullable=True)
    features_utilizadas = db.Column(db.Text, nullable=True)  # JSON com nomes das features
    
    # Arquivos
    caminho_modelo = db.Column(db.String(255), nullable=False)  # Caminho do arquivo .pkl
    
    # Status
    ativo = db.Column(db.Boolean, default=True)
    data_treinamento = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<ModeloTreinado {self.nome} v{self.versao}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'versao': self.versao,
            'algoritmo': self.algoritmo,
            'acuracia': self.acuracia,
            'precision': self.precision,
            'recall': self.recall,
            'f1_score': self.f1_score,
            'total_amostras_treino': self.total_amostras_treino,
            'total_amostras_teste': self.total_amostras_teste,
            'ativo': self.ativo,
            'data_treinamento': self.data_treinamento.isoformat()
        }
