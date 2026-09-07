import streamlit as st
from transformers import pipeline
import PyPDF2
import io
import re
from docx import Document
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import datetime
import os

# ========================================
# إعدادات الصفحة
# ========================================
st.set_page_config(
    page_title="ملخص المستندات الذكي",
    page_icon="📄",
    layout="wide"
)

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

# ========================================
# دوال التنظيف والتحليل
# ========================================

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

# ========================================
# تحميل النماذج (مرة واحدة)
# ========================================
@st.cache_resource
def load_models():
    with st.spinner("⏳ جاري تحميل نماذج الذكاء الاصطناعي..."):
        # نموذج تلخيص أقوى
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    return summarizer, classifier

try:
    summarizer, classifier = load_models()
except Exception as e:
    st.error(f"❌ مشكلة في تحميل النماذج: {str(e)}")
    st.stop()

# ========================================
# رفع الملف
# ========================================
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

    # ========================================
    # التلخيص (باستخدام BART)
    # ========================================
    st.divider()
    st.subheader("📝 الملخص")

    if len(clean_text_content.split()) < 50:
        st.warning("⚠️ النص قصير جداً (أقل من 50 كلمة)")
        summary = clean_text_content
    else:
        with st.spinner("⏳ جاري تلخيص النص..."):
            try:
                # BART بياخد نص طويل ويلخصه
                result = summarizer(
                    clean_text_content,
                    max_length=150,
                    min_length=50,
                    do_sample=False
                )
                summary = result[0]['summary_text']
                st.success("✅ تم التلخيص بنجاح!")
            except Exception as e:
                st.error(f"❌ مش قادر ألخص النص: {str(e)}")
                summary = clean_text_content

    st.write(summary)

    # ========================================
    # التصنيف
    # ========================================
    st.divider()
    st.subheader("🏷️ التصنيف")

    with st.spinner("⏳ جاري تصنيف النص..."):
        try:
            labels = ["مالي", "طبي", "تقني", "قانوني", "تعليمي", "تسويقي", "سياسي", "اجتماعي", "رياضي", "ديني", "فني"]
            result = classifier(clean_text_content[:1000], labels)
            label = result['labels'][0]
            score = result['scores'][0]
            st.success("✅ تم التصنيف بنجاح!")
        except Exception as e:
            st.error(f"❌ مش قادر أصنف النص: {str(e)}")
            label = "غير معروف"
            score = 0

    col1, col2 = st.columns(2)
    with col1:
        st.metric("التصنيف", label)
    with col2:
        st.metric("نسبة الثقة", f"{score:.2%}")

    # ========================================
    # إحصائيات
    # ========================================
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

    # ========================================
    # تحميل التقرير (PDF + TXT)
    # ========================================
    st.divider()
    st.subheader("📥 تحميل التقرير")

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

    # دالة لإنشاء PDF
    def create_pdf(text, summary, label, score, word_count, char_count, sentence_count):
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # استخدام خط عربي
        try:
            pdfmetrics.registerFont(TTFont('ArialUnicode', 'ArialUnicodeMS.ttf'))
            font_name = 'ArialUnicode'
        except:
            font_name = 'Helvetica'
        
        # العنوان
        c.setFont(font_name, 20)
        c.drawString(2*cm, height - 2*cm, "تقرير تحليل المستند")
        c.line(2*cm, height - 2.5*cm, width - 2*cm, height - 2.5*cm)
        
        # التاريخ
        c.setFont(font_name, 12)
        c.drawString(2*cm, height - 3.5*cm, f"التاريخ: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        # النتيجة
        c.setFont(font_name, 14)
        c.drawString(2*cm, height - 5*cm, f"التصنيف: {label}")
        c.drawString(2*cm, height - 6*cm, f"نسبة الثقة: {score:.2%}")
        c.drawString(2*cm, height - 7*cm, f"عدد الكلمات: {word_count}")
        c.drawString(2*cm, height - 8*cm, f"عدد الأحرف: {char_count}")
        c.drawString(2*cm, height - 9*cm, f"عدد الجمل: {sentence_count}")
        
        # الملخص
        c.setFont(font_name, 12)
        c.drawString(2*cm, height - 11*cm, "الملخص:")
        
        y = height - 12*cm
        for line in summary.split('\n'):
            if y < 2*cm:
                c.showPage()
                y = height - 2*cm
            if len(line) > 80:
                line = line[:80] + "..."
            c.drawString(2*cm, y, line)
            y -= 0.6*cm
        
        # النص الأصلي (مختصر)
        c.setFont(font_name, 10)
        c.drawString(2*cm, y - 1*cm, "النص الأصلي (مختصر):")
        y -= 1.5*cm
        
        for line in text[:500].split('\n'):
            if y < 2*cm:
                c.showPage()
                y = height - 2*cm
            if len(line) > 80:
                line = line[:80] + "..."
            c.drawString(2*cm, y, line)
            y -= 0.5*cm
        
        # التذييل
        c.setFont(font_name, 10)
        c.drawString(2*cm, 2*cm, "تم إنشاء التقرير بواسطة تطبيق ملخص المستندات الذكي")
        
        c.save()
        buffer.seek(0)
        return buffer

    # أزرار التحميل
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            label="📥 تحميل التقرير (TXT)",
            data=report_text,
            file_name=f"تقرير_{uploaded_file.name}.txt",
            mime="text/plain"
        )
    
    with col2:
        with st.spinner("⏳ جاري إنشاء PDF..."):
            pdf_buffer = create_pdf(
                clean_text_content, summary, label, score,
                word_count, char_count, sentence_count
            )
            st.download_button(
                label="📥 تحميل التقرير (PDF)",
                data=pdf_buffer,
                file_name=f"تقرير_{uploaded_file.name}.pdf",
                mime="application/pdf"
            )

else:
    st.info("⏳ انتظر رفع ملف لتحليله")
    st.markdown("""
    ### 🚀 طريقة الاستخدام:
    1. اضغط على زر **"اختر ملف"**
    2. اختر ملف `.txt` أو `.pdf` أو `.docx`
    3. انتظر لحظات وستظهر النتيجة
    4. يمكنك تحميل التقرير بصيغة TXT أو PDF
    """)