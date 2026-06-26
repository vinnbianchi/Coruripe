@echo off

:: 1. Entra na pasta correta do projeto
cd /d "C:\siteclima"

:: 2. Executa a sua automação em Python
python automacao_completa.py

:: 3. Executa os comandos do Git enviando APENAS o index.html
git add index.html
git commit -m "Atualizacao automatica do index.html"
git push origin main --force