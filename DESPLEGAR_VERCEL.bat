@echo off
chcp 65001 > nul
echo ========================================================
echo   DESPLIEGUE AUTOMATICO DE OPINIONPULSE AI EN VERCEL
echo ========================================================
echo.
echo Iniciando proceso de publicacion Serverless en Vercel...
echo.
call npx vercel --prod
echo.
echo ========================================================
echo   ¡Despliegue finalizado!
echo ========================================================
pause
