import streamlit as st
from transformers import pipeline
import PyPDF2
import io
import re
import os

# إعدادات الصفحة
st.set_page_config(
    page_title="ملخص المستندات الذكي",
    page_icon="📄",
    layout="wide"
)

st.title("📄 ملخص المستندات الذكي")
st.markdown("ارفع أي ملف نصي أو PDF، وهلخصه وأصنفه لك في ثواني!")

def clean_text(text):
    text = re.sub(r'[═─▄▀█░▒▓▔▕▖▗▘▙▚▛▜▝▞▟■□▢▣▤▥▦▧▨▩▪▫▬▭▮▯]', '', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'═+', '', text)
    text = re.sub(r'─+', '', text)
    return text.strip()

@st.cache_resource
def load_models():
    with st.spinner("⏳ جاري تحميل النماذج..."):
        os.environ["USE_TF"] = "1"
        os.environ["TRANSFORMERS_NO_TORCH"] = "1"
        classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
        summarizer = pipeline("text-generation", model="google/flan-t5-base")
    return summarizer, classifier

try:
    summarizer, classifier = load_models()
except Exception as e:
    st.error(f"❌ مشكلة في تحميل النماذج: {str(e)}")
    st.stop()

uploaded_file = st.file_uploader("📂 اختر ملف", type=["txt", "pdf"])

if uploaded_file is not None:
    try:
        if uploaded_file.type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
        else:
            text = uploaded_file.read().decode("utf-8")
    except Exception as e:
        st.error(f"❌ مش قادر أقرا الملف: {str(e)}")
        st.stop()
    
    clean_text_content = clean_text(text)
    
    with st.expander("📄 النص الأصلي"):
        st.text(clean_text_content[:1000] + ("..." if len(clean_text_content) > 1000 else ""))
    
    st.divider()
    st.subheader("📝 الملخص")
    
    if len(clean_text_content.split()) < 30:
        st.warning("⚠️ النص قصير جداً (أقل من 30 كلمة)")
        summary = clean_text_content
    else:
        with st.spinner("⏳ جاري تلخيص النص..."):
            try:
                prompt = f"Summarize this text in one short paragraph: {clean_text_content[:500]}"
                result = summarizer(prompt, max_new_tokens=100, do_sample=False)
                summary = result[0]['generated_text']
                st.success("✅ تم التلخيص!")
            except Exception as e:
                st.error(f"❌ خطأ: {str(e)}")
                summary = clean_text_content
    
    st.write(summary)
    
    st.divider()
    st.subheader("🏷️ التصنيف")
    
    with st.spinner("⏳ جاري تصنيف النص..."):
        try:
            labels = ["مالي", "طبي", "تقني", "قانوني", "تعليمي", "تسويقي", "سياسي", "اجتماعي", "رياضي"]
            result = classifier(clean_text_content[:1000], labels)
            label = result['labels'][0]
            score = result['scores'][0]
            st.success("✅ تم التصنيف!")
        except Exception as e:
            st.error(f"❌ خطأ: {str(e)}")
            label = "غير معروف"
            score = 0
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("التصنيف", label)
    with col2:
        st.metric("نسبة الثقة", f"{score:.2%}")
    
    st.divider()
    st.subheader("📊 إحصائيات")
    st.metric("عدد الكلمات", len(clean_text_content.split()))
    
    st.divider()
    report_text = f"""
    ═══════════════════════════════════════════════════════════════
                          📄 تقرير تلخيص المستند
    ═══════════════════════════════════════════════════════════════
    
    التصنيف: {label} (نسبة الثقة: {score:.2%})
    عدد الكلمات: {len(clean_text_content.split())}
    
    ═══════════════════════════════════════════════════════════════
    الملخص:
    ═══════════════════════════════════════════════════════════════
    
    {summary}
    
    ═══════════════════════════════════════════════════════════════
    النص الأصلي (مختصر):
    ═══════════════════════════════════════════════════════════════
    
    {clean_text_content[:500]}{'...' if len(clean_text_content) > 500 else ''}
    
    ═══════════════════════════════════════════════════════════════
    ✅ تم إنشاء التقرير بواسطة تطبيق ملخص المستندات الذكي
    ═══════════════════════════════════════════════════════════════
    """
    
    st.download_button(
        label="📥 تحميل التقرير",
        data=report_text,
        file_name="تقرير_المستند.txt",
        mime="text/plain"
    )

else:
    st.info("⏳ انتظر رفع ملف لتحليله")
    st.markdown("""
    ### 🚀 طريقة الاستخدام:
    1. اضغط على زر **"اختر ملف"**
    2. اختر ملف `.txt` أو `.pdf`
    3. انتظر لحظات وستظهر النتيجة
    4. يمكنك تحميل التقرير
    """)