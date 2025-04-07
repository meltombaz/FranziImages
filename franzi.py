import os
import re
import numpy as np
import streamlit as st
import imageio.v2 as imageio
from collections import defaultdict
from skimage.transform import resize
from PIL import Image
import tempfile

st.set_page_config(page_title="TIFF Channel Overlay", layout="wide")
st.title("🔬 TIFF Channel Overlay Generator")

uploaded_files = st.file_uploader(
    "📤 Upload DAPI / EGFP / RFP TIFF files (e.g., random_DAPI_abcd1234efgh.tif)",
    type=["tif", "tiff"],
    accept_multiple_files=True
)

def get_channel_and_identifier(filename):
    """Extract channel and 12-char identifier from filename"""
    match = re.search(r"(DAPI|EGFP|GFP|RFP).*?([A-Za-z0-9]{12})\.tif{1,2}$", filename, re.IGNORECASE)
    if match:
        channel = match.group(1).upper()
        identifier = match.group(2)
        return channel, identifier
    return None, None

if uploaded_files:
    image_groups = defaultdict(dict)

    with tempfile.TemporaryDirectory() as temp_dir:
        st.write("📁 Processing in temporary workspace...")

        # Save uploaded files
        for uploaded in uploaded_files:
            save_path = os.path.join(temp_dir, uploaded.name)
            with open(save_path, "wb") as f:
                f.write(uploaded.read())

        # Group files by identifier
        for fname in os.listdir(temp_dir):
            if not fname.lower().endswith((".tif", ".tiff")):
                continue
            channel, identifier = get_channel_and_identifier(fname)
            if channel and identifier:
                file_path = os.path.join(temp_dir, fname)
                if 'DAPI' in channel:
                    image_groups[identifier]['blue'] = file_path
                elif 'EGFP' in channel or 'GFP' in channel:
                    image_groups[identifier]['green'] = file_path
                elif 'RFP' in channel:
                    image_groups[identifier]['red'] = file_path

        overlays = []

        for identifier, channels in image_groups.items():
            if not any(c in channels for c in ['red', 'green', 'blue']):
                continue

            # Load first channel to determine shape
            target_shape = None
            for c in channels.values():
                img = imageio.imread(c)
                if img.ndim == 3:
                    img = img[:, :, 0]
                target_shape = img.shape
                break

            rgb = np.zeros((*target_shape, 3), dtype=np.uint8)
            colored_channels = {}

            for color in ['red', 'green', 'blue']:
                if color in channels:
                    img = imageio.imread(channels[color])
                    if img.ndim == 3:
                        img = img[:, :, 0]
                    if img.shape != target_shape:
                        img = resize(img, target_shape, preserve_range=True, anti_aliasing=True)
                    img_norm = (img / img.max() * 255).astype(np.uint8)

                    channel_idx = {'red': 0, 'green': 1, 'blue': 2}[color]
                    rgb[:, :, channel_idx] = img_norm

                    # For display
                    channel_img = np.zeros((*target_shape, 3), dtype=np.uint8)
                    channel_img[:, :, channel_idx] = img_norm
                    colored_channels[color] = Image.fromarray(channel_img)

            # Save merged image
            merged_img = Image.fromarray(rgb)
            overlays.append((identifier, colored_channels, merged_img))

        st.success(f"✅ {len(overlays)} overlays generated!")

        for identifier, colored_channels, merged_image in overlays:
            st.markdown(f"### 🧪 `{identifier}`")
            cols = st.columns(4)
            for i, color in enumerate(['red', 'green', 'blue']):
                if color in colored_channels:
                    cols[i].image(colored_channels[color], caption=f"{color.upper()} Channel", use_container_width=True)
                else:
                    cols[i].markdown(f"❌ No {color.upper()} channel")
            cols[3].image(merged_image, caption="🧬 Merged Overlay", use_container_width=True)
else:
    st.info("👆 Upload TIFF files with names like `random_DAPI_abcd1234efgh.tif`, `random_EGFP_abcd1234efgh.tif`, etc.")
