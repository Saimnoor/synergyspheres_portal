import streamlit as st
import leafmap.foliumap as leafmap
import json
import os
import tempfile

# --- MODULE CHECKS ---
try:
    from streamlit_ace import st_ace
    HAS_EDITOR = True
except ImportError:
    HAS_EDITOR = False

# --- DATABASE & FILE STORAGE ---
DB_FILE = "my_custom_tools.json"

def load_tools():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def save_tool(name, code):
    tools = load_tools()
    tools[name] = code
    with open(DB_FILE, "w") as f:
        json.dump(tools, f)

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="Synergyspheres GIS & Spatial Station")
st.subheader("🌐 Synergyshperes Professional GIS & Spatial Station")

# 2. Sidebar Navigation
st.sidebar.title("🗄️ Student Explorer")
workspace = st.sidebar.radio("Navigation Pane", ["Layer Manager", "Raster Data Hub", "Geoprocessing Suite", "Developer Console"])

# Session State Init
if 'clicked_coords' not in st.session_state:
    st.session_state['clicked_coords'] = (30.38, 69.35)
if 'executed_scripts' not in st.session_state:
    st.session_state['executed_scripts'] = []
if 'uploaded_raster' not in st.session_state:
    st.session_state['uploaded_raster'] = None

# --- MODE 1: Layer Manager ---
selected_basemap = "OpenStreetMap"
if workspace == "Layer Manager":
    st.sidebar.write("### 📖 Active Layers")
    map_choice = st.sidebar.selectbox("Imagery Engine", ["Standard Streets", "Satellite Imagery", "Topographic", "Dark Canvas"])
    basemap_dict = {"Standard Streets": "OpenStreetMap", "Satellite Imagery": "SATELLITE", "Topographic": "TERRAIN", "Dark Canvas": "CartoDB.DarkMatter"}
    selected_basemap = basemap_dict[map_choice]

    st.sidebar.markdown("---")
    st.sidebar.write("### 🔒 Your Tool Vault")
    saved_tools = load_tools()
    if saved_tools:
        for tool_name, script in saved_tools.items():
            if st.sidebar.checkbox(f"Enable {tool_name}"):
                st.session_state['executed_scripts'].append(script)

# --- MODE 2: Raster Data Hub (TIFF/Satellite Upload) ---
elif workspace == "Raster Data Hub":
    st.sidebar.write("### 🛰️ Satellite Data Import")
    st.sidebar.info("Upload .tif or .geotiff files to overlay them on the map.")
    tif_file = st.sidebar.file_uploader("Choose a TIFF file", type=['tif', 'tiff', 'geotiff'])
    
    if tif_file:
        # Save uplaoded file to a temporary location for the map to read
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.tif')
        tfile.write(tif_file.read())
        st.session_state['uploaded_raster'] = tfile.name
        st.sidebar.success("TIFF loaded successfully!")
    
    if st.sidebar.button("Clear Raster Imagery"):
        st.session_state['uploaded_raster'] = None

# --- MODE 3: Geoprocessing Suite ---
elif workspace == "Geoprocessing Suite":
    st.sidebar.write("### ⚙️ Coordinate Finder")
    st.sidebar.metric("Latitude", f"{st.session_state['clicked_coords'][0]:.6f}")
    st.sidebar.metric("Longitude", f"{st.session_state['clicked_coords'][1]:.6f}")

# --- MODE 4: Developer Console ---
elif workspace == "Developer Console":
    if not HAS_EDITOR:
        st.error("⚠️ Run: pip install streamlit-ace")
    else:
        st.sidebar.write("### 🐍 Live Python Editor")
        tool_name = st.sidebar.text_input("Tool Name", "My New Tool")
        editor_code = st_ace(value="# Write logic here\nm.add_marker(location=st.session_state['clicked_coords'])", 
                            language="python", theme="monokai", min_lines=15)
        
        col1, col2 = st.sidebar.columns(2)
        if col1.button("▶️ Run"): st.session_state['temp_code'] = editor_code
        if col2.button("💾 Save"):
            save_tool(tool_name, editor_code)
            st.sidebar.success(f"'{tool_name}' saved!")

# 3. Initialize Map Engine
m = leafmap.Map(center=st.session_state['clicked_coords'], zoom=5, draw_control=True, measure_control=True, scale_control=True, latlon_control=True)

# 4. Apply Basemaps
if selected_basemap == "SATELLITE":
    m.add_tile_layer(url="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}", name="Satellite", attribution="Google")
else:
    m.add_basemap(selected_basemap)

# 5. Handle TIFF Display
if st.session_state['uploaded_raster']:
    try:
        # leafmap automatically handles the local tile server for rasters
        m.add_raster(st.session_state['uploaded_raster'], layer_name="Uploaded Satellite Data")
    except Exception as e:
        st.error(f"Could not render TIFF: {e}")

# 6. EXECUTION ENGINE
if 'temp_code' in st.session_state and workspace == "Developer Console":
    try: exec(st.session_state['temp_code'])
    except Exception as e: st.error(f"Error: {e}")

for script in st.session_state['executed_scripts']:
    try: exec(script)
    except: pass
st.session_state['executed_scripts'] = []

# 7. Display Map
map_output = m.to_streamlit(height=500)
if map_output and map_output.get("last_clicked"):
    new_coords = (map_output['last_clicked']['lat'], map_output['last_clicked']['lng'])
    if new_coords != st.session_state['clicked_coords']:
        st.session_state['clicked_coords'] = new_coords
        st.rerun()
