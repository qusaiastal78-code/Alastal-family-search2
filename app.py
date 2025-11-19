import streamlit as st
import pandas as pd
from PIL import Image
import os
import io

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
    /* تطبيق خطوط عربية حديثة على جميع العناصر النصية */
    h1, h2, h3, h4, p, div, input, label, .stTextInput > label, 
    div[data-testid="stCaptionContainer"], table, th, td {
        font-family: 'Tahoma', 'Arial', sans-serif;
        text-align: right;
        width: 100%;
    }
    .stAlert {
        direction: rtl;
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

# --- تحميل ومعالجة البيانات ---
@st.cache_data
def load_data():
    """
    تحميل الملف بطريقة مرنة لحل مشاكل الترميز وتسمية الأعمدة (KeyError).
    """
    df = None
    # قائمة بالتشفيرات المحتملة للملفات العربية
    encodings_to_try = ['utf-8', 'utf-8-sig', 'windows-1256', 'iso-8859-6']
    file_name = "data.csv" # الاسم المتوقع للملف
    
    # 1. محاولة قراءة الملف بالترميزات المختلفة
    for encoding in encodings_to_try:
        try:
            # استخدام محرك بايثون لتجاهل الأسطر المعيبة
            df = pd.read_csv(
                file_name, 
                encoding=encoding, 
                on_bad_lines='skip', 
                engine='python' 
            )
            break
        except Exception: 
            continue
            
    if df is None:
        st.error("فشل قراءة الملف بجميع الترميزات. يرجى التأكد من سلامة ملف data.csv")
        return None

    try:
        # 2. تنظيف أسماء الأعمدة وحل مشكلة KeyError
        
        # تنظيف شامل لإزالة المسافات والأسطر الجديدة من جميع أسماء الأعمدة
        df.columns = df.columns.astype(str).str.replace('\n', ' ').str.strip()
        
        # 💡 التعديل الجديد: تحديد قائمة بأسماء الأعمدة المحتملة لرقم الهوية الأساسي
        possible_id_columns = ['رقم الهوية', 'هوية', 'هوية الزوجة 1', 'الرقم', 'ID', 'id']
        id_column_name = None
        
        # البحث عن اسم العمود الفعلي ضمن القائمة المحتملة
        for col in df.columns:
            cleaned_col = col.strip()
            # البحث عن تطابق دقيق أو جزئي
            if cleaned_col in possible_id_columns or 'هوية' in cleaned_col:
                id_column_name = col
                break
        
        if id_column_name is None:
             st.error("لم يتم العثور على أي عمود يمثل 'رقم الهوية' في ملف البيانات. يرجى مراجعة عناوين الأعمدة في ملف Excel وتسمية عمود الهوية بـ 'رقم الهوية'.")
             return None

        # إعادة تسمية العمود الذي وجدناه إلى 'رقم الهوية' ليتطابق مع باقي الكود
        if id_column_name != 'رقم الهوية':
             df.rename(columns={id_column_name: 'رقم الهوية'}, inplace=True)
        
        # 3. معالجة البيانات
        
        # التأكد من تحويل رقم الهوية إلى نص وإزالة أي فواصل عشرية (مثل .0)
        df['رقم الهوية'] = df['رقم الهوية'].astype(str).str.replace('.0', '', regex=False).str.strip()
            
        return df
    except Exception as e:
        st.error(f"حدث خطأ أثناء معالجة البيانات: {e}")
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
        # استخدام placeholder في حالة عدم وجود الصورة
        st.markdown('<div style="text-align:center; height:110px; line-height:110px; border: 1px solid #ccc;">شعار العائلة</div>', unsafe_allow_html=True)

with col2:
    st.title("مجلس عائلة الأسطل")
    st.markdown("### نظام الاستعلام عن بيانات أبناء العائلة")

st.markdown("---")

# --- واجهة البحث ---
st.markdown("#### 🔎 أدخل رقم الهوية للبحث:")
id_query = st.text_input("رقم الهوية", placeholder="مثال: 80xxxxxxx", label_visibility="collapsed").strip()

# تحديد الأعمدة المطلوبة للعرض مع أسمائها المحسنة في الواجهة
columns_mapping = {
    'رقم الهوية': 'رقم الهوية',
    'الاسم': 'الاسم الكامل',
    'رقم الهاتف': 'رقم الجوال',
    'الفرع': 'الفرع',
    'الحالة الاجتماعية': 'الحالة الاجتماعية',
    'عدد افراد الاسرة': 'عدد الأفراد',
    'هوية الزوجة 1': 'هوية الزوج/ة الأولى'
}

if id_query:
    if df is not None:
        # البحث في عمود 'رقم الهوية'
        result = df[df['رقم الهوية'] == id_query]
        
        if not result.empty:
            st.success("✅ تم العثور على السجل")
            
            # تجهيز البيانات للعرض
            row = result.iloc[0]
            display_data = {}
            missing_fields = []
            
            # الأعمدة الأساسية التي يجب أن تكون موجودة ولا تُعتبر اختيارية
            required_fields = ['الاسم', 'رقم الهاتف', 'الفرع', 'الحالة الاجتماعية', 'عدد افراد الاسرة']
            
            # إعادة بناء قائمة الأعمدة لتأكيد وجودها قبل العرض
            current_columns = df.columns.tolist()
            
            for col_db, col_display in columns_mapping.items():
                
                # المعالجة الخاصة لعمود الهوية الرئيسي
                if col_db == 'رقم الهوية':
                    if 'رقم الهوية' in current_columns:
                        display_data[col_display] = row['رقم الهوية']
                    continue

                # المعالجة للأعمدة الأخرى
                if col_db in current_columns:
                    val = row[col_db]
                    display_data[col_display] = val
                    
                    # التحقق من النواقص للبيانات الأساسية فقط
                    is_missing = pd.isna(val) or (isinstance(val, str) and val.strip() == "") or str(val).strip().lower() == "nan"
                    
                    if is_missing and col_db in required_fields:
                         missing_fields.append(col_display)
                elif col_db in required_fields:
                    # إذا كان العمود الأساسي مفقوداً من الملف أصلاً
                    missing_fields.append(col_display)


            # عرض الجدول بشكل عمودي منسق
            data_to_display = pd.DataFrame(display_data.items(), columns=['البيان', 'القيمة'])
            st.table(data_to_display)
            
            # --- التنبيه عند نقص البيانات ---
            if missing_fields:
                st.markdown(f"""
                <div style="background-color: #fff0f0; padding: 20px; border-radius: 10px; border-right: 5px solid #ff3333; margin-top: 20px;">
                    <h4 style="color: #cc0000; margin:0;">⚠️ تنبيه: بيانات ناقصة!</h4>
                    <p style="color: #555; font-size:16px;">يرجى استكمال البيانات التالية: <b>{', '.join(missing_fields)}</b></p>
                    <hr>
                    <p style="color: #333; font-weight: bold;">
                        يرجى سرعة التواصل مع <strong style="color:#004d00;">السيد/ م. أيمن ناجي الأسطل</strong><br>
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

# --- الفوتر (حقوق الملكية) ---
st.markdown("""
    <div class="footer">
        جميع الحقوق محفوظة لمجلس عائلة الأسطل © 2025<br>
        تم إنشاء وتطوير هذا الموقع بواسطة: <strong style="color:#004d00;">السيد قصي صبحي الأسطل</strong>
    </div>
    """, unsafe_allow_html=True)