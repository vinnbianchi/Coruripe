import time
from playwright.sync_api import sync_playwright

def capturar_quadro():
    with sync_playwright() as p:
        # Abre o navegador visível
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print("Acessando a página de login...")
        page.goto("https://simplefarm.usinacoruripe.com.br/Login")

        # 1. Login
        page.fill("#UserName", "vgbianchi")
        page.fill("#Password", "Infoway9679")
        page.click("input[type='submit']")
        page.wait_for_load_state("networkidle")
        print("Login efetuado!")

        # ==========================================
        # PARTE 1: CAPTURAR ABA 1 (Relatório Geral - Cota Turno)
        # ==========================================
        print("\n--- PROCESSANDO ABA 1 ---")
        print("Acessando a aba 'Relatório Geral - Cota Turno'...")
        seletor_aba_1 = "#tabstrip-tab-2, li[role='tab']:has-text('Relatório Geral - Cota Turno')"
        page.wait_for_selector(seletor_aba_1, state="visible")
        page.click(seletor_aba_1, force=True)
        page.wait_for_load_state("networkidle")
        
        print("Aguardando carregamento dos dados da Aba 1...")
        time.sleep(5) 

        # Usando o ID específico da Aba 1 para evitar os favoritos ocultos
        seletor_quadro_1 = "#grid-stack-203"
        page.wait_for_selector(seletor_quadro_1, state="attached")
        html_aba_1 = page.inner_html(seletor_quadro_1)
        print("Aba 1 capturada com sucesso!")


       # ==========================================
        # PARTE 2: CAPTURAR ABA 2 (Cota Turno - 2)
        # ==========================================
        print("\n--- PROCESSANDO ABA 2 ---")
        
        # Seletor ultra-simplificado e direto por ID (visto no seu HTML do print)
        seletor_aba_2 = "#tabstrip-tab-3"
        
        print("Aguardando a aba 'Cota Turno - 2' ficar pronta...")
        page.wait_for_selector(seletor_aba_2, state="attached")
        
        print("Clicando na aba 'Cota Turno - 2'...")
        # Removemos o argumento inválido. O Playwright já rola a página sozinho se precisar.
        page.click(seletor_aba_2, force=True)
        
        # Disparo de segurança via JavaScript caso o clique físico falhe no Kendo UI
        page.locator(seletor_aba_2).evaluate("el => el.click()")
        
        print("Aba alterada! Aguardando o carregamento dos dados...")
        page.wait_for_load_state("networkidle")
        time.sleep(6) 

        # Seletor cirúrgico: foca no painel da Aba 2 (ID 238) e pega todo o conteúdo de dados dele
        seletor_quadro_2 = "div[data-panelid='238'], #tabstrip-3, div.k-content.k-active"
        page.wait_for_selector(seletor_quadro_2, state="attached")
        
        # Captura o HTML interno do painel da Aba 2, ignorando de vez os "Favoritos"
        if page.locator("div[data-panelid='238']").count() > 0:
            html_aba_2 = page.locator("div[data-panelid='238']").inner_html()
        else:
            html_aba_2 = page.locator("div.k-content.k-active").inner_html()
            
        print("Aba 2 capturada com sucesso de forma isolada!")

        # Fecha o navegador de automação
        browser.close()


        # ==========================================
        # PARTE 3: GERAR O HTML FINAL UNIFICADO (TEXTO MAIOR E EM NEGRITO)
        # ==========================================
        html_final = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <title>Relatório Geral - Cota Turno</title>
            <style>
                /* Configurações Globais */
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    padding: 20px; 
                    background: #f4f6f9; 
                    margin: 0;
                }}
                h1 {{ color: #d75413; font-size: 300px; margin-bottom: 5px; }}
                h2 {{
                    color: #e65729; font-size: 25px; margin-top: 30px; margin-bottom: 10px;
                    border-left: 4px solid #2980b9; padding-left: 10px;
                }}
                p {{ color: #7f8c8d; font-size: 14px; margin-bottom: 20px; }}
                
                /* Container Principal do Quadro */
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
                
                # ==========================================
                # PARTE 3: SINCRO-LAYOUT DO CABEÇALHO AZUL
                # ==========================================
                
                # ==========================================
                # PARTE 3: LARGURA PADRONIZADA E RÍGIDA
                # ==========================================
                
                /* Formatação Geral das Tabelas */
                .quadro table {{ 
                    width: 100% !important; 
                    border-collapse: collapse !important; 
                    margin-top: 0px !important;
                    margin-bottom: 0px !important;
                    min-width: 1700px !important; /* Alargado ligeiramente para comportar as colunas fixas */
                    table-layout: fixed !important; 
                }}
                
                /* Remove travas de largura dinâmicas que o Kendo injeta em elementos <col> */
                .quadro col {{
                    width: auto !important;
                }}
                
                /* Estilo base e LARGURA FIXA IGUAL para todas as células */
                .quadro th, .quadro td {{ 
                    border: 1px solid #e0e0e0 !important; 
                    padding: 10px 6px !important;       /* Padding lateral reduzido para ajudar no espaço */
                    font-size: 14px !important;          
                    font-weight: bold !important;       
                    
                    /* Força todas as colunas a terem exatamente o mesmo tamanho */
                    width: 150px !important;             
                    max-width: 150px !important;
                    min-width: 150px !important;
                    
                    /* Comportamento para engolir o texto sem quebrar o layout */
                    white-space: nowrap !important; 
                    overflow: hidden !important;        /* Esconde o texto que ultrapassar */
                    text-overflow: ellipsis !important; /* Adiciona '...' no final do texto cortado */
                }}
                
                /* Cor de Fundo do Cabeçalho */
                .quadro th, .quadro thead tr {{ 
                    background-color: #2c3e50 !important; 
                    color: white !important; 
                }}

                /* --- MAPEAMENTO DE ALINHAMENTO --- */
                
                /* Coluna 1 (Grupo): Alinhada à Esquerda (mas com a mesma largura das outras) */
                .quadro th:nth-child(1), 
                .quadro td:nth-child(1) {{ 
                    text-align: left !important; 
                }}
                
                /* Todas as outras colunas (numéricas): Alinhadas à Direita */
                .quadro td:nth-child(n+2) {{ text-align: right !important; }}
                .quadro th:nth-child(n+2) {{ text-align: right !important; }}


                
                /* ALTERADO AQUI: Letra maior (14px) e tudo em Negrito (bold) */
                .quadro th, .quadro td {{ 
                    border: 1px solid #e0e0e0 !important; 
                    padding: 10px 12px !important; 
                    text-align: left !important;
                    font-size: 18px !important;          /* Aumentado de 13px para 14px */
                    font-weight: bold !important;       /* Força o negrito em todas as células */
                    white-space: nowrap !important; 
                }}
                
                /* Estilo do Cabeçalho */
                .quadro th, .quadro thead tr {{ 
                    background-color: #2c3e50 !important; 
                    color: white !important; 
                    font-weight: 700 !important;        /* Destaca ainda mais o cabeçalho */
                }}
                
                /* Linhas Alternadas */
                .quadro tr:nth-child(even) {{ 
                    background-color: #f8f9fa !important; 
                }}
                
                /* Garante exibição de botões nativos */
                .quadro .k-icon, .quadro .k-button {{
                    display: inline-block;
                }}
            </style>
        </head>
        <body>
            <img src="data:image/png;base64,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"  width= "180"; height="100"; margin-right: 5px; alt="Logo Usina Coruripe"
            <h1 style="color: #000000; font-size: 300px; margin-top: 30px; margin-bottom: 10px; border-left: 4px solid #d35400; padding-left: 10px;"></h1>
            
            <h2>COTA = TURNO A    -    CAMPO FLORIDO</h2>
            <div class="quadro">
                {html_aba_1}
            </div>

            <h2>COTA = TURNO B    -    CAMPO FLORIDO</h2>
            <div class="quadro">
                {html_aba_2}
            </div>
        </body>
        </html>
        """

        with open("painel_automatico.html", "w", encoding="utf-8") as f:
            f.write(html_final)
        
        print("\nProntinho! O arquivo 'painel_automatico.html' foi gerado com as letras maiores e em negrito.")

if __name__ == "__main__":
    capturar_quadro()