import base64
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app.b3scraper")

class B3Scraper:
    
    def __init__(self, bucket_name: str = None):
        self.bucket_name = bucket_name

        self.base_page = "https://sistemaswebb3-listados.b3.com.br/indexPage/day/IBOV"
        self.base_api = "https://sistemaswebb3-listados.b3.com.br/indexProxy/indexCall/GetPortfolioDay"

        self.headers_json = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://www.b3.com.br",
            "Referer": "https://www.b3.com.br/",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
        }
        self.headers_html = {
            **self.headers_json,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        }

        self.session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",)
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        self.session.mount("http://", HTTPAdapter(max_retries=retries))

    def fetch_ibov_data(self, date_str: Optional[str] = None) -> List[Dict]:
        
        try:
            data = self._get_json_ibov(date_str)
            if data and data.get("results"):
                results = [
                    {
                        "cod": str(r.get("cod", "")).strip(),
                        "asset": str(r.get("asset", "")).strip(),
                        "type": str(r.get("type", "")).strip(),
                        "theoricalQty": str(r.get("theoricalQty", "")).strip(),
                        "part": str(r.get("part", "")).strip(),
                    }
                    for r in data["results"]
                ]
                total = data.get("page", {}).get("totalRecords")
                logger.info(
                    f"Recebidos {len(results)} registros via JSON "
                    f"(totalRecords={total})"
                )
                return results

            logger.warning("JSON vazio/indisponível. Tentando fallback por HTML…")
            return self._parse_from_html()

        except Exception as e:
            logger.error(f"Erro no scraping B3: {e}")
            return []


    def _get_json_ibov(self, date_str: Optional[str]) -> Optional[Dict]:
       
        payload = {
            "language": "pt-br",
            "pageNumber": 1,
            "pageSize": 120,
            "index": "IBOV",
            "segment": "1",
        }
        if date_str:
            payload["date"] = date_str  # ex: "25/09/25" ou "25/09/2025"

        encoded = base64.b64encode(
            json.dumps(payload, separators=(",", ":")).encode("utf-8")
        ).decode("utf-8")

        url = f"{self.base_api}/{encoded}"
        logger.info(f"Chamando JSON B3 (indexProxy): {url}")
        resp = self.session.get(url, headers=self.headers_json, timeout=30)
        resp.raise_for_status()

        try:
            data = resp.json()
            if isinstance(data, dict) and "results" in data:
                return data
        except ValueError:
            logger.info("Resposta não é JSON válido.")
        return None

    def _parse_from_html(self) -> List[Dict]:
       
        logger.info(f"Fazendo scraping da página HTML: {self.base_page}")
        response = self.session.get(self.base_page, headers=self.headers_html, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        rows = soup.find_all("tr")
        stocks_data: List[Dict] = []
        for row in rows:
            cells = row.find_all("td")
            if len(cells) == 5:
                try:
                    cod = cells[0].get_text(strip=True)
                    asset = cells[1].get_text(strip=True)
                    type_ = cells[2].get_text(strip=True)
                    theoricalQty_str = cells[3].get_text(strip=True)
                    part_str = cells[4].get_text(strip=True)
                    if not cod or not asset or not type_:
                        continue
                    stocks_data.append({
                        "cod": cod,
                        "asset": asset,
                        "type": type_,
                        "theoricalQty": theoricalQty_str,
                        "part": part_str,
                    })
                except Exception as e:
                    logger.warning(f"Erro ao processar linha: {e}")
                    continue

        if not stocks_data:
            logger.warning("Nenhum dado extraído da tabela. Retornando lista vazia.")
        else:
            logger.info(f"Extraídos {len(stocks_data)} registros da tabela HTML")
        return stocks_data


    def _parse_number(self, value: str) -> Optional[float]:
        if not value or value.strip() == '':
            return None
        try:
            clean_value = value.strip().replace('.', '').replace(',', '.')
            clean_value = ''.join(c for c in clean_value if c.isdigit() or c in '.,')
            if not clean_value:
                return None
            return float(clean_value)
        except (ValueError, AttributeError):
            return None

    def _parse_percentage(self, value: str) -> Optional[float]:
        if not value or value.strip() == '':
            return None
        try:
            clean_value = value.strip().replace('%', '').replace(',', '.')
            clean_value = ''.join(c for c in clean_value if c.isdigit() or c in '.,')
            if not clean_value:
                return None
            return float(clean_value)
        except (ValueError, AttributeError):
            return None
