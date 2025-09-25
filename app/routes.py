from datetime import datetime

from flask import Blueprint, request, jsonify, Response, current_app
import io
import pandas as pd
from .models import IbovAtivo
from .extensions import db
from app.b3scraper import B3Scraper

bp = Blueprint('main', __name__)

# Endpoint para exportar ativos IBOV em CSV


@bp.route('/ibov/scrap', methods=['POST'])
def scrap_ibov():
    from app.models import IbovAtivo
    from app.extensions import db
    try:
        scraper = B3Scraper()
        ativos = scraper.fetch_ibov_data()
        salvos = 0
        for ativo in ativos:
            # Evita duplicidade por código e data
            existe = IbovAtivo.query.filter_by(codigo=ativo['cod'], data=datetime.now().date()).first()
            if not existe:
                novo = IbovAtivo(
                    codigo=ativo['cod'],
                    nome=ativo['asset'],
                    tipo=ativo['type'],
                    participacao=ativo['part'],
                    theoricalQty=ativo['theoricalQty'],
                    data=datetime.now().date()
                )
                db.session.add(novo)
                salvos += 1
        db.session.commit()
        return {'mensagem': 'Carteira IBOV coletada e salva com sucesso!', 'total': salvos}, 201
    except Exception as e:
        return {'erro': str(e)}, 500



# Endpoint para listar ativos IBOV salvos
@bp.route('/ibov/ativos', methods=['GET'])
def listar_ibov_ativos():
    ativos = IbovAtivo.query.order_by(IbovAtivo.participacao.desc()).all()
    return jsonify([
        {
            'id': a.id,
            'codigo': a.codigo,
            'nome': a.nome,
            'tipo': a.tipo,
            'participacao': a.participacao,
            'data': a.data.isoformat()
        } for a in ativos
    ])
