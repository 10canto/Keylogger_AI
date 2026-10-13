# 🚀 Deployment Guide - KeyGuard AI v2.6

## Step-by-Step: Deploy Your Installer to the Landing Page

### ✅ Prerequisites
- [x] Installer built: `installer_output\KeyloggerDetector_Setup.exe` (160 MB)
- [x] Landing page updated with v2.6 download link
- [x] GitHub account with repository access

---

## 📦 Step 1: Upload Installer to GitHub Releases

### Option A: Using GitHub Web Interface (Easiest)

1. **Go to your GitHub repository:**
   ```
   https://github.com/Antobenedict2006/Keylogger
   ```

2. **Click on "Releases" (right sidebar)**

3. **Click "Draft a new release"**

4. **Fill in the release details:**
   - **Tag version:** `v2.6`
   - **Release title:** `KeyGuard AI v2.6 - Fast Baseline Training`
   - **Description:**
   ```markdown
   ## 🎉 KeyGuard AI v2.6 - Fast Baseline Training
   
   ### ✨ What's New
   
   - **⚡ Two-Tier Baseline System** - Start protecting your system in just 5-10 minutes!
     - UI unlocks after 120 keystrokes + 200 mouse movements
     - Full statistical baseline continues collecting to 2000/3000 in background
   
   - **🔔 Baseline Completion Notifications**
     - Green success banner in UI
     - Desktop notification when training completes
     - Clear "✅ Baseline Saved!" message
   
   - **🔧 Enhanced Baseline Logic**
     - Checks both keyboard AND mouse baselines
     - Environment variable support for customization
     - Better training progress tracking
   
   ### 📥 Download
   
   **Windows Installer:** `KeyloggerDetector_Setup.exe` (160 MB)
   
   ### 🧪 Testing
   
   Set custom thresholds for demos:
   ```powershell
   $env:KGAI_BASELINE_KEYSTROKES = "50"
   $env:KGAI_BASELINE_MOUSE = "100"
   ```
   
   ### 📋 System Requirements
   
   - Windows 10 or 11 (64-bit)
   - Administrator privileges
   - ~100 MB disk space
   
   ### ⚠️ First-Run Notice
   
   Windows SmartScreen may show a warning. Click "More info" → "Run anyway"
   This is normal for new independent software without expensive code-signing certificates.
   
   ---
   
   **Full Changelog:** See [CHANGELOG.md](link-to-changelog)
   ```

5. **Upload the installer:**
   - Drag and drop: `installer_output\KeyloggerDetector_Setup.exe`
   - Wait for upload to complete (may take a few minutes due to size)

6. **Click "Publish release"**

7. **Copy the download URL** (it will be):
   ```
   https://github.com/Antobenedict2006/Keylogger/releases/download/v2.6/KeyloggerDetector_Setup.exe
   ```

### Option B: Using GitHub CLI (Advanced)

```powershell
# Install GitHub CLI if not already installed
# https://cli.github.com/

# Authenticate
gh auth login

# Create release and upload
cd "C:\Users\Anto\Downloads\Keylogger-main (3)\Keylogger-main (2)\Keylogger-main\Keylogger-main"

gh release create v2.6 `
  --title "KeyGuard AI v2.6 - Fast Baseline Training" `
  --notes "See release notes above" `
  installer_output\KeyloggerDetector_Setup.exe
```

---

## 🌐 Step 2: Deploy Landing Page to Vercel

Your landing page is already updated! Now deploy it:

### Using Vercel CLI (Recommended)

```powershell
cd "C:\Users\Anto\Downloads\Keylogger-main (3)\Keylogger-main (2)\Keylogger-main\Keylogger-main\landing-page"

# Install Vercel CLI if not already installed
npm install -g vercel

# Deploy to production
vercel --prod
```

### Using Vercel GitHub Integration

1. **Push changes to GitHub:**
   ```powershell
   cd "C:\Users\Anto\Downloads\Keylogger-main (3)\Keylogger-main (2)\Keylogger-main\Keylogger-main"
   
   git add landing-page/index.html landing-page/style.css
   git commit -m "Update to v2.6 with fast baseline training"
   git push origin main
   ```

2. **Vercel auto-deploys** (if connected to your GitHub repo)

---

## 🎯 Step 3: Verify Everything Works

### Test Checklist

- [ ] **GitHub Release**
  - Visit: `https://github.com/Antobenedict2006/Keylogger/releases`
  - Verify v2.6 release is visible
  - Test download link works

