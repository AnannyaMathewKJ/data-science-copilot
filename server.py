import http.server
import socketserver
import urllib.parse
import urllib.request
import json
import os
import subprocess
import csv
import collections
import traceback
import sys
import math

CUSTOM_GEMINI_KEY = ""
PORT = 3000
DATA_DIR = os.path.join(os.getcwd(), "data")

# Create data directory if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)

# -------------------------------------------------------------
# PRESETS DEFINITIONS
# -------------------------------------------------------------
PRESETS = [
    {
        "id": "sales_dashboard",
        "title": "Sales Dashboard",
        "description": "Upload a monthly sales CSV — get an instant revenue-by-region bar chart.",
        "datasetName": "sales_data.csv",
        "datasetType": "csv",
        "query": "Show me the total revenue grouped by region in a bar chart.",
        "fileContent": """date,product,region,revenue,units_sold
2025-01-05,Laptop,North,12000,10
2025-01-08,Phone,South,8000,16
2025-01-12,Tablet,East,4500,9
2025-01-15,Laptop,West,15000,12
2025-01-18,Phone,North,9000,18
2025-01-22,Tablet,South,3500,7
2025-01-25,Laptop,East,11000,9
2025-01-28,Phone,West,10500,21
2025-02-02,Laptop,South,13500,11
2025-02-05,Phone,East,7500,15
2025-02-09,Tablet,West,5000,10
2025-02-12,Laptop,North,14000,11
2025-02-16,Phone,South,8500,17
2025-02-20,Tablet,East,4000,8"""
    },
    {
        "id": "data_quality_audit",
        "title": "Data Quality Audit",
        "description": "Detect missing values, outliers, duplicates, and invalid records; produce a clean data report.",
        "datasetName": "user_profiles_dirty.csv",
        "datasetType": "csv",
        "query": "Perform a comprehensive data quality audit and output a summary of missing values, anomalies, and row counts.",
        "fileContent": """user_id,name,email,signup_date,age,country
101,Alice Smith,alice@example.com,2025-03-01,28,USA
102,Bob Jones,,2025-03-02,34,Canada
103,Charlie Brown,charlie@example,2025-03-03,-5,UK
104,David Miller,david@example.com,2025-03-04,45,USA
101,Alice Smith,alice@example.com,2025-03-01,28,USA
105,Eve Davis,eve@example.com,2025-03-05,,Germany
106,Frank Wilson,frank@com,2025-03-06,120,France
107,Grace Taylor,grace@example.com,2025-03-07,22,USA
108,Henry Clark,henry@example.com,2025-03-08,31,Canada
109,Ivy Thomas,,2025-03-09,-1,Australia
107,Grace Taylor,grace@example.com,2025-03-07,22,USA"""
    },
    {
        "id": "trend_analysis",
        "title": "Trend Analysis",
        "description": "Ask 'Is my traffic growing?' over a time-series CSV and receive a trend line with key observations.",
        "datasetName": "web_traffic.csv",
        "datasetType": "csv",
        "query": "Is my page views and unique visitors traffic growing? Produce a daily trend chart with key observations.",
        "fileContent": """date,page_views,unique_visitors,bounce_rate
2025-05-01,1200,800,42.5
2025-05-02,1250,830,41.2
2025-05-03,1100,750,45.0
2025-05-04,1300,870,39.8
2025-05-05,1450,950,38.5
2025-05-06,1500,1020,37.2
2025-05-07,1400,920,39.0
2025-05-08,1650,1100,36.5
2025-05-09,1700,1150,35.0
2025-05-10,1550,1050,37.8
2025-05-11,1800,1220,34.2
2025-05-12,1950,1300,33.0
2025-05-13,2100,1400,31.5
2025-05-14,2050,1380,32.4"""
    },
    {
        "id": "cohort_analysis",
        "title": "Cohort Analysis",
        "description": "Auto-segment customers by spending levels (VIP vs Medium vs Budget) and average orders.",
        "datasetName": "customer_segments.json",
        "datasetType": "json",
        "query": "Segment our customers into High (spend > 1000), Medium (spend 100-1000), and Low (spend < 100) spend cohorts. Tell me how many customers and total spend are in each cohort.",
        "fileContent": """[
  {"customer_id": 1, "name": "Alice", "total_spend": 1250.00, "order_count": 15, "last_active": "2025-06-01"},
  {"customer_id": 2, "name": "Bob", "total_spend": 150.50, "order_count": 2, "last_active": "2025-05-15"},
  {"customer_id": 3, "name": "Charlie", "total_spend": 3200.00, "order_count": 42, "last_active": "2025-06-05"},
  {"customer_id": 4, "name": "David", "total_spend": 450.00, "order_count": 5, "last_active": "2025-05-28"},
  {"customer_id": 5, "name": "Eve", "total_spend": 89.99, "order_count": 1, "last_active": "2024-04-10"},
  {"customer_id": 6, "name": "Frank", "total_spend": 1420.00, "order_count": 18, "last_active": "2025-06-03"},
  {"customer_id": 7, "name": "Grace", "total_spend": 600.00, "order_count": 8, "last_active": "2025-05-20"},
  {"customer_id": 8, "name": "Henry", "total_spend": 2100.00, "order_count": 25, "last_active": "2025-06-04"},
  {"customer_id": 9, "name": "Ivy", "total_spend": 45.00, "order_count": 1, "last_active": "2025-03-15"},
  {"customer_id": 10, "name": "Jack", "total_spend": 1150.00, "order_count": 14, "last_active": "2025-06-02"}
]"""
    },
    {
        "id": "adhoc_queries",
        "title": "Ad-hoc Queries",
        "description": "Query operational inventory data directly without writing SQL or Python, finding items with low stock or high cost.",
        "datasetName": "inventory_levels.json",
        "datasetType": "json",
        "query": "Show me which inventory categories have the highest total financial value in stock (stock multiplied by price). Group them and summarize.",
        "fileContent": """[
  {"item_id": "I001", "name": "Wireless Mouse", "category": "Electronics", "stock": 120, "price": 25.00, "warehouse": "A"},
  {"item_id": "I002", "name": "Gaming Keyboard", "category": "Electronics", "stock": 45, "price": 75.00, "warehouse": "B"},
  {"item_id": "I003", "name": "Ergonomic Chair", "category": "Furniture", "stock": 15, "price": 199.99, "warehouse": "A"},
  {"item_id": "I004", "name": "Desk Lamp", "category": "Furniture", "stock": 80, "price": 35.50, "warehouse": "C"},
  {"item_id": "I005", "name": "Water Bottle", "category": "Accessories", "stock": 350, "price": 12.00, "warehouse": "B"},
  {"item_id": "I006", "name": "USB-C Hub", "category": "Electronics", "stock": 200, "price": 40.00, "warehouse": "A"},
  {"item_id": "I007", "name": "Notebook (5 pack)", "category": "Office Supplies", "stock": 150, "price": 8.99, "warehouse": "C"},
  {"item_id": "I008", "name": "Gel Pens (12 pack)", "category": "Office Supplies", "stock": 220, "price": 5.49, "warehouse": "A"},
  {"item_id": "I009", "name": "Standing Desk", "category": "Furniture", "stock": 8, "price": 349.99, "warehouse": "B"}
]"""
    }
]

