# FlaskMag Ad Filtering Guide

How to filter out advertisements and focus on real content (travel reports, test rides, product reviews).

---

## The Advertisement Problem

When searching magazine PDFs, results often include:
- ❌ Product advertisements
- ❌ Classified ads
- ❌ Promotional content
- ❌ Sponsor pages

**You want only:**
- ✅ Travel and touring reports
- ✅ Motorcycle test rides
- ✅ Product reviews
- ✅ Technical articles

---

## Solution: Multi-Layer Ad Filtering

### Method 1: Ad Keyword Blacklist (Easiest)

Add these filter keywords to the code to exclude advertisement-related content:

**German motorcycle magazine ad keywords:**
```python
AD_KEYWORDS = [
    # German ad indicators
    'anzeige', 'werbung', 'inserat', 'promotion', 'sponsored',
    'advertorial', 'werbebeitrag',

    # Pricing indicators (ads often have prices)
    '€', 'eur', 'preis ab', 'ab €', 'uvp', 'statt €',

    # Sales language
    'jetzt kaufen', 'bestellen', 'angebot', 'rabatt',
    'sonderpreis', 'aktion', 'prozent',

    # Contact/dealer info (common in ads)
    'händler', 'vertrieb', 'info@', 'www.', 'tel:', 'fax:',

    # Classified ads
    'zu verkaufen', 'verkaufe', 'biete', 'suche',

    # Product catalog language
    'lieferbar', 'verfügbar', 'bestellnummer', 'artikel-nr',
]
```

### Method 2: Content Length Filter

Advertisements are typically shorter than articles:
- **Ads:** 50-300 words
- **Articles:** 500+ words

Filter by minimum word count.

### Method 3: Page Range Exclusion

Ads are often concentrated in specific areas:
- **First 2-3 pages** (cover ads, table of contents ads)
- **Last 2-3 pages** (back cover ads, classifieds)
- **Specific ad sections** (if you know the page numbers)

### Method 4: File/Magazine Specific Rules

Different magazines have different patterns:
- **Tourenfahrer:** Ads on pages 2-5, 90-95
- **Motorrad:** Classifieds section pages 80-90
- etc.

---

## Implementation Options

### Option A: Simple Filter (Add to existing code)

Add this function before the `smart_search` function:

```python
# ============================================================================
# AD FILTERING
# ============================================================================

# German motorcycle magazine ad keywords
AD_KEYWORDS = [
    'anzeige', 'werbung', 'inserat', 'promotion', 'sponsored',
    'advertorial', 'preis ab', 'ab €', 'uvp', 'rabatt',
    'jetzt kaufen', 'bestellen', 'sonderpreis', 'aktion',
    'händler', 'vertrieb', 'zu verkaufen', 'verkaufe',
]

def is_likely_advertisement(text, min_words=100):
    """
    Detect if text is likely an advertisement

    Args:
        text: Text to analyze
        min_words: Minimum word count for non-ads (default 100)

    Returns:
        True if likely an ad, False otherwise
    """
    text_lower = text.lower()

    # Check 1: Too short (ads are usually brief)
    word_count = len(text.split())
    if word_count < min_words:
        return True

    # Check 2: Contains ad keywords
    ad_keyword_count = sum(1 for keyword in AD_KEYWORDS if keyword in text_lower)

    # If 2+ ad keywords found, likely an ad
    if ad_keyword_count >= 2:
        return True

    # Check 3: High density of prices (multiple € symbols)
    euro_count = text_lower.count('€') + text_lower.count('eur')
    if euro_count >= 3:
        return True

    # Check 4: Contains contact info patterns
    contact_patterns = ['tel:', 'fax:', 'info@', 'www.', 'http']
    contact_count = sum(1 for pattern in contact_patterns if pattern in text_lower)
    if contact_count >= 2:
        return True

    return False


def filter_advertisement_results(results, enable_filter=True, min_words=100):
    """
    Filter out advertisement pages from search results

    Args:
        results: List of search results
        enable_filter: Whether to apply filter (default True)
        min_words: Minimum words for non-ad content

    Returns:
        Filtered results list
    """
    if not enable_filter:
        return results

    filtered = []
    ads_removed = 0

    for result in results:
        full_text = result.get('full_text', '')

        if not is_likely_advertisement(full_text, min_words):
            filtered.append(result)
        else:
            ads_removed += 1

    # Store stats for display
    if ads_removed > 0:
        st.info(f"🚫 Filtered out {ads_removed} advertisement results")

    return filtered
```

Then modify the `smart_search` function to use the filter:

```python
def smart_search(keyword, pdf_cache, enable_ad_filter=True, min_words=100):
    """Optimized search function with ad filtering"""
    if not keyword.strip():
        return []

    keyword = keyword.strip()
    results = []

    # Get candidate files from SQLite index
    candidate_files = search_text_index(keyword)
    if candidate_files is None:
        candidate_files = [k for k in pdf_cache.keys() if k != '_metadata']

    # Search each PDF
    for pdf_file in candidate_files:
        if pdf_file not in pdf_cache:
            continue

        pages = pdf_cache[pdf_file]
        page_results = search_pages_parallel(pdf_file, pages, keyword)
        results.extend(page_results)

    # Apply ad filter
    if enable_ad_filter:
        results = filter_advertisement_results(results, True, min_words)

    return results
```

### Option B: UI Controls (Add to sidebar)

Add filter controls in the sidebar for user customization:

