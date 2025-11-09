"""
Flask Stream Network - Remote Access via Network Share (Fritz!Box Compatible)
Key improvements over v13:
- Network share support (Fritz!Box, Samba, CIFS)
- Automatic network path detection (Windows/Linux)
- Connection retry logic for unreliable networks
- Network status monitoring
- Optimized for remote access via Tailscale/VPN
- All v13 features included
"""

import os
import pickle
import sqlite3
import multiprocessing
import base64
import platform
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import closing
from datetime import datetime
from pathlib import Path
import re
from collections import defaultdict

import pdfplumber
import streamlit as st
import streamlit.components.v1 as components
import fitz  # PyMuPDF for PDF rendering

# ============================================================================
# NETWORK CONFIGURATION
# ============================================================================

# Fritz!Box Network Share Configuration
# Replace these with your actual Fritz!Box settings
FRITZBOX_IP = "192.168.178.1"  # Default Fritz!Box IP (or use fritz.box)
FRITZBOX_SHARE_NAME = "USB-Storage"  # Check your Fritz!Box storage name
FRITZBOX_USERNAME = ""  # Leave empty if no authentication required
FRITZBOX_PASSWORD = ""  # Leave empty if no authentication required

# Network path configuration - CHOOSE YOUR PLATFORM
if platform.system() == 'Windows':
    # Windows UNC paths (\\computer\share\folder)
    NETWORK_BASE = f"\\\\{FRITZBOX_IP}\\{FRITZBOX_SHARE_NAME}"
    # OR if you've mapped a network drive:
    # NETWORK_BASE = "Z:"  # Mapped network drive letter

    PDF_DIRECTORIES = [
        f"{NETWORK_BASE}\\PDFs\\Tourenfahrer",
        f"{NETWORK_BASE}\\PDFs\\Alpentourer",
        f"{NETWORK_BASE}\\PDFs\\MR",
        f"{NETWORK_BASE}\\PDFs\\MS",
        f"{NETWORK_BASE}\\PDFs\\MRide",
        f"{NETWORK_BASE}\\PDFs\\Bike",
        f"{NETWORK_BASE}\\PDFs\\Motorrad",
        f"{NETWORK_BASE}\\PDFs\\Ride",
        f"{NETWORK_BASE}\\PDFs\\MSL"
    ]
    LOGO_PATH = f"{NETWORK_BASE}\\logo3.png"

else:  # Linux/WSL
    # Linux SMB mount points
    # You need to mount the Fritz!Box share first:
    # sudo mount -t cifs //<FRITZBOX_IP>/<SHARE_NAME> /mnt/fritzbox -o username=<user>,password=<pass>
    NETWORK_BASE = "/mnt/fritzbox"  # Your SMB mount point

    PDF_DIRECTORIES = [
        f"{NETWORK_BASE}/PDFs/Tourenfahrer",
        f"{NETWORK_BASE}/PDFs/Alpentourer",
        f"{NETWORK_BASE}/PDFs/MR",
        f"{NETWORK_BASE}/PDFs/MS",
        f"{NETWORK_BASE}/PDFs/MRide",
        f"{NETWORK_BASE}/PDFs/Bike",
        f"{NETWORK_BASE}/PDFs/Motorrad",
        f"{NETWORK_BASE}/PDFs/Ride",
        f"{NETWORK_BASE}/PDFs/MSL"
    ]
    LOGO_PATH = f"{NETWORK_BASE}/logo3.png"

# Local cache directory (stores on PC, not network share for speed)
LOCAL_CACHE_DIR = os.path.join(os.path.expanduser("~"), ".flaskmag_cache")
os.makedirs(LOCAL_CACHE_DIR, exist_ok=True)

CACHE_FILE = os.path.join(LOCAL_CACHE_DIR, "pdf_cache.pkl")
TEXT_INDEX_DB = os.path.join(LOCAL_CACHE_DIR, "text_index.db")

# Performance settings
CONTEXT_CHARS = 150
MAX_WORKERS = min(multiprocessing.cpu_count(), 12)

# Network settings
NETWORK_RETRY_COUNT = 3
NETWORK_RETRY_DELAY = 2  # seconds
NETWORK_TIMEOUT = 30  # seconds for network operations

# Global file path cache - built once at startup
_file_path_cache = {}
_network_status = {"connected": False, "last_check": None, "message": ""}


# ============================================================================
# NETWORK HELPER FUNCTIONS
# ============================================================================

