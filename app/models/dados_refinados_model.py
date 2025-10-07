
from app.utils.extensions import db
from datetime import datetime


class DadosRefinados(db.Model):
   
    __tablename__ = 'dados_refinados'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(10), nullable=False, index=True)
    nome = db.Column(db.String(120), nullable=False)
    
    participacao_pct = db.Column(db.Float, nullable=False)  # % de participação no índice
    qtde_teorica = db.Column(db.Float, nullable=False)      # Quantidade teórica normalizada
    tipo_on = db.Column(db.Integer, default=0)              # 1 se ON, 0 caso contrário
    tipo_pn = db.Column(db.Integer, default=0)              # 1 se PN, 0 caso contrário
    
    variacao_percentual = db.Column(db.Float, nullable=True)  # Variação em relação ao dia anterior
    media_movel_7d = db.Column(db.Float, nullable=True)       # Média móvel 7 dias
    volatilidade = db.Column(db.Float, nullable=True)         # Desvio padrão
    
    recomendacao = db.Column(db.Integer, nullable=True)
    
    data_processamento = db.Column(db.DateTime, default=datetime.now)
    data_referencia = db.Column(db.Date, nullable=False)
    
    def __repr__(self):
        return f'<DadosRefinados {self.codigo} - {self.data_referencia}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'nome': self.nome,
            'participacao_pct': self.participacao_pct,
            'qtde_teorica': self.qtde_teorica,
            'tipo_on': self.tipo_on,
            'tipo_pn': self.tipo_pn,
            'variacao_percentual': self.variacao_percentual,
            'media_movel_7d': self.media_movel_7d,
            'volatilidade': self.volatilidade,
            'recomendacao': self.recomendacao,
            'data_referencia': self.data_referencia.isoformat()
        }
