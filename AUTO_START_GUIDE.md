# FlaskMag Auto-Start Guide for Windows 11

Complete guide to automatically start FlaskMag when your PC boots, ensuring remote access is always available.

---

## Why Auto-Start?

**Problem:** If your PC restarts (Windows updates, power outage, manual restart), FlaskMag won't be running and you can't access it remotely.

**Solution:** Configure FlaskMag to start automatically on boot.

**Benefits:**
- ✅ Always available for remote access
- ✅ No manual intervention needed
- ✅ Survives Windows updates and restarts
- ✅ Peace of mind when traveling

---

## Quick Start (5 Minutes)

The fastest method - use the Startup Folder:

### Step 1: Edit the Startup Script

1. **Find the script:** `start_flaskmag.bat` in your FlaskMag folder

2. **Right-click** → **Edit** (opens in Notepad)

3. **Update this line:**
   ```batch
   SET FLASKMAG_DIR=C:\path\to\FlaskMag
   ```

   Change to your actual path, for example:
   ```batch
   SET FLASKMAG_DIR=C:\Users\YourName\Documents\FlaskMag
   ```

4. **Choose which version to run** (line 15):
   ```batch
   SET FLASKMAG_FILE=flask_stream_secure.py
   ```

   Options:
   - `flask_stream_secure.py` - Recommended (auth + mobile)
   - `flask_stream_network.py` - Network only (no auth)
   - `flask_stream13.py` - Local only

5. **Save and close**

### Step 2: Test the Script

1. **Double-click** `start_flaskmag.bat`
2. You should see a console window saying "Starting FlaskMag..."
3. After a moment, a minimized window opens with FlaskMag running
4. **Test access:** Open browser → `http://localhost:8501`
5. If it works, proceed to Step 3

### Step 3: Add to Startup Folder

**Method A: Using Run Dialog (Fastest)**
```
1. Press Win + R
2. Type: shell:startup
3. Press Enter (Startup folder opens)
4. Copy start_flaskmag.bat into this folder
5. Done! FlaskMag will start on next boot
```

**Method B: Manual Navigation**
```
1. Open File Explorer
2. Navigate to:
   C:\Users\YourName\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
3. Copy start_flaskmag.bat here
4. Done!
```

### Step 4: Test Auto-Start

```
1. Restart your PC
2. Wait 1-2 minutes after login
3. Check if FlaskMag is running: http://localhost:8501
4. Success! ✅
```

---

## Method Comparison

| Method | Difficulty | Reliability | Features |
|--------|-----------|-------------|----------|
| **Startup Folder** | Easy ⭐ | Good | Simple, fast |
| **Task Scheduler** | Medium ⭐⭐ | Excellent | Delays, retries, logging |
| **Windows Service** | Hard ⭐⭐⭐ | Best | Always runs, no login needed |

---

## Method 1: Startup Folder (Recommended)

### Pros
- ✅ Easiest to set up (5 minutes)
- ✅ Easy to disable (just remove from folder)
- ✅ Runs when you log in
- ✅ Can see console window if needed

### Cons
- ❌ Only starts after user login
- ❌ Visible console window (can be minimized)
- ❌ No automatic retry on failure

### Setup Instructions

See **Quick Start** section above for complete instructions.

### Troubleshooting

**Problem: Script runs but FlaskMag doesn't start**

1. **Check paths in script:**
   ```batch
   SET FLASKMAG_DIR=C:\Users\YourName\Documents\FlaskMag
   ```
   Make sure this path is correct!

2. **Test Python and Streamlit:**
   ```cmd
   python --version
   streamlit --version
   ```
   Both should work without errors.

3. **Check dependencies:**
   ```cmd
   cd C:\path\to\FlaskMag
   pip install -r requirements.txt
   ```

4. **Run script manually:**
   ```cmd
   cd C:\path\to\FlaskMag
   start_flaskmag.bat
   ```
   Look for error messages.

**Problem: Console window is annoying**

Edit `start_flaskmag.bat` and change:
```batch
start "FlaskMag" /MIN streamlit run ...
```

