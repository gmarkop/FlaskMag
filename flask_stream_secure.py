"""
Flask Stream Secure - Network Access with Authentication & Mobile Optimization
Key improvements over network edition:
- User authentication system with hashed passwords
- Mobile-responsive design
- Touch-friendly UI for tablets and phones
- Session management
- Configurable multi-user support
- All network edition features included
"""

import os
import pickle
import sqlite3
import multiprocessing
import base64
import platform
import time
import hashlib
import yaml
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
# AUTHENTICATION CONFIGURATION
# ============================================================================

# Authentication settings
ENABLE_AUTHENTICATION = True  # Set to False to disable login requirement
AUTH_CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".flaskmag_cache", "auth_config.yaml")

# Default configuration (will be created if auth_config.yaml doesn't exist)
DEFAULT_AUTH_CONFIG = {
    'credentials': {
        'usernames': {
            'admin': {
                'name': 'Administrator',
                'password': None,  # Will be set to hashed version of 'admin123'
            }
        }
    },
    'cookie': {
        'expiry_days': 30,
        'key': 'flaskmag_auth_key',  # Change this for production
        'name': 'flaskmag_auth_cookie'
    }
}

# ============================================================================
# NETWORK CONFIGURATION
# ============================================================================

# Fritz!Box Network Share Configuration
FRITZBOX_IP = "192.168.178.1"
FRITZBOX_SHARE_NAME = "USB-Storage"
FRITZBOX_USERNAME = ""
FRITZBOX_PASSWORD = ""

# Network path configuration
if platform.system() == 'Windows':
    NETWORK_BASE = f"\\\\{FRITZBOX_IP}\\{FRITZBOX_SHARE_NAME}"
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
    NETWORK_BASE = "/mnt/fritzbox"
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

# Local cache directory
LOCAL_CACHE_DIR = os.path.join(os.path.expanduser("~"), ".flaskmag_cache")
os.makedirs(LOCAL_CACHE_DIR, exist_ok=True)

CACHE_FILE = os.path.join(LOCAL_CACHE_DIR, "pdf_cache.pkl")
TEXT_INDEX_DB = os.path.join(LOCAL_CACHE_DIR, "text_index.db")

# Performance settings
CONTEXT_CHARS = 150
MAX_WORKERS = min(multiprocessing.cpu_count(), 12)

# Network settings
NETWORK_RETRY_COUNT = 3
NETWORK_RETRY_DELAY = 2
NETWORK_TIMEOUT = 30

# Global variables
_file_path_cache = {}
_network_status = {"connected": False, "last_check": None, "message": ""}


# ============================================================================
# MOBILE-RESPONSIVE CSS
# ============================================================================

def inject_mobile_css():
    """Inject mobile-responsive CSS for better mobile/tablet experience"""
    st.markdown("""
    <style>
    /* Mobile-first responsive design */

    /* Larger touch targets for mobile */
    .stButton > button {
        min-height: 44px !important;
        font-size: 16px !important;
        padding: 12px 24px !important;
        margin: 4px 0 !important;
        width: 100%;
    }

    /* Better input fields on mobile */
    .stTextInput > div > div > input {
        font-size: 16px !important;
        min-height: 44px !important;
    }

    /* Mobile-optimized search results */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }

        /* Stack columns on mobile */
        [data-testid="column"] {
            width: 100% !important;
            flex: 100% !important;
        }

        /* Smaller fonts for mobile */
        h1 {
            font-size: 1.5rem !important;
        }

        h2 {
            font-size: 1.3rem !important;
        }

        h3 {
            font-size: 1.1rem !important;
        }

        /* Better expander on mobile */
        .streamlit-expanderHeader {
            font-size: 14px !important;
        }
    }

    /* Tablet optimization */
    @media (min-width: 769px) and (max-width: 1024px) {
        .main .block-container {
            max-width: 95% !important;
        }
    }

    /* Better PDF viewer on mobile */
    .stImage {
        max-width: 100% !important;
    }

    /* Touch-friendly radio buttons */
    .stRadio > div {
        gap: 0.5rem;
    }

    .stRadio label {
        padding: 8px !important;
        min-height: 44px !important;
    }

    /* Better sidebar on mobile */
    @media (max-width: 768px) {
        [data-testid="stSidebar"] {
            min-width: 100vw !important;
        }
    }

    /* Login page styling */
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background: white;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }

    /* Welcome message */
    .welcome-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }

    /* Logout button styling */
    .logout-container {
        position: fixed;
        top: 10px;
        right: 10px;
        z-index: 999;
    }
    </style>
    """, unsafe_allow_html=True)