def check_network_connectivity():
    """Check if network share is accessible"""
    try:
        # Try to list the base network directory
        if os.path.exists(NETWORK_BASE):
            # Try to actually read the directory (not just check existence)
            os.listdir(NETWORK_BASE)
            _network_status["connected"] = True
            _network_status["last_check"] = datetime.now()
            _network_status["message"] = f"✅ Connected to {NETWORK_BASE}"
            return True
        else:
            _network_status["connected"] = False
            _network_status["last_check"] = datetime.now()
            _network_status["message"] = f"❌ Network share not accessible: {NETWORK_BASE}"
            return False
    except (PermissionError, OSError) as e:
        _network_status["connected"] = False
        _network_status["last_check"] = datetime.now()
        _network_status["message"] = f"❌ Network error: {str(e)}"
        return False


def retry_network_operation(func, *args, **kwargs):
    """Retry a network operation with exponential backoff"""
    for attempt in range(NETWORK_RETRY_COUNT):
        try:
            return func(*args, **kwargs)
        except (PermissionError, OSError, IOError) as e:
            if attempt < NETWORK_RETRY_COUNT - 1:
                wait_time = NETWORK_RETRY_DELAY * (2 ** attempt)
                st.warning(f"Network error (attempt {attempt + 1}/{NETWORK_RETRY_COUNT}): {e}")
                st.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                st.error(f"Network operation failed after {NETWORK_RETRY_COUNT} attempts: {e}")
                raise


def display_network_status():
    """Display network connection status in the UI"""
    if _network_status["last_check"]:
        if _network_status["connected"]:
            st.success(_network_status["message"])
        else:
            st.error(_network_status["message"])

            # Provide troubleshooting tips
            with st.expander("🔧 Network Troubleshooting"):
                st.markdown(f"""
                **Connection Failed to:** `{NETWORK_BASE}`

                **Windows Users:**
                1. Open File Explorer and try to access: `{NETWORK_BASE}`
                2. If prompted, enter Fritz!Box credentials
                3. Consider mapping as network drive (right-click → Map network drive)
                4. Check if Fritz!Box storage is turned on

                **Linux/WSL Users:**
                1. Mount the share first:
                   ```bash
                   sudo mkdir -p /mnt/fritzbox
                   sudo mount -t cifs //{FRITZBOX_IP}/{FRITZBOX_SHARE_NAME} /mnt/fritzbox -o username=guest,password=
                   ```
                2. Check if mount is successful: `ls /mnt/fritzbox`

                **General Troubleshooting:**
                - Verify Fritz!Box is powered on
                - Check USB drive is connected to Fritz!Box
                - Verify you're connected to your home network (or VPN)
                - Check Fritz!Box settings: Home Network → Storage (NAS)
                - Ping Fritz!Box: `ping {FRITZBOX_IP}`
                """)


# ============================================================================
# FILE PATH CACHE (Optimization 1: O(1) lookups with network retry)
# ============================================================================

def build_file_path_cache():
    """Build a mapping of filename -> full_path for fast O(1) lookups"""
    cache = {}

    if not check_network_connectivity():
        st.warning("⚠️ Network share not accessible. Some features may be limited.")
        return cache

    for pdf_dir in PDF_DIRECTORIES:
        if not os.path.exists(pdf_dir):
            continue
        try:
            # Use retry logic for network directory listing
            def list_directory():
                return os.listdir(pdf_dir)

            filenames = retry_network_operation(list_directory)

            for filename in filenames:
                if filename.lower().endswith('.pdf'):
                    # Store absolute path
                    cache[filename] = os.path.abspath(os.path.join(pdf_dir, filename))
        except (PermissionError, OSError) as e:
            st.warning(f"Cannot access directory {pdf_dir}: {e}")

    return cache


def get_pdf_path(filename):
    """Fast O(1) lookup of PDF path"""
    return _file_path_cache.get(filename) or _file_path_cache.get(os.path.basename(filename))


def get_all_pdf_files():
    """Get all PDF files from all configured directories with network retry"""
    all_pdf_files = []

    for pdf_dir in PDF_DIRECTORIES:
        if os.path.exists(pdf_dir):
            try:
                def get_pdfs():
                    return [
                        os.path.join(pdf_dir, f)
                        for f in os.listdir(pdf_dir)
                        if f.lower().endswith(".pdf")
                    ]

                pdf_files = retry_network_operation(get_pdfs)
                all_pdf_files.extend(pdf_files)

            except Exception as e:
                st.warning(f"Error accessing {pdf_dir}: {e}")

    return all_pdf_files