```python
# In the sidebar section of main()
with st.sidebar:
    st.header("🔍 Search Filters")

    # Ad filter toggle
    enable_ad_filter = st.checkbox(
        "Filter out advertisements",
        value=True,
        help="Exclude pages that appear to be advertisements"
    )

    if enable_ad_filter:
        min_words = st.slider(
            "Minimum words (articles are longer)",
            min_value=50,
            max_value=500,
            value=100,
            step=50,
            help="Pages with fewer words are filtered as ads"
        )
    else:
        min_words = 0

    # Custom keyword exclusions
    with st.expander("⚙️ Advanced Filters"):
        custom_exclude = st.text_area(
            "Exclude pages containing (one per line):",
            value="",
            help="Additional keywords to filter out"
        )

        exclude_first_pages = st.number_input(
            "Skip first N pages",
            min_value=0,
            max_value=10,
            value=0,
            help="Often contain ads and table of contents"
        )

        exclude_last_pages = st.number_input(
            "Skip last N pages",
            min_value=0,
            max_value=10,
            value=0,
            help="Often contain classified ads"
        )
```

Then use these settings in search:

```python
# When calling smart_search
results = smart_search(
    keyword,
    pdf_cache,
    enable_ad_filter=enable_ad_filter,
    min_words=min_words
)

# Apply additional filters
if exclude_first_pages > 0 or exclude_last_pages > 0:
    results = filter_page_ranges(results, exclude_first_pages, exclude_last_pages)

if custom_exclude:
    results = filter_custom_keywords(results, custom_exclude.split('\n'))
```

---

## Recommended Configuration

### For German Motorcycle Magazines

**Best filter settings:**
```python
enable_ad_filter = True
min_words = 150  # Articles are usually 150+ words
exclude_first_pages = 2  # Skip cover ads
exclude_last_pages = 3  # Skip classifieds
```

**Additional keywords to exclude:**
```
anzeige
werbung
händlerverzeichnis
impressum
vorschau
```

---

## Testing Your Filter

### Test 1: Search Without Filter
```python
enable_ad_filter = False
results = smart_search("BMW", pdf_cache, False, 0)
# Shows all results including ads
```

### Test 2: Search With Filter
```python
enable_ad_filter = True
results = smart_search("BMW", pdf_cache, True, 150)
# Shows only articles about BMW
```

### Test 3: Check What Was Filtered
Add logging to see what's being filtered:

```python
def is_likely_advertisement(text, min_words=100, verbose=False):
    # ... existing checks ...

    if is_ad and verbose:
        st.write(f"🚫 Filtered: {text[:100]}... (Reason: {reason})")

    return is_ad
```

---

## Fine-Tuning for Your Collection

### Step 1: Identify False Positives

If legitimate articles are being filtered:
- **Reduce min_words** (try 100 instead of 150)
- **Remove overly broad keywords** from AD_KEYWORDS
- **Check specific magazine patterns**

### Step 2: Identify False Negatives

If ads are still showing:
- **Increase min_words** (try 200)
- **Add magazine-specific ad keywords**
- **Use page range exclusions**

### Step 3: Magazine-Specific Tuning

```python
# Example: Different settings per magazine
MAGAZINE_FILTERS = {
    'Tourenfahrer': {
        'min_words': 150,
        'exclude_first': 2,
        'exclude_last': 3,
        'ad_keywords': ['anzeige', 'werbung']
    },
    'Motorrad': {
        'min_words': 200,
        'exclude_first': 3,
        'exclude_last': 5,
        'ad_keywords': ['promotion', 'sponsored']
    },
}

def get_filter_settings(pdf_filename):
    for mag_name, settings in MAGAZINE_FILTERS.items():
        if mag_name.lower() in pdf_filename.lower():
            return settings
    return DEFAULT_SETTINGS
```

---

## Advanced: Machine Learning Classifier (Future)

For even better filtering:

1. **Train a classifier** on labeled ad vs. article pages
2. **Use text features:**
   - Word count
   - Sentence length
   - Keyword density
   - Contact info presence
   - Price mentions

3. **sklearn example:**
```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

# Train on labeled examples
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(texts)
classifier = MultinomialNB()
classifier.fit(X, labels)  # labels: 0=article, 1=ad

# Predict
is_ad = classifier.predict(vectorizer.transform([new_text]))[0]
```

---

## Quick Reference

### Enable Basic Ad Filtering
Add to `smart_search()` call:
```python
results = smart_search(keyword, pdf_cache, enable_ad_filter=True, min_words=150)
```

### Common Ad Keywords (German)
```
anzeige, werbung, inserat, promotion, sponsored,
preis ab, rabatt, jetzt kaufen, händler, zu verkaufen
```

### Recommended Settings
- **Minimum words:** 150
- **Skip first pages:** 2
- **Skip last pages:** 3

### Test Effectiveness
```python
total_results = len(results_unfiltered)
filtered_results = len(results_filtered)
ads_removed = total_results - filtered_results
effectiveness = (ads_removed / total_results) * 100
print(f"Filtered {ads_removed} ads ({effectiveness:.1f}%)")
```

---

## Summary

**For best results filtering German motorcycle magazine ads:**

1. ✅ Enable ad keyword filtering (default keywords work well)
2. ✅ Set minimum words to 150
3. ✅ Skip first 2 pages (cover ads)
4. ✅ Skip last 2-3 pages (classifieds)
5. ✅ Fine-tune based on your specific magazines

**Expected improvement:**
- Before: 100 results (50% ads, 50% articles)
- After: 55 results (90% articles, 10% false positives)

This dramatically improves search quality by focusing on actual content!

---

**Want me to create a ready-to-use version with these filters built-in?** I can add:
- Pre-configured German motorcycle magazine ad keywords
- UI toggle for easy enable/disable
- Statistics showing how many ads were filtered
- Fine-tuning controls in sidebar

Just let me know!
