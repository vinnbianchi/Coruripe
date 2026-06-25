import hmac
import hashlib
import time
import os
import requests
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÕES DA WEATHERLINK ---
API_KEY = "uecxhqarycebpd9cvepuy0m5pddti7z7"
API_SECRET = "o3umrge9teply7yckebql5dggplul9dp"
STATION_ID = "a176898a-e63c-45eb-980c-dd7175bea3e8"  # Geralmente um número numérico interno da API

# --- CONFIGURAÇÕES DE E-MAIL ---
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

EMAIL_REMETENTE = "vinnbianchi@gmail.com"
SENHA_APP = "wgug ssik qrtj wijr"  # Gerada na segurança da conta Google
EMAIL_DESTINATARIO = "vinicius.bianchi@usinacoruripe.com.br,vinnbianchi@hotmail.com"


def buscar_dados_api(station_id, api_key, api_secret):
    """Faz a autenticação e busca os dados atuais da estação usando o UUID ou ID numérico"""
    endpoint = f"/v2/current/{station_id}"
    base_url = "https://api.weatherlink.com"
    timestamp = int(time.time())
    
    # Parâmetros obrigatórios na URL
    params = {
        "api-key": api_key,
        "t": timestamp
    }
    
    # REGRA DE ASSINATURA DA WEATHERLINK V2:
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
    """Extrai todas as variáveis meteorológicas baseadas no JSON real da estação"""
    # Adicionamos a descrição "Usina" e a Data/Hora logo no início do dicionário
    dados = {
        "Estacao": "Usina",
        "Data_Hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    sensores = json_data.get("sensors", [])
    
    for sensor in sensores:
        data_list = sensor.get("data", [])
        if not data_list:
            continue
        
        data = data_list[0]
        sensor_type = sensor.get("sensor_type")
        
        # --- 1. SENSOR EXTERNO PRINCIPAL (Vento, Chuva, Temp Externa, Umidade Externa) ---
        if sensor_type == 37:
            # Chuva
            if "rainfall_daily_mm" in data:
                dados["Chuva_Acumulada_Dia_mm"] = data.get("rainfall_daily_mm")
            if "rainfall_monthly_mm" in data:
                dados["Chuva_Acumulada_Mes_mm"] = data.get("rainfall_monthly_mm")
            if "rainfall_year_mm" in data:
                dados["Chuva_Acumulada_Ano_mm"] = data.get("rainfall_year_mm")
            if "rain_storm_mm" in data:
                dados["Chuva_Ultima_Tempestade_mm"] = data.get("rain_storm_mm")

            # Temperatura e Umidade Externa
            if "temp" in data:
                dados["Temp_Externa_F"] = data.get("temp")
                dados["Temp_Externa_C"] = round((data.get("temp") - 32) * 5/9, 2) if data.get("temp") is not None else None
            if "hum" in data:
                dados["Umidade_Externa_%"] = data.get("hum")
            if "dew_point" in data:
                dados["Ponto_Orvalho_C"] = round((data.get("dew_point") - 32) * 5/9, 2) if data.get("dew_point") is not None else None
            if "wind_chill" in data:
                dados["Sensacao_Termica_Vento_C"] = round((data.get("wind_chill") - 32) * 5/9, 2) if data.get("wind_chill") is not None else None
            if "heat_index" in data:
                dados["Indice_Calor_C"] = round((data.get("heat_index") - 32) * 5/9, 2) if data.get("heat_index") is not None else None
                
            # Vento
            if "wind_speed_last" in data:
                dados["Vento_Velocidade_Atual_kmh"] = round(data.get("wind_speed_last") * 1.60934, 1) if data.get("wind_speed_last") is not None else None
            if "wind_dir_last" in data:
                dados["Vento_Direcao_Atual_Graus"] = data.get("wind_dir_last")
            if "wind_speed_avg_last_10_min" in data:
                dados["Vento_Medio_10min_kmh"] = round(data.get("wind_speed_avg_last_10_min") * 1.60934, 1) if data.get("wind_speed_avg_last_10_min") is not None else None
            if "wind_speed_hi_last_10_min" in data:
                dados["Vento_Rajada_Max_10min_kmh"] = round(data.get("wind_speed_hi_last_10_min") * 1.60934, 1) if data.get("wind_speed_hi_last_10_min") is not None else None
                
        # --- 2. SENSOR AMBIENTE INTERNO ---
        elif sensor_type == 243:
            if "temp_in" in data:
                dados["Temp_Interna_C"] = round((data.get("temp_in") - 32) * 5/9, 2) if data.get("temp_in") is not None else None
            if "hum_in" in data:
                dados["Umidade_Interna_%"] = data.get("hum_in")

        # --- 3. BARÔMETRO (Pressão Atmosférica) ---
        elif sensor_type == 242:
            if "bar_sea_level" in data:
                dados["Pressao_Nivel_Mar_hPa"] = round(data.get("bar_sea_level") * 33.8639, 1) if data.get("bar_sea_level") is not None else None
            if "bar_trend" in data:
                dados["Tendencia_Barometrica"] = data.get("bar_trend")

        # --- 4. DIAGNÓSTICO DO DISPOSITIVO (Wi-Fi e Bateria) ---
        elif sensor_type == 504:
            if "wifi_rssi" in data:
                dados["Sinal_WiFi_dBm"] = data.get("wifi_rssi")
                
    return dados

def enviar_email(arquivo_planilha):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = EMAIL_DESTINATARIO 
    msg['Subject'] = f"Relatório Meteorológico Oficial - {datetime.now().strftime('%d/%m/%Y')}"

    corpo = "Olá,\n\nSegue em anexo a planilha atualizada com os dados extraídos diretamente da API da WeatherLink.\n\n"
    msg.attach(MIMEText(corpo, 'plain'))

    with open(arquivo_planilha, "rb") as anexo:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(anexo.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename= {arquivo_planilha}")
        msg.attach(part)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_REMETENTE, SENHA_APP)
        
        lista_destinatarios = EMAIL_DESTINATARIO.split(',')
        server.sendmail(EMAIL_REMETENTE, lista_destinatarios, msg.as_string())
        server.quit()
        print("E-mail enviado com sucesso para todos os destinatários!")
    except Exception as e:
        print(f"Erro ao enviar o e-mail: {e}")

# --- EXECUÇÃO DO FLUXO PRINCIPAL ---
try:
    print("Conectando à API da WeatherLink...")
    json_resposta = buscar_dados_api(STATION_ID, API_KEY, API_SECRET)
    
    print("Processando dados recebidos...")
    novos_dados = processar_json_para_dados(json_resposta)
    print("Dados extraídos com sucesso:", novos_dados)
    
    nome_arquivo = "Historico_Estacao_CFL.xlsx"
    df_novo = pd.DataFrame([novos_dados])
    
    # REORGANIZADO: Colunas de chuva movidas para logo após Data_Hora
    ordem_colunas = [
        "Estacao", 
        "Data_Hora", 
        "Chuva_Acumulada_Dia_mm", 
        "Chuva_Acumulada_Mes_mm", 
        "Chuva_Acumulada_Ano_mm", 
        "Chuva_Ultima_Tempestade_mm",
        "Temp_Externa_C", 
        "Temp_Externa_F", 
        "Umidade_Externa_%", 
        "Ponto_Orvalho_C", 
        "Sensacao_Termica_Vento_C", 
        "Indice_Calor_C",
        "Vento_Velocidade_Atual_kmh", 
        "Vento_Direcao_Atual_Graus", 
        "Vento_Medio_10min_kmh", 
        "Vento_Rajada_Max_10min_kmh",
        "Temp_Interna_C", 
        "Umidade_Interna_%", 
        "Pressao_Nivel_Mar_hPa", 
        "Tendencia_Barometrica", 
        "Sinal_WiFi_dBm"
    ]
    
    df_novo = df_novo.reindex(columns=ordem_colunas)
    
    if os.path.exists(nome_arquivo):
        df_existente = pd.read_excel(nome_arquivo)
        df_existente = df_existente.reindex(columns=ordem_colunas)
        df_final = pd.concat([df_existente, df_novo], ignore_index=True)
    else:
        df_final = df_novo
        
    df_final.to_excel(nome_arquivo, index=False)
    print("Planilha Excel atualizada com as colunas de chuva reorganizadas!")
    
    enviar_email(nome_arquivo)

except Exception as erro:
    print(f"Ocorreu uma falha no processo: {erro}")