# Write preset files to disk initially
for prs in PRESETS:
    path_file = os.path.join(DATA_DIR, prs["datasetName"])
    with open(path_file, "w", encoding="utf-8") as out:
        out.write(prs["fileContent"].strip())

# -------------------------------------------------------------
# CORE HELPERS
# -------------------------------------------------------------
def lookup_rag_manual(stderr: str) -> str:
    if "ModuleNotFoundError" in stderr and ("pandas" in stderr or "numpy" in stderr):
        return """### Python Standard Library Data Manipulation Manual (Pandas Fallback RAG Document)
Since external libraries like 'pandas' or 'numpy' are unavailable in this restricted sandbox, you MUST write pure Python code using standard modules:
- Reading CSV: Use 'csv.DictReader'
- Reading JSON: Use 'json.load'
- Grouping/Aggregating: Use 'collections.defaultdict'
Example of reading, sanitizing keys, converting column values, and calculating average:
```python
import csv
from collections import defaultdict
with open('data_file', 'r') as f:
    reader = csv.DictReader(f)
    # Strip column header whitespaces
    headers = [h.strip() for h in reader.fieldnames] if reader.fieldnames else []
    data = []
    for row in reader:
        # Strip data keys and values
        clean_row = {k.strip(): v.strip() for k, v in row.items() if k is not None}
        data.append(clean_row)

# Aggregation logic
grouped = defaultdict(list)
for row in data:
    category = row.get('region', 'Unknown')
    val = float(row.get('revenue', 0.0)) # convert to float safely
    grouped[category].append(val)

# Format summary as array of dicts for charting:
chart_data = []
for cat, values in grouped.items():
    chart_data.append({"category": cat, "total": sum(values)})
```"""
    elif "KeyError" in stderr:
        return """### KeyError Resolution Manual (RAG Document)
A KeyError occurs when accessing a column or key that is not present in the dictionary.
Common causes and fixes:
1. Space padding: Headers or values may contain leading/trailing whitespaces. Always sanitize keys:
   `clean_row = {k.strip(): v.strip() for k, v in row.items()}`
2. Typo: Double-check the spelling of the requested column against the available columns.
3. Access: Print or check `list(row.keys())` before accessing. Use `dict.get(key, default)` instead of `dict[key]` to prevent crashes."""
    elif "ValueError" in stderr or "TypeError" in stderr:
        return """### Safe Type Conversion Manual (RAG Document)
ValueError/TypeError occurs when converting empty strings or dirty strings to float/int.
Safe conversion helper function:
```python
def safe_float(val, default=0.0):
    if not val:
        return default
    try:
        return float(str(val).replace('$', '').replace(',', '').strip())
    except ValueError:
        return default
```"""
    else:
        return """### General Python Script Sandbox Execution Manual
Your script must run standalone and output a single JSON block to stdout.
Ensure that:
1. You read from './data_file' using standard 'csv' or 'json' libraries.
2. You output valid JSON string via `print(json.dumps(...))`.
3. Do not output anything else to stdout."""


def parse_csv_preview(content: str):
    # .splitlines() handles \r\n (Windows) and \n (Mac/Linux) automatically
    lines = [l.strip() for l in content.splitlines() if l.strip()]
    if not lines:
        return {"headers": [], "rows": []}
    
    reader = csv.reader(lines)
    try:
        headers = [h.strip() for h in next(reader)]
    except StopIteration:
        return {"headers": [], "rows": []}
        
    rows = []
    for i, row_vals in enumerate(reader):
        if i >= 10:
            break
        row_obj = {}
        for idx, h in enumerate(headers):
            row_obj[h] = row_vals[idx].strip() if idx < len(row_vals) else ""
        rows.append(row_obj)
        
    return {"headers": headers, "rows": rows}


