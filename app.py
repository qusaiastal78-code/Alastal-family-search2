import streamlit as st
import pandas as pd
from PIL import Image
import os

# --- إعدادات الصفحة ---
st.set_page_config(
    page_title="مجلس عائلة الأسطل - نظام البحث",
    page_icon="🔍",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- تصميم الواجهة لتدعم اللغة العربية (RTL) ---
st.markdown("""
    <style>
    .main {
        direction: rtl;
        text-align: right;
    }
    h1, h2, h3, p, div, input, label, .stTextInput > label {
        font-family: 'Tajawal', sans-serif;
        text-align: right;
        width: 100%;
    }
    .stAlert {
        direction: rtl;
        text-align: right;
    }
    div[data-testid="stCaptionContainer"] {
        text-align: right;
    }
    /* تنسيق الجدول */
    .dataframe {
        width: 100%;
        text-align: right !important;
    }
    /* تنسيق الفوتر */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f1f1f1;
        color: #333;
        text-align: center;
        padding: 10px;
        font-size: 14px;
        border-top: 2px solid #ddd;
        z-index: 1000;
    }
    /* إخفاء القائمة الافتراضية */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- تحميل البيانات ---
@st.cache_data
def load_data():
    try:
        # قراءة الملف - يرجى التأكد من أن اسم الملف هنا مطابق لاسم الملف بجانب الكود
        # يفضل تغيير اسم ملف الاكسل إلى data.csv لسهولة القراءة
        df = pd.read_csv("data.csv") 
        
        # تنظيف أسماء الأعمدة
        df.columns = df.columns.str.replace('\n', ' ').str.strip()
        
        # تحويل رقم الهوية إلى نص
        if 'رقم الهوية' in df.columns:
            df['رقم الهوية'] = df['رقم الهوية'].astype(str).str.replace('.0', '', regex=False)
        
        return df
    except Exception as e:
        st.error(f"حدث خطأ أثناء تحميل ملف البيانات. تأكد أن اسم الملف هو data.csv: {e}")
        return None

df = load_data()

# --- ترويسة الصفحة والشعار ---
col1, col2 = st.columns([1, 4])

with col1:
    logo_path = "logo.jpg"  # تأكد أن اسم صورة الشعار هو logo.jpg
    if os.path.exists(logo_path):
        image = Image.open(logo_path)
        st.image(image, width=110)
    else:
        st.write("شعار العائلة")

with col2:
    st.title("مجلس عائلة الأسطل")
    st.markdown("### نظام الاستعلام عن بيانات أبناء العائلة")

st.markdown("---")

# --- واجهة البحث ---
st.markdown("#### 🔎 أدخل رقم الهوية للبحث:")
id_query = st.text_input("رقم الهوية", placeholder="مثال: 80xxxxxxx", label_visibility="collapsed")

# تحديد الأعمدة المطلوبة للعرض مع أسمائها المحسنة
columns_mapping = {
    'رقم الهوية': 'رقم الهوية',
    'الاسم': 'الاسم الرباعي',
    'رقم الهاتف': 'رقم الجوال',
    'الفرع': 'الفرع',
    'الحالة الاجتماعية': 'الحالة الاجتماعية',
    'عدد افراد الاسرة': 'عدد الأفراد',
    'هوية الزوجة 1': 'هوية الزوج/ة'
}

if id_query:
    if df is not None:
        # البحث
        result = df[df['رقم الهوية'] == id_query]
        
        if not result.empty:
            st.success("✅ تم العثور على السجل")
            
            # تجهيز البيانات للعرض
            row = result.iloc[0]
            display_data = {}
            missing_fields = []
            
            for col_db, col_display in columns_mapping.items():
                if col_db in df.columns:
                    val = row[col_db]
                    display_data[col_display] = val
                    
                    # التحقق من النواقص (استثناء هوية الزوج/ة إذا كان الشخص أعزب مثلاً يمكن تعديل الشرط)
                    # هنا نعتبر أي خانة فارغة نقصاً، عدا هوية الزوجة قد تكون اختيارية حسب الحالة
                    if pd.isna(val) or str(val).strip() == "" or str(val).strip().lower() == "nan":
                         # نعتبر الفرع ورقم الهاتف والاسم أساسيات
                         if col_db in ['الفرع', 'رقم الهاتف', 'الاسم', 'الحالة الاجتماعية']:
                             missing_fields.append(col_display)
            
            # عرض الجدول بشكل عمودي منسق
            st.table(pd.DataFrame(display_data.items(), columns=['البيان', 'القيمة']))
            
            # --- التنبيه عند نقص البيانات ---
            if missing_fields:
                st.markdown(f"""
                <div style="background-color: #fff0f0; padding: 20px; border-radius: 10px; border-right: 5px solid #ff3333; margin-top: 20px;">
                    <h4 style="color: #cc0000; margin:0;">⚠️ تنبيه: بيانات ناقصة!</h4>
                    <p style="color: #555; font-size:16px;">يرجى استكمال البيانات التالية: <b>{', '.join(missing_fields)}</b></p>
                    <hr>
                    <p style="color: #333; font-weight: bold;">
                        يرجى سرعة التواصل مع السيد/ م. أيمن ناجي الأسطل<br>
                        لتزويده بالبيانات الناقصة لإكمال السجل.
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("✨ جميع البيانات الأساسية مكتملة لهذا السجل.")
                
        else:
            st.warning(f"لم يتم العثور على أي سجل برقم الهوية: {id_query}")

# --- مسافة فارغة للفوتر ---
st.write("<br><br><br>", unsafe_allow_html=True)

# --- الفوتر ---
st.markdown("""
    <div class="footer">
        جميع الحقوق محفوظة لمجلس عائلة الأسطل © 2025<br>
        تم إنشاء وتطوير هذا الموقع بواسطة: <strong style="color:#004d00;">السيد قصي صبحي الأسطل</strong>
    </div>
    """, unsafe_allow_html=True)