import os
import numpy as np
import streamlit as st
import imageio.v2 as imageio
from glob import glob
from collections import defaultdict
from skimage.transform import resize
from PIL import Image

st.title("🔬 TIFF Channel Overlay Generator")

# Folder uploader
folder = st.text_input("📂 Enter full path to folder with TIFF files:", "")

if folder and os.path.exists(folder):
    tif_files = sorted(glob(os.path.join(folder, "*.tif")))

    if not tif_files:
        st.warning("No .tif files found in the selected folder.")
    else:
        image_groups = defaultdict(dict)

        for file in tif_files:
            fname = os.path.basename(file)
            parts = fname.split('_', 1)
            if len(parts) != 2:
                continue  # skip if format doesn't match

            channel, identifier_with_ext = parts
            identifier = os.path.splitext(identifier_with_ext)[0]
            channel = channel.upper()

            if 'DAPI' in channel:
                image_groups[identifier]['blue'] = file
            elif 'EGFP' in channel or 'GFP' in channel:
                image_groups[identifier]['green'] = file
            elif 'RFP' in channel:
                image_groups[identifier]['red'] = file

        # Output folder
        output_folder = os.path.join(folder, "merged_overlays")
        os.makedirs(output_folder, exist_ok=True)

        merged_images = []

        for identifier, channels in image_groups.items():
            # Determine image shape
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

            out_path = os.path.join(output_folder, f"{identifier}_overlay.png")
            imageio.imwrite(out_path, rgb)
            merged_images.append((identifier, out_path))

        st.success(f"✅ Done! {len(merged_images)} overlays saved to: {output_folder}")

        with st.expander("📸 Preview Merged Images"):
            for identifier, path in merged_images:
                st.image(Image.open(path), caption=f"{identifier}_overlay", use_column_width=True)

else:
    st.info("👆 Please enter a valid folder path.")