# ============================================================================
# PDF CACHE MANAGEMENT
# ============================================================================

@st.cache_data
def load_cached_data(cache_file=CACHE_FILE):
    """Load cached PDF data with Streamlit caching"""
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "rb") as f:
                return pickle.load(f)
        except (pickle.PickleError, EOFError):
            st.warning("Cache file corrupted, rebuilding...")
            return {}
    return {}


def save_cache(data, cache_file=CACHE_FILE):
    """Save cached data with error handling"""
    try:
        with open(cache_file, "wb") as f:
            pickle.dump(data, f)
    except Exception as e:
        st.error(f"Failed to save cache: {e}")


def get_file_modification_time(file_path):
    """Get file modification timestamp with network retry"""
    def get_mtime():
        return os.path.getmtime(file_path)

    return retry_network_operation(get_mtime)


# ============================================================================
# PDF TEXT EXTRACTION
# ============================================================================

def extract_pdf_text_pdfplumber(pdf_path):
    """Extract text from PDF using pdfplumber with network retry"""
    def do_extraction():
        pages_text = []
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                try:
                    # Extract text with better formatting preservation
                    text = page.extract_text()
                    if text:
                        # Clean up text: normalize whitespace but preserve some structure
                        text = re.sub(r'\s+', ' ', text.strip())
                        pages_text.append(text)
                    else:
                        pages_text.append("")
                except Exception as e:
                    st.warning(f"Error extracting page {page_num + 1} from {os.path.basename(pdf_path)}: {e}")
                    pages_text.append("")
        return pages_text

    try:
        return retry_network_operation(do_extraction)
    except Exception as e:
        st.error(f"Failed to process {os.path.basename(pdf_path)}: {e}")
        return []


def check_for_updates(pdf_files, pdf_cache):
    """Check if any PDFs have been modified since last cache"""
    cache_metadata = pdf_cache.get('_metadata', {})
    updated_files = []

    for pdf_file_path in pdf_files:
        file_name = os.path.basename(pdf_file_path)
        try:
            current_mtime = get_file_modification_time(pdf_file_path)
            cached_mtime = cache_metadata.get(file_name, {}).get('mtime', 0)

            if current_mtime > cached_mtime:
                updated_files.append(pdf_file_path)
        except Exception as e:
            st.warning(f"Cannot check modification time for {file_name}: {e}")

    return updated_files


def process_pdfs_batch(pdf_files, pdf_cache):
    """Process PDFs in batches with optimized threading and progress tracking"""
    if not pdf_files:
        return pdf_cache

    progress_bar = st.progress(0)
    status_text = st.empty()

    processed_count = 0
    total_files = len(pdf_files)

    # Initialize metadata if not exists
    if '_metadata' not in pdf_cache:
        pdf_cache['_metadata'] = {}

    st.info(f"Using {MAX_WORKERS} worker threads for optimal performance")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all tasks
        future_to_file = {
            executor.submit(extract_pdf_text_pdfplumber, pdf_file_path): pdf_file_path
            for pdf_file_path in pdf_files
        }

        # Process completed tasks
        for future in as_completed(future_to_file):
            pdf_file_path = future_to_file[future]
            file_name = os.path.basename(pdf_file_path)

            try:
                text_pages = future.result()
                pdf_cache[file_name] = text_pages

                # Update metadata
                pdf_cache['_metadata'][file_name] = {
                    'mtime': get_file_modification_time(pdf_file_path),
                    'processed_at': datetime.now().isoformat()
                }

                processed_count += 1
                progress = processed_count / total_files
                progress_bar.progress(progress)
                status_text.text(f"Processed {processed_count}/{total_files}: {file_name}")

            except Exception as e:
                st.error(f"Failed to process {file_name}: {e}")

    progress_bar.empty()
    status_text.empty()

    return pdf_cache


# ============================================================================
# SQLITE TEXT INDEX (Optimization 2: Fast database searches)
# ============================================================================

