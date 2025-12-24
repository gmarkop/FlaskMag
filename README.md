# FlaskMag - PDF Keyword Search Application

A powerful, high-performance Streamlit application for searching and browsing through PDF magazine collections with advanced features like parallel processing, caching, and cross-browser compatibility.

## Overview

FlaskMag is a sophisticated PDF search tool designed to help you quickly find content across large collections of PDF magazines. It features intelligent caching, SQLite-based indexing, parallel text extraction, and an intuitive web interface for viewing search results with context highlighting.

## Available Versions

### 📁 Local Version (`flask_stream13.py`)
- For local access only (at home)
- PDFs stored on local hard drive or internal storage
- Fastest performance
- No network dependencies

### 🌐 Network Version (`flask_stream_network.py`)
- **Access your PDFs remotely from anywhere in the world**
- PDFs stored on network share (Fritz!Box USB storage, NAS, etc.)
- Built-in network retry logic for reliability
- Optimized for use with Tailscale/VPN
- Local caching for fast searches even over slow connections
- **Perfect for: Accessing your collection while traveling, from office, or anywhere with internet**

👉 **See [NETWORK_SETUP_GUIDE.md](NETWORK_SETUP_GUIDE.md) for complete remote access setup instructions**

### 🔐 Secure Edition (`flask_stream_secure.py`) - **RECOMMENDED!**
- **Everything from Network Version PLUS:**
- 🔐 **User authentication** with password protection
- 📱 **Mobile-optimized design** for phones and tablets
- 👆 **Touch-friendly UI** with larger buttons
- 👥 **Multi-user support** with configurable accounts
- 🔒 **Session management** for secure access
- **Perfect for: Remote access with security, mobile/tablet usage, multi-user households**

👉 **See [AUTHENTICATION_MOBILE_GUIDE.md](AUTHENTICATION_MOBILE_GUIDE.md) for setup and mobile usage**

## Key Features

### Search & Indexing
- **Fast Full-Text Search**: SQLite-based text indexing for rapid keyword searches
- **Context Highlighting**: Shows surrounding text with highlighted keywords (black text on yellow background)
- **Smart Results Grouping**: Results organized by file with match counts
- **File Filtering**: Quick filter to narrow down results by filename
- **Multi-Directory Support**: Search across multiple PDF directories simultaneously
- **Advertisement Filtering**: Intelligent filtering to exclude ads and focus on actual content (travel reports, test rides, reviews)
  - Configurable word count threshold
  - Ad keyword detection (German magazines optimized)
  - Page position filtering (skip first/last pages)
  - See [AD_FILTERING_GUIDE.md](AD_FILTERING_GUIDE.md) and [IMPLEMENT_AD_FILTER.md](IMPLEMENT_AD_FILTER.md)

### Performance Optimizations
- **Parallel Processing**: Multi-threaded PDF processing using ThreadPoolExecutor
- **Intelligent Caching**: Pickle-based cache with modification time tracking
- **O(1) File Lookups**: Fast file path resolution using hash-based cache
- **Lazy Loading**: Only processes new or modified PDFs
- **Cached PDF Rendering**: Streamlit cache for rendered page images (1-hour TTL)

### PDF Viewing
- **In-Browser PDF Viewer**: Rendered page preview with PyMuPDF
- **Download PDFs**: Direct download button for full PDFs
- **Open in Browser**: Opens full PDF in new tab (works in all browsers including Edge)
- **Page Navigation**: Jump directly to pages with search results
- **High-Quality Rendering**: Configurable zoom (1.5x default) for clear viewing

### User Interface
- **Responsive Layout**: Two-column design (results + viewer)
- **Grouped View Mode**: Accordion-style results grouped by file
- **Linear View Mode**: Paginated list of all results (20 per page)
- **Progress Tracking**: Visual progress bars during PDF processing
- **Statistics Dashboard**: Real-time stats on cached files, pages, and performance

### Security & Authentication (Secure Edition)
- **Password Protection**: SHA-256 hashed passwords
- **Multi-User Support**: Configurable user accounts
- **Session Management**: Cookie-based sessions with expiry
- **Secure Access**: Authentication required for remote access
- **User Profiles**: Individual accounts with display names

### Mobile Optimization (Secure Edition)
- **Responsive Design**: Auto-adjusts for phone and tablet screens
- **Touch-Friendly**: 44px minimum touch targets
- **Mobile Navigation**: Optimized sidebar and menus
- **Fast on Mobile**: Local caching for quick searches
- **Add to Home Screen**: Works like a native app

### Cross-Platform & Browser Support
- **Platform Detection**: Automatic path configuration for Windows and Linux/WSL
- **Edge Browser Compatible**: Uses blob URLs instead of data URIs (v13 fix)
- **All Major Browsers**: Tested on Chrome, Firefox, Edge, and Safari
- **Mobile Browsers**: Optimized for Safari (iOS) and Chrome (Android)

