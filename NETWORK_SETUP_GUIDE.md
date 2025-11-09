# FlaskMag Network Setup Guide
## Remote Access via Tailscale + Fritz!Box Network Share

This guide will help you set up FlaskMag to access your PDF collection remotely using your Fritz!Box 7530's network storage and Tailscale VPN.

---

## Overview

**What we're setting up:**
- PDFs stored on external HDD connected to Fritz!Box 7530
- FlaskMag app running on your PC
- Tailscale VPN for secure remote access
- Access your magazines from anywhere in the world

**Advantages:**
- ✅ Secure encrypted connection
- ✅ No complex router configuration
- ✅ Works through any firewall/NAT
- ✅ Free for personal use
- ✅ Access as if you're on home network

---

## Part 1: Fritz!Box Network Storage Setup

### Step 1: Enable Fritz!Box Storage

1. Open Fritz!Box web interface: `http://fritz.box` or `http://192.168.178.1`
2. Log in with your Fritz!Box password
3. Navigate to: **Home Network → Storage (NAS)**
4. Check the status of your USB storage device
5. Make sure **"Storage (NAS) active"** is enabled

### Step 2: Verify USB Storage Name

1. In the Storage (NAS) page, note your storage name (usually `USB-Storage` or similar)
2. You can also create specific folders for organization:
   - Example: `USB-Storage/PDFs/Tourenfahrer/`
   - Example: `USB-Storage/PDFs/Bike/`

### Step 3: Organize Your PDFs on the Network Share

**From your PC:**

**Windows:**
1. Open File Explorer
2. In the address bar, type: `\\fritz.box\` or `\\192.168.178.1\`
3. You should see your `USB-Storage` folder
4. Create folder structure:
   ```
   USB-Storage/
   └── PDFs/
       ├── Tourenfahrer/
       ├── Alpentourer/
       ├── Bike/
       ├── Motorrad/
       └── ... (your magazine collections)
   ```
5. Copy your PDF files into these folders

**Linux/WSL:**
```bash
# Create mount point
sudo mkdir -p /mnt/fritzbox

# Mount the share
sudo mount -t cifs //192.168.178.1/USB-Storage /mnt/fritzbox -o username=guest,password=

# Access your files
ls /mnt/fritzbox/PDFs/
```

### Step 4: Test Network Access

**Windows - Quick Test:**
1. Open File Explorer
2. Navigate to: `\\fritz.box\USB-Storage\PDFs\`
3. You should see your PDF folders
4. Try opening a PDF file to confirm it works

**Linux - Quick Test:**
```bash
# After mounting (see above)
ls /mnt/fritzbox/PDFs/
```

---

## Part 2: Configure FlaskMag for Network Access

### Step 1: Edit Configuration in flask_stream_network.py

Open `flask_stream_network.py` and update these settings at the top:

```python
# Fritz!Box Network Share Configuration
FRITZBOX_IP = "192.168.178.1"      # Usually this is correct
FRITZBOX_SHARE_NAME = "USB-Storage"  # Verify in Fritz!Box settings
FRITZBOX_USERNAME = ""              # Leave empty unless you set authentication
FRITZBOX_PASSWORD = ""              # Leave empty unless you set authentication
```

### Step 2: Configure PDF Directories

Update the paths to match your folder structure:

**Windows example:**
```python
# In the Windows section of the code
PDF_DIRECTORIES = [
    f"{NETWORK_BASE}\\PDFs\\Tourenfahrer",
    f"{NETWORK_BASE}\\PDFs\\Alpentourer",
    f"{NETWORK_BASE}\\PDFs\\Bike",
    # Add your other folders here
]
```

**Linux example:**
```python
# In the Linux section of the code
PDF_DIRECTORIES = [
    f"{NETWORK_BASE}/PDFs/Tourenfahrer",
    f"{NETWORK_BASE}/PDFs/Alpentourer",
    f"{NETWORK_BASE}/PDFs/Bike",
    # Add your other folders here
]
```

### Step 3: Test Locally First

Before setting up remote access, test that the network version works locally:

```bash
# Make sure you're connected to your home network
streamlit run flask_stream_network.py
```

Expected behavior:
- ✅ Network status shows "Connected"
- ✅ PDFs are indexed from network share
- ✅ Search and viewing work normally

If you see errors, check:
- Fritz!Box is powered on and USB drive is connected
- You can access `\\fritz.box\USB-Storage\` from File Explorer
- Paths in configuration match your actual folder structure

---

## Part 3: Tailscale Setup for Remote Access

### Step 1: Create Tailscale Account

1. Go to: https://tailscale.com/
2. Click **"Get Started"**
3. Sign up with:
   - Google account, OR
   - Microsoft account, OR
   - GitHub account, OR
   - Email (create new account)

### Step 2: Install Tailscale on Your Home PC

**Windows:**
1. Download: https://tailscale.com/download/windows
2. Run the installer
3. After installation, Tailscale will start automatically
4. Sign in with your Tailscale account
5. You'll see a Tailscale icon in your system tray

**Linux:**
```bash
# Download and install
curl -fsSL https://tailscale.com/install.sh | sh