# ============================================================================
# AUTHENTICATION FUNCTIONS
# ============================================================================

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def create_default_auth_config():
    """Create default authentication configuration file"""
    config = DEFAULT_AUTH_CONFIG.copy()
    # Hash the default password
    config['credentials']['usernames']['admin']['password'] = hash_password('admin123')

    os.makedirs(os.path.dirname(AUTH_CONFIG_FILE), exist_ok=True)
    with open(AUTH_CONFIG_FILE, 'w') as f:
        yaml.dump(config, f)

    return config


def load_auth_config():
    """Load authentication configuration"""
    if not os.path.exists(AUTH_CONFIG_FILE):
        return create_default_auth_config()

    with open(AUTH_CONFIG_FILE, 'r') as f:
        return yaml.safe_load(f)


def verify_credentials(username, password):
    """Verify username and password"""
    config = load_auth_config()

    if username in config['credentials']['usernames']:
        stored_hash = config['credentials']['usernames'][username]['password']
        return stored_hash == hash_password(password)

    return False


def get_user_info(username):
    """Get user information"""
    config = load_auth_config()

    if username in config['credentials']['usernames']:
        return config['credentials']['usernames'][username]

    return None


def show_login_page():
    """Display login page with mobile-optimized design"""
    inject_mobile_css()

    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("<div class='login-container'>", unsafe_allow_html=True)

        # Logo if available (optional)
        if os.path.exists(LOGO_PATH):
            try:
                st.image(LOGO_PATH, width=200)
            except:
                pass

        st.title("🔐 FlaskMag Login")
        st.markdown("**Secure access to your PDF collection**")
        st.markdown("---")

        # Login form
        with st.form("login_form"):
            username = st.text_input("👤 Username", key="login_username")
            password = st.text_input("🔑 Password", type="password", key="login_password")

            col_a, col_b = st.columns(2)
            with col_a:
                submit = st.form_submit_button("🚀 Login", use_container_width=True)

            if submit:
                if verify_credentials(username, password):
                    user_info = get_user_info(username)
                    st.session_state['authenticated'] = True
                    st.session_state['username'] = username
                    st.session_state['name'] = user_info['name']
                    st.success(f"✅ Welcome back, {user_info['name']}!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")

        # Help text
        st.markdown("---")
        st.info("""
        **Default credentials:**
        - Username: `admin`
        - Password: `admin123`

        ⚠️ **Important:** Change default password after first login!
        Edit `~/.flaskmag_cache/auth_config.yaml`
        """)

        st.markdown("</div>", unsafe_allow_html=True)


def show_logout_button():
    """Display logout button"""
    # Create logout button in top-right
    st.markdown(f"""
    <div style="position: fixed; top: 60px; right: 20px; z-index: 999;">
        <span style="background: white; padding: 5px 10px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            👤 {st.session_state.get('name', 'User')}
        </span>
    </div>
    """, unsafe_allow_html=True)

    # Logout button in sidebar
    with st.sidebar:
        st.markdown("---")
        if st.button("🚪 Logout", key="logout_button", use_container_width=True):
            st.session_state['authenticated'] = False
            st.session_state.pop('username', None)
            st.session_state.pop('name', None)
            st.rerun()


def check_authentication():
    """Check if user is authenticated"""
    if not ENABLE_AUTHENTICATION:
        return True

    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False

    return st.session_state['authenticated']


# ============================================================================
# NETWORK HELPER FUNCTIONS (Same as network edition)
# ============================================================================

def check_network_connectivity():
    """Check if network share is accessible"""
    try:
        if os.path.exists(NETWORK_BASE):
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
    """Display network connection status"""
    if _network_status["last_check"]:
        if _network_status["connected"]:
            st.success(_network_status["message"])
        else:
            st.error(_network_status["message"])
            with st.expander("🔧 Network Troubleshooting"):
                st.markdown(f"""
                **Connection Failed to:** `{NETWORK_BASE}`

                **Quick Checks:**
                1. Verify Fritz!Box is powered on
                2. Check USB drive is connected
                3. Test network access: Open File Explorer → `{NETWORK_BASE}`
                4. Ensure you're connected to home network or VPN
                """)