def parse_json_preview(content: str):
    try:
        data = json.loads(content)
        if isinstance(data, list):
            headers = list(data[0].keys()) if len(data) > 0 else []
            rows = data[:10]
            return {"headers": headers, "rows": rows}
        else:
            headers = list(data.keys())
            rows = [data]
            return {"headers": headers, "rows": rows}
    except Exception:
        return {"headers": [], "rows": []}


# -------------------------------------------------------------
# BEAUTIFUL SVG CHART GENERATOR (GEOMETRIC BALANCE DESIGN)
# -------------------------------------------------------------
def generate_svg_chart(chart_type, chart_data, chart_config):
    if not chart_data or chart_type == "none" or chart_type == "":
        return ""
        
    x_key = chart_config.get("xKey", "label")
    y_keys = chart_config.get("yKeys", ["value"])
    y_key = y_keys[0] if y_keys else "value"
    
    labels = []
    values = []
    for item in chart_data:
        lbl = str(item.get(x_key, item.get("label", "")))
        val_raw = item.get(y_key, item.get("value", 0))
        try:
            val = float(val_raw)
        except (ValueError, TypeError):
            val = 0.0
        labels.append(lbl)
        values.append(val)
        
    if not values:
        return ""
        
    max_val = max(values) if max(values) > 0 else 1.0
    min_val = min(values) if min(values) < 0 else 0.0
    
    # SVG size config
    width = 600
    height = 300
    padding_left = 60
    padding_right = 30
    padding_top = 40
    padding_bottom = 50
    
    chart_w = width - padding_left - padding_right
    chart_h = height - padding_top - padding_bottom
    
    svg = []
    svg.append(f'<svg viewBox="0 0 {width} {height}" class="w-full h-full" xmlns="http://www.w3.org/2000/svg">')
    
    # Deep Dark elegant background
    svg.append(f'<rect width="{width}" height="{height}" fill="#0f172a" rx="16" />')
    
    # Grid lines
    svg.append('<g stroke="#1e293b" stroke-width="1" stroke-dasharray="2 4">')
    for i in range(5):
        y_pos = padding_top + i * (chart_h / 4)
        svg.append(f'<line x1="{padding_left}" y1="{y_pos}" x2="{width - padding_right}" y2="{y_pos}" />')
    svg.append('</g>')
    
    if chart_type == "bar":
        num_bars = len(values)
        bar_gap = 12
        total_gaps_w = bar_gap * (num_bars + 1)
        bar_w = (chart_w - total_gaps_w) / num_bars if num_bars > 0 else chart_w
        
        for idx, (lbl, val) in enumerate(zip(labels, values)):
            h_ratio = val / max_val
            bar_h = chart_h * h_ratio
            x_pos = padding_left + bar_gap + idx * (bar_w + bar_gap)
            y_pos = padding_top + chart_h - bar_h
            
            svg.append(f'<rect x="{x_pos}" y="{y_pos}" width="{bar_w}" height="{bar_h}" rx="4" fill="url(#barGrad)" />')
            
            lbl_short = lbl[:10] + ".." if len(lbl) > 12 else lbl
            svg.append(f'<text x="{x_pos + bar_w/2}" y="{height - padding_bottom + 20}" fill="#94a3b8" font-size="10" text-anchor="middle" font-family="Inter, system-ui">{lbl_short}</text>')
            svg.append(f'<text x="{x_pos + bar_w/2}" y="{y_pos - 6}" fill="#e2e8f0" font-size="9" text-anchor="middle" font-family="JetBrains Mono, monospace">{val:,.0f}</text>')
            
    elif chart_type in ["line", "area"]:
        num_points = len(values)
        points = []
        for idx, (lbl, val) in enumerate(zip(labels, values)):
            x_pos = padding_left + idx * (chart_w / (num_points - 1)) if num_points > 1 else padding_left + chart_w/2
            h_ratio = val / max_val
            y_pos = padding_top + chart_h - (chart_h * h_ratio)
            points.append((x_pos, y_pos, lbl, val))
            
        path_d = []
        area_d = []
        if points:
            path_d.append(f"M {points[0][0]} {points[0][1]}")
            area_d.append(f"M {points[0][0]} {padding_top + chart_h}")
            area_d.append(f"L {points[0][0]} {points[0][1]}")
            for p in points[1:]:
                path_d.append(f"L {p[0]} {p[1]}")
                area_d.append(f"L {p[0]} {p[1]}")
            area_d.append(f"L {points[-1][0]} {padding_top + chart_h}")
            area_d.append("Z")
            
        if chart_type == "area" and points:
            svg.append(f'<path d="{" ".join(area_d)}" fill="url(#areaGrad)" opacity="0.3" />')
            
        svg.append(f'<path d="{" ".join(path_d)}" fill="none" stroke="#6366f1" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />')
        
        for p in points:
            svg.append(f'<circle cx="{p[0]}" cy="{p[1]}" r="4.5" fill="#ffffff" stroke="#6366f1" stroke-width="2.5" />')
            svg.append(f'<text x="{p[0]}" y="{p[1] - 8}" fill="#e2e8f0" font-size="9" text-anchor="middle" font-family="JetBrains Mono, monospace">{p[3]:,.0f}</text>')
            lbl_short = p[2][:8] + ".." if len(p[2]) > 10 else p[2]
            svg.append(f'<text x="{p[0]}" y="{height - padding_bottom + 20}" fill="#94a3b8" font-size="10" text-anchor="middle" font-family="Inter, system-ui">{lbl_short}</text>')
            
    elif chart_type == "scatter":
        num_points = len(values)
        for idx, (lbl, val) in enumerate(zip(labels, values)):
            x_pos = padding_left + idx * (chart_w / (num_points - 1)) if num_points > 1 else padding_left + chart_w/2
            h_ratio = val / max_val
            y_pos = padding_top + chart_h - (chart_h * h_ratio)
            
            svg.append(f'<circle cx="{x_pos}" cy="{y_pos}" r="7" fill="#6366f1" opacity="0.85" stroke="#818cf8" stroke-width="1.5" />')
            svg.append(f'<text x="{x_pos}" y="{y_pos - 10}" fill="#e2e8f0" font-size="9" text-anchor="middle" font-family="JetBrains Mono, monospace">{val:,.0f}</text>')
            lbl_short = lbl[:8] + ".." if len(lbl) > 10 else lbl
            svg.append(f'<text x="{x_pos}" y="{height - padding_bottom + 20}" fill="#94a3b8" font-size="10" text-anchor="middle" font-family="Inter, system-ui">{lbl_short}</text>')
            
    elif chart_type == "pie":
        total_sum = sum(values) if sum(values) > 0 else 1.0
        cx = padding_left + chart_w/2
        cy = padding_top + chart_h/2
        r = min(chart_w, chart_h)/2 * 0.95
        
        colors = ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#14b8a6", "#3b82f6"]
        
        start_angle = 0.0
        for idx, (lbl, val) in enumerate(zip(labels, values)):
            slice_angle = (val / total_sum) * 360.0
            
            x1 = cx + r * math.cos(math.radians(start_angle - 90))
            y1 = cy + r * math.sin(math.radians(start_angle - 90))
            
            end_angle = start_angle + slice_angle
            x2 = cx + r * math.cos(math.radians(end_angle - 90))
            y2 = cy + r * math.sin(math.radians(end_angle - 90))
            
            large_arc = 1 if slice_angle > 180 else 0
            color = colors[idx % len(colors)]
            
            if slice_angle >= 359.9:
                svg.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" />')
            else:
                svg.append(f'<path d="M {cx} {cy} L {x1} {y1} A {r} {r} 0 {large_arc} 1 {x2} {y2} Z" fill="{color}" stroke="#0f172a" stroke-width="1.5" />')
                
            label_angle = start_angle + slice_angle / 2
            lx = cx + (r * 0.65) * math.cos(math.radians(label_angle - 90))
            ly = cy + (r * 0.65) * math.sin(math.radians(label_angle - 90))
            percentage = (val / total_sum) * 100
            if percentage > 5:
                svg.append(f'<text x="{lx}" y="{ly}" fill="#ffffff" font-size="9" font-weight="bold" text-anchor="middle" font-family="Inter, system-ui">{percentage:.1f}%</text>')
                
            start_angle = end_angle
            
        svg.append(f'<g transform="translate({cx + r + 20}, {padding_top})">')
        for idx, (lbl, val) in enumerate(zip(labels, values)):
            if idx < 6:
                color = colors[idx % len(colors)]
                ly_pos = idx * 18
                lbl_short = lbl[:12] + ".." if len(lbl) > 14 else lbl
                svg.append(f'<rect x="0" y="{ly_pos}" width="10" height="10" rx="2" fill="{color}" />')
                svg.append(f'<text x="16" y="{ly_pos + 9}" fill="#94a3b8" font-size="10" font-family="Inter, system-ui">{lbl_short} ({val:,.0f})</text>')
        svg.append('</g>')
        
    svg.append('<g font-size="9" fill="#94a3b8" text-anchor="end" font-family="JetBrains Mono, monospace">')
    for i in range(5):
        y_pos = padding_top + i * (chart_h / 4)
        val_at_y = max_val - i * ((max_val - min_val) / 4)
        svg.append(f'<text x="{padding_left - 10}" y="{y_pos + 3}">{val_at_y:,.0f}</text>')
    svg.append('</g>')
    
    svg.append('<defs>')
    svg.append('  <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">')
    svg.append('    <stop offset="0%" stop-color="#818cf8" />')
    svg.append('    <stop offset="100%" stop-color="#4f46e5" />')
    svg.append('  </linearGradient>')
    svg.append('  <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">')
    svg.append('    <stop offset="0%" stop-color="#6366f1" stop-opacity="0.4" />')
    svg.append('    <stop offset="100%" stop-color="#6366f1" stop-opacity="0" />')
    svg.append('  </linearGradient>')
    svg.append('</defs>')
    svg.append('</svg>')
    
    return "".join(svg)