- [ ] **Landing Page**
  - Visit: Your Vercel URL (e.g., `keyguard-ai.vercel.app`)
  - Click "Download for Windows" button
  - Verify it downloads `KeyloggerDetector_Setup.exe`

- [ ] **Installer**
  - Run the downloaded installer
  - Verify it installs correctly
  - Test the application launches

- [ ] **Fast Baseline**
  - Open app
  - Type ~120 characters, move mouse ~200 times
  - Verify UI unlocks quickly
  - Check for green banner + notification

---

## 🔧 Alternative Hosting Options

### If GitHub Release is Unavailable

**Option 1: Google Drive**
1. Upload installer to Google Drive
2. Right-click → Share → Anyone with link can view
3. Get shareable link
4. Update landing page href to Google Drive link

**Option 2: Dropbox**
1. Upload to Dropbox
2. Generate public link
3. Replace `www.dropbox.com` with `dl.dropboxusercontent.com` in URL
4. Update landing page

**Option 3: Self-Hosted (Advanced)**
- Use AWS S3
- Use Azure Blob Storage
- Use your own web server

---

## 📝 Update Landing Page Download Link

The landing page is already updated with:

```html
<a href="https://github.com/Antobenedict2006/Keylogger/releases/download/v2.6/KeyloggerDetector_Setup.exe" 
   class="btn-download" download>
    <span class="btn-icon">⬇️</span>
    <div class="btn-text">
        <span class="btn-main">Download for Windows</span>
        <span class="btn-sub">Version v2.6 • 160 MB • Fast Baseline Training</span>
    </div>
</a>
```

**New Features Highlighted:**
- ✨ Hero section now shows "v2.6" badge
- ✨ Animated highlight: "NEW: Fast 5-minute baseline training"
- ✨ Updated version and file size

---

## 🚨 Important Notes

### File Size Considerations
- **160 MB** is large for web hosting
- GitHub Releases is perfect for this (supports large files)
- Vercel/Netlify static hosting has file size limits

### Windows SmartScreen Warning
- Users will see SmartScreen warning on first run
- This is NORMAL for unsigned executables
- Your landing page already explains this in "System Requirements"

### Code Signing (Optional Future)
To eliminate SmartScreen warnings:
1. Purchase code signing certificate (~$100-400/year)
2. Sign the executable with `signtool.exe`
3. Build reputation over time

---

## 📊 Analytics (Optional)

Track downloads by adding to `script.js`:

```javascript
document.querySelector('.btn-download')?.addEventListener('click', () => {
    // Google Analytics
    if (typeof gtag !== 'undefined') {
        gtag('event', 'download', {
            'event_category': 'installer',
            'event_label': 'v2.6',
            'value': 1
        });
    }
    
    // Or Simple Analytics / Plausible
    console.log('Download initiated:', new Date().toISOString());
});
```

---

## ✅ Deployment Checklist

- [ ] Build installer with improved baseline logic
- [ ] Create GitHub Release v2.6
- [ ] Upload installer to release
- [ ] Update landing page (already done!)
- [ ] Deploy landing page to Vercel
- [ ] Test download link
- [ ] Test installer installation
- [ ] Test fast baseline training
- [ ] Share link with users

---

## 🎉 You're Done!

Your users can now:
1. Visit your Vercel landing page
2. Click "Download for Windows"
3. Install KeyGuard AI v2.6
4. Start protecting their system in just 5-10 minutes!

**Landing Page:** `https://your-app.vercel.app`
**Installer Download:** `https://github.com/Antobenedict2006/Keylogger/releases/download/v2.6/KeyloggerDetector_Setup.exe`

---

## 📞 Need Help?

- **Vercel Issues:** Check [Vercel Docs](https://vercel.com/docs)
- **GitHub Releases:** Check [GitHub Docs](https://docs.github.com/en/repositories/releasing-projects-on-github)
- **Installer Issues:** Run `.\scripts\build.ps1 -Clean` to rebuild

