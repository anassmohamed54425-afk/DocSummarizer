import streamlit as st
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
import nltk
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from collections import Counter
import heapq

# تحميل بيانات NLTK
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

# ========================================
# دوال التلخيص والتصنيف (خفيفة)
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

def summarize_text(text, num_sentences=4):
    sentences = sent_tokenize(text)
    if len(sentences) <= num_sentences:
        return text
    
    stop_words = set(stopwords.words('arabic') + stopwords.words('english'))
    word_freq = Counter()
    for sentence in sentences:
        words = re.findall(r'\w+', sentence.lower())
        for word in words:
            if word not in stop_words:
                word_freq[word] += 1
    
    max_freq = max(word_freq.values()) if word_freq else 1
    for word in word_freq:
        word_freq[word] = word_freq[word] / max_freq
    
    sentence_scores = {}
    for sentence in sentences:
        words = re.findall(r'\w+', sentence.lower())
        score = sum(word_freq.get(word, 0) for word in words)
        sentence_scores[sentence] = score
    
    summarized_sentences = heapq.nlargest(num_sentences, sentence_scores, key=sentence_scores.get)
    return ' '.join(summarized_sentences)

def classify_text(text):
    categories = {
        "مالي": ["مال", "اقتصاد", "بنك", "استثمار", "سوق", "أسهم", "دولار", "ربح", "خسارة", "ضريبة"],
        "طبي": ["طبي", "صحي", "مرض", "علاج", "دواء", "جراحة", "تشخيص", "مستشفى", "طبيب", "صحة"],
        "تقني": ["تقني", "برمجة", "حاسوب", "ذكاء اصطناعي", "بيانات", "خوارزمية", "تطبيق", "موقع", "برنامج", "تكنولوجيا"],
        "قانوني": ["قانون", "محكمة", "عقد", "دعوى", "محامي", "حكم", "تشريع", "حقوق", "إجراء", "قضائي"],
        "تعليمي": ["تعليم", "مدرسة", "جامعة", "طالب", "معلم", "منهج", "دراسة", "بحث", "علمي", "أكاديمي"],
        "تسويقي": ["تسويق", "إعلان", "علامة تجارية", "عملاء", "مبيعات", "عرض", "ترويج", "منتج", "خدمة", "سوق"],
        "سياسي": ["سياسي", "حكومة", "برلمان", "انتخاب", "وزير", "رئيس", "قرار", "أمة", "دستور", "حزب"],
        "اجتماعي": ["اجتماعي", "مجتمع", "أسرة", "ثقافة", "سكان", "تنمية", "فقر", "بطالة", "تعاون", "تكافل"],
        "رياضي": ["رياضي", "كرة", "ملعب", "لاعب", "مدرب", "بطولة", "مباراة", "نادي", "جمباز", "سباق"],
        "ديني": ["ديني", "إسلامي", "مسجد", "صلاة", "قرآن", "حديث", "فتوى", "إيمان", "عقيدة", "عبادة"],
        "فني": ["فني", "فن", "موسيقى", "رسم", "مسرح", "سينما", "تمثيل", "غناء", "تشكيل", "أدب"]
    }
    
    text_lower = text.lower()
    category_scores = {}
    for category, keywords in categories.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        category_scores[category] = score
    
    if max(category_scores.values()) == 0:
        return "عام", 0.5
    
    best_category = max(category_scores, key=category_scores.get)
    best_score = category_scores[best_category]
    max_possible = len(categories[best_category])
    confidence = best_score / max_possible if max_possible > 0 else 0
    
    return best_category, min(confidence, 0.95)

# ========================================
# واجهة Streamlit
# ========================================
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

    if len(clean_text_content.split()) < 50:
        st.warning("⚠️ النص قصير جداً (أقل من 50 كلمة)")
        summary = clean_text_content
    else:
        with st.spinner("⏳ جاري تلخيص النص..."):
            try:
                summary = summarize_text(clean_text_content, num_sentences=4)
                st.success("✅ تم التلخيص بنجاح!")
            except Exception as e:
                st.error(f"❌ مش قادر ألخص النص: {str(e)}")
                summary = clean_text_content

    st.write(summary)

    st.divider()
    st.subheader("🏷️ التصنيف")

    with st.spinner("⏳ جاري تصنيف النص..."):
        try:
            label, score = classify_text(clean_text_content)
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

    def create_pdf(text, summary, label, score, word_count, char_count, sentence_count):
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        try:
            pdfmetrics.registerFont(TTFont('ArialUnicode', 'ArialUnicodeMS.ttf'))
            font_name = 'ArialUnicode'
        except:
            font_name = 'Helvetica'
        
        c.setFont(font_name, 20)
        c.drawString(2*cm, height - 2*cm, "تقرير تحليل المستند")
        c.line(2*cm, height - 2.5*cm, width - 2*cm, height - 2.5*cm)
        
        c.setFont(font_name, 12)
        c.drawString(2*cm, height - 3.5*cm, f"التاريخ: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        c.setFont(font_name, 14)
        c.drawString(2*cm, height - 5*cm, f"التصنيف: {label}")
        c.drawString(2*cm, height - 6*cm, f"نسبة الثقة: {score:.2%}")
        c.drawString(2*cm, height - 7*cm, f"عدد الكلمات: {word_count}")
        c.drawString(2*cm, height - 8*cm, f"عدد الأحرف: {char_count}")
        c.drawString(2*cm, height - 9*cm, f"عدد الجمل: {sentence_count}")
        
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
        
        c.setFont(font_name, 10)
        c.drawString(2*cm, 2*cm, "تم إنشاء التقرير بواسطة تطبيق ملخص المستندات الذكي")
        
        c.save()
        buffer.seek(0)
        return buffer

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