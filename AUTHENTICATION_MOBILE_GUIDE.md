## FlaskMag Secure Edition - Authentication & Mobile Guide

Complete guide for setting up authentication and using FlaskMag on mobile devices.

---

## Overview

The **Secure Edition** (`flask_stream_secure.py`) adds:
- 🔐 **User authentication** with password protection
- 📱 **Mobile-responsive design** for phones and tablets
- 👆 **Touch-friendly UI** with larger buttons
- 🔒 **Session management** for secure access
- 👥 **Multi-user support** with configurable accounts

---

## Part 1: Authentication Setup

### Quick Start

1. **Install required package:**
   ```bash
   pip install pyyaml
   ```

2. **Run the secure version:**
   ```bash
   streamlit run flask_stream_secure.py
   ```

3. **Login with default credentials:**
   - Username: `admin`
   - Password: `admin123`

⚠️ **IMPORTANT:** Change the default password immediately after first login!

---

### Changing the Default Password

#### Method 1: Edit Configuration File (Recommended)

1. **Locate the config file:**
   ```
   ~/.flaskmag_cache/auth_config.yaml
   ```

   On Windows: `C:\Users\YourName\.flaskmag_cache\auth_config.yaml`
   On Linux: `/home/username/.flaskmag_cache/auth_config.yaml`

2. **Generate a password hash:**

   Run this Python script to hash your password:
   ```python
   import hashlib

   password = "your_new_password_here"
   hashed = hashlib.sha256(password.encode()).hexdigest()
   print(f"Hashed password: {hashed}")
   ```

3. **Edit `auth_config.yaml`:**
   ```yaml
   credentials:
     usernames:
       admin:
         name: Administrator
         password: YOUR_HASHED_PASSWORD_HERE
   cookie:
     expiry_days: 30
     key: flaskmag_auth_key
     name: flaskmag_auth_cookie
   ```

4. **Restart FlaskMag** and login with your new password

---

### Adding Multiple Users

Edit `auth_config.yaml` to add more users:

```yaml
credentials:
  usernames:
    admin:
      name: Administrator
      password: hashed_password_1

    john:
      name: John Doe
      password: hashed_password_2

    jane:
      name: Jane Smith
      password: hashed_password_3

cookie:
  expiry_days: 30
  key: flaskmag_auth_key
  name: flaskmag_auth_cookie
```

**To add a new user:**

1. Choose a username (lowercase, no spaces)
2. Choose a display name
3. Generate password hash (see above)
4. Add to configuration file
5. Restart FlaskMag

---

### Security Best Practices

#### 1. Change Default Credentials
Never use `admin`/`admin123` in production! Change immediately.

#### 2. Use Strong Passwords
- Minimum 12 characters
- Mix of letters, numbers, symbols
- Don't reuse passwords

#### 3. Change the Cookie Key
In `auth_config.yaml`, change:
```yaml
cookie:
  key: your_unique_random_string_here  # Make this unique!
```

Generate a random key:
```python
import secrets
print(secrets.token_urlsafe(32))
```

#### 4. Set Appropriate Session Expiry
```yaml
cookie:
  expiry_days: 7  # Users must login every 7 days
```

#### 5. Disable Authentication (Local Use Only)
If using only on your local PC without network access:

Edit `flask_stream_secure.py`:
```python
ENABLE_AUTHENTICATION = False  # Line ~36
```

⚠️ **Only do this for local-only use! Never disable for remote access!**

---

## Part 2: Mobile Optimization

### Mobile Features

The secure edition includes:
- ✅ Responsive layout (auto-adjusts for screen size)
- ✅ Touch-friendly buttons (44px minimum height)
- ✅ Larger text inputs for mobile keyboards
- ✅ Optimized PDF viewer for mobile screens
- ✅ Collapsible sidebar for more screen space
- ✅ Simplified navigation for small screens

---

### Using on Mobile Devices

#### Method 1: Tailscale + Mobile App