## Installation

### Prerequisites

- Python 3.7 or higher
- pip package manager

### Required Python Packages

**Option 1: Install from requirements.txt (Recommended)**

```bash
pip install -r requirements.txt
```

**Option 2: Install manually**

For Local or Network versions:
```bash
pip install streamlit pdfplumber PyMuPDF
```

For Secure Edition (includes authentication):
```bash
pip install streamlit pdfplumber PyMuPDF pyyaml
```

**Required libraries:**
- `streamlit` - Web application framework
- `pdfplumber` - PDF text extraction
- `PyMuPDF` (fitz) - PDF rendering and image generation
- `pyyaml` - YAML config file support (Secure Edition only)
- `sqlite3` - Built-in (comes with Python)
- `pickle` - Built-in (comes with Python)

## Configuration

### PDF Directories

Edit the `PDF_DIRECTORIES` list in `flask_stream13.py` to point to your PDF collections:

**For Windows:**
```python
PDF_DIRECTORIES = [
    "E:\\PDF\\Tourenfahrer",
    "E:\\PDF\\Alpentourer",
    # Add your directories here
]
```

**For Linux/WSL:**
```python
PDF_DIRECTORIES = [
    "/mnt/e/PDF/Tourenfahrer",
    "/mnt/e/PDF/Alpentourer",
    # Add your directories here
]
```

The application automatically detects your platform and uses the appropriate paths.

### Logo (Optional)

Set the `LOGO_PATH` variable to display a custom logo:

```python
LOGO_PATH = "C:\\path\\to\\your\\logo.png"  # Windows
LOGO_PATH = "/home/user/path/to/logo.png"  # Linux
```

### Performance Tuning

Adjust these constants in the configuration section:

```python
MAX_WORKERS = min(multiprocessing.cpu_count(), 12)  # Thread count
CONTEXT_CHARS = 150  # Characters shown around keyword matches
```

### Auto-Start on Boot (Windows)

For 24/7 remote access, configure FlaskMag to start automatically when your PC boots:

```bash
# Edit the startup script with your paths
start_flaskmag.bat

# Add to Windows Startup folder
Win + R → shell:startup → Copy script here
```

👉 **See [AUTO_START_GUIDE.md](AUTO_START_GUIDE.md) for complete auto-start setup (3 methods included)**

**Benefits:**
- Always available for remote access
- Survives Windows updates and restarts
- No manual intervention needed
- Essential for reliable remote access

## Usage

### Starting the Application

Choose the version that fits your needs:

**Local Version (fastest, home only):**
```bash
streamlit run flask_stream13.py
```

**Network Version (remote access, no auth):**
```bash
streamlit run flask_stream_network.py
```

**Secure Edition (remote + authentication + mobile) - RECOMMENDED:**
```bash
streamlit run flask_stream_secure.py
```

The application will open in your default browser at `http://localhost:8501`

**Remote Access:**
- Once configured with Tailscale, access from anywhere at `http://<your-tailscale-ip>:8501`
- See [NETWORK_SETUP_GUIDE.md](NETWORK_SETUP_GUIDE.md) for network setup
- See [AUTHENTICATION_MOBILE_GUIDE.md](AUTHENTICATION_MOBILE_GUIDE.md) for authentication and mobile usage

**First Login (Secure Edition):**
- Username: `admin`
- Password: `admin123`
- ⚠️ **Change default password immediately!** See authentication guide.

### First-Time Setup

1. **Directory Validation**: The app checks if configured PDF directories exist
2. **File Indexing**: Builds a fast lookup cache of all PDF files
3. **Process PDFs**: Click "Process PDFs" to extract text from all PDFs
4. **Search Index**: Automatically creates SQLite database for fast searches

### Searching PDFs

1. Enter your keyword(s) in the search box
2. Click "Search" or press Enter
3. Results appear grouped by file (or use linear view)
4. Click "View" on any result to display that PDF page
5. Use "Download" or "Open" buttons to access the full PDF

### View Modes

**Grouped by File (Recommended)**
- Results organized by PDF filename
- Shows match count per file
- Auto-expands when 3 or fewer files have results
- Ideal for seeing which magazines have the most matches

**All Results (Linear)**
- Paginated list of all matches
- 20 results per page
- Good for scanning through all occurrences

### Cache Management

**Clear Cache**
- Removes all cached PDF text and index
- Use when PDFs have been updated or moved

**Rebuild Index**
- Recreates the SQLite search database
- Use if search results seem incomplete

## Technical Architecture

### Data Flow

```
PDF Files → Text Extraction (pdfplumber) → Pickle Cache → SQLite Index → Search Results
                    ↓
            Modification Tracking
                    ↓
            Only Process Updated Files
```