# ============================================================================
# FILE PATH CACHE & PDF FUNCTIONS (Same as network edition)
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
            def list_directory():
                return os.listdir(pdf_dir)

            filenames = retry_network_operation(list_directory)
            for filename in filenames:
                if filename.lower().endswith('.pdf'):
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


@st.cache_data
def load_cached_data(cache_file=CACHE_FILE):
    """Load cached PDF data"""
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "rb") as f:
                return pickle.load(f)
        except (pickle.PickleError, EOFError):
            st.warning("Cache file corrupted, rebuilding...")
            return {}
    return {}


def save_cache(data, cache_file=CACHE_FILE):
    """Save cached data"""
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


def extract_pdf_text_pdfplumber(pdf_path):
    """Extract text from PDF using pdfplumber with network retry"""
    def do_extraction():
        pages_text = []
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                try:
                    text = page.extract_text()
                    if text:
                        text = re.sub(r'\s+', ' ', text.strip())
                        pages_text.append(text)
                    else:
                        pages_text.append("")
                except Exception as e:
                    st.warning(f"Error extracting page {page_num + 1}: {e}")
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
    """Process PDFs in batches with optimized threading"""
    if not pdf_files:
        return pdf_cache

    progress_bar = st.progress(0)
    status_text = st.empty()
    processed_count = 0
    total_files = len(pdf_files)

    if '_metadata' not in pdf_cache:
        pdf_cache['_metadata'] = {}

    st.info(f"Using {MAX_WORKERS} worker threads")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_file = {
            executor.submit(extract_pdf_text_pdfplumber, pdf_file_path): pdf_file_path
            for pdf_file_path in pdf_files
        }

        for future in as_completed(future_to_file):
            pdf_file_path = future_to_file[future]
            file_name = os.path.basename(pdf_file_path)

            try:
                text_pages = future.result()
                pdf_cache[file_name] = text_pages
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
# SQLITE & SEARCH FUNCTIONS (Same as network edition - keeping for brevity)
# ============================================================================

def create_text_index_db(pdf_cache):
    """Create SQLite-based text index"""
    with closing(sqlite3.connect(TEXT_INDEX_DB)) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS text_index (
                filename TEXT PRIMARY KEY,
                full_text TEXT,
                page_count INTEGER
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_fulltext ON text_index(full_text)')
        conn.execute('DELETE FROM text_index')

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
    """Fast SQLite-based search"""
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


def search_with_context(keyword, text, original_text):
    """Extract context around keyword matches"""
    keyword_lower = keyword.lower()
    text_lower = text.lower()
    results = []
    pattern = re.compile(re.escape(keyword_lower))
    matches = [m.start() for m in pattern.finditer(text_lower)]

    for pos in matches:
        context_start = max(0, pos - CONTEXT_CHARS)
        context_end = min(len(text), pos + len(keyword) + CONTEXT_CHARS)

        while context_start > 0 and original_text[context_start] not in ' \n\t':
            context_start -= 1
        while context_end < len(original_text) and original_text[context_end] not in ' \n\t':
            context_end += 1

        context = original_text[context_start:context_end].strip()
        highlighted_context = re.sub(
            f"({re.escape(keyword)})",
            r"<span style='background-color: yellow; color: black; font-weight: bold; padding: 2px;'>\1</span>",
            context,
            flags=re.IGNORECASE
        )
        results.append(highlighted_context)

    return results


def search_pages_parallel(pdf_file, pages, keyword):
    """Search pages in parallel"""
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
            "full_path": get_pdf_path(pdf_file)
        } for context in contexts]

    page_results = []
    if len(pages) > 20:
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = executor.map(search_single_page, enumerate(pages))
            for result_list in futures:
                page_results.extend(result_list)
    else:
        for i, page_text in enumerate(pages):
            page_results.extend(search_single_page((i, page_text)))

    return page_results


def smart_search(keyword, pdf_cache):
    """Optimized search function"""
    if not keyword.strip():
        return []

    keyword = keyword.strip()
    results = []
    candidate_files = search_text_index(keyword)
    if candidate_files is None:
        candidate_files = [k for k in pdf_cache.keys() if k != '_metadata']

    for pdf_file in candidate_files:
        if pdf_file not in pdf_cache:
            continue
        pages = pdf_cache[pdf_file]
        page_results = search_pages_parallel(pdf_file, pages, keyword)
        results.extend(page_results)

    return results


