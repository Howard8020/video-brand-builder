@echo off
REM ===================================================================
REM  Video Brand Builder - LOCAL backend (internal production mode)
REM
REM  Runs the API on this machine. All persistent data lives on the D:
REM  data drive, deliberately OUTSIDE the repo, so the drive can be
REM  physically moved to another server later and the data travels with
REM  it. Only this file would need its paths changed.
REM
REM    D:\vbb\generated   rendered MP4 clips
REM    D:\vbb\data        SQLite database
REM
REM  Secrets (JWT, Anthropic key, GCP service account) come from
REM  .env in this folder - never from this script.
REM ===================================================================

setlocal
set "BACKEND_DIR=%~dp0"
cd /d "%BACKEND_DIR%"

REM ---- data drive ---------------------------------------------------
set "VBB_DATA_DIR=D:\vbb"
set "VBB_GENERATED_DIR=%VBB_DATA_DIR%\generated"
set "VBB_ASSEMBLED_DIR=%VBB_DATA_DIR%\assembled"
set "DATABASE_URL=sqlite:///%VBB_DATA_DIR%/data/video_brand_builder.db"

REM ---- internal mode ------------------------------------------------
REM No Stripe, no credit metering: we render for ourselves. The rate
REM limits below are therefore the ONLY bound on Vertex AI spend.
set "VBB_RENDER_BYPASS_CREDITS=true"
set "VBB_RENDER_LIMIT_PER_DAY=1"
set "VBB_RENDER_LIMIT_PER_HOUR=2"
set "VBB_RENDER_MAX_CONCURRENT=12"

REM ---- local origins (frontend dev server) --------------------------
set "VBB_CORS_ORIGINS=http://localhost:3000,http://localhost:3002,http://127.0.0.1:3000,http://127.0.0.1:3002"
set "FRONTEND_URL=http://localhost:3002"

REM ---- sanity: the data drive must actually be present --------------
if not exist "%VBB_DATA_DIR%" (
  echo ERROR: data drive not found at %VBB_DATA_DIR%
  echo        Plug in the drive, or update VBB_DATA_DIR in this script.
  exit /b 1
)
if not exist "%VBB_DATA_DIR%\generated" mkdir "%VBB_DATA_DIR%\generated"
if not exist "%VBB_DATA_DIR%\assembled" mkdir "%VBB_DATA_DIR%\assembled"
if not exist "%VBB_DATA_DIR%\data" mkdir "%VBB_DATA_DIR%\data"

echo.
echo   Data drive : %VBB_DATA_DIR%
echo   Renders    : %VBB_GENERATED_DIR%
echo   Database   : sqlite (on D:)
echo   Credits    : BYPASSED (internal mode)
echo   Daily cap  : %VBB_RENDER_LIMIT_PER_DAY% ad(s) per day
echo.
echo   API        : http://127.0.0.1:8001  (health: /api/health)
echo.

"%BACKEND_DIR%.venv\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8001

endlocal