**iOS Setup:**
1. Install Tailscale from App Store
2. Sign in with your Tailscale account (same as PC)
3. Connect to Tailscale
4. Open Safari
5. Go to: `http://100.x.x.x:8501` (your PC's Tailscale IP)
6. Login with your credentials
7. **Add to Home Screen** for app-like experience:
   - Tap the Share button
   - Tap "Add to Home Screen"
   - Name it "FlaskMag"

**Android Setup:**
1. Install Tailscale from Play Store
2. Sign in with your Tailscale account
3. Connect to Tailscale
4. Open Chrome browser
5. Go to: `http://100.x.x.x:8501`
6. Login with your credentials
7. **Add to Home Screen:**
   - Tap the menu (3 dots)
   - Tap "Add to Home Screen"
   - Name it "FlaskMag"

---

#### Method 2: Local Network (Home WiFi Only)

**On your PC:**
1. Find your local IP address:
   - Windows: `ipconfig` → look for IPv4 Address
   - Linux: `ip addr` or `hostname -I`
   - Example: `192.168.1.100`

2. Run FlaskMag:
   ```bash
   streamlit run flask_stream_secure.py
   ```

**On your mobile device:**
1. Connect to the same WiFi network
2. Open browser
3. Go to: `http://192.168.1.100:8501` (use your PC's IP)
4. Login and use

**Note:** This only works when you're on the same WiFi network.

---

### Mobile Usage Tips

#### 1. PDF Viewing on Mobile
- Tap the PDF image to zoom
- Use two-finger pinch to zoom in browser
- Landscape orientation works better for PDFs
- Use "Download PDF" for offline viewing

#### 2. Search on Mobile
- Keyboard auto-appears when tapping search box
- Use autocorrect/suggestions
- Recent searches are shown (browser feature)

#### 3. Navigation
- Use hamburger menu (☰) in top-left for sidebar
- Swipe to close sidebar and see more content
- Scroll results with one finger

#### 4. Performance
- First load may be slower on mobile
- Cached searches are fast
- Close other apps for better performance
- Use WiFi instead of cellular for speed

---

### Tablet Optimization

#### iPad/Android Tablets
- Landscape mode recommended
- Side-by-side results and PDF viewer works great
- External keyboard supported
- Can connect to external display

#### Surface/2-in-1 Devices
- Touch or mouse/trackpad both work
- Tablet mode optimizes for touch
- Desktop mode gives more features
- Stylus support (for highlighting, etc.)

---

## Part 3: Advanced Authentication

### Single Sign-On (SSO) Options

For advanced users who want enterprise authentication:

#### Option 1: OAuth via Streamlit
Integrate with Google/GitHub login:
```python
# Requires additional configuration
# See Streamlit authentication documentation
```

#### Option 2: LDAP/Active Directory
Connect to corporate directory:
```python
# Requires python-ldap package
# Advanced setup required
```

**Note:** These require code modifications. Contact for assistance.

---

### Session Security

#### Current Session Settings
- **Cookie-based:** Sessions stored in browser cookies
- **Expiry:** Default 30 days (configurable)
- **Secure flag:** Automatically set over HTTPS
- **HttpOnly:** Not accessible via JavaScript

#### Forcing Re-login
To force all users to re-login:

1. Delete session data:
   ```bash
   rm ~/.flaskmag_cache/auth_config.yaml
   ```

2. Restart FlaskMag

3. All users must login again

---

## Part 4: Mobile-Specific CSS Customization

### Custom Styling

You can customize the mobile experience by editing `inject_mobile_css()` function in `flask_stream_secure.py`.

#### Example Customizations:

**Change Button Colors:**
```css
.stButton > button {
    background-color: #4CAF50 !important;  /* Green */
    color: white !important;
}
```

**Larger Font on Mobile:**
```css
@media (max-width: 768px) {
    body {
        font-size: 18px !important;
    }
}
```

**Custom Login Page Background:**
```css
.login-container {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}
```

---

## Part 5: Troubleshooting

### Authentication Issues

#### Problem: "Invalid username or password"
**Solutions:**
1. Check username is lowercase
2. Verify you're using the correct password
3. Check `auth_config.yaml` exists
4. Verify password hash is correct

#### Problem: Can't access config file
**Solutions:**
1. Check file exists: `~/.flaskmag_cache/auth_config.yaml`
2. Create it manually (see template above)
3. Check file permissions:
   ```bash
   chmod 644 ~/.flaskmag_cache/auth_config.yaml
   ```

#### Problem: Session expires too quickly
**Solution:**
Edit `auth_config.yaml`:
```yaml
cookie:
  expiry_days: 90  # Increase to 90 days
```

---

### Mobile Issues

#### Problem: App not loading on mobile
**Solutions:**
1. Verify you're on the same network (or Tailscale connected)
2. Check PC is running FlaskMag
3. Try PC's IP address instead of hostname
4. Disable any VPN on mobile (except Tailscale)
5. Check firewall isn't blocking port 8501

#### Problem: Buttons too small on mobile
**Solutions:**
1. The secure edition has larger buttons by default
2. Zoom in browser if needed
3. Use tablet/landscape mode
4. Check CSS is loading (force refresh)

#### Problem: PDF won't display on mobile
**Solutions:**
1. Check network connection is stable
2. Try downloading PDF instead
3. Reduce zoom quality (if option available)
4. Close other browser tabs
5. Use WiFi instead of cellular

#### Problem: Typing is difficult
**Solutions:**
1. Use device keyboard suggestions
2. Enable autocomplete in browser
3. Use voice input (mobile feature)
4. Consider external keyboard for tablets

---

## Part 6: Performance Optimization for Mobile

### Best Practices

#### 1. Cache Everything First
Before going mobile, process all PDFs at home:
- Connect to home network
- Run "Process PDFs"
- Wait for indexing to complete
- Cache is stored locally for fast access

#### 2. Use WiFi When Possible
- Cellular can be slow for PDFs
- WiFi is faster and more stable
- Consider downloading PDFs for offline viewing

#### 3. Close Background Apps
- Free up mobile device memory
- Close other browser tabs
- Restart browser if slow

#### 4. Adjust Search Strategy
- Search for specific terms (not generic words)
- Use filters to narrow results
- Fewer results = faster loading

---

## Part 7: Multi-Device Setup

### Recommended Setup

#### Devices:
1. **Home PC** (Windows/Linux)
   - Runs FlaskMag 24/7
   - Stores all PDFs on network share
   - High performance for processing

2. **Laptop** (for travel)
   - Access via Tailscale
   - Login with credentials
   - Fast searching (cached)

3. **Tablet** (for reading)
   - Perfect for PDF viewing
   - Touch-optimized UI
   - Landscape mode ideal

4. **Phone** (quick searches)
   - Emergency access
   - Quick keyword searches
   - Download PDFs for offline

---

### Session Management Across Devices

Each device maintains its own session:
- Login once per device
- Session lasts 30 days (configurable)
- Can be logged in on multiple devices simultaneously
- Logout only affects current device

---

## Part 8: Backup and Security

### Backing Up Authentication

#### What to Backup:
1. **Configuration file:**
   ```
   ~/.flaskmag_cache/auth_config.yaml
   ```

2. **Cache files** (optional, for performance):
   ```
   ~/.flaskmag_cache/pdf_cache.pkl
   ~/.flaskmag_cache/text_index.db
   ```

#### Backup Command:
```bash
# Linux/Mac
cp -r ~/.flaskmag_cache ~/flaskmag_backup_$(date +%Y%m%d)

# Windows (PowerShell)
Copy-Item -Recurse "$env:USERPROFILE\.flaskmag_cache" -Destination "$env:USERPROFILE\flaskmag_backup_$(Get-Date -Format 'yyyyMMdd')"
```

---

### Security Checklist

- [ ] Changed default admin password
- [ ] Using strong passwords (12+ characters)
- [ ] Changed cookie key to unique value
- [ ] Set appropriate session expiry
- [ ] Using Tailscale for remote access (not exposing to internet)
- [ ] Backed up auth_config.yaml
- [ ] Tested login from each device
- [ ] Verified logout works properly
- [ ] Reviewed active sessions periodically

---

## Part 9: Quick Reference

### Configuration File Template

Save as `~/.flaskmag_cache/auth_config.yaml`:

```yaml
credentials:
  usernames:
    admin:
      name: Administrator
      password: YOUR_HASHED_PASSWORD_HERE

    user1:
      name: User One
      password: HASHED_PASSWORD_2

    user2:
      name: User Two
      password: HASHED_PASSWORD_3

cookie:
  expiry_days: 30
  key: CHANGE_THIS_TO_RANDOM_STRING
  name: flaskmag_auth_cookie
```

### Password Hash Generator

```python
#!/usr/bin/env python3
import hashlib

password = input("Enter password: ")
hashed = hashlib.sha256(password.encode()).hexdigest()
print(f"\nHashed password:\n{hashed}")
print(f"\nAdd this to auth_config.yaml under 'password:'")
```

Save as `hash_password.py` and run:
```bash
python hash_password.py
```

---

### Mobile Access Checklist

#### Before Leaving Home:
- [ ] FlaskMag is running on home PC
- [ ] All PDFs are processed and cached
- [ ] Tailscale is installed and connected on home PC
- [ ] Tested remote access works
- [ ] Know your Tailscale IP: `100.x.x.x`

#### On Mobile Device:
- [ ] Tailscale app installed
- [ ] Signed in with same account
- [ ] Connected to Tailscale network
- [ ] Bookmarked FlaskMag URL
- [ ] Added to home screen (optional)
- [ ] Tested login works

---

## Part 10: FAQ

### Q: Can I use Face ID / Fingerprint?
**A:** Your browser may support biometric autofill for saved passwords. Enable in browser settings.

### Q: How do I keep PC running 24/7?
**A:**
- Windows: Settings → Power → Sleep → Never
- Linux: Disable sleep in power settings
- Consider Wake-on-LAN for remote wake

### Q: What if I forget my password?
**A:**
1. Access your PC directly (keyboard/monitor)
2. Edit `~/.flaskmag_cache/auth_config.yaml`
3. Replace with new password hash
4. Or delete file to reset to defaults

### Q: Can multiple users login simultaneously?
**A:** Yes! Each user can have their own account and session.

### Q: Does it work offline?
**A:** Search works offline if cache exists. Viewing PDFs requires network access to Fritz!Box.

### Q: Can I use HTTPS instead of HTTP?
**A:** Yes, but requires reverse proxy setup (nginx, Caddy, etc.). Advanced configuration needed.

### Q: How much data does mobile use?
**A:**
- Search: < 100 KB per search (cached)
- PDF viewing: 1-5 MB per page
- Recommendation: Use WiFi when possible

### Q: Can I share PDFs with others?
**A:** Yes:
- Download button saves PDF locally
- Share button in mobile browser
- Or create separate user account for them

---

## Summary

The **Secure Edition** provides:
- ✅ Password-protected access
- ✅ Mobile-optimized interface
- ✅ Multi-user support
- ✅ Session management
- ✅ Touch-friendly UI
- ✅ All network features

**Recommended for:**
- Remote access scenarios
- Multi-user households
- Public/shared network access
- Mobile/tablet primary usage

**Default credentials:**
- Username: `admin`
- Password: `admin123`
- **⚠️ CHANGE IMMEDIATELY!**

---

**Enjoy secure, mobile-optimized access to your PDF collection from anywhere! 📱🔐**

For additional help, refer to:
- [NETWORK_SETUP_GUIDE.md](NETWORK_SETUP_GUIDE.md) - Tailscale and network setup
- [README.md](README.md) - General documentation
- Comments in `flask_stream_secure.py` - Code-level details