### File Structure

```
FlaskMag/
├── flask_stream13.py      # Main application
├── pdf_cache.pkl          # Cached PDF text (auto-generated)
├── text_index.db          # SQLite search index (auto-generated)
└── logo3.png              # Optional logo
```

### Key Components

1. **File Path Cache** (`build_file_path_cache`)
   - O(1) filename-to-path lookups
   - Built once at startup
   - Supports multiple directories

2. **PDF Cache Management** (`load_cached_data`, `save_cache`)
   - Pickle-based serialization
   - Tracks modification times
   - Only re-processes changed files

3. **Text Extraction** (`extract_pdf_text_pdfplumber`)
   - Uses pdfplumber for accuracy
   - Parallel processing with ThreadPoolExecutor
   - Normalizes whitespace for better searching

4. **SQLite Text Index** (`create_text_index_db`)
   - Full-text search capability
   - Indexed for performance
   - Stores filename, text, and page count

5. **Smart Search** (`smart_search`)
   - Pre-filters candidates using SQLite
   - Parallel page searching for large PDFs
   - Returns results with context

6. **PDF Rendering** (`render_pdf_page`)
   - Uses PyMuPDF for high-quality rendering
   - Cached with Streamlit @st.cache_data
   - Configurable zoom level

## Version History

### Secure Edition (Latest) - Authentication & Mobile
- **NEW: User authentication system** with SHA-256 password hashing
- **NEW: Mobile-responsive design** optimized for phones and tablets
- **Touch-friendly UI** with 44px minimum tap targets
- **Multi-user support** with configurable accounts
- **Session management** with cookie-based authentication
- **Mobile optimizations:** responsive CSS, larger buttons, optimized layouts
- **All Network Edition features** included (remote access, network retry, etc.)
- See `flask_stream_secure.py` and [AUTHENTICATION_MOBILE_GUIDE.md](AUTHENTICATION_MOBILE_GUIDE.md)

### Network Edition - Remote Access
- **Network share support** for Fritz!Box, NAS, and SMB/CIFS shares
- **Remote access via Tailscale/VPN** - access your collection from anywhere
- **Automatic network retry logic** for unreliable connections
- **Network status monitoring** with troubleshooting tips
- **Local caching** for fast searches over network
- **All Version 13 features included**
- See `flask_stream_network.py` and [NETWORK_SETUP_GUIDE.md](NETWORK_SETUP_GUIDE.md)

### Version 13 - Edge Browser Fix
- Fixed "Open PDF" button for Edge browser
- Switched from data URIs to blob URLs
- Eliminates "about:blank#blocked" error
- Compatible with all major browsers
- See `flask_stream13.py` for local-only use

### Version 12 Features
- File-grouped results view
- Quick filename filtering
- Improved result organization
- Enhanced UI/UX

### Earlier Versions
- SQLite-based search indexing
- Multi-threaded PDF processing
- Cached PDF rendering
- Context highlighting
- Cross-platform support

## Performance Metrics

- **Multi-Threading**: Uses up to 12 worker threads (CPU-dependent)
- **Cache Hit Rate**: Only processes new/modified files
- **Search Speed**: SQLite indexing enables sub-second searches
- **Rendering Cache**: 1-hour TTL reduces repeated rendering

## Troubleshooting

### PDFs Not Found
- Check that `PDF_DIRECTORIES` paths are correct
- Verify directories exist and are accessible
- Check platform-specific path format (Windows vs Linux)

### Slow Processing
- Increase `MAX_WORKERS` for more parallel threads
- Ensure PDFs are on fast storage (SSD recommended)
- Check for corrupted PDFs causing errors

### Search Results Missing
- Click "Rebuild Index" in the sidebar
- Clear cache and re-process PDFs
- Check if keyword case sensitivity matters

### Edge Browser Issues
- Version 13 should fix all Edge-related issues
- Uses blob URLs instead of data URIs
- If issues persist, try clearing browser cache

## Browser Compatibility

- ✅ Google Chrome (all versions)
- ✅ Mozilla Firefox (all versions)
- ✅ Microsoft Edge (v13 fixed)
- ✅ Safari (macOS/iOS)
- ✅ Opera, Brave, and other Chromium-based browsers

## License

This project is provided as-is for personal and educational use.

## Credits

Built with:
- [Streamlit](https://streamlit.io/) - Web application framework
- [pdfplumber](https://github.com/jsvine/pdfplumber) - PDF text extraction
- [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF rendering
- SQLite - Database indexing

## Contributing

Suggestions and improvements are welcome! This is a personal project for managing PDF magazine collections.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify your configuration matches your system
3. Review the error messages in the Streamlit interface

---

**Version**: 13 (Edge Browser Fixed)
**Last Updated**: 2025
**Platform**: Cross-platform (Windows, Linux, WSL)
