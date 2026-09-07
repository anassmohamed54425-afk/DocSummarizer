import streamlit as st
from transformers import pipeline
import PyPDF2
import io
import re
from docx import Document
import datetime

st.set_page_config(page_title="ملخص المستندات الذكي", page_icon="📄", layout="wide")

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #4A6CF7, #6C4AF7);
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        color: white;
        margin-bottom: 30px;
    }
    .result-card {
        background: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin: 20px 0;
        border-right: 6px solid #4A6CF7;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1 style="font-size: 40px; margin: 0;">📄 ملخص المستندات الذكي</h1>
    <p style="font-size: 18px; opacity: 0.9; margin: 10px 0 0;">
        رفع ملف، تلخيص، تصنيف، وتقرير PDF
    </p>
</div>
""", unsafe_allow_html=True)

def clean_text(text):
    text = re.sub(r'[═─▄▀█░▒▓▔▕▖▗▘▙▚▛▜▝▞▟■□▢▣▤▥▦▧▨▩▪▫▬▭▮▯]', '', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'═+', '', text)
    text = re.sub(r'─+', '', text)
    return text.strip()

def read_file(uploaded_file):
    content = uploaded_file.read()
    filename = uploaded_file.name
    if filename.endswith('.pdf'):
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    elif filename.endswith('.docx'):
        doc = Document(io.BytesIO(content))
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    else:
        return content.decode("utf-8")

@st.cache_resource
def load_models():
    with st.spinner("⏳ جاري تحميل النماذج..."):
        summarizer = pipeline("text-generation", model="google/flan-t5-base")
        classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    return summarizer, classifier

try:
    summarizer, classifier = load_models()
except Exception as e:
    st.error(f"❌ مشكلة في تحميل النماذج: {str(e)}")
    st.stop()

uploaded_file = st.file_uploader("📂 اختر ملف", type=["txt", "pdf", "docx"])

if uploaded_file is not None:
    try:
        text = read_file(uploaded_file)
    except Exception as e:
        st.error(f"❌ مشكلة في قراءة الملف: {str(e)}")
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
        with st.spinner("⏳ جاري التلخيص..."):
            try:
                prompt = f"Summarize this text in one short paragraph: {clean_text_content[:500]}"
                result = summarizer(prompt, max_new_tokens=150, do_sample=False)
                summary = result[0]['generated_text']
                st.success("✅ تم التلخيص!")
            except Exception as e:
                st.error(f"❌ خطأ: {str(e)}")
                summary = clean_text_content

    st.write(summary)

    st.divider()
    st.subheader("🏷️ التصنيف")

    with st.spinner("⏳ جاري التصنيف..."):
        try:
            labels = ["مالي", "طبي", "تقني", "قانوني", "تعليمي", "تسويقي", "سياسي", "اجتماعي", "رياضي", "ديني", "فني"]
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
    word_count = len(clean_text_content.split())
    char_count = len(clean_text_content)
    sentence_count = len(re.findall(r'[.!؟]+', clean_text_content))

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("عدد الكلمات", word_count)
    with col2:
        st.metric("عدد الأحرف", char_count)
    with col3:
        st.metric("عدد الجمل", sentence_count)

    st.divider()
    report_text = f"""
    ═══════════════════════════════════════════════════════════════
                          📄 تقرير تلخيص المستند
    ═══════════════════════════════════════════════════════════════

    التصنيف: {label} (نسبة الثقة: {score:.2%})
    عدد الكلمات: {word_count}
    عدد الأحرف: {char_count}
    عدد الجمل: {sentence_count}

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
        file_name=f"تقرير_{uploaded_file.name}.txt",
        mime="text/plain"
    )

else:
    st.info("⏳ انتظر رفع ملف لتحليله")
    st.markdown("""
    ### 🚀 طريقة الاستخدام:
    1. اضغط على زر **"اختر ملف"**
    2. اختر ملف `.txt` أو `.pdf` أو `.docx`
    3. انتظر لحظات وستظهر النتيجة
    4. يمكنك تحميل التقرير
    """)