# -------------------------------------------------------------
# GEMINI API INTEGRATION
# -------------------------------------------------------------
def call_gemini(prompt: str) -> str:
    api_key = CUSTOM_GEMINI_KEY or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Missing valid API key. Configure GEMINI_API_KEY in the environment settings.")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "aistudio-build"
    }
    
    body = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.1
        }
    }
    
    req = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'), headers=headers, method="POST")
    with urllib.request.urlopen(req) as res:
        response_data = json.loads(res.read().decode('utf-8'))
        text = response_data["candidates"][0]["content"]["parts"][0]["text"]
        return text


# -------------------------------------------------------------
# CODE SANDBOX EXECUTION
# -------------------------------------------------------------
def run_python_code(code: str, dataset_path: str):
    sandbox_path = os.path.join(os.getcwd(), "sandbox.py")
    local_data_path = os.path.join(os.getcwd(), "data_file")
    
    # Write code to sandbox
    with open(sandbox_path, "w", encoding="utf-8") as f:
        f.write(code)
        
    # Copy dataset file
    import shutil
    shutil.copyfile(dataset_path, local_data_path)
    
    # Run sandbox process
    try:
        res = subprocess.run(["python3", "sandbox.py"], capture_output=True, text=True, timeout=10)
        stdout = res.stdout
        stderr = res.stderr
        exit_code = res.returncode
    except subprocess.TimeoutExpired:
        stdout = ""
        stderr = "Execution timed out (10s limit)"
        exit_code = -1
    except Exception as e:
        stdout = ""
        stderr = f"Sandbox startup failure: {str(e)}"
        exit_code = -2
        
    # Clean up
    for p in [sandbox_path, local_data_path]:
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass
                
    return stdout, stderr, exit_code