def group_results_by_file(results):
    """Group search results by PDF file"""
    file_groups = defaultdict(list)
    for result in results:
        file_groups[result['file']].append(result)
    sorted_files = sorted(file_groups.items(), key=lambda x: len(x[1]), reverse=True)
    return dict(sorted_files)


@st.cache_data(ttl=3600)
def render_pdf_page(pdf_path, page_number, zoom=1.5):
    """Render PDF page with caching"""
    def do_render():
        doc = fitz.open(pdf_path)
        if page_number > len(doc):
            doc.close()
            return None
        page = doc[page_number - 1]
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        doc.close()
        return img_data

    try:
        return retry_network_operation(do_render)
    except Exception as e:
        st.error(f"Error rendering PDF: {e}")
        return None


def display_pdf_viewer(pdf_path, page_number, keyword=None):
    """Display PDF page viewer"""
    if not pdf_path or not os.path.exists(pdf_path):
        st.error(f"❌ PDF file not found: {pdf_path}")
        return

    try:
        img_data = render_pdf_page(pdf_path, page_number)
        if img_data:
            img_b64 = base64.b64encode(img_data).decode()
            directory_name = os.path.basename(os.path.dirname(pdf_path))

            st.markdown(f"""
            <div style="text-align: center; border: 2px solid #ddd; border-radius: 10px; padding: 10px; background: white;">
                <h4>📄 {os.path.basename(pdf_path)} - Page {page_number}</h4>
                <p style="color: #666; font-size: 12px;">📂 From: {directory_name}</p>
                <img src="data:image/png;base64,{img_b64}" style="max-width: 100%; height: auto; border: 1px solid #ccc;">
            </div>
            """, unsafe_allow_html=True)

            try:
                def read_pdf():
                    with open(pdf_path, "rb") as f:
                        return f.read()

                pdf_data = retry_network_operation(read_pdf)
                btn_col1, btn_col2 = st.columns(2)

                with btn_col1:
                    st.download_button(
                        label="📥 Download PDF",
                        data=pdf_data,
                        file_name=os.path.basename(pdf_path),
                        mime="application/pdf",
                        key=f"download_{pdf_path}_{page_number}",
                        use_container_width=True
                    )

                with btn_col2:
                    pdf_b64 = base64.b64encode(pdf_data).decode()
                    button_id = f"open_pdf_{hash(pdf_path)}_{page_number}"

                    open_pdf_html = f"""
                    <button id="{button_id}"
                            style="display: inline-block;
                                   padding: 0.5rem 1rem;
                                   background-color: #ff4b4b;
                                   color: white;
                                   border-radius: 0.25rem;
                                   font-weight: 400;
                                   text-align: center;
                                   width: 100%;
                                   min-height: 44px;
                                   border: none;
                                   font-size: 1rem;
                                   cursor: pointer;">
                        📖 Open PDF
                    </button>
                    <script>
                    document.getElementById('{button_id}').addEventListener('click', function() {{
                        const byteCharacters = atob('{pdf_b64}');
                        const byteNumbers = new Array(byteCharacters.length);
                        for (let i = 0; i < byteCharacters.length; i++) {{
                            byteNumbers[i] = byteCharacters.charCodeAt(i);
                        }}
                        const byteArray = new Uint8Array(byteNumbers);
                        const blob = new Blob([byteArray], {{type: 'application/pdf'}});
                        const url = URL.createObjectURL(blob);
                        window.open(url, '_blank');
                        setTimeout(function() {{
                            URL.revokeObjectURL(url);
                        }}, 60000);
                    }});
                    </script>
                    """
                    components.html(open_pdf_html, height=50)
            except Exception as e:
                st.error(f"Error reading PDF: {e}")
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
        page_title="FlaskMag Secure - PDF Search",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Inject mobile-responsive CSS
    inject_mobile_css()

    # Check authentication
    if not check_authentication():
        show_login_page()
        return

    # Show logout button
    show_logout_button()

    # Welcome message
    st.markdown(f"""
    <div class='welcome-message'>
        <h2>Welcome, {st.session_state.get('name', 'User')}! 👋</h2>
        <p>Search your PDF magazine collection securely from anywhere</p>
    </div>
    """, unsafe_allow_html=True)

    # Logo
    if os.path.exists(LOGO_PATH):
        try:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(LOGO_PATH, width=300)
        except:
            pass

    st.title("🔍 FlaskMag Secure - PDF Search")
    st.write("🔐 Authenticated access | 📱 Mobile optimized | 🌐 Network enabled")

    # Network check
    with st.spinner("Checking network..."):
        check_network_connectivity()
    display_network_status()

    if not _network_status["connected"]:
        st.stop()

    # Build cache
    if not _file_path_cache:
        with st.spinner("Building file index..."):
            _file_path_cache = build_file_path_cache()
            if _file_path_cache:
                st.success(f"✅ Indexed {len(_file_path_cache)} PDF files")

    # Directory status
    valid_directories = [d for d in PDF_DIRECTORIES if os.path.exists(d)]
    invalid_directories = [d for d in PDF_DIRECTORIES if not os.path.exists(d)]

    if not valid_directories:
        st.error("❌ No PDF directories found")
        st.stop()

    with st.expander(f"📚 {len(valid_directories)} directories available"):
        for d in valid_directories:
            try:
                pdf_count = len([f for f in os.listdir(d) if f.lower().endswith('.pdf')])
                st.success(f"✅ {os.path.basename(d)}: {pdf_count} PDFs")
            except:
                pass

    # Get files
    with st.spinner("Scanning..."):
        pdf_files = get_all_pdf_files()

    if not pdf_files:
        st.warning("No PDF files found")
        st.stop()

    st.success(f"📚 {len(pdf_files)} PDFs | 🚀 {MAX_WORKERS} threads | 🔐 Secure access")

    # Load cache
    with st.spinner("Loading cache..."):
        pdf_cache = load_cached_data()

    # Check updates
    files_to_process = check_for_updates(pdf_files, pdf_cache)
    new_files = [f for f in pdf_files if os.path.basename(f) not in pdf_cache]
    files_to_process.extend(new_files)
    files_to_process = list(set(files_to_process))

    # Process PDFs
    if files_to_process:
        st.warning(f"⚡ {len(files_to_process)} files need processing")
        if st.button("🚀 Process PDFs", type="primary", use_container_width=True):
            with st.spinner("Processing..."):
                pdf_cache = process_pdfs_batch(files_to_process, pdf_cache)
                save_cache(pdf_cache)
                with st.spinner("Building index..."):
                    create_text_index_db(pdf_cache)
                st.success("✅ Complete!")
                st.rerun()

    # Create index if needed
    if not os.path.exists(TEXT_INDEX_DB) and pdf_cache:
        with st.spinner("Creating search index..."):
            create_text_index_db(pdf_cache)
            st.success("✅ Index created!")

    # Search interface
    st.markdown("---")
    col1, col2 = st.columns([4, 1])

    with col1:
        keyword = st.text_input(
            "🔎 Search:",
            placeholder="Enter keyword...",
            key="search_input"
        )

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        search_button = st.button("🔍 Search", type="primary", use_container_width=True)

    # Search functionality
    if keyword and (search_button or keyword):
        with st.spinner(f"Searching for '{keyword}'..."):
            results = smart_search(keyword, pdf_cache)

        if results:
            st.success(f"✅ {len(results)} results in {len(set(r['file'] for r in results))} files")

            # Results columns
            col1, col2 = st.columns([1, 1])

            with col1:
                st.header("📋 Results")
                file_groups = group_results_by_file(results)

                file_filter = st.text_input(
                    "🔍 Filter files:",
                    placeholder="Type filename...",
                    key="file_filter"
                )

                if file_filter:
                    file_groups = {
                        filename: file_results
                        for filename, file_results in file_groups.items()
                        if file_filter.lower() in filename.lower()
                    }

                if len(file_groups) > 0:
                    st.info(f"📊 {len(file_groups)} files")

                    display_mode = st.radio(
                        "View:",
                        ["Grouped", "All"],
                        horizontal=True,
                        key="display_mode"
                    )

                    if 'selected_result' not in st.session_state:
                        st.session_state.selected_result = None

                    if display_mode == "Grouped":
                        result_counter = 0
                        for filename, file_results in file_groups.items():
                            dir_name = ""
                            if file_results[0].get('full_path'):
                                dir_name = os.path.basename(os.path.dirname(file_results[0]['full_path']))

                            with st.expander(
                                f"📄 {filename} ({len(file_results)}) 📂 {dir_name}",
                                expanded=len(file_groups) <= 3
                            ):
                                for result in file_results:
                                    col_a, col_b = st.columns([3, 1])
                                    with col_a:
                                        st.markdown(f"**Page {result['page_number']}**")
                                        st.markdown(f"{result['context']}", unsafe_allow_html=True)
                                    with col_b:
                                        if st.button("👁️ View", key=f"view_{result_counter}", use_container_width=True):
                                            st.session_state.selected_result = result
                                    st.markdown("---")
                                    result_counter += 1
                    else:
                        all_results = []
                        for file_results in file_groups.values():
                            all_results.extend(file_results)

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

                        st.write(f"Showing {start_idx + 1}-{end_idx} of {len(all_results)}")

                        for i, result in enumerate(all_results[start_idx:end_idx]):
                            col_a, col_b = st.columns([3, 1])
                            with col_a:
                                st.markdown(f"**📄 {result['file']}** - Page {result['page_number']}")
                                st.markdown(f"{result['context']}", unsafe_allow_html=True)
                            with col_b:
                                if st.button("👁️ View", key=f"view_linear_{start_idx + i}", use_container_width=True):
                                    st.session_state.selected_result = result
                            st.markdown("---")
                else:
                    st.warning(f"No files matching '{file_filter}'")

            with col2:
                st.header("📖 Viewer")

                if st.session_state.selected_result:
                    result = st.session_state.selected_result
                    pdf_path = result.get('full_path') or get_pdf_path(result['file'])

                    if pdf_path:
                        with st.spinner("Loading..."):
                            display_pdf_viewer(pdf_path, result['page_number'], keyword)
                    else:
                        st.error(f"❌ File not found: {result['file']}")
                else:
                    st.info("👆 Click 'View' to display PDF")

                    if results:
                        st.markdown("### 📊 Top Files")
                        top_files = list(file_groups.items())[:5]
                        for filename, file_results in top_files:
                            st.metric(filename[:30], f"{len(file_results)} matches")
        else:
            st.warning("❌ No results found")

    # Sidebar
    with st.sidebar:
        st.header("🌐 Network")
        st.info(f"""
        **Base:** `{os.path.basename(NETWORK_BASE)}`
        **Platform:** {platform.system()}
        **User:** {st.session_state.get('name', 'Unknown')}
        """)

        if st.button("🔄 Refresh", use_container_width=True):
            check_network_connectivity()
            st.rerun()

        st.header("📊 Stats")
        if pdf_cache:
            cached_files = len([k for k in pdf_cache.keys() if k != '_metadata'])
            st.metric("Cached", cached_files)
            total_pages = sum(len(pages) for k, pages in pdf_cache.items() if k != '_metadata')
            st.metric("Pages", total_pages)
            st.metric("Threads", MAX_WORKERS)

        st.header("⚙️ Settings")
        st.info("""
        **Secure Edition:**
        - ✅ Authentication
        - ✅ Mobile optimized
        - ✅ Network support
        - ✅ All v13 features
        """)

        if st.button("🔧 Advanced", use_container_width=True):
            st.info(f"""
            **Config:**
            - Auth: {ENABLE_AUTHENTICATION}
            - Workers: {MAX_WORKERS}
            - Context: {CONTEXT_CHARS} chars
            - Cache: {LOCAL_CACHE_DIR}
            """)

        st.header("🛠️ Cache")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear", help="Clear cache", use_container_width=True):
                if os.path.exists(CACHE_FILE):
                    os.remove(CACHE_FILE)
                if os.path.exists(TEXT_INDEX_DB):
                    os.remove(TEXT_INDEX_DB)
                st.success("Cleared!")
                st.rerun()

        with col2:
            if st.button("🔄 Rebuild", help="Rebuild index", use_container_width=True):
                if os.path.exists(TEXT_INDEX_DB):
                    os.remove(TEXT_INDEX_DB)
                if pdf_cache:
                    create_text_index_db(pdf_cache)
                st.success("Rebuilt!")


if __name__ == "__main__":
    try:
        import pdfplumber
        import fitz
        import yaml
    except ImportError as e:
        st.error(f"""
        Missing library: {e}

        Install required packages:
        ```
        pip install pdfplumber PyMuPDF streamlit pyyaml
        ```
        """)
        st.stop()

    main()
