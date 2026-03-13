import streamlit as st
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans
import colorsys
import io
import pandas as pd
from rembg import remove

# إعداد الصفحة
st.set_page_config(page_title="ريفناس بيوتي V2.1", layout="wide")

# قاموس الألوان السودانية الأساسي
COLOR_NAMES = {
    "Red": "أحمر", "Blue": "أزرق", "Green": "أخضر", "Yellow": "أصفر",
    "Pink": "بمبي", "Purple": "بنفسجي", "Brown": "بني", "Black": "أسود",
    "White": "أبيض", "Gray": "رمادي", "Orange": "برتقالي", "Teal": "جنزاري"
}

def get_dominant_color_smart(pil_image, k=3):
    img_array = np.array(pil_image)
    output_array = remove(img_array)
    img_no_bg = Image.fromarray(output_array).convert("RGBA")
    data = np.array(img_no_bg)
    pixels = data[data[:, :, 3] > 0][:, :3]
    
    if len(pixels) == 0: return [255, 255, 255]
    
    kmeans = KMeans(n_clusters=k, n_init='auto', random_state=42)
    kmeans.fit(pixels)
    counts = np.bincount(kmeans.labels_)
    dominant_rgb = kmeans.cluster_centers_[np.argmax(counts)].astype(int)
    return dominant_rgb

def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

def rgb_to_hsl(rgb):
    r, g, b = rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0
    h, s, l = colorsys.rgb_to_hls(r, g, b)
    return int(h * 360), int(s * 100), int(l * 100)

# دالة ذكية لتحديد اسم اللون بناءً على الـ HSL
def identify_color_name(h, s, l):
    if l < 15: return "أسود ملكي"
    if l > 85: return "أبيض ناصع"
    if s < 15: return "رمادي"
    
    if h < 15 or h > 345: return "أحمر / خمري"
    if 15 <= h < 45: return "برتقالي / بصلي"
    if 45 <= h < 75: return "أصفر / ذهبي"
    if 75 <= h < 155: return "أخضر / خضاري"
    if 155 <= h < 195: return "جنزاري / فيروزي"
    if 195 <= h < 255: return "أزرق / كحلي"
    if 255 <= h < 315: return "بنفسجي / ليلكي"
    if 315 <= h < 345: return "بمبي / وردي"
    return "لون مختلط"

st.markdown("<h1 style='text-align: center; color: #4B0082;'>ريفناس بيوتي: محلل الألوان الذكي</h1>", unsafe_allow_html=True)

uploaded_files = st.sidebar.file_uploader("ارفع صور التياب", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)

if uploaded_files:
    results = []
    for file in uploaded_files:
        img = Image.open(file)
        rgb = get_dominant_color_smart(img)
        hex_val = rgb_to_hex(rgb)
        h, s, l = rgb_to_hsl(rgb)
        color_name = identify_color_name(h, s, l)
        
        results.append({
            'name': file.name, 'image': img, 'hex': hex_val,
            'h': h, 'l': l, 'color_name': color_name
        })

    sorted_results = sorted(results, key=lambda x: (x['h'], x['l']))

    st.write("### الترتيب اللوني مع أسماء الألوان:")
    cols = st.columns(4)
    for idx, item in enumerate(sorted_results):
        with cols[idx % 4]:
            st.image(item['image'], use_column_width=True)
            st.markdown(f"<div style='background-color:{item['hex']}; height:10px; border-radius:5px;'></div>", unsafe_allow_html=True)
            st.markdown(f"**اللون:** {item['color_name']}")
            st.code(item['hex'])
            st.write(f"الترتيب: {idx + 1}")

    df = pd.DataFrame([{ 'الترتيب': i+1, 'اسم اللون': r['color_name'], 'الكود': r['hex'] } for i, r in enumerate(sorted_results)])
    st.download_button("تحميل القائمة النهائية (Excel)", df.to_csv(index=False).encode('utf-8-sig'), "rifnas_final_order.csv", "text/csv")
