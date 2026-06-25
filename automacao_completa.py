import hmac
import hashlib
import time
import os
import requests
import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright

# --- CONFIGURAÇÕES DA WEATHERLINK ---
API_KEY = "uecxhqarycebpd9cvepuy0m5pddti7z7"
API_SECRET = "o3umrge9teply7yckebql5dggplul9dp"
STATION_ID = "a176898a-e63c-45eb-980c-dd7175bea3e8"

def buscar_dados_api(station_id, api_key, api_secret):
    """Faz a autenticação e busca os dados atuais da estação meteorológica"""
    endpoint = f"/v2/current/{station_id}"
    base_url = "https://api.weatherlink.com"
    timestamp = int(time.time())
    
    params = {
        "api-key": api_key,
        "t": timestamp
    }
    
    msg_sign = f"api-key{api_key}station-id{station_id}t{timestamp}"
    api_signature = hmac.new(
        api_secret.encode('utf-8'),
        msg_sign.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    params["api-signature"] = api_signature
    response = requests.get(base_url + endpoint, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Erro na API WeatherLink ({response.status_code}): {response.text}")

def processar_json_para_dados(json_data):
    """Extrai as variáveis meteorológicas do JSON da estação"""
    dados = {
        "Estacao": "Usina",
        "Data_Hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }
    
    senores = json_data.get("sensors", [])
    for sensor in senores:
        data_list = sensor.get("data", [])
        if not data_list:
            continue
        
        data = data_list[0]
        sensor_type = sensor.get("sensor_type")
        
        # SENSOR EXTERNO PRINCIPAL (Vento, Chuva, Temp Externa, Umidade)
        if sensor_type == 37:
            if "rainfall_daily_mm" in data: dados["Chuva_Acumulada_Dia_mm"] = data.get("rainfall_daily_mm")
            if "rainfall_monthly_mm" in data: dados["Chuva_Acumulada_Mes_mm"] = data.get("rainfall_monthly_mm")
            if "rainfall_year_mm" in data: dados["Chuva_Acumulada_Ano_mm"] = data.get("rainfall_year_mm")
            if "rain_storm_mm" in data: dados["Chuva_Ultima_Tempestade_mm"] = data.get("rain_storm_mm")

            if "temp" in data:
                dados["Temp_Externa_C"] = round((data.get("temp") - 32) * 5/9, 2) if data.get("temp") is not None else None
            if "hum" in data: dados["Umidade_Externa_%"] = data.get("hum")
            if "dew_point" in data: dados["Ponto_Orvalho_C"] = round((data.get("dew_point") - 32) * 5/9, 2) if data.get("dew_point") is not None else None
            if "wind_chill" in data: dados["Sensacao_Termica_Vento_C"] = round((data.get("wind_chill") - 32) * 5/9, 2) if data.get("wind_chill") is not None else None
            if "heat_index" in data: dados["Indice_Calor_C"] = round((data.get("heat_index") - 32) * 5/9, 2) if data.get("heat_index") is not None else None
                
            if "wind_speed_last" in data: dados["Vento_Velocidade_Atual_kmh"] = round(data.get("wind_speed_last") * 1.60934, 1) if data.get("wind_speed_last") is not None else None
            if "wind_dir_last" in data: dados["Vento_Direcao_Atual_Graus"] = data.get("wind_dir_last")
            if "wind_speed_avg_last_10_min" in data: dados["Vento_Medio_10min_kmh"] = round(data.get("wind_speed_avg_last_10_min") * 1.60934, 1) if data.get("wind_speed_avg_last_10_min") is not None else None
            if "wind_speed_hi_last_10_min" in data: dados["Vento_Rajada_Max_10min_kmh"] = round(data.get("wind_speed_hi_last_10_min") * 1.60934, 1) if data.get("wind_speed_hi_last_10_min") is not None else None
                
        # SENSOR AMBIENTE INTERNO
        elif sensor_type == 243:
            if "temp_in" in data: dados["Temp_Interna_C"] = round((data.get("temp_in") - 32) * 5/9, 2) if data.get("temp_in") is not None else None
            if "hum_in" in data: dados["Umidade_Interna_%"] = data.get("hum_in")

        # BARÔMETRO (Pressão)
        elif sensor_type == 242:
            if "bar_sea_level" in data: dados["Pressao_Nivel_Mar_hPa"] = round(data.get("bar_sea_level") * 33.8639, 1) if data.get("bar_sea_level") is not None else None

        # DIAGNÓSTICO (Wi-Fi)
        elif sensor_type == 504:
            if "wifi_rssi" in data: dados["Sinal_WiFi_dBm"] = data.get("wifi_rssi")
                
    return dados

def gerar_tabela_clima_html(dados):
    """Estrutura uma tabela HTML bonita e limpa com os dados meteorológicos obtidos"""
    de_para = {
        "Data_Hora": "Data/Hora da Leitura",
        "Chuva_Acumulada_Dia_mm": "Chuva Acumulada no Dia",
        "Chuva_Acumulada_Mes_mm": "Chuva Acumulada no Mês",
        "Chuva_Acumulada_Ano_mm": "Chuva Acumulada no Ano",
        "Chuva_Ultima_Tempestade_mm": "Última Tempestade",
        "Vento_Velocidade_Atual_kmh": "Velocidade do Vento Atual",
        "Vento_Medio_10min_kmh": "Vento Médio (10 min)",
        "Vento_Rajada_Max_10min_kmh": "Rajada Máxima (10 min)",
        "Sensacao_Termica_Vento_C": "Sensação Térmica",
        "Ponto_Orvalho_C": "Ponto de Orvalho",
        "Pressao_Nivel_Mar_hPa": "Pressão Atmosférica",
        "Temp_Externa_C": "Temperatura Externa",
        "Umidade_Externa_%": "Umidade Externa",
    }
    
    html_clima = """
    <table class="tabela-clima" style="width: 100%; border-collapse: collapse; font-size: 15px; background: white; border-radius: 8px; overflow: hidden;">
        <thead>
            <tr style="background-color: #d35400; color: white; text-align: left;">
                <th style="padding: 12px 15px; border: 1px solid #e0e0e0; font-size: 16px; width: 60%;">Variável Meteorológica</th>
                <th style="padding: 12px 15px; border: 1px solid #e0e0e0; font-size: 16px; text-align: right; width: 40%;">Indicador Atual</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for chave, rotulo in de_para.items():
        valor = dados.get(chave)
        if valor is not None:
            unidade = ""
            if "mm" in chave: unidade = " mm"
            elif "C" in chave: unidade = " °C"
            elif "%" in chave: unidade = " %"
            elif "kmh" in chave: unidade = " km/h"
            elif "hPa" in chave: unidade = " hPa"
            elif "dBm" in chave: unidade = " dBm"
            
            # Ajustado: background-color unificado para branco (#ffffff) em ambas as colunas
            html_clima += f"""
            <tr style="border-bottom: 1px solid #eef2f5; background-color: #ffffff;">
                <td style="padding: 10px 15px; font-weight: bold; color: #2c3e50; border: 1px solid #e0e0e0; text-align: left !important; width: 60% !important;">{rotulo}</td>
                <td style="padding: 10px 15px; color: #333; font-weight: bold; text-align: right; border: 1px solid #e0e0e0; font-size: 16px; width: 40% !important;">{valor}{unidade}</td>
            </tr>
            """
            
    html_clima += "</tbody></table>"
    return html_clima

def executar_automacao_completa():
    print("1. Buscando dados da API WeatherLink...")
    try:
        json_resposta = buscar_dados_api(STATION_ID, API_KEY, API_SECRET)
        dados_clima = processar_json_para_dados(json_resposta)
        tabela_clima_html = gerar_tabela_clima_html(dados_clima)
        print("Dados climáticos obtidos com sucesso!")
    except Exception as e:
        print(f"Aviso: Falha ao obter dados climáticos ({e}). Gerando sem informações do clima.")
        tabela_clima_html = "<p>Dados meteorológicos indisponíveis no momento.</p>"

    print("\n2. Iniciando extração do SimpleFarm via Playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("Acessando a página de login...")
        page.goto("https://simplefarm.usinacoruripe.com.br/Login")

        page.fill("#UserName", "vgbianchi")
        page.fill("#Password", "Infoway9679")
        page.click("input[type='submit']")
        page.wait_for_load_state("networkidle")
        print("Login efetuado!")

        # --- CAPTURAR ABA 1 ---
        print("Acessando a aba 'Relatório Geral - Cota Turno'...")
        seletor_aba_1 = "#tabstrip-tab-2, li[role='tab']:has-text('Relatório Geral - Cota Turno')"
        page.wait_for_selector(seletor_aba_1, state="visible")
        page.click(seletor_aba_1, force=True)
        page.wait_for_load_state("networkidle")
        time.sleep(5) 

        seletor_quadro_1 = "#grid-stack-203"
        page.wait_for_selector(seletor_quadro_1, state="attached")
        html_aba_1 = page.inner_html(seletor_quadro_1)
        print("Aba 1 integrada!")

        # --- CAPTURAR ABA 2 ---
        print("Acessando a aba 'Cota Turno - 2'...")
        seletor_aba_2 = "#tabstrip-tab-3"
        page.wait_for_selector(seletor_aba_2, state="attached")
        page.click(seletor_aba_2, force=True)
        page.locator(seletor_aba_2).evaluate("el => el.click()")
        page.wait_for_load_state("networkidle")
        time.sleep(6) 

        seletor_quadro_2 = "div[data-panelid='238'], #tabstrip-3, div.k-content.k-active"
        page.wait_for_selector(seletor_quadro_2, state="attached")
        
        if page.locator("div[data-panelid='238']").count() > 0:
            html_aba_2 = page.locator("div[data-panelid='238']").inner_html()
        else:
            html_aba_2 = page.locator("div.k-content.k-active").inner_html()
        print("Aba 2 integrated!")

        browser.close()

        # --- CONSTRUÇÃO DO HTML UNIFICADO ---
        html_final = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <title>Relatório Integrado - Cota Turno & Clima</title>
            <style>
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    padding: 20px; 
                    background: #f4f6f9; 
                    margin: 0;
                }}
                h1 {{ color: #2c3e50; font-size: 32px; margin-bottom: 5px; }}
                h2 {{
                    color: #e65729; font-size: 25px; margin-top: 30px; margin-bottom: 10px;
                    border-left: 4px solid #2980b9; padding-left: 10px;
                }}
                .quadro {{ 
                    background: white; 
                    padding: 20px; 
                    border-radius: 8px; 
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
                    max-width: 100%;
                    overflow-x: auto !important; 
                    overflow-y: visible !important; 
                    height: auto !important;
                    margin-bottom: 25px;
                }}
                
                /* DESTRUIÇÃO DE TRAVAS DO KENDO UI */
                .quadro *, 
                .quadro div, 
                .quadro .k-grid-content, 
                .quadro .k-grid, 
                .quadro .k-grid-virtualscrollable,
                .quadro .grid-stack,
                .quadro .grid-stack-item {{
                    height: auto !important; 
                    max-height: none !important;
                    overflow: visible !important; 
                    position: relative !important;
                }}
                
                /* Formatação Geral das Tabelas do SimpleFarm */
                .quadro table {{ 
                    width: 100% !important; 
                    border-collapse: collapse !important; 
                    margin-top: 0px !important;
                    margin-bottom: 0px !important;
                    min-width: 2200px !important;   
                    table-layout: fixed !important; 
                }}
                
                /* AJUSTADO: Alvo cirúrgico para a tabela de clima ficar sem barras e com metade do tamanho da tela */
                .quadro-clima {{
                    width: 50% !important;
                    max-width: 600px !important;
                    min-width: 350px !important;
                    overflow-x: hidden !important; /* Sem barra de rolagem */
                }}

                .quadro table.tabela-clima {{
                    min-width: 100% !important;
                    max-width: 100% !important;
                    table-layout: fixed !important;
                }}
                
                /* Remove travas de largura inline injetadas por JavaScript */
                .quadro col {{
                    width: auto !important;
                }}
                
                /* Correção da Sobreposição do SimpleFarm */
                .quadro th, .quadro td {{ 
                    border: 1px solid #e0e0e0 !important; 
                    padding: 10px 12px !important; 
                    font-size: 18px !important;          
                    font-weight: bold !important;       
                    white-space: nowrap !important;
                    overflow: hidden !important;        
                    text-overflow: ellipsis !important; 
                }}
                
                /* DEFINIÇÃO CIRÚRGICA DE LARGURAS POR COLUNA (Apenas tabelas normais do SimpleFarm) */
                .quadro table:not(.tabela-clima) th:nth-child(1), 
                .quadro table:not(.tabela-clima) td:nth-child(1) {{ 
                    width: 320px !important;
                    min-width: 320px !important;
                    text-align: left !important; 
                }}
                
                .quadro table:not(.tabela-clima) th:nth-child(n+2), 
                .quadro table:not(.tabela-clima) td:nth-child(n+2) {{ 
                    width: 140px !important;
                    min-width: 140px !important;
                    text-align: right !important; 
                }}
                
                /* Modificações específicas para os textos e fundos da tabela do clima */
                .quadro table.tabela-clima th, 
                .quadro table.tabela-clima td {{
                    white-space: normal !important;
                    font-size: 16px !important;
                    background-color: #ffffff !important; /* Mesma cor em todas as linhas */
                }}
                
                .quadro th, .quadro thead tr {{ 
                    background-color: #2c3e50 !important; 
                    color: white !important; 
                    font-weight: 700 !important;        
                }}
                
                /* Garante a cor laranja na linha de cima da tabela de clima */
                .quadro table.tabela-clima thead tr, .quadro table.tabela-clima thead th {{
                    background-color: #d35400 !important;
                }}

                .quadro .k-icon, .quadro .k-button {{
                    display: inline-block;
                }}
            </style>
        </head>
        <body>
            <div style="display: flex; align-items: center; margin-bottom: 20px;">
                <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQb37nV2w2MUoPfUrYi45QPnhOqeMu-pcC6UYKDZGkoOQ&s" width="180" height="100" style="margin-right: 15px;" alt="Logo_Usina">
                <h1 style="margin-left: 15px; color: #2c3e50;">Controle Agrícola - Usina Coruripe</h1>
            </div>

            <h2>COTA = TURNO A    -    CAMPO FLORIDO</h2>
            <div class="quadro">
                {html_aba_1}
            </div>

            <h2>COTA = TURNO B    -    CAMPO FLORIDO</h2>
            <div class="quadro">
                {html_aba_2}
            </div>

            <h2>CONDIÇÕES METEOROLÓGICAS</h2>
            <div class="quadro quadro-clima">
                {tabela_clima_html}
            </div>
            <footer>
                <p>&copy; Desenvolvido por Vinicius Bianchi - (34) 99766-8139</p>
            </footer>
        </body>
        </html>
        """

        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_final)
        
        print("\nSucesso! O arquivo 'index.html' foi gerado com as correções visuais solicitadas.")

if __name__ == "__main__":
    executar_automacao_completa()