def create_text_index_db(pdf_cache):
    """Create SQLite-based text index for faster searches"""
    with closing(sqlite3.connect(TEXT_INDEX_DB)) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS text_index (
                filename TEXT PRIMARY KEY,
                full_text TEXT,
                page_count INTEGER
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_fulltext ON text_index(full_text)')

        # Clear existing data
        conn.execute('DELETE FROM text_index')

        # Insert data
        for pdf_file, pages in pdf_cache.items():
            if pdf_file == '_metadata':
                continue

            full_text = ' '.join(pages).lower()
            conn.execute(
                'INSERT OR REPLACE INTO text_index (filename, full_text, page_count) VALUES (?, ?, ?)',
                (pdf_file, full_text, len(pages))
            )

        conn.commit()

    return TEXT_INDEX_DB


def search_text_index(keyword):
    """Fast SQLite-based search to get candidate files"""
    if not os.path.exists(TEXT_INDEX_DB):
        return None

    keyword_pattern = f'%{keyword.lower()}%'

    try:
        with closing(sqlite3.connect(TEXT_INDEX_DB)) as conn:
            cursor = conn.execute(
                'SELECT filename FROM text_index WHERE full_text LIKE ?',
                (keyword_pattern,)
            )
            return [row[0] for row in cursor.fetchall()]
    except sqlite3.Error:
        return None


# ============================================================================
# SEARCH FUNCTIONALITY (Optimization 3: Parallel processing)
# ============================================================================

def search_with_context(keyword, text, original_text):
    """Extract context around keyword matches with improved highlighting - optimized version"""
    keyword_lower = keyword.lower()
    text_lower = text.lower()
    results = []

    # Find all match positions at once using regex
    pattern = re.compile(re.escape(keyword_lower))
    matches = [m.start() for m in pattern.finditer(text_lower)]

    for pos in matches:
        # Calculate context boundaries
        context_start = max(0, pos - CONTEXT_CHARS)
        context_end = min(len(text), pos + len(keyword) + CONTEXT_CHARS)

        # Adjust to word boundaries
        while context_start > 0 and original_text[context_start] not in ' \n\t':
            context_start -= 1
        while context_end < len(original_text) and original_text[context_end] not in ' \n\t':
            context_end += 1

        # Extract context
        context = original_text[context_start:context_end].strip()

        # Highlight keyword with better styling (black text on yellow background for readability)
        highlighted_context = re.sub(
            f"({re.escape(keyword)})",
            r"<span style='background-color: yellow; color: black; font-weight: bold; padding: 2px;'>\1</span>",
            context,
            flags=re.IGNORECASE
        )

        results.append(highlighted_context)

    return results


def search_pages_parallel(pdf_file, pages, keyword):
    """Search pages in parallel for faster processing"""
    def search_single_page(page_data):
        page_number, page_text = page_data
        if keyword.lower() not in page_text.lower():
            return []

        contexts = search_with_context(keyword, page_text, page_text)
        return [{
            "file": pdf_file,
            "page_number": page_number + 1,
            "context": context,
            "full_text": page_text,
            "full_path": get_pdf_path(pdf_file)  # Use optimized O(1) lookup
        } for context in contexts]

    page_results = []

    # Use parallel processing for PDFs with many pages
    if len(pages) > 20:
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = executor.map(search_single_page, enumerate(pages))
            for result_list in futures:
                page_results.extend(result_list)
    else:
        # Sequential for small PDFs (less overhead)
        for i, page_text in enumerate(pages):
            page_results.extend(search_single_page((i, page_text)))

    return page_results


def smart_search(keyword, pdf_cache):
    """Optimized search function with SQLite backend and parallel processing"""
    if not keyword.strip():
        return []

    keyword = keyword.strip()
    results = []

    # Get candidate files from SQLite index
    candidate_files = search_text_index(keyword)
    if candidate_files is None:
        candidate_files = [k for k in pdf_cache.keys() if k != '_metadata']

    # Search each PDF (pages processed in parallel internally)
    for pdf_file in candidate_files:
        if pdf_file not in pdf_cache:
            continue

        pages = pdf_cache[pdf_file]
        page_results = search_pages_parallel(pdf_file, pages, keyword)
        results.extend(page_results)

    return results


# ============================================================================
# RESULTS ORGANIZATION (New in v12)
# ============================================================================

def group_results_by_file(results):
    """Group search results by PDF file with counts"""
    file_groups = defaultdict(list)
    for result in results:
        file_groups[result['file']].append(result)

    # Sort by number of results (descending)
    sorted_files = sorted(file_groups.items(), key=lambda x: len(x[1]), reverse=True)
    return dict(sorted_files)


# ============================================================================
# PDF RENDERING (Optimization 4: Cached rendering)
# ============================================================================

@st.cache_data(ttl=3600)  # Cache rendered pages for 1 hour
def render_pdf_page(pdf_path, page_number, zoom=1.5):
    """Render a specific PDF page as image using PyMuPDF with caching and network retry"""
    def do_render():
        doc = fitz.open(pdf_path)
        if page_number > len(doc):
            doc.close()
            return None

        page = doc[page_number - 1]  # PyMuPDF uses 0-based indexing

        # Render page to image with zoom
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")

        doc.close()
        return img_data

    try:
        return retry_network_operation(do_render)
    except Exception as e:
        st.error(f"Error rendering PDF page: {e}")
        return None


def display_pdf_viewer(pdf_path, page_number, keyword=None):
    """Display PDF page with optional keyword highlighting"""
    if not pdf_path or not os.path.exists(pdf_path):
        st.error(f"❌ PDF file not found at: {pdf_path}")
        st.write("🔍 Debug info:")
        st.write(f"  - Path provided: `{pdf_path}`")
        st.write(f"  - Platform: {platform.system()}")
        st.write(f"  - Network base: `{NETWORK_BASE}`")
        st.write(f"  - Network status: {_network_status['connected']}")
        return

    try:
        img_data = render_pdf_page(pdf_path, page_number)

        if img_data:
            # Convert to base64 for display
            img_b64 = base64.b64encode(img_data).decode()

            # Show which directory the file is from
            directory = os.path.dirname(pdf_path)
            directory_name = os.path.basename(directory)

            st.markdown(f"""
            <div style="text-align: center; border: 2px solid #ddd; border-radius: 10px; padding: 10px; background: white;">
                <h4>📄 {os.path.basename(pdf_path)} - Page {page_number}</h4>
                <p style="color: #666; font-size: 12px;">📂 From: {directory_name} (Network Share)</p>
                <img src="data:image/png;base64,{img_b64}" style="max-width: 100%; height: auto; border: 1px solid #ccc;">
            </div>
            """, unsafe_allow_html=True)

            # Download and Open buttons
            try:
                def read_pdf():
                    with open(pdf_path, "rb") as f:
                        return f.read()

                pdf_data = retry_network_operation(read_pdf)

                # Create two columns for buttons
                btn_col1, btn_col2 = st.columns(2)

                with btn_col1:
                    st.download_button(
                        label="📥 Download Full PDF",
                        data=pdf_data,
                        file_name=os.path.basename(pdf_path),
                        mime="application/pdf",
                        key=f"download_{pdf_path}_{page_number}"
                    )

                with btn_col2:
                    # Use blob URL method instead of data URI (fixes Edge browser issue)
                    pdf_b64 = base64.b64encode(pdf_data).decode()

                    # Create a unique ID for this button
                    button_id = f"open_pdf_{hash(pdf_path)}_{page_number}"

                    # JavaScript to create blob URL and open PDF (works in all browsers including Edge)
                    open_pdf_html = f"""
                    <button id="{button_id}"
                            style="display: inline-block;
                                   padding: 0.25rem 0.75rem;
                                   background-color: #ff4b4b;
                                   color: white;
                                   text-decoration: none;
                                   border-radius: 0.25rem;
                                   font-weight: 400;
                                   text-align: center;
                                   white-space: nowrap;
                                   user-select: none;
                                   border: 1px solid transparent;
                                   font-size: 1rem;
                                   line-height: 1.6;
                                   cursor: pointer;">
                        📖 Open Full PDF
                    </button>
                    <script>
                    document.getElementById('{button_id}').addEventListener('click', function() {{
                        // Convert base64 to blob (works better than data URI in Edge)
                        const byteCharacters = atob('{pdf_b64}');
                        const byteNumbers = new Array(byteCharacters.length);
                        for (let i = 0; i < byteCharacters.length; i++) {{
                            byteNumbers[i] = byteCharacters.charCodeAt(i);
                        }}
                        const byteArray = new Uint8Array(byteNumbers);
                        const blob = new Blob([byteArray], {{type: 'application/pdf'}});

                        // Create blob URL and open in new tab
                        const url = URL.createObjectURL(blob);
                        window.open(url, '_blank');

                        // Clean up after 1 minute
                        setTimeout(function() {{
                            URL.revokeObjectURL(url);
                        }}, 60000);
                    }});
                    </script>
                    """

                    # Use components.html for better JavaScript execution
                    components.html(open_pdf_html, height=50)

            except Exception as e:
                st.error(f"Error reading PDF for download/open: {e}")
        else:
            st.error("Could not render PDF page")
    except Exception as e:
        st.error(f"Error in PDF viewer: {e}")


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    global _file_path_cache

    st.set_page_config(
        page_title="PDF Keyword Search - Network Edition",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Add logo if exists
    if os.path.exists(LOGO_PATH):
        try:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(LOGO_PATH, width=300)
        except Exception:
            pass  # Logo not critical

    st.title("🔍 PDF Keyword Search - Network Edition")
    st.write("Search through your PDF magazines on Fritz!Box network share - Access from anywhere via Tailscale!")

    # Network status check
    with st.spinner("Checking network connectivity..."):
        check_network_connectivity()

    display_network_status()

    if not _network_status["connected"]:
        st.stop()

    # Build path cache once at startup (Optimization 1)
    if not _file_path_cache:
        with st.spinner("Building file index from network share..."):
            _file_path_cache = build_file_path_cache()
            if _file_path_cache:
                st.success(f"✅ Indexed {len(_file_path_cache)} PDF files from network")
            else:
                st.warning("⚠️ No PDF files found. Check your network paths.")

    # Check if PDF directories exist
    valid_directories = [d for d in PDF_DIRECTORIES if os.path.exists(d)]
    invalid_directories = [d for d in PDF_DIRECTORIES if not os.path.exists(d)]

    if not valid_directories:
        st.error("❌ None of the configured PDF directories exist on network share:")
        for d in PDF_DIRECTORIES:
            st.error(f"  - {d}")
        st.info(f"""
        💡 **Configuration needed:**
        - Network Base: `{NETWORK_BASE}`
        - Platform: {platform.system()}
        - Update PDF_DIRECTORIES in the code for your network structure
        """)
        st.stop()

    # Show directory status
    with st.expander(f"📚 Found {len(valid_directories)} valid network directories", expanded=False):
        for d in valid_directories:
            try:
                pdf_count = len([f for f in os.listdir(d) if f.lower().endswith('.pdf')])
                st.success(f"  ✅ {d} ({pdf_count} PDFs)")
            except Exception as e:
                st.warning(f"  ⚠️ {d} - Error: {e}")

        if invalid_directories:
            st.warning("⚠️ Skipping invalid directories:")
            for d in invalid_directories:
                st.warning(f"  ❌ {d}")

    # Get PDF files from all directories
    with st.spinner("Scanning network directories..."):
        pdf_files = get_all_pdf_files()

    if not pdf_files:
        st.warning("No PDF files found in any configured network directories")
        st.stop()

    st.success(f"📚 Found {len(pdf_files)} total PDF files | 🚀 Using {MAX_WORKERS} worker threads | 🌐 Network Share")

    # Load cached data (from local PC for speed)
    with st.spinner("Loading cached data from local storage..."):
        pdf_cache = load_cached_data()

    # Check for new or updated files
    files_to_process = check_for_updates(pdf_files, pdf_cache)
    new_files = [f for f in pdf_files if os.path.basename(f) not in pdf_cache]
    files_to_process.extend(new_files)

    # Remove duplicates
    files_to_process = list(set(files_to_process))

    # Process new/updated PDFs
    if files_to_process:
        st.warning(f"⚡ Found {len(files_to_process)} files to process/update from network share.")
        if st.button("🚀 Process PDFs", key="process_button", type="primary"):
            with st.spinner("Processing PDFs from network share (this may take longer over network)..."):
                pdf_cache = process_pdfs_batch(files_to_process, pdf_cache)
                save_cache(pdf_cache)

                # Rebuild SQLite index after processing
                with st.spinner("Building search index..."):
                    create_text_index_db(pdf_cache)

                st.success("✅ PDF processing complete! Cache saved locally for faster future access.")
                st.rerun()

    # Create SQLite text index if needed (Optimization 2)
    if not os.path.exists(TEXT_INDEX_DB) and pdf_cache:
        with st.spinner("Creating SQLite search index..."):
            create_text_index_db(pdf_cache)
            st.success("✅ Search index created!")

    # Search interface
    st.markdown("---")
    col1, col2 = st.columns([4, 1])

    with col1:
        keyword = st.text_input(
            "🔎 Enter keyword(s) to search:",
            placeholder="Type your search term here...",
            key="search_input"
        )

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Spacing
        search_button = st.button("🔍 Search", type="primary")

    # Search functionality
    if keyword and (search_button or keyword):
        with st.spinner(f"🔍 Searching for '{keyword}'..."):
            results = smart_search(keyword, pdf_cache)

        # Display results
        if results:
            st.success(f"✅ Found {len(results)} results across {len(set(r['file'] for r in results))} files!")

            # Create two columns: Results and PDF Viewer
            col1, col2 = st.columns([1, 1])

            with col1:
                st.header("📋 Search Results")

                # Group results by file
                file_groups = group_results_by_file(results)

                # Filter bar for filenames
                file_filter = st.text_input(
                    "🔍 Filter files by name:",
                    placeholder="Type filename to filter...",
                    key="file_filter"
                )

                # Filter files based on search
                if file_filter:
                    file_groups = {
                        filename: file_results
                        for filename, file_results in file_groups.items()
                        if file_filter.lower() in filename.lower()
                    }

                # Results summary
                if len(file_groups) > 0:
                    st.info(f"📊 Showing {len(file_groups)} files with results")

                    # Display mode selection
                    display_mode = st.radio(
                        "View mode:",
                        ["Grouped by File (Recommended)", "All Results (Linear)"],
                        horizontal=True,
                        key="display_mode"
                    )

                    # Store selected result in session state
                    if 'selected_result' not in st.session_state:
                        st.session_state.selected_result = None

                    if display_mode == "Grouped by File (Recommended)":
                        # FILE-GROUPED ACCORDION VIEW
                        result_counter = 0
                        for filename, file_results in file_groups.items():
                            # Get directory info
                            dir_name = ""
                            if file_results[0].get('full_path'):
                                dir_name = os.path.basename(os.path.dirname(file_results[0]['full_path']))

                            # Expander for each file
                            with st.expander(
                                f"📄 {filename} ({len(file_results)} results) 📂 {dir_name}",
                                expanded=len(file_groups) <= 3  # Auto-expand if 3 or fewer files
                            ):
                                for result in file_results:
                                    col_a, col_b = st.columns([3, 1])

                                    with col_a:
                                        st.markdown(f"**Page {result['page_number']}**")
                                        st.markdown(f"{result['context']}", unsafe_allow_html=True)

                                    with col_b:
                                        if st.button(f"👁️ View", key=f"view_{result_counter}", help="View this page"):
                                            st.session_state.selected_result = result

                                    st.markdown("---")
                                    result_counter += 1

                    else:
                        # ALL RESULTS LINEAR VIEW with pagination
                        all_results = []
                        for file_results in file_groups.values():
                            all_results.extend(file_results)

                        # Pagination
                        results_per_page = 20
                        total_pages = (len(all_results) - 1) // results_per_page + 1

                        page_num = st.number_input(
                            f"Page (1-{total_pages}):",
                            min_value=1,
                            max_value=total_pages,
                            value=1,
                            key="page_num"
                        )

                        start_idx = (page_num - 1) * results_per_page
                        end_idx = min(start_idx + results_per_page, len(all_results))

                        st.write(f"Showing results {start_idx + 1}-{end_idx} of {len(all_results)}")

                        for i, result in enumerate(all_results[start_idx:end_idx]):
                            col_a, col_b = st.columns([3, 1])

                            with col_a:
                                dir_name = ""
                                if result.get('full_path'):
                                    dir_name = os.path.basename(os.path.dirname(result['full_path']))
                                    directory_info = f" 📂 {dir_name}"
                                else:
                                    directory_info = ""

                                st.markdown(f"**📄 {result['file']}**{directory_info} - Page {result['page_number']}")
                                st.markdown(f"{result['context']}", unsafe_allow_html=True)

                            with col_b:
                                if st.button(f"👁️ View", key=f"view_linear_{start_idx + i}", help="View this page"):
                                    st.session_state.selected_result = result

                            st.markdown("---")

                else:
                    st.warning(f"No files matching '{file_filter}'")

            with col2:
                st.header("📖 PDF Viewer")

                if st.session_state.selected_result:
                    result = st.session_state.selected_result

                    # Use the stored full path from search results
                    pdf_path = result.get('full_path')

                    if pdf_path and os.path.exists(pdf_path):
                        with st.spinner("Loading PDF from network share..."):
                            display_pdf_viewer(pdf_path, result['page_number'], keyword)
                    else:
                        # Fallback: try to find the file using optimized cache
                        pdf_filename = result['file']
                        pdf_path = get_pdf_path(pdf_filename)

                        if pdf_path:
                            with st.spinner("Loading PDF from network share..."):
                                display_pdf_viewer(pdf_path, result['page_number'], keyword)
                        else:
                            st.error(f"❌ Could not find PDF file: {pdf_filename}")
                            st.write("🔍 Searched in these directories:")
                            for directory in PDF_DIRECTORIES:
                                if os.path.exists(directory):
                                    st.write(f"  - {directory} ✅")
                                else:
                                    st.write(f"  - {directory} ❌")
                else:
                    st.info("👆 Click 'View' on any search result to display the PDF page here")

                    # Quick stats
                    if results:
                        st.markdown("### 📊 Quick Stats")
                        top_files = list(file_groups.items())[:5]
                        for filename, file_results in top_files:
                            st.metric(filename, f"{len(file_results)} matches")

        else:
            st.warning("❌ No results found. Try different keywords or check your spelling.")

    # Sidebar with statistics and controls
    with st.sidebar:
        st.header("🌐 Network Info")
        st.info(f"""
        **Network Base:** `{NETWORK_BASE}`
        **Fritz!Box IP:** `{FRITZBOX_IP}`
        **Platform:** {platform.system()}
        **Cache Location:** Local PC
        """)

        if st.button("🔄 Refresh Network Status"):
            check_network_connectivity()
            display_network_status()
            st.rerun()

        st.header("📊 Statistics")
        if pdf_cache:
            cached_files = len([k for k in pdf_cache.keys() if k != '_metadata'])
            st.metric("Cached PDFs", cached_files)

            total_pages = sum(len(pages) for k, pages in pdf_cache.items() if k != '_metadata')
            st.metric("Total Pages", total_pages)

            st.metric("Worker Threads", MAX_WORKERS)
            st.metric("Indexed Files", len(_file_path_cache))

        st.header("⚙️ Settings")

        # Version info
        st.info("""
        **Network Edition Features:**
        - ✅ Fritz!Box network share support
        - ✅ Automatic retry on network errors
        - ✅ Local cache for speed
        - ✅ Tailscale/VPN ready
        - ✅ All v13 features
        """)

        # Advanced settings
        if st.button("🔧 Advanced Settings"):
            st.info(f"""
            **Current Configuration:**
            - Platform: {platform.system()}
            - PDF Library: pdfplumber
            - Rendering: PyMuPDF (fitz)
            - Max Workers: {MAX_WORKERS}
            - Context Characters: {CONTEXT_CHARS}
            - Cache File: {CACHE_FILE}
            - Index DB: {TEXT_INDEX_DB}
            - Network Retry: {NETWORK_RETRY_COUNT} attempts
            - Network Timeout: {NETWORK_TIMEOUT}s
            """)

            st.write("**Configured Network Directories:**")
            for i, directory in enumerate(PDF_DIRECTORIES, 1):
                status = "✅" if os.path.exists(directory) else "❌"
                try:
                    pdf_count = len([f for f in os.listdir(directory) if f.lower().endswith('.pdf')]) if os.path.exists(
                        directory) else 0
                except Exception:
                    pdf_count = "?"
                st.write(f"{i}. {status} `{directory}` ({pdf_count} PDFs)")

        st.header("🛠️ Cache Management")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🗑️ Clear Cache", help="Clear all cached data"):
                if os.path.exists(CACHE_FILE):
                    os.remove(CACHE_FILE)
                if os.path.exists(TEXT_INDEX_DB):
                    os.remove(TEXT_INDEX_DB)
                st.success("Cache cleared!")
                st.rerun()

        with col2:
            if st.button("🔄 Rebuild Index", help="Rebuild search index"):
                if os.path.exists(TEXT_INDEX_DB):
                    os.remove(TEXT_INDEX_DB)
                if pdf_cache:
                    create_text_index_db(pdf_cache)
                st.success("Index rebuilt!")


if __name__ == "__main__":
    # Check if required libraries are installed
    try:
        import pdfplumber
        import fitz
    except ImportError as e:
        st.error(f"""
        Missing required library: {e}

        Please install the required packages:
        ```
        pip install pdfplumber PyMuPDF streamlit
        ```
        """)
        st.stop()

    main()