# -------------------------------------------------------------
# SAFE JSON PARSER HELPER
# -------------------------------------------------------------
def safe_parse_json(text: str):
    try:
        import re
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            return json.loads(json_match.group(0))
        return json.loads(text)
    except Exception:
        return None


# -------------------------------------------------------------
# MULTIPART MULTIFILE FORM PARSER
# -------------------------------------------------------------
def parse_multipart(body: bytes, boundary: bytes):
    parts = body.split(b'--' + boundary)
    fields = {}
    for part in parts:
        if not part or part == b'\r\n' or part == b'--\r\n' or part == b'--':
            continue
            
        try:
            head, val = part.split(b'\r\n\r\n', 1)
        except ValueError:
            continue
            
        head_str = head.decode('utf-8', errors='ignore')
        name = None
        filename = None
        for line in head_str.split('\r\n'):
            if line.lower().startswith('content-disposition:'):
                parts_disp = line.split(';')
                for p in parts_disp:
                    p = p.strip()
                    if p.startswith('name='):
                        name = p.split('=', 1)[1].strip('"\'')
                    elif p.startswith('filename='):
                        filename = p.split('=', 1)[1].strip('"\'')
        
        if name:
            if val.endswith(b'\r\n'):
                val = val[:-2]
            
            if filename:
                fields[name] = {
                    "filename": filename,
                    "content": val.decode('utf-8', errors='ignore'),
                    "raw": val
                }
            else:
                fields[name] = val.decode('utf-8', errors='ignore')
                
    return fields


# -------------------------------------------------------------
# STATE PERSISTENCE
# -------------------------------------------------------------
STATE_FILE = os.path.join(DATA_DIR, "active_state.json")

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
            
    # Default State matches Presets[0]
    default_prs = PRESETS[0]
    return {
        "datasetName": default_prs["datasetName"],
        "datasetType": default_prs["datasetType"],
        "datasetContent": default_prs["fileContent"],
        "query": default_prs["query"],
        "executionSteps": [],
        "chartType": "none",
        "chartData": [],
        "chartConfig": {},
        "insightSummary": "Co-pilot workspace is ready. Click 'Run Co-Pilot Agent' to begin.",
        "finalCode": ""
    }

def save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print("Error saving state:", str(e))