# Start Tailscale
sudo tailscale up

# Copy the URL and authenticate in browser
```

### Step 3: Note Your PC's Tailscale IP

**Windows:**
1. Right-click Tailscale icon in system tray
2. Click on your device name
3. Note the IP address (e.g., `100.x.x.x`)

**Linux:**
```bash
tailscale ip -4
# Output example: 100.101.102.103
```

### Step 4: Install Tailscale on Remote Device

Install Tailscale on any device you want to use remotely:

**Laptop/Another PC:**
- Windows: https://tailscale.com/download/windows
- Mac: https://tailscale.com/download/mac
- Linux: https://tailscale.com/download/linux

**Mobile:**
- iOS: App Store → Search "Tailscale"
- Android: Play Store → Search "Tailscale"

**Important:** Sign in with the SAME Tailscale account!

### Step 5: Test Remote Connection

1. On your remote device, connect to Tailscale
2. Verify you can see your home PC in Tailscale network
3. Try to ping your home PC:
   ```bash
   ping 100.x.x.x  (your home PC's Tailscale IP)
   ```

---

## Part 4: Running FlaskMag Remotely

### Step 1: Start FlaskMag on Your Home PC

On your **home PC** (connected to your home network):

```bash
streamlit run flask_stream_network.py
```

Note the port number (usually `8501`)

### Step 2: Access from Remote Device

On your **remote device** (laptop, phone, etc.):

1. Make sure Tailscale is connected
2. Open web browser
3. Go to: `http://100.x.x.x:8501` (replace with your home PC's Tailscale IP)
4. You should see FlaskMag interface!

**Example:**
- If your home PC's Tailscale IP is `100.101.102.103`
- Access URL: `http://100.101.102.103:8501`

### Step 3: Use FlaskMag Remotely

Everything works exactly the same as local access:
- Search for keywords
- View PDFs
- Download PDFs
- All data comes from your Fritz!Box storage

**Note:** Initial loading may be slightly slower over remote connection, but cached searches will be fast!

---

## Part 5: Making Your PC Auto-Start FlaskMag

### Option A: Windows - Create Startup Script

1. Create a file `start_flaskmag.bat`:
   ```batch
   @echo off
   cd C:\path\to\FlaskMag
   streamlit run flask_stream_network.py
   ```

2. Save in your FlaskMag folder

3. Create a shortcut to this file in:
   - Press `Win + R`
   - Type: `shell:startup`
   - Press Enter
   - Copy the `.bat` file here

Now FlaskMag starts automatically when you log into Windows!

### Option B: Linux - Create Systemd Service

1. Create service file:
   ```bash
   sudo nano /etc/systemd/system/flaskmag.service
   ```

2. Add this content:
   ```ini
   [Unit]
   Description=FlaskMag PDF Search
   After=network.target

   [Service]
   Type=simple
   User=YOUR_USERNAME
   WorkingDirectory=/path/to/FlaskMag
   ExecStart=/usr/bin/streamlit run flask_stream_network.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start:
   ```bash
   sudo systemctl enable flaskmag
   sudo systemctl start flaskmag
   ```

---

## Part 6: Advanced - Wake Your PC Remotely

If you want to wake your PC remotely when it's asleep:

### Enable Wake-on-LAN

**On your PC:**
1. Enter BIOS/UEFI (usually press Del/F2 during boot)
2. Find and enable "Wake-on-LAN" or "WOL"
3. Save and exit

**In Windows:**
1. Device Manager → Network adapters
2. Right-click your network adapter → Properties
3. Power Management tab
4. Check "Allow this device to wake the computer"
5. Advanced tab
6. Enable "Wake on Magic Packet"

**Using Tailscale to Wake PC:**
1. Keep another always-on device on your home network (Raspberry Pi, old PC, router with custom firmware)
2. Install Tailscale on that device too
3. SSH into that device remotely
4. Send WOL packet to your main PC:
   ```bash
   wakeonlan XX:XX:XX:XX:XX:XX  # Your PC's MAC address
   ```

---

## Troubleshooting

### Problem: Cannot access Fritz!Box share

**Solution:**
1. Verify Fritz!Box is on: `ping fritz.box` or `ping 192.168.178.1`
2. Check storage is active in Fritz!Box settings
3. Try accessing `\\fritz.box\` in File Explorer
4. Restart Fritz!Box if needed

### Problem: "Network share not accessible" error

**Solution:**
1. Check you're connected to home network (or Tailscale VPN)
2. Verify path in code matches actual Fritz!Box folder structure
3. Try using IP address instead of hostname:
   - Change `\\fritz.box\` to `\\192.168.178.1\`

### Problem: Cannot connect via Tailscale

**Solution:**
1. Verify Tailscale is running on both devices (home PC and remote device)
2. Check both devices are signed into the SAME Tailscale account
3. Try pinging: `ping 100.x.x.x`
4. Check firewall isn't blocking Tailscale

### Problem: Connection is very slow

**Solutions:**
1. First time processing will be slower - PDFs are cached locally after first scan
2. Use "Direct Connections" in Tailscale settings for better performance
3. Consider processing PDFs locally first, then use remote access for searching only
4. Check your internet upload speed on home network

### Problem: PDFs won't render

**Solution:**
1. Check network connectivity status in app
2. Verify PDF file exists on Fritz!Box
3. Try "Refresh Network Status" button in sidebar
4. Clear cache and rebuild index

---

## Configuration Reference

### Minimum Requirements

**Home PC:**
- Windows 10/11 or Linux
- Python 3.7+
- Connected to same network as Fritz!Box
- 4GB RAM minimum (8GB recommended)

**Fritz!Box:**
- Fritz!Box 7530 or similar model
- USB storage enabled
- Connected to home network

**Internet Connection:**
- Any speed works
- Faster upload speed = better remote performance

### Recommended Setup

```
Internet
   ↓
Fritz!Box 7530 (Router + NAS)
   ↓
USB Hard Drive (PDFs stored here)
   ↓
Home Network (WiFi/Ethernet)
   ↓
Your PC (Running FlaskMag + Tailscale)
   ↓
Tailscale VPN Network
   ↓
Remote Devices (Laptop, Phone, Tablet)
```

---

## Security Notes

### Tailscale Security
- ✅ End-to-end encrypted
- ✅ Zero-trust network model
- ✅ No open ports on your router
- ✅ Only devices you authorize can connect

### Fritz!Box Security
- Consider setting username/password for network share
- Update Fritz!Box firmware regularly
- Don't expose Fritz!Box directly to internet

### Additional Security (Optional)

Add authentication to FlaskMag app (requires code modification):

**Option 1: Streamlit Authentication**
```bash
pip install streamlit-authenticator
```

**Option 2: Reverse Proxy with Auth**
Use nginx or Caddy as reverse proxy with basic auth

I can help implement these if needed!

---

## Performance Tips

### 1. Cache Strategy
- Cache is stored locally on PC (not on network share)
- First PDF processing takes time - do it once at home
- After caching, remote access is fast

### 2. Optimize for Remote Use
- Process all PDFs while at home first
- Search index is local (fast)
- Only PDF viewing requires network share access

### 3. Network Optimization
- Use 5GHz WiFi on home network (faster)
- Consider Ethernet cable for home PC
- Close bandwidth-heavy apps while using remotely

---

## Alternative: Fritz!Box VPN (Instead of Tailscale)

If you prefer using Fritz!Box's built-in VPN:

### Enable Fritz!Box VPN

1. Fritz!Box interface → Internet → Permit Access → VPN
2. Add new VPN connection
3. Download configuration file
4. Import on remote device (Windows, Mac, mobile)

**Pros:**
- No third-party service needed
- Direct connection to home network

**Cons:**
- More complex setup
- Doesn't work through all firewalls
- Manual configuration required

**I recommend Tailscale** for easier setup and better reliability!

---

## Getting Help

If you encounter issues:

1. Check this troubleshooting guide
2. Verify network connectivity in the app
3. Review error messages in Streamlit interface
4. Check that all paths are configured correctly

**Common Issues:**
- Most problems are path/configuration related
- Verify you can access Fritz!Box share manually first
- Test locally before testing remotely

---

## Summary Checklist

- [ ] Fritz!Box storage is enabled and accessible
- [ ] PDFs are organized in folders on USB drive
- [ ] Edited `flask_stream_network.py` with correct paths
- [ ] Tested app works locally on home network
- [ ] Tailscale installed on home PC
- [ ] Tailscale installed on remote devices
- [ ] Both devices connected to same Tailscale account
- [ ] Can access FlaskMag remotely via Tailscale IP
- [ ] (Optional) Set up auto-start on home PC

---

**You're all set! Enjoy accessing your PDF magazine collection from anywhere! 📚🌍**

For questions or issues, refer to the troubleshooting section or check the main README.md for additional information.
