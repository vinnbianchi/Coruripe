@echo off
:: Força o terminal a reconhecer caracteres com acento (como o Ú de AÇÚCAR)
chcp 65001 > nul

:: 1. Entra na pasta correta do projeto
cd /d "C:\Users\vgbianchi\OneDrive - SA USINA CORURIPE AÇÚCAR E ALCOOL\Área de Trabalho\siteclima"

:: 2. Executa a sua automação em Python
python automacao_completa.py

:: 3. Executa os comandos do Git para atualizar o GitHub
git add .
git commit -m "Atualizacao automatica apos rodar script Python"
git push origin main

pause