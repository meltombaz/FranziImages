import os
import numpy as np
import streamlit as st
import imageio.v2 as imageio
from collections import defaultdict
from skimage.transform import resize
from PIL import Image
import tempfile

st.set_page_config(page_title="TIFF Channel Overlay", layout="wide")
st.title("🔬 TIFF Channel Overlay Generator")

uploaded_files = st.file_uploader("📤 Upload DAPI / EGFP / RFP TIFF files (e.g., DAPI_sample1.tif)", 
                                   type=["tif", "tiff"], 
                                   accept_multiple_files=True)

if uploaded_files:
    image_groups = defaultdict(dict)

    with tempfile.TemporaryDirectory() as temp_dir:
        st.write("📁 Processing in temporary workspace...")

        for uploaded in uploaded_files:
            save_path = os.path.join(temp_dir, uploaded.name)
            with open(save_path, "wb") as f:
                f.write(uploaded.read())

        for fname in os.listdir(temp_dir):
            if not fname.lower().endswith((".tif", ".tiff")):
                continue
            parts = fname.split('_', 1)
            if len(parts) != 2:
                continue
            channel, identifier_with_ext = parts
            identifier = os.path.splitext(identifier_with_ext)[0]
            channel = channel.upper()
            file_path = os.path.join(temp_dir, fname)

            if 'DAPI' in channel:
                image_groups[identifier]['blue'] = file_path
            elif 'EGFP' in channel or 'GFP' in channel:
                image_groups[identifier]['green'] = file_path
            elif 'RFP' in channel:
                image_groups[identifier]['red'] = file_path

        overlays = []

        for identifier, channels in image_groups.items():
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

                    # For preview of individual channels
                    color_img = np.zeros((*target_shape, 3), dtype=np.uint8)
                    color_img[:, :, channel_idx] = img_norm
                    colored_channels[color] = Image.fromarray(color_img)

            # Save merged overlay
            merged_path = os.path.join(temp_dir, f"{identifier}_overlay.png")
            imageio.imwrite(merged_path, rgb)
            overlays.append((identifier, merged_path, colored_channels, Image.fromarray(rgb)))

        st.success(f"✅ {len(overlays)} overlays generated!")

        for identifier, merged_path, colored_channels, merged_image in overlays:
            st.markdown(f"### 🧪 `{identifier}`")
            cols = st.columns(4)

            for i, color in enumerate(['red', 'green', 'blue']):
                if color in colored_channels:
                    cols[i].image(colored_channels[color], caption=f"{color.upper()} Channel", use_container_width=True)

            cols[-1].image(merged_image, caption="🧬 Merged Overlay", use_container_width=True)

            with open(merged_path, "rb") as f:
                st.download_button(
                    label=f"💾 Download Merged: {identifier}_overlay.png",
                    data=f.read(),
                    file_name=f"{identifier}_overlay.png",
                    mime="image/png"
                )
else:
    st.info("👆 Upload TIFF files with names like `DAPI_sample1.tif`, `EGFP_sample1.tif`, etc.")
