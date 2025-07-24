@echo off
REM Script de nettoyage automatique des fichiers temporaires
REM Supprime les fichiers dans temp/ plus anciens que 5 heures

echo [%date% %time%] Debut du nettoyage automatique des fichiers temporaires

cd /d "c:\Users\mlemsi\Desktop\workspace\Workspace_DataAlign"

REM Supprimer les fichiers plus anciens que 5 heures (300 minutes)
forfiles /p temp /m *.* /c "cmd /c del @path" /d -1 2>nul

if %errorlevel% equ 0 (
    echo [%date% %time%] Nettoyage termine avec succes
) else (
    echo [%date% %time%] Aucun fichier a supprimer ou erreur
)

REM Executer le script Python pour un nettoyage plus precis
python cleanup_temp.py

echo [%date% %time%] Fin du nettoyage automatique