This starts it minimized to taskbar.

---

## Method 2: Task Scheduler (Advanced)

### Pros
- ✅ More reliable than Startup Folder
- ✅ Can delay start (wait for network)
- ✅ Can run even if no user logged in
- ✅ Automatic retry on failure
- ✅ Logging and monitoring

### Cons
- ❌ More complex setup
- ❌ Requires admin rights

### Setup Instructions

#### Step 1: Prepare PowerShell Script

1. **Edit** `start_flaskmag.ps1`

2. **Update configuration:**
   ```powershell
   $FlaskMagDir = "C:\Users\YourName\Documents\FlaskMag"
   $FlaskMagFile = "flask_stream_secure.py"
   $StreamlitPort = 8501
   $WaitSeconds = 30
   ```

3. **Test the script:**
   ```powershell
   # Right-click start_flaskmag.ps1 → Run with PowerShell
   ```

#### Step 2: Enable PowerShell Script Execution

```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Step 3: Create Scheduled Task

**Option A: Using GUI (Easier)**

1. **Open Task Scheduler:**
   ```
   Win + R → taskschd.msc → Enter
   ```

2. **Create Basic Task:**
   ```
   Actions → Create Basic Task
   Name: FlaskMag Auto-Start
   Description: Automatically start FlaskMag on system boot
   Click Next
   ```

3. **Trigger:**
   ```
   When do you want the task to start?
   → Select "When I log on"
   Click Next
   ```

4. **Action:**
   ```
   What action do you want to perform?
   → Select "Start a program"
   Click Next

   Program/script: powershell.exe

   Add arguments:
   -WindowStyle Hidden -ExecutionPolicy Bypass -File "C:\path\to\FlaskMag\start_flaskmag.ps1"

   (Replace with your actual path!)

   Click Next → Finish
   ```

5. **Advanced Settings:**
   ```
   Right-click your new task → Properties

   General tab:
   ☑ Run whether user is logged on or not
   ☑ Run with highest privileges

   Conditions tab:
   ☑ Start only if the computer is on AC power (uncheck if laptop)

   Settings tab:
   ☑ Allow task to be run on demand
   ☑ If the task fails, restart every: 1 minute
      Attempt to restart up to: 3 times

   Click OK
   ```

**Option B: Using PowerShell (Advanced)**

```powershell
# Run as Administrator

$TaskName = "FlaskMag Auto-Start"
$ScriptPath = "C:\path\to\FlaskMag\start_flaskmag.ps1"

# Create action
$Action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-WindowStyle Hidden -ExecutionPolicy Bypass -File `"$ScriptPath`""

# Create trigger (at logon)
$Trigger = New-ScheduledTaskTrigger -AtLogOn

# Create settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)

# Register task
Register-ScheduledTask -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "Automatically start FlaskMag on boot" `
    -RunLevel Highest

Write-Host "Task created successfully!"
```

#### Step 4: Test the Task

```powershell
# Manually run the task
Start-ScheduledTask -TaskName "FlaskMag Auto-Start"

# Check status
Get-ScheduledTask -TaskName "FlaskMag Auto-Start"

# View task history
Get-ScheduledTask -TaskName "FlaskMag Auto-Start" | Get-ScheduledTaskInfo
```

#### Step 5: Test on Reboot

```
1. Restart your PC
2. Wait 1-2 minutes
3. Check: http://localhost:8501
4. Success! ✅
```

### Troubleshooting Task Scheduler

**View Task History:**
```
1. Task Scheduler → Task Scheduler Library
2. Find "FlaskMag Auto-Start"
3. Click History tab (bottom)
4. Look for errors
```

**Common Issues:**

1. **Task runs but FlaskMag doesn't start:**
   - Check PowerShell script paths
   - Verify "Run with highest privileges" is checked
   - Check execution policy: `Get-ExecutionPolicy`

2. **Task doesn't run at all:**
   - Verify trigger is "At log on"
   - Check "Run whether user is logged on or not"
   - Ensure user has admin rights

3. **PowerShell errors:**
   - Check script syntax
   - Run script manually to see errors
   - Check paths are absolute (not relative)

