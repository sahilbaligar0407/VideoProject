@echo off
echo 🐍 Setting up ClipGenius Backend...
echo.

echo 📦 Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ❌ Failed to create virtual environment. Make sure Python is installed.
    pause
    exit /b 1
)

echo ✅ Virtual environment created successfully!

echo.
echo 🔧 Activating virtual environment...
call venv\Scripts\activate

echo.
echo 📥 Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies.
    pause
    exit /b 1
)

echo ✅ Dependencies installed successfully!

echo.
echo 🔑 Setting up environment variables...
if not exist .env (
    copy env.example .env
    echo ✅ Created .env file from template
    echo.
    echo ⚠️  IMPORTANT: Edit .env file and add your OpenAI API key!
    echo    OPENAI_API_KEY=your_actual_api_key_here
    echo.
) else (
    echo ✅ .env file already exists
)

echo.
echo 🚀 Setup complete! To start the server:
echo    1. Activate virtual environment: venv\Scripts\activate
echo    2. Run: python run.py
echo.
echo 📚 API docs will be available at: http://localhost:8000/docs
echo.

pause
