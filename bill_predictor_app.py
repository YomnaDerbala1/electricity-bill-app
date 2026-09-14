import streamlit as st
import pandas as pd
import numpy as np
import joblib

st.set_page_config(page_title="توقع فاتورة الكهرباء", layout="centered")

# =========================================================
# الخلفية (نفس روح تصميم الصورة: أزرق داكن + خطوط دوائر إلكترونية)
# لو حابة الخلفية الأصلية بالظبط: اعملي فولدر باسم static جوه فولدر
# التطبيق، حطي فيه الصورة باسم background.png، وفكي التعليق عن
# السطر التاني في الـ CSS وامسحي أول تدرج لوني.
# =========================================================
st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at 15% 10%, rgba(255,170,60,0.10), transparent 25%),
            radial-gradient(circle at 90% 15%, rgba(60,140,255,0.12), transparent 30%),
            linear-gradient(135deg, #04101f 0%, #071b33 45%, #0a2540 100%);
        background-attachment: fixed;
    }
    /* static/background.png:
    .stApp { background: url("app/static/background.png") no-repeat center center fixed; background-size: cover; }
    */
    h1, h2, h3, p, label, .stMarkdown, span {
        color: #eaf2ff !important;
    }
    .block-container {
        background: rgba(4, 16, 31, 0.55);
        border-radius: 16px;
        padding: 2rem 2.5rem;
        border: 1px solid rgba(90, 160, 255, 0.25);
    }
    div[data-baseweb="select"] > div, .stNumberInput input, .stSlider {
        background-color: rgba(255,255,255,0.06) !important;
        color: #eaf2ff !important;
    }
    .stButton button {
    background: linear-gradient(90deg, #1d6fd6, #0a4a99);
    color: white;
    border: none;
    font-weight: 600;
    } div[data-baseweb="slider"] div[role="slider"] {
        background-color: #1d6fd6 !important;
        border-color: #1d6fd6 !important;
    }
    div[data-baseweb="slider"] > div > div {
        background-color: #1d6fd6 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("توقع فاتورة الكهرباء الشهرية")
st.write("دخّلي بيانات الأسرة، وهيتوقع الموديل الفاتورة القادمة.")

# =========================================================
# تحميل الموديل (Pipeline كامل: معالجة + موديل، مدرّب على بيانات السنتين)
# =========================================================
@st.cache_resource
def load_model():
    return joblib.load("electricity_bill_model.pkl")

model = load_model()

# نفس أسماء الأعمدة الخام بالظبط زي ما استخدمناها في تدريب الـ Pipeline
numeric_features = [
    "usage_1", "usage_2", "usage_3", "bill_1", "bill_2", "bill_3", "usage_avg3",
    "حجم الأسرة", "عدد الأجهزة الكهربائية الكبيرة", "درجة الحرارة المتوسطة (م)",
    "عدد الغرف", "هل_ذروة_صيف", "month_sin", "month_cos",
    "عدد مرات انقطاع الكهرباء",
]
categorical_features = ["فئة الدخل", "يوجد تكييف", "نوع السكن", "المحافظة"]

st.subheader("استهلاك وفاتورة آخر 3 شهور")
col1, col2, col3 = st.columns(3)
with col1:
    usage_1 = st.number_input("استهلاك آخر شهر (ك.و)", min_value=0, value=300)
    bill_1 = st.number_input("فاتورة آخر شهر (جنيه)", min_value=0.0, value=380.0)
with col2:
    usage_2 = st.number_input("استهلاك شهرين قبل (ك.و)", min_value=0, value=280)
    bill_2 = st.number_input("فاتورة شهرين قبل (جنيه)", min_value=0.0, value=350.0)
with col3:
    usage_3 = st.number_input("استهلاك 3 شهور قبل (ك.و)", min_value=0, value=270)
    bill_3 = st.number_input("فاتورة 3 شهور قبل (جنيه)", min_value=0.0, value=340.0)

st.subheader("بيانات الأسرة")
col4, col5 = st.columns(2)
with col4:
    family_size = st.slider("حجم الأسرة", 1, 8, 4)
    appliance_count = st.slider("عدد الأجهزة الكهربائية الكبيرة", 1, 8, 3)
    rooms = st.slider("عدد الغرف", 2, 10, 4)
    outage_count = st.slider("عدد مرات انقطاع الكهرباء المتوقعة", 0, 6, 1)
with col5:
    avg_temp = st.slider("درجة الحرارة المتوقعة (°م)", 10, 45, 28)
    income_level = st.selectbox("فئة الدخل", ["محدود الدخل", "متوسط", "فوق المتوسط", "مرتفع"])
    housing_type = st.selectbox("نوع السكن", ["شقة", "فيلا", "دور في منزل"])
    governorate = st.selectbox("المحافظة", ["القاهرة", "الجيزة", "الإسكندرية", "الشرقية", "الدقهلية", "أسيوط", "المنوفية"])

col6, col7 = st.columns(2)
with col6:
    has_ac = st.checkbox("يوجد تكييف", value=True)
with col7:
    target_month = st.selectbox(
        "الشهر المطلوب توقع فاتورته",
        list(range(1, 13)),
        index=6,
        format_func=lambda m: ["يناير","فبراير","مارس","أبريل","مايو","يونيو",
                                "يوليو","أغسطس","سبتمبر","أكتوبر","نوفمبر","ديسمبر"][m-1],
    )

if st.button("توقع الفاتورة"):
    is_summer_peak = 1 if target_month in [6, 7, 8] else 0
    month_sin = np.sin(2 * np.pi * target_month / 12)
    month_cos = np.cos(2 * np.pi * target_month / 12)

    raw_row = {
        "usage_1": usage_1, "usage_2": usage_2, "usage_3": usage_3,
        "bill_1": bill_1, "bill_2": bill_2, "bill_3": bill_3,
        "usage_avg3": (usage_1 + usage_2 + usage_3) / 3,
        "حجم الأسرة": family_size,
        "عدد الأجهزة الكهربائية الكبيرة": appliance_count,
        "درجة الحرارة المتوسطة (م)": avg_temp,
        "عدد الغرف": rooms,
        "هل_ذروة_صيف": is_summer_peak,
        "month_sin": month_sin,
        "month_cos": month_cos,
        "عدد مرات انقطاع الكهرباء": outage_count,
        "فئة الدخل": income_level,
        "يوجد تكييف": "نعم" if has_ac else "لا",
        "نوع السكن": housing_type,
        "المحافظة": governorate,
    }

    row_df = pd.DataFrame([raw_row])[numeric_features + categorical_features]

    # الـ Pipeline بيتكفل بكل حاجة (Imputation + Encoding + التنبؤ) في خطوة واحدة
    prediction = model.predict(row_df)[0]

    st.success(f"الفاتورة المتوقعة: {prediction:.2f} جنيه")