---

## Method 3: Windows Service (Expert)

### Pros
- ✅ Most reliable (always runs)
- ✅ Starts before login
- ✅ Automatically restarts on failure
- ✅ Professional solution

### Cons
- ❌ Complex setup
- ❌ Requires third-party tools (NSSM)
- ❌ Advanced troubleshooting needed

### Setup Instructions

#### Step 1: Download NSSM (Non-Sucking Service Manager)

```
1. Visit: https://nssm.cc/download
2. Download latest version (e.g., nssm-2.24.zip)
3. Extract to C:\nssm\
4. Copy nssm.exe from win64 folder to C:\nssm\
```

#### Step 2: Create Service

```cmd
REM Run Command Prompt as Administrator

cd C:\nssm

REM Create service
nssm install FlaskMag

REM A GUI will open - fill in:
```

**Application tab:**
```
Path: C:\Python311\Scripts\streamlit.exe
Startup directory: C:\path\to\FlaskMag
Arguments: run flask_stream_secure.py --server.port 8501 --server.headless true
Service name: FlaskMag
```

**Details tab:**
```
Display name: FlaskMag PDF Search
Description: FlaskMag PDF search application for remote access
Startup type: Automatic (Delayed Start)
```

**Log on tab:**
```
Select: This account
Username: YOUR_USERNAME
Password: YOUR_PASSWORD
(This is needed to access network shares)
```

**I/O tab:**
```
Output (stdout): C:\path\to\FlaskMag\flaskmag.log
Error (stderr): C:\path\to\FlaskMag\flaskmag_error.log
```

**Environment tab:**
```
(Leave default)
```

**Exit actions tab:**
```
Restart application
Delay restart by: 10000 milliseconds
```

Click **Install service**

#### Step 3: Start Service

```cmd
REM Start the service
nssm start FlaskMag

REM Check status
nssm status FlaskMag

REM View service
services.msc
```

#### Step 4: Test

```
1. Service should start immediately
2. Check: http://localhost:8501
3. Restart PC to test auto-start
4. Check again after reboot
```

### Managing the Service

```cmd
REM Stop service
nssm stop FlaskMag

REM Restart service
nssm restart FlaskMag

REM Check status
nssm status FlaskMag

REM Remove service
nssm remove FlaskMag confirm
```

### Troubleshooting Service

**Check logs:**
```
C:\path\to\FlaskMag\flaskmag.log
C:\path\to\FlaskMag\flaskmag_error.log
```

**Common issues:**

1. **Service won't start:**
   - Check paths are correct
   - Verify Python/Streamlit installed
   - Check user account has permissions
   - View Event Viewer for errors

2. **Service starts but app doesn't work:**
   - Check logs for errors
   - Verify network shares are accessible
   - Test running Streamlit manually

3. **Can't access network shares:**
   - Service must run under your user account
   - Don't use "Local System" account
   - Provide correct username/password

---

## Verification Checklist

After setting up auto-start:

- [ ] Script runs manually without errors
- [ ] FlaskMag accessible at http://localhost:8501
- [ ] Restarted PC and FlaskMag auto-started
- [ ] Can access remotely via Tailscale
- [ ] Tested login works (Secure Edition)
- [ ] Checked after Windows Update
- [ ] Verified network share access works
- [ ] Set PC to never sleep (if 24/7 access needed)

---

## Performance Tips

### Delay Start for Network Initialization

The scripts include a 30-second delay by default. Adjust if needed:

**Batch script:**
```batch
timeout /t 30 /nobreak > nul
```

**PowerShell script:**
```powershell
$WaitSeconds = 30
```

**Why delay?**
- WiFi needs time to connect
- Network shares need time to mount
- Tailscale needs time to establish VPN

### Minimize Resource Usage

**Use headless mode:**
```
--server.headless true --browser.gatherUsageStats false
```

This prevents browser auto-opening and telemetry.

### Monitor Startup

**Check if running:**
```powershell
Get-Process streamlit
```

**Check port usage:**
```cmd
netstat -ano | findstr :8501
```

