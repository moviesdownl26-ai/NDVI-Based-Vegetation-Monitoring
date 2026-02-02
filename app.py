import streamlit as st
import ee
import geemap.foliumap as geemap


# -------------------------------------
# Initialize Earth Engine
# -------------------------------------
ee.Initialize()

# -------------------------------------
# Streamlit Page Config
# -------------------------------------
st.set_page_config(page_title="NDVI Monitoring – Karnataka", layout="wide")

st.title("🌱 NDVI Based Vegetation Monitoring in Karnataka")

st.markdown("""
### Purpose of the Study
To assess vegetation density and distribution across Karnataka using NDVI from Sentinel-2 satellite imagery.

### Background and Context
Vegetation monitoring is essential for agriculture management, forest conservation, and environmental planning.
Remote sensing combined with geospatial analytics enables large-scale and real-time observation of land conditions.

### Tools Used
Google Earth Engine, Sentinel-2 Imagery, NDVI, Geemap, Streamlit, ngrok
""")

# -------------------------------------
# Load Karnataka Boundary
# -------------------------------------
states = ee.FeatureCollection("FAO/GAUL/2015/level1")
karnataka = states.filter(ee.Filter.eq("ADM1_NAME", "Karnataka"))

# -------------------------------------
# Load Sentinel-2 Data
# -------------------------------------
collection = (
    ee.ImageCollection("COPERNICUS/S2_SR")
    .filterBounds(karnataka)
    .filterDate("2023-01-01", "2023-12-31")
    .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
)

# -------------------------------------
# NDVI Calculation
# -------------------------------------
def add_ndvi(image):
    ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")
    return image.addBands(ndvi)

ndvi_image = collection.map(add_ndvi).select("NDVI").median().clip(karnataka)

# -------------------------------------
# NDVI Classification
# -------------------------------------
dense = ndvi_image.gt(0.6)
moderate = ndvi_image.gt(0.4).And(ndvi_image.lte(0.6))
sparse = ndvi_image.gt(0.2).And(ndvi_image.lte(0.4))
nonveg = ndvi_image.lte(0.2)

# -------------------------------------
# STREAMLIT MAP SELECTOR
# -------------------------------------
st.subheader("🗺️ Interactive Maps")

map_option = st.selectbox(
    "Select Map Type",
    ["NDVI Continuous Heatmap", "NDVI Vegetation Classification"]
)

# -------------------------------------
# MAP 1: NDVI CONTINUOUS HEATMAP
# -------------------------------------
if map_option == "NDVI Continuous Heatmap":

    Map = geemap.Map(center=[15.3, 75.7], zoom=6)

    Map.addLayer(
        ndvi_image,
        {"min": -1, "max": 1, "palette": ["red", "yellow", "green"]},
        "NDVI Heatmap"
    )

    Map.addLayer(karnataka, {"color": "black"}, "Karnataka Boundary")
    Map.addLayerControl()
    Map.to_streamlit(height=650)

# -------------------------------------
# MAP 2: NDVI CLASSIFICATION MAP
# -------------------------------------
# -------------------------------------
# MAP 2: NDVI CLASSIFICATION + SAMPLE POINTS
# -------------------------------------
else:
    Map = geemap.Map(center=[15.3, 75.7], zoom=6)

    # Add NDVI classified regions
    Map.addLayer(dense.selfMask(), {"palette": "darkgreen"}, "Dense Vegetation")
    Map.addLayer(moderate.selfMask(), {"palette": "green"}, "Moderate Vegetation")
    Map.addLayer(sparse.selfMask(), {"palette": "orange"}, "Sparse Vegetation")
    Map.addLayer(nonveg.selfMask(), {"palette": "gray"}, "Built-up / Bare")
    Map.addLayer(karnataka, {"color": "black"}, "Karnataka Boundary")

    # -------------------------------------
    # CREATE SAMPLE NDVI POINTS
    # -------------------------------------
    points = ndvi_image.sample(
        region=karnataka,
        scale=1000,
        numPixels=300,
        geometries=True
    )

    # Classify points by NDVI value
    def classify_point(f):
        v = ee.Number(f.get("NDVI"))
        return f.set(
            "Class",
            ee.Algorithms.If(
                v.gt(0.6), "Dense",
                ee.Algorithms.If(
                    v.gt(0.4), "Moderate",
                    ee.Algorithms.If(
                        v.gt(0.2), "Sparse",
                        "Built-up"
                    )
                )
            )
        )

    points = points.map(classify_point)

    # Add colored point layers
    Map.addLayer(points.filter(ee.Filter.eq("Class", "Dense")),
                 {"color": "darkgreen"}, "Dense Points")

    Map.addLayer(points.filter(ee.Filter.eq("Class", "Moderate")),
                 {"color": "green"}, "Moderate Points")

    Map.addLayer(points.filter(ee.Filter.eq("Class", "Sparse")),
                 {"color": "orange"}, "Sparse Points")

    Map.addLayer(points.filter(ee.Filter.eq("Class", "Built-up")),
                 {"color": "red"}, "Built-up Points")

    Map.addLayerControl()
    Map.to_streamlit(height=650)


# -------------------------------------
# KEY FINDINGS
# -------------------------------------
st.markdown("""
### Key Findings
- The Western Ghats region of Karnataka exhibits dense vegetation due to forest reserves.
- Central Karnataka shows moderate vegetation dominated by agricultural land.
- Northern Karnataka and urban zones show sparse or non-vegetation areas.
- NDVI effectively differentiates vegetation health across diverse landscapes.
""")

# -------------------------------------
# RECOMMENDATIONS
# -------------------------------------
st.markdown("""
### Recommendations
- Government agencies can use NDVI monitoring for early detection of deforestation.
- Agricultural departments can apply NDVI analysis for crop health assessment.
- Urban planners can track vegetation loss due to city expansion.
- Seasonal NDVI tracking can help identify drought-prone regions.
- Integration with rainfall and soil data can improve environmental decision-making.
""")

# -------------------------------------
# FUTURE SCOPE
# -------------------------------------
st.markdown("""
### Future Research Directions
- Multi-temporal NDVI trend analysis across multiple years.
- District-wise vegetation statistics dashboards.
- Integration of Enhanced Vegetation Index (EVI).
- Machine learning-based land cover classification.
""")

