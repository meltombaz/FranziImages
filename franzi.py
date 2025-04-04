import os
import numpy as np
import streamlit as st
import imageio.v2 as imageio
from collections import defaultdict
from skimage.transform import resize
from PIL import Image
import tempfile

st.set_page_config(page_title="TIFF Channel Overlay", layout="centered")
st.title("🔬 TIFF Channel Overlay Generator")

uploaded_files = st.file_uploader("📤 Upload your DAPI / EGFP / RFP TIFF files", 
                                   type=["tif", "tiff"], 
                                   accept_multiple_files=True)

if uploaded_files:
    image_groups = defaultdict(dict)

    with tempfile.TemporaryDirectory() as temp_dir:
        st.write(f"📁 Working in temporary directory...")

        # Save uploaded files temporarily
        for uploaded in uploaded_files:
            save_path = os.path.join(temp_dir, uploaded.name)
            with open(save_path, "wb") as f:
                f.write(uploaded.read())

        # Parse and group
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

            for color in ['red', 'green', 'blue']:
                if color in channels:
                    img = imageio.imread(channels[color])
                    if img.ndim == 3:
                        img = img[:, :, 0]
                    if img.shape != target_shape:
                        img = resize(img, target_shape, preserve_range=True, anti_aliasing=True)
                    img = (img / img.max() * 255).astype(np.uint8)
                    channel_idx = {'red': 0, 'green': 1, 'blue': 2}[color]
                    rgb[:, :, channel_idx] = img

            out_path = os.path.join(temp_dir, f"{identifier}_overlay.png")
            imageio.imwrite(out_path, rgb)
            overlays.append((identifier, out_path))

        st.success(f"✅ {len(overlays)} overlays generated!")

        for identifier, path in overlays:
            st.image(Image.open(path), caption=f"{identifier}_overlay", use_column_width=True)
            with open(path, "rb") as f:
                st.download_button(
                    label=f"💾 Download {identifier}_overlay.png",
                    data=f.read(),
                    file_name=f"{identifier}_overlay.png",
                    mime="image/png"
                )
else:
    st.info("👆 Upload at least two or more TIFF images (named like DAPI_*, EGFP_*, RFP_*)")
