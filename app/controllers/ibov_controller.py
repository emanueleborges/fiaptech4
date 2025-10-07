
from datetime import datetime, timedelta
from flask import jsonify
from app.models.ibov_model import IbovAtivo
from app.utils.extensions import db
from app.services.b3_scraper_service import B3Scraper
import time


class IbovController:
    
    @staticmethod
    def scrap_ibov():
       
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
    
    @staticmethod
    def scrap_historico(meses=6):
        
        try:
            scraper = B3Scraper()
            hoje = datetime.now()
            total_salvos = 0
            total_dias = 0
            erros = 0
            
            for dias_atras in range(0, meses * 30):  
                data_alvo = hoje - timedelta(days=dias_atras)
                
                if data_alvo.weekday() >= 5:  
                    continue
                
                data_str = data_alvo.strftime('%d/%m/%y')  
                
                try:
                    print(f"[HISTÓRICO] Coletando {data_str}...", end=" ")
                    ativos = scraper.fetch_ibov_data(date_str=data_str)
                    
                    if ativos:
                        salvos_dia = 0
                        for ativo in ativos:
                            existe = IbovAtivo.query.filter_by(
                                codigo=ativo['cod'], 
                                data=data_alvo.date()
                            ).first()
                            
                            if not existe:
                                novo = IbovAtivo(
                                    codigo=ativo['cod'],
                                    nome=ativo['asset'],
                                    tipo=ativo['type'],
                                    participacao=ativo['part'],
                                    theoricalQty=ativo['theoricalQty'],
                                    data=data_alvo.date()
                                )
                                db.session.add(novo)
                                salvos_dia += 1
                        
                        db.session.commit()
                        total_salvos += salvos_dia
                        total_dias += 1
                        print(f"✅ {salvos_dia} ativos")
                    else:
                        print(f"❌ Sem dados")
                        erros += 1
                    
                    time.sleep(0.5)
                    
                except Exception as e_dia:
                    print(f"❌ Erro: {str(e_dia)[:50]}")
                    erros += 1
                    continue
            
            return jsonify({
                'mensagem': f'Coleta histórica concluída!',
                'dias_coletados': total_dias,
                'total_registros': total_salvos,
                'media_por_dia': round(total_salvos / total_dias if total_dias > 0 else 0, 1),
                'erros': erros,
                'periodo': f'Últimos {meses} meses'
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'erro': str(e)}), 500
