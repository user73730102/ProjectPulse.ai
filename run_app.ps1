# run_app.ps1
# Helper script to boot the ProjectPulse AI stack locally

Write-Host "Starting ProjectPulse AI Stack..." -ForegroundColor Cyan

# 1. Ensure .env exists in backend
cd backend
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created backend/.env file. Please edit it with your API keys if you haven't already." -ForegroundColor Magenta
}
cd ..

# 2. Start Database and Backend via Docker
Write-Host "`n[1/2] Building and Starting Database and Backend in Docker..." -ForegroundColor Yellow
# This bypasses all MSYS2 Windows python compilation issues!
docker-compose up -d --build

# Wait for backend to be ready (docker-compose will init db and seed data)
Start-Sleep -Seconds 10

# 3. Start Frontend
Write-Host "`n[2/2] Starting Next.js Frontend on port 3000..." -ForegroundColor Yellow
cd frontend
if (-not (Test-Path "node_modules")) {
    npm.cmd install
}
Start-Process -NoNewWindow -FilePath "npm.cmd" -ArgumentList "run dev"

cd ..

Write-Host "`n=======================================================" -ForegroundColor Green
Write-Host "ProjectPulse AI is running!" -ForegroundColor Green
Write-Host "Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "Backend API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "=======================================================" -ForegroundColor Green
Write-Host "`nDemo Credentials:"
Write-Host "  PM:         admin@projectpulse.ai"
Write-Host "  Engineer:   engineer@projectpulse.ai"
Write-Host "  Auditor:    auditor@projectpulse.ai"
Write-Host "  Contractor: contractor@eaton.com"
Write-Host "Password for all is 'XXXXXX123' (e.g. admin123)"

Write-Host "`nPress Ctrl+C to exit this script (note: background processes may keep running)."
