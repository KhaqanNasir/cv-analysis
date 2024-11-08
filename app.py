import pdfplumber
import torch
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
import streamlit as st
import matplotlib.pyplot as plt
import docx2txt  # For extracting text from Word documents

# Load the pretrained model and tokenizer
model_name = "distilbert-base-uncased"
tokenizer = DistilBertTokenizer.from_pretrained(model_name)
model = DistilBertForSequenceClassification.from_pretrained(model_name, num_labels=5)

# Function to extract text from a PDF CV
def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text.strip()

# Function to extract text from a Word CV
def extract_text_from_word(docx_path):
    return docx2txt.process(docx_path)

# Function to analyze the CV text and return scores
def analyze_cv_text(cv_text):
    inputs = tokenizer(cv_text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probabilities = torch.softmax(logits, dim=1).numpy()
    return probabilities

# Function to rank candidates based on their CV analysis
def rank_candidates(cv_data):
    all_candidates = []
    for cv in cv_data:
        cv_scores = analyze_cv_text(cv)
        skills_score = cv_scores[0][0] * 100
        experience_score = cv_scores[0][1] * 100
        total_score = (0.5 * skills_score + 0.5 * experience_score)
        all_candidates.append((cv, total_score, skills_score, experience_score))
    return all_candidates

# Function to reset the session state
def reset_state():
    if "uploaded_files" in st.session_state:
        del st.session_state["uploaded_files"]
    if "candidates" in st.session_state:
        del st.session_state["candidates"]
    st.session_state["uploaded_files"] = None
    st.session_state["candidates"] = []

# Streamlit UI
st.set_page_config(page_title="CV Analysis Tool", layout="wide")
st.markdown("""
    <h2 style='text-align: center;'>Developed by <i>Muhammad Khaqan Nasir</i></h2>
    <p style='text-align: center; color: navy;'>
        <a style='text-decoration:none;' href='https://www.linkedin.com/in/khaqan-nasir/' target='_blank'>
            <img src='https://cdn-icons-png.flaticon.com/512/174/174857.png' alt='ImageNotFound' width='20' style='vertical-align: middle; margin-right: 8px;'/>
            LinkedIn
        </a>
    </p><br><br>
    """, unsafe_allow_html=True)

st.title("🌟 CV Analysis and Candidate Ranking Tool 🌟")
st.markdown("## Upload your CVs for analysis and receive scores based on skills and experience!")

# Check if session state has 'uploaded_files'
if "uploaded_files" not in st.session_state:
    st.session_state["uploaded_files"] = None

# Upload the CV files (accepts both PDF and Word documents)
uploaded_files = st.file_uploader(
    "Choose CV files", type=["pdf", "docx"], accept_multiple_files=True, help="Upload your CVs in PDF or DOCX format"
)

if uploaded_files:
    st.session_state["uploaded_files"] = uploaded_files
    cvs = []

    # Extract text from each uploaded file based on file type
    with st.spinner("Extracting text from the CVs..."):
        for uploaded_file in uploaded_files:
            if uploaded_file.type == "application/pdf":
                cvs.append(extract_text_from_pdf(uploaded_file))
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                cvs.append(extract_text_from_word(uploaded_file))

    candidates = rank_candidates(cv_data=cvs)

    # Display candidate analysis if any CV data is available
    if candidates:
        st.subheader("Candidates Analysis")
        for index, candidate in enumerate(candidates):
            cv, total_score, skills_score, experience_score = candidate
            
            # Create colored sections for better distinction
            total_color = 'color: #2ca02c;'  # Green for total score
            skills_color = 'color: #1f77b4;'  # Blue for skills score
            experience_color = 'color: #ff7f0e;'  # Orange for experience score
            
            st.markdown(f"**CV Snippet {index + 1}:** <span style='color: #d62728;'>{cv[:30]}...</span>", unsafe_allow_html=True)
            st.markdown(f"**Total Score:** <span style='{total_color}'>{total_score:.2f}%</span>", unsafe_allow_html=True)
            st.markdown(f"**Skills Score:** <span style='{skills_color}'>{skills_score:.2f}%</span>", unsafe_allow_html=True)
            st.markdown(f"**Experience Score:** <span style='{experience_color}'>{experience_score:.2f}%</span>", unsafe_allow_html=True)

        # Plotting the scores for each CV
        st.subheader("Comparison of Skills and Experience Scores")

        labels = [f"CV {i + 1}" for i in range(len(candidates))]
        skills_scores = [candidate[2] for candidate in candidates]
        experience_scores = [candidate[3] for candidate in candidates]

        x = range(len(candidates))

        fig, ax = plt.subplots(figsize=(6, 4))  # Adjust the size here

        ax.bar(x, skills_scores, width=0.4, label='Skills Score', color='#1f77b4', align='center')
        ax.bar([p + 0.4 for p in x], experience_scores, width=0.4, label='Experience Score', color='#ff7f0e', align='center')

        ax.set_ylim(0, 100)
        ax.set_xticks([p + 0.2 for p in x])
        ax.set_xticklabels(labels)
        ax.set_ylabel("Percentile (%)")
        ax.set_title("Comparison of Candidate Skills and Experience Scores")
        ax.legend()

        st.pyplot(fig)

        best_candidate = max(candidates, key=lambda x: x[1])
        best_cv, best_total_score, best_skills_score, best_experience_score = best_candidate
        st.markdown(f"### **Best Candidate:** CV Snippet: {best_cv[:30]}...")
        st.write(f"**Best Total Score:** {best_total_score:.2f}%")
        st.write(f"**Best Skills Score:** {best_skills_score:.2f}%")
        st.write(f"**Best Experience Score:** {best_experience_score:.2f}%")
    else:
        st.warning("No candidates found. Please check the CV content.")

# Clear button to reset uploaded CVs
if st.button("Clear CVs"):
    if st.session_state.get("uploaded_files") or st.session_state.get("candidates"):
        reset_state()
        st.success("CVs cleared successfully!")
    else:
        st.warning("No CVs uploaded to clear.")

# Footer
st.markdown("""
---
*This CV analysis tool helps you evaluate your qualifications based on your CV. Ensure your CV is well-formatted and clear for the best results!*
""")