# -------------------------------------------------------------
# CUSTOM HTTP HANDLER
# -------------------------------------------------------------
class MyHandler(http.server.BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        # Override to suppress noisy server console logs
        pass

    def do_GET(self):
        url_parsed = urllib.parse.urlparse(self.path)
        path = url_parsed.path
        query_params = urllib.parse.parse_qs(url_parsed.query)
        
        # REST API presets
        if path == "/api/presets":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(PRESETS).encode('utf-8'))
            return
            
        # Default application route
        if path == "/":
            state = load_state()
            
            # Load Preset parameter if present
            if "preset" in query_params:
                preset_id = query_params["preset"][0]
                matched = [p for p in PRESETS if p["id"] == preset_id]
                if matched:
                    prs = matched[0]
                    state = {
                        "datasetName": prs["datasetName"],
                        "datasetType": prs["datasetType"],
                        "datasetContent": prs["fileContent"],
                        "query": prs["query"],
                        "executionSteps": [],
                        "chartType": "none",
                        "chartData": [],
                        "chartConfig": {},
                        "insightSummary": "Preset loaded. Run Co-Pilot Agent to execute the analysis.",
                        "finalCode": ""
                    }
                    save_state(state)
            
            # Load index.html template
            with open("index.html", "r", encoding="utf-8") as t_file:
                template = t_file.read()
                
            # Build Presets HTML Cards
            presets_html = []
            for idx, prs in enumerate(PRESETS):
                is_selected = state["datasetName"] == prs["datasetName"]
                selected_border = "border-indigo-500 bg-indigo-500/10 shadow-lg shadow-indigo-500/10 ring-1 ring-indigo-500/20" if is_selected else "border-slate-800 bg-slate-900/40 hover:bg-slate-900 hover:border-slate-700"
                active_badge = f'<span class="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></span>' if is_selected else ""
                
                presets_html.append(f"""
                <a href="/?preset={prs['id']}" class="p-4 rounded-xl text-left border transition-all flex flex-col justify-between group h-full relative {selected_border}">
                  <div>
                    <div class="flex items-center justify-between mb-2">
                      <span class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-500/10 text-slate-500">
                        Use Case {idx + 1}
                      </span>
                      {active_badge}
                    </div>
                    <h4 class="font-bold text-sm tracking-tight mb-1 group-hover:text-indigo-400 transition-colors text-white">
                      {prs['title']}
                    </h4>
                    <p class="text-[11px] line-clamp-2 leading-relaxed text-slate-400">
                      {prs['description']}
                    </p>
                  </div>
                  <div class="flex items-center justify-between mt-3 pt-2 border-t border-slate-800/60 text-[10px] text-slate-500 font-mono">
                    <span class="flex items-center gap-1">
                      {prs['datasetName']}
                    </span>
                    <span class="text-indigo-400 font-bold group-hover:translate-x-1 transition-all">→</span>
                  </div>
                </a>
                """)
            presets_html_str = "\n".join(presets_html)
            
            # Build Dataset Preview Table
            preview_html = []
            if state["datasetType"] == "csv":
                preview = parse_csv_preview(state["datasetContent"])
            else:
                preview = parse_json_preview(state["datasetContent"])
                
            if preview["headers"]:
                preview_html.append('<table class="w-full text-[11px] text-left border-collapse">')
                # Table Headers
                preview_html.append('<thead>')
                preview_html.append('<tr class="bg-slate-950/60 border-b border-slate-800">')
                for h in preview["headers"]:
                    preview_html.append(f'<th class="p-2 font-mono text-slate-400 font-semibold">{h}</th>')
                preview_html.append('</tr>')
                preview_html.append('</thead>')
                # Table Rows
                preview_html.append('<tbody class="divide-y divide-slate-800/40">')
                for r in preview["rows"]:
                    preview_html.append('<tr>')
                    for h in preview["headers"]:
                        val_str = str(r.get(h, ""))
                        preview_html.append(f'<td class="p-2 text-slate-300 font-mono font-medium whitespace-nowrap">{val_str}</td>')
                    preview_html.append('</tr>')
                preview_html.append('</tbody>')
                preview_html.append('</table>')
            else:
                preview_html.append('<div class="p-6 text-center text-slate-500 text-xs">Dataset is empty or invalid</div>')
            preview_html_str = "".join(preview_html)
            
            # Build Trace Steps HTML
            trace_html = []
            if state.get("executionSteps"):
                for step in state["executionSteps"]:
                    is_success = step.get("status") == "success"
                    status_color = "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" if is_success else "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                    status_text = "Success" if is_success else "Correction needed"
                    
                    # Escape HTML for display
                    safe_code = step.get("code", "").replace("<", "&lt;").replace(">", "&gt;")
                    safe_stdout = step.get("stdout", "").replace("<", "&lt;").replace(">", "&gt;")
                    safe_stderr = step.get("stderr", "").replace("<", "&lt;").replace(">", "&gt;")
                    
                    stdout_section = f"""
                    <div class="bg-slate-950 p-2.5 rounded-lg border border-slate-850 relative text-[10px] font-mono leading-relaxed text-emerald-400/80 max-h-24 overflow-y-auto">
                      <span class="text-[8px] uppercase font-bold text-slate-500 absolute top-1 right-2">Stdout</span>
                      <pre class="whitespace-pre overflow-x-auto">{safe_stdout}</pre>
                    </div>
                    """ if step.get("stdout") else ""
                    
                    stderr_section = f"""
                    <div class="bg-rose-950/20 p-2.5 border-l-2 border-rose-500/60 text-rose-400 text-[10px] rounded-r-lg space-y-1 font-mono">
                      <div class="flex items-center gap-1 text-rose-400 font-bold uppercase text-[8px]">
                        <span>Python Interpreter Traceback (Stderr):</span>
                      </div>
                      <pre class="whitespace-pre-wrap leading-relaxed overflow-x-auto">{safe_stderr}</pre>
                    </div>
                    """ if step.get("stderr") else ""
                    
                    rag_section = ""
                    if step.get("status") == "error":
                        rag_doc = lookup_rag_manual(step.get("stderr", ""))
                        rag_section = f"""
                        <div class="bg-indigo-950/25 p-2.5 border-l-2 border-indigo-400/50 text-indigo-300 text-[10px] rounded-r-lg space-y-1 font-mono">
                          <div class="flex items-center gap-1 text-indigo-400 font-bold uppercase text-[8px]">
                            <span>RAG Corpus Document Retrieved:</span>
                          </div>
                          <pre class="whitespace-pre-wrap leading-relaxed overflow-x-auto">{rag_doc}</pre>
                        </div>
                        """
                    
                    trace_html.append(f"""
                    <div class="p-3.5 rounded-xl border border-slate-800 bg-slate-900/10 space-y-3">
                      <div class="flex items-center justify-between text-[11px]">
                        <span class="text-slate-400 flex items-center gap-1">
                          <span class="text-indigo-400 font-bold">[{step.get('stepNumber')}]</span>
                          <span class="font-semibold text-slate-200">{step.get('title')}</span>
                        </span>
                        <span class="text-[9px] font-bold px-1.5 py-0.2 rounded uppercase {status_color}">
                          {status_text}
                        </span>
                      </div>
                      
                      <div class="bg-slate-950 p-2.5 rounded-lg border border-slate-850 relative text-[10px] font-mono leading-relaxed text-indigo-300 max-h-28 overflow-y-auto">
                        <span class="text-[8px] uppercase font-bold text-slate-500 absolute top-1 right-2">Code Generated</span>
                        <pre class="whitespace-pre overflow-x-auto">{safe_code}</pre>
                      </div>
                      
                      {stdout_section}
                      {stderr_section}
                      {rag_section}
                    </div>
                    """)
            else:
                trace_html.append("""
                <div class="p-8 rounded-xl border border-slate-800 border-dashed text-center space-y-3">
                  <div class="mx-auto w-10 h-10 rounded-xl bg-slate-800 text-slate-500 flex items-center justify-center">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                      <path d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                    </svg>
                  </div>
                  <div>
                    <h4 class="text-xs font-semibold text-slate-300">No agent traces active</h4>
                    <p class="text-[10px] text-slate-500">Provide an analytical prompt and click Analyze to start</p>
                  </div>
                </div>
                """)
            trace_html_str = "\n".join(trace_html)
            
            # Build Visual Tab Content
            chart_svg = generate_svg_chart(state.get("chartType", "none"), state.get("chartData", []), state.get("chartConfig", {}))
            
            visual_tab_html = []
            if chart_svg:
                visual_tab_html.append(f"""
                <div class="grid grid-cols-1 md:grid-cols-12 gap-5 items-center flex-1">
                  <!-- Chart rendering column -->
                  <div class="md:col-span-7 flex items-center justify-center bg-slate-950 p-4 border border-slate-850 rounded-xl h-[230px]">
                    {chart_svg}
                  </div>
                  <!-- Insights narrative column -->
                  <div class="md:col-span-5 space-y-2">
                    <span class="text-[10px] uppercase font-bold text-slate-500 font-mono tracking-wider">Analysis Narrative Insight</span>
                    <p class="text-xs text-slate-300 leading-relaxed font-medium">
                      {state.get('insightSummary', '')}
                    </p>
                  </div>
                </div>
                """)
            else:
                # Fallback message
                visual_tab_html.append(f"""
                <div class="flex-1 flex flex-col items-center justify-center text-center p-10 border border-dashed border-slate-850 rounded-xl bg-slate-950/20 space-y-3">
                  <div class="w-12 h-12 rounded-2xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                      <path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 002 2h2a2 2 0 002-2"></path>
                    </svg>
                  </div>
                  <div>
                    <h4 class="text-xs font-semibold text-slate-300">Analytical Insights Deck ready</h4>
                    <p class="text-[11px] text-slate-500 max-w-sm">
                      {state.get('insightSummary', 'Run the Co-pilot. Charts and observations will be dynamically drawn here.')}
                    </p>
                  </div>
                </div>
                """)
            visual_tab_str = "".join(visual_tab_html)
            
            # Safe clean final code
            final_code_str = state.get("finalCode", "").strip()
            if not final_code_str:
                final_code_str = "# Final standalone python script will populate here"
                
            # Perform substitutions
            html_rendered = template \
                .replace("{{ PRESETS_HTML }}", presets_html_str) \
                .replace("{{ ACTIVE_DATASET_NAME }}", state["datasetName"]) \
                .replace("{{ ACTIVE_DATASET_TYPE }}", state["datasetType"].upper()) \
                .replace("{{ DATASET_PREVIEW_HTML }}", preview_html_str) \
                .replace("{{ ACTIVE_QUERY }}", state["query"]) \
                .replace("{{ TRACE_STEPS_HTML }}", trace_html_str) \
                .replace("{{ VISUAL_TAB_CONTENT }}", visual_tab_str) \
                .replace("{{ FINAL_CODE }}", final_code_str)
                
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html_rendered.encode('utf-8'))
            return
            
        # Fallback for 404
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        url_parsed = urllib.parse.urlparse(self.path)
        path = url_parsed.path
        
        # Read Content details
        content_length = int(self.headers.get('Content-Length', 0))
        content_type = self.headers.get('Content-Type', '')
        
        body_bytes = self.rfile.read(content_length) if content_length > 0 else b''
        
        # Parse fields
        fields = {}
        if 'multipart/form-data' in content_type:
            boundary_str = content_type.split('boundary=')[1].strip()
            fields = parse_multipart(body_bytes, boundary_str.encode('utf-8'))
        elif 'application/x-www-form-urlencoded' in content_type:
            # Parse form urlencoded
            decoded = body_bytes.decode('utf-8', errors='ignore')
            qs = urllib.parse.parse_qs(decoded)
            fields = {k: v[0] for k, v in qs.items()}
            
        if path == "/upload":
            # Handle uploaded files
            if "dataset_file" in fields and isinstance(fields["dataset_file"], dict):
                file_info = fields["dataset_file"]
                name = file_info["filename"]
                content = file_info["content"]
                
                # Determine type
                file_type = "json" if name.lower().endswith(".json") else "csv"
                
                # Save uploaded file
                dataset_path = os.path.join(DATA_DIR, name)
                with open(dataset_path, "w", encoding="utf-8") as f:
                    f.write(content)
                    
                # Setup active state
                state = {
                    "datasetName": name,
                    "datasetType": file_type,
                    "datasetContent": content,
                    "query": "Perform a comprehensive data quality audit and output a summary of missing values, anomalies, and row counts." if file_type == "csv" else "Show me the total spend grouped by categories.",
                    "executionSteps": [],
                    "chartType": "none",
                    "chartData": [],
                    "chartConfig": {},
                    "insightSummary": "Custom dataset uploaded successfully! Ask any questions above.",
                    "finalCode": ""
                }
                save_state(state)
                
            # Redirect to GET /
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()
            return
            
        if path == "/analyze":
            query = fields.get("query", "").strip()
            dataset_name = fields.get("dataset_name", "").strip()
            
            # Load active state to retrieve dataset contents
            state = load_state()
            
            # Make sure we got active dataset content
            dataset_path = os.path.join(DATA_DIR, state["datasetName"])
            
            # Parse preview
            preview = {"headers": []}
            if state["datasetType"] == "csv":
                preview = parse_csv_preview(state["datasetContent"])
            else:
                preview = parse_json_preview(state["datasetContent"])
                
            execution_steps = []
            current_attempt = 1
            max_attempts = 3
            success = False
            parsed_result = None
            final_code = ""
            
            # Construct base Gemini Prompt
            initial_prompt = f"""You are the Autonomous Data Science Co-Pilot.
The user uploaded a dataset named "{state['datasetName']}".
It has the following headers: {", ".join(preview["headers"])}.
Here is a small preview of the data:
{json.dumps(preview["rows"][:3], indent=2)}

The user asks: "{query}"

Since this is a restricted Python sandbox environment, you MUST write executable Python code using only standard modules (such as 'csv', 'json', 'collections', 'datetime', 'math', 'statistics'). Do NOT import pandas or numpy, as they are not available in this Python installation.

Your code must:
1. Open the local file './data_file' and parse it.
2. Safely clean whitespaces from header keys and cell values (e.g., using k.strip() and v.strip()).
3. Perform calculations, groupings, analysis or quality audit as asked.
4. Output a single JSON string directly to stdout. Do not output anything else.
   The output JSON format MUST be exactly:
   {{
     "chartType": "bar" | "line" | "pie" | "scatter" | "area" | "none",
     "chartData": [
        {{"label": "Group A", "value": 100}},
        ...
     ],
     "chartConfig": {{
        "xKey": "label",
        "yKeys": ["value"],
        "xLabel": "Label Header",
        "yLabel": "Value Header"
     }},
     "insight": "Write a descriptive professional data analysis insight paragraph here."
   }}

Write ONLY the executable Python code block inside a markdown python block:
```python
# code here
```"""
            
            try:
                while current_attempt <= max_attempts and not success:
                    prompt = initial_prompt
                    if current_attempt > 1:
                        # Self-correction prompt
                        last_step = execution_steps[-1]
                        rag_manual = lookup_rag_manual(last_step.get("stderr", ""))
                        
                        prompt = f"""You are the Autonomous Data Science Co-Pilot.
We ran your previous python script in the sandbox and it failed!
Error output (stderr):
{last_step.get("stderr")}

Failed python code was:
```python
{last_step.get("code")}
```

Here is the relevant Official RAG Reference Manual on resolving this error:
{rag_manual}

Please fix the error. Write a corrected standalone Python script that reads './data_file', performs the calculations requested, and outputs the specified JSON to stdout. Do not use external libraries. Ensure you strip headers/values and cast values safely!

Write ONLY the executable Python code block inside:
```python
# code here
```"""
                    
                    step_log = {
                        "stepNumber": current_attempt,
                        "title": "Generating initial analytical code" if current_attempt == 1 else f"Self-Correction Attempt {current_attempt - 1} (RAG Guided)",
                        "status": "running",
                        "code": "",
                        "stdout": "",
                        "stderr": ""
                    }
                    execution_steps.append(step_log)
                    
                    # Call Gemini
                    gemini_text = call_gemini(prompt)
                    
                    # Extract python block
                    import re
                    code_match = re.search(r'```python([\s\S]*?)```', gemini_text)
                    code_to_run = code_match.group(1).strip() if code_match else gemini_text.strip()
                    
                    if code_to_run.startswith("python"):
                        code_to_run = code_to_run[6:].strip()
                        
                    step_log["code"] = code_to_run
                    final_code = code_to_run
                    
                    # Run code sandbox
                    stdout, stderr, exit_code = run_python_code(code_to_run, dataset_path)
                    step_log["stdout"] = stdout
                    step_log["stderr"] = stderr
                    
                    if exit_code == 0 and stdout:
                        parsed = safe_parse_json(stdout)
                        if parsed and ("chartData" in parsed or "insight" in parsed):
                            success = True
                            parsed_result = parsed
                            step_log["status"] = "success"
                        else:
                            step_log["status"] = "error"
                            step_log["stderr"] = "Invalid output format. Script stdout was not parseable as the required JSON schema. Stdout was: " + stdout
                    else:
                        step_log["status"] = "error"
                        if not step_log["stderr"]:
                            step_log["stderr"] = f"Script exited with code {exit_code}."
                            
                    current_attempt += 1
                    
                # Save analysis output to state
                state["query"] = query
                state["executionSteps"] = execution_steps
                state["chartType"] = parsed_result.get("chartType", "none") if parsed_result else "none"
                state["chartData"] = parsed_result.get("chartData", []) if parsed_result else []
                state["chartConfig"] = parsed_result.get("chartConfig", {}) if parsed_result else {}
                state["insightSummary"] = parsed_result.get("insight", "Analysis complete but returned no detailed written narrative.") if parsed_result else "Co-pilot analysis loop completed, but all sandbox executions returned errors. Review the Traceback logs to identify sandbox execution issues."
                state["finalCode"] = final_code
                save_state(state)
                
            except Exception as e:
                print("Exception during analyze:", str(e))
                traceback.print_exc()
                state["query"] = query
                state["insightSummary"] = f"An analytical engine runtime exception occurred: {str(e)}"
                save_state(state)
                
            # Redirect back to GET /
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()
            return
            
        # Fallback for POST 404
        self.send_response(404)
        self.end_headers()


# -------------------------------------------------------------
# START SERVER
# -------------------------------------------------------------
if __name__ == "__main__":
    print(f"Starting Python HTTP Server on port {PORT}...")
    handler = MyHandler
    # Allow port reuse to avoid 'Address already in use' errors
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(( '0.0.0.0', PORT ), handler) as httpd:
        print("Server running successfully!")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
