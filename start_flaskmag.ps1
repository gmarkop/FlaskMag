# FlaskMag Auto-Start Script for Windows (PowerShell)
# This script starts FlaskMag Secure Edition automatically

# =============================================================================
# CONFIGURATION - Update these paths for your system
# =============================================================================

$FlaskMagDir = "C:\path\to\FlaskMag"
$FlaskMagFile = "flask_stream_secure.py"  # or flask_stream_network.py or flask_stream13.py
$StreamlitPort = 8501
$WaitSeconds = 30  # Wait time before starting (for network initialization)

# =============================================================================
# SCRIPT START
# =============================================================================

Write-Host "========================================"
Write-Host "FlaskMag Auto-Start Script (PowerShell)"
Write-Host "========================================"
Write-Host ""

# Wait for system initialization
Write-Host "Waiting $WaitSeconds seconds for system initialization..."
Start-Sleep -Seconds $WaitSeconds

# Check if directory exists
if (-not (Test-Path $FlaskMagDir)) {
    Write-Host "ERROR: FlaskMag directory not found: $FlaskMagDir" -ForegroundColor Red
    Write-Host "Please update `$FlaskMagDir in this script" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if Python file exists
$FlaskMagPath = Join-Path $FlaskMagDir $FlaskMagFile
if (-not (Test-Path $FlaskMagPath)) {
    Write-Host "ERROR: FlaskMag file not found: $FlaskMagPath" -ForegroundColor Red
    Write-Host "Please update `$FlaskMagFile in this script" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if already running
$StreamlitProcess = Get-Process streamlit -ErrorAction SilentlyContinue
if ($StreamlitProcess) {
    Write-Host "FlaskMag appears to be already running. Skipping..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    exit 0
}

# Change to FlaskMag directory
Set-Location $FlaskMagDir

# Start FlaskMag
Write-Host "Starting FlaskMag..." -ForegroundColor Green
Write-Host "  Directory: $FlaskMagDir"
Write-Host "  File: $FlaskMagFile"
Write-Host "  Port: $StreamlitPort"
Write-Host ""

# Create process start info
$ProcessInfo = New-Object System.Diagnostics.ProcessStartInfo
$ProcessInfo.FileName = "streamlit"
$ProcessInfo.Arguments = "run `"$FlaskMagFile`" --server.port $StreamlitPort --server.headless true --browser.gatherUsageStats false"
$ProcessInfo.WorkingDirectory = $FlaskMagDir
$ProcessInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Minimized
$ProcessInfo.CreateNoWindow = $false

# Start the process
try {
    $Process = [System.Diagnostics.Process]::Start($ProcessInfo)
    Start-Sleep -Seconds 5

    # Check if still running
    if (-not $Process.HasExited) {
        Write-Host ""
        Write-Host "========================================"
        Write-Host "FlaskMag started successfully!" -ForegroundColor Green
        Write-Host "========================================"
        Write-Host ""
        Write-Host "Access FlaskMag at:"
        Write-Host "  Local:  http://localhost:$StreamlitPort"
        Write-Host "  Remote: http://<your-tailscale-ip>:$StreamlitPort"
        Write-Host ""
        Write-Host "Process ID: $($Process.Id)"
        Write-Host ""
        Write-Host "To stop FlaskMag, run: Stop-Process -Id $($Process.Id)"
        Write-Host ""
    } else {
        Write-Host ""
        Write-Host "ERROR: FlaskMag process exited immediately" -ForegroundColor Red
        Write-Host "Exit code: $($Process.ExitCode)" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please check:" -ForegroundColor Yellow
        Write-Host "  1. Python is installed and in PATH"
        Write-Host "  2. Streamlit is installed (pip install streamlit)"
        Write-Host "  3. All dependencies are installed (pip install -r requirements.txt)"
        Write-Host ""
        Read-Host "Press Enter to exit"
        exit 1
    }
}
catch {
    Write-Host ""
    Write-Host "ERROR: Failed to start FlaskMag" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Close after 10 seconds
Write-Host "This window will close in 10 seconds..."
Start-Sleep -Seconds 10
