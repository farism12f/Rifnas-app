import streamlit as st
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans
import colorsys
import io
import pandas as pd

# إعداد الصفحة
st.set_page_config(page_title="نظام ريفناس الذكي لتنسيق التياب", layout="wide")

# دالة لاستخراج اللون المسيطر باستخدام K-Means
def get_dominant_color(pil_image, k=3):
    # تحويل الصورة إلى Numpy array وتصغيرها لتسريع المعالجة
    img = pil_image.convert('RGB')
    img.thumbnail((100, 100))
    img_data = np.array(img)
    
    # تحويل البيانات إلى تنسيق 2D
    pixels = img_data.reshape(-1, 3)
    
    # تطبيق K-Means لتجميع الألوان
    kmeans = KMeans(n_clusters=k, n_init='auto', random_state=42)
    kmeans.fit(pixels)
    
    # الحصول على الألوان المسيطرة (المراكز) وحساب حجم كل تجميع
    colors = kmeans.cluster_centers_
    labels = kmeans.labels_
    label_counts = np.bincount(labels)
    total_count = len(labels)
    
    # ترتيب الألوان حسب حجم التجميع (الأكثر شيوعاً أولاً)
    sorted_indices = np.argsort(label_counts)[::-1]
    dominant_color_rgb = colors[sorted_indices[0]].astype(int)
    
    return dominant_color_rgb

# دالة لتحويل RGB إلى كود Hex
def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

# دالة لتحويل RGB إلى HSL للترتيب المنطقي
def rgb_to_hsl(rgb):
    r, g, b = rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0
    h, s, l = colorsys.rgb_to_hls(r, g, b)
    # تعديل الـ Hue ليكون بين 0 و 360، والـ L و S بين 0 و 100
    return int(h * 360), int(s * 100), int(l * 100)

# واجهة المستخدم
st.markdown("<h1 style='text-align: center; color: #4B0082;'>ريفناس بيوتي: نظام التنسيق الذكي للتياب السودانية</h1>", unsafe_allow_html=True)
st.write("---")

st.sidebar.header("الإعدادات")
uploaded_files = st.sidebar.file_uploader("ارفع صور التياب هنا (يمكن رفع عدة صور)", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)

if uploaded_files:
    data_list = []
    
    # معالجة الصور المرفوعة
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, file in enumerate(uploaded_files):
        status_text.text(f"معالجة الصورة: {file.name}")
        img = Image.open(file)
        
        # استخراج البيانات
        dom_rgb = get_dominant_color(img)
        hex_code = rgb_to_hex(dom_rgb)
        hue, sat, light = rgb_to_hsl(dom_rgb)
        
        data_list.append({
            'file_name': file.name,
            'image': img,
            'dominant_rgb': dom_rgb,
            'hex_code': hex_code,
            'hue': hue,
            'saturation': sat,
            'lightness': light
        })
        
        progress_bar.progress((i + 1) / len(uploaded_files))
    
    progress_bar.empty()
    status_text.empty()
    
    # خوارزمية الترتيب الذكي (حسب الـ Hue أولاً، ثم الـ Lightness)
    sorted_data = sorted(data_list, key=lambda x: (x['hue'], x['lightness']))
    
    st.markdown("### الترتيب المقترح للرف (من اليسار إلى اليمين):")
    
    # عرض الصور المرتبة في صفوف
    images_per_row = 6
    for i in range(0, len(sorted_data), images_per_row):
        cols = st.columns(images_per_row)
        for j in range(images_per_row):
            if i + j < len(sorted_data):
                item = sorted_data[i + j]
                # تصغير الصورة للعرض
                display_img = item['image'].copy()
                display_img.thumbnail((300, 300))
                
                with cols[j]:
                    st.image(display_img, use_column_width=True)
                    st.markdown(f"<div style='background-color:{item['hex_code']}; width:30px; height:30px; border-radius:50%; display:inline-block; margin-right:5px; vertical-align:middle;'></div><span style='color:{item['hex_code']}'>{item['hex_code']}</span>", unsafe_allow_html=True)
                    st.write(f"الترتيب اللوني: {i+j+1}")
    
    st.write("---")
    
    # تصدير البيانات إلى ملف Excel
    st.markdown("### تصدير بيانات الرف:")
    
    export_data = []
    for i, item in enumerate(sorted_data):
        export_data.append({
            'ترتيب الرف': i + 1,
            'اسم الصورة': item['file_name'],
            'كود اللون (Hex)': item['hex_code'],
            'صبغة اللون (Hue)': item['hue'],
            'الإضاءة (Lightness)': item['lightness'],
            'التسعيرة المقترحة (مثال)': f"{50000 + i*1000} SDG" # مثال لتسعيرة ديناميكية
        })
    
    df = pd.DataFrame(export_data)
    
    # دالة لتحميل ملف Excel
    def to_excel(df):
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, index=False, sheet_name='Sheet1')
        writer.close()
        processed_data = output.getvalue()
        return processed_data

    excel_data = to_excel(df)
    st.download_button(label="تحميل قائمة الرف (Excel)", data=excel_data, file_name='revnas_shaila_config.xlsx', mime='application/vnd.ms-excel')

else:
    st.info("قم برفع صور التياب من القائمة الجانبية للبدء.")