---

## Stopping FlaskMag

### If Started from Startup Folder

**Option 1: Task Manager**
```
Ctrl + Shift + Esc → Processes → Find "streamlit" → End Task
```

**Option 2: Close Console Window**
```
Find "FlaskMag" window in taskbar → Close
```

### If Started from Task Scheduler

```powershell
Stop-ScheduledTask -TaskName "FlaskMag Auto-Start"
```

### If Running as Service

```cmd
nssm stop FlaskMag
```

---

## Disabling Auto-Start

### Startup Folder Method

```
1. Win + R → shell:startup
2. Delete start_flaskmag.bat
3. Restart PC
```

### Task Scheduler Method

```
1. Win + R → taskschd.msc
2. Find "FlaskMag Auto-Start"
3. Right-click → Disable (or Delete)
```

### Windows Service Method

```cmd
nssm stop FlaskMag
nssm remove FlaskMag confirm
```

---

## Updating FlaskMag

When you update FlaskMag files:

1. **No changes needed** if paths stay the same
2. **Restart FlaskMag** to load new code:
   ```
   - Startup Folder: Close console window, reopen
   - Task Scheduler: Stop and start task
   - Service: nssm restart FlaskMag
   ```
3. **Test** that auto-start still works

---

## Common Issues

### Issue: "Python not found"

**Solution:**
```cmd
REM Check Python installation
python --version

REM If not found, add Python to PATH:
REM System Properties → Environment Variables → Path → Add Python directory
```

### Issue: "Streamlit not found"

**Solution:**
```cmd
REM Install Streamlit
pip install streamlit

REM Or reinstall all dependencies
cd C:\path\to\FlaskMag
pip install -r requirements.txt
```

### Issue: Script runs but FlaskMag not accessible

**Solution:**
1. Check firewall isn't blocking port 8501
2. Verify FlaskMag actually started (check Task Manager)
3. Check for errors in console window
4. Try accessing via IP: http://127.0.0.1:8501

### Issue: Network shares not accessible on startup

**Solution:**
1. Increase delay in script (to 60 seconds)
2. Verify network share credentials
3. Map network drive permanently (assign drive letter)
4. Use Task Scheduler with "Start when available" option

---

## Best Practices

1. **Test manually first** before setting up auto-start
2. **Use absolute paths** (not relative)
3. **Add 30-60 second delay** for network initialization
4. **Keep logs** (Task Scheduler and Service methods)
5. **Set PC to never sleep** for 24/7 availability
6. **Test after Windows Updates** to ensure still working
7. **Document your setup** (which method, which script, etc.)

---

## Summary

**For Most Users:**
→ Use **Startup Folder** method (easiest, works great)

**For Reliability:**
→ Use **Task Scheduler** method (better error handling)

**For Production/Always-On:**
→ Use **Windows Service** method (most robust)

**Recommended Approach:**
```
1. Start with Startup Folder method
2. Test for a few days
3. If issues occur, upgrade to Task Scheduler
4. Only use Service if you need enterprise-grade reliability
```

---

## Quick Reference

**Edit script paths:**
```batch
start_flaskmag.bat → Line 9: SET FLASKMAG_DIR=
```

**Test script:**
```cmd
cd C:\path\to\FlaskMag
start_flaskmag.bat
```

**Add to startup:**
```
Win + R → shell:startup → Copy script here
```

**Check if running:**
```cmd
tasklist | findstr streamlit
```

**Access FlaskMag:**
```
Local:  http://localhost:8501
Remote: http://<tailscale-ip>:8501
```

---

**Your FlaskMag is now configured for automatic startup! 🚀**

After setup, your PC will automatically start FlaskMag on boot, ensuring remote access is always available when you need it.

For additional help, see:
- [NETWORK_SETUP_GUIDE.md](NETWORK_SETUP_GUIDE.md) - Tailscale and network configuration
- [AUTHENTICATION_MOBILE_GUIDE.md](AUTHENTICATION_MOBILE_GUIDE.md) - Authentication and mobile usage
- [README.md](README.md) - General documentation
