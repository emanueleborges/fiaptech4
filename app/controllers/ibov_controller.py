"""
Controller - Lógica de negócio dos endpoints IBOV
Responsável por processar as requisições e retornar respostas
"""
from datetime import datetime
from flask import jsonify
from app.models.ibov_model import IbovAtivo
from app.utils.extensions import db
from app.services.b3_scraper_service import B3Scraper


class IbovController:
    """Controller para operações com ativos IBOV"""
    
    @staticmethod
    def scrap_ibov():
        """
        Executa o scraping dos dados do IBOVESPA e salva no banco
        
        Returns:
            tuple: (response_data, status_code)
        """
        try:
            scraper = B3Scraper()
            ativos = scraper.fetch_ibov_data()
            salvos = 0
            
            for ativo in ativos:
                # Evita duplicidade por código e data
                existe = IbovAtivo.query.filter_by(
                    codigo=ativo['cod'], 
                    data=datetime.now().date()
                ).first()
                
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
            
            return jsonify({
                'mensagem': 'Carteira IBOV coletada e salva com sucesso!', 
                'total': salvos
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'erro': str(e)}), 500
    
    @staticmethod
    def listar_ativos():
        """
        Lista todos os ativos IBOV salvos no banco
        
        Returns:
            tuple: (response_data, status_code)
        """
        try:
            ativos = IbovAtivo.query.order_by(IbovAtivo.participacao.desc()).all()
            
            result = [
                {
                    'id': a.id,
                    'codigo': a.codigo,
                    'nome': a.nome,
                    'tipo': a.tipo,
                    'participacao': a.participacao,
                    'data': a.data.isoformat()
                } for a in ativos
            ]
            
            return jsonify(result), 200
            
        except Exception as e:
            return jsonify({'erro': str(e)}), 500
