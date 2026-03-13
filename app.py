import streamlit as st
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans
import colorsys
import io
import pandas as pd
from rembg import remove

# إعداد الصفحة
st.set_page_config(page_title="نظام ريفناس الذكي V2", layout="wide")

# دالة سحرية لحذف الخلفية واستخراج لون القماش فقط
def get_dominant_color_smart(pil_image, k=3):
    # 1. إزالة الخلفية باستخدام AI (تلقائياً سيركز على التوب)
    with st.spinner('جاري تحليل القماش وعزل الخلفية...'):
        img_array = np.array(pil_image)
        output_array = remove(img_array)
        img_no_bg = Image.fromarray(output_array).convert("RGBA")

    # 2. الحصول على بيانات البكسلات
    data = np.array(img_no_bg)
    
    # 3. استخراج البكسلات التي ليست شفافة (أي القماش فقط)
    # الفلتر هنا يختار البكسلات اللي الـ Alpha channel حقها أكبر من 0
    pixels = data[data[:, :, 3] > 0][:, :3]
    
    if len(pixels) == 0:
        return [255, 255, 255] # أبيض افتراضي في حال الفشل

    # 4. استخدام KMeans لتحديد اللون المسيطر داخل القماش فقط
    kmeans = KMeans(n_clusters=k, n_init='auto', random_state=42)
    kmeans.fit(pixels)
    
    # اختيار اللون الأكثر تكراراً (Dominant)
    counts = np.bincount(kmeans.labels_)
    dominant_rgb = kmeans.cluster_centers_[np.argmax(counts)].astype(int)
    
    return dominant_rgb

def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

def rgb_to_hsl(rgb):
    r, g, b = rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0
    h, s, l = colorsys.rgb_to_hls(r, g, b)
    return int(h * 360), int(s * 100), int(l * 100)

# واجهة المستخدم
st.markdown("<h1 style='text-align: center; color: #4B0082;'>ريفناس بيوتي (الإصدار الذكي V2)</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>نظام عزل الخلفية وتحديد لون القماش بدقة</p>", unsafe_allow_html=True)

uploaded_files = st.sidebar.file_uploader("ارفع صور التياب (سيتم عزل المانكان والخلفية آلياً)", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)

if uploaded_files:
    results = []
    for file in uploaded_files:
        img = Image.open(file)
        
        # استخراج اللون الذكي
        rgb = get_dominant_color_smart(img)
        hex_val = rgb_to_hex(rgb)
        h, s, l = rgb_to_hsl(rgb)
        
        results.append({
            'name': file.name,
            'image': img,
            'hex': hex_val,
            'h': h, 'l': l, 'rgb': rgb
        })

    # ترتيب النتائج لونياً
    sorted_results = sorted(results, key=lambda x: (x['h'], x['l']))

    # العرض في الموقع
    st.write("### الترتيب اللوني الدقيق بعد عزل الخلفية:")
    cols = st.columns(4)
    for idx, item in enumerate(sorted_results):
        with cols[idx % 4]:
            st.image(item['image'], use_column_width=True)
            st.markdown(f"<div style='background-color:{item['hex']}; height:20px; border-radius:5px;'></div>", unsafe_allow_html=True)
            st.write(f"اللون: {item['hex']}")
            st.write(f"الترتيب: {idx + 1}")

    # زر التحميل (Excel)
    df = pd.DataFrame([{ 'الترتيب': i+1, 'الاسم': r['name'], 'الكود': r['hex'] } for i, r in enumerate(sorted_results)])
    st.download_button("تحميل القائمة المرتبة", df.to_csv(index=False).encode('utf-8-sig'), "rifnas_order.csv", "text/csv")
else:
    st.info("ارفع الصور وسأقوم بحذف الخلفية والمانكان والتركيز على لون التوب فقط.")
