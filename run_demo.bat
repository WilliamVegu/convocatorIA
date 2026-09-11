@echo off
REM ==============================================================================
REM ATS TCS Peru - 1-Click Demo Launcher for Windows
REM Talent Acquisition Engine & Candidate Lifecycle Management
REM ==============================================================================

setlocal enabledelayedexpansion

echo ==============================================================================
echo [ATS TCS PERU] Iniciando Sistema de Adquisicion de Talento...
echo ==============================================================================

REM 1. Verificar instalacion de Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python no se encuentra instalado o no esta en el PATH del sistema.
    echo Por favor instale Python 3.11+ desde https://www.python.org/
    pause
    exit /b 1
)

REM 2. Crear y activar entorno virtual .venv si no existe
if not exist ".venv" (
    echo [INFO] Creando entorno virtual .venv...
    python -m venv .venv
)

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM 3. Instalar dependencias si requirements.txt existe
if exist "requirements.txt" (
    echo [INFO] Verificando dependencias del sistema...
    pip install -r requirements.txt --quiet
)

REM 4. Poblar datos historicos y base de datos relacional
echo [INFO] Inicializando base de datos corporativa y datos semilla...
python scripts/seed_historical_data.py

REM 5. Lanzar aplicacion interactiva en Streamlit
echo [INFO] Lanzando interfaz web Streamlit en el navegador predeterminado...
echo ==============================================================================
echo Aplicacion disponible en: http://localhost:8501
echo Credenciales Demo:
echo   - Head of TA: admin.ta@tcs.com / Password123!
echo   - Senior Recruiter: recruiter.lead@tcs.com / Password123!
echo   - Compliance Officer: compliance.officer@tcs.com / Password123!
echo ==============================================================================

python -m streamlit run src/app.py --server.headless=false

pause
