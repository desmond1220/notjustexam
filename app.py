"""
NotJustExam - Exam Study Portal
A Streamlit application for managing and studying exam dumps
Enhanced with ZIP file upload support and improved navigation
"""

import streamlit as st
import json
import os
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any
import re
from datetime import datetime
from bs4 import BeautifulSoup
import io
import hashlib
import base64

# Page configuration
st.set_page_config(
    page_title="NotJustExam Study Portal",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced Custom CSS with sticky navigation
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 20px;
    }
    .question-container {
        padding: 20px;
        border: 2px solid #1f77b4;
        border-radius: 10px;
        margin: 20px 0;
        background-color: white;
    }
    .question-text {
        line-height: 1.8;
        margin: 16px 0;
    }
    .question-text ul {
        margin: 12px 0;
        padding-left: 24px;
    }
    .question-text li {
        margin: 8px 0;
        line-height: 1.6;
    }
    .discussion, .ai-answer {
        margin: 16px 0;
        line-height: 1.7;
    }
    .discussion ul, .ai-answer ul {
        margin: 12px 0 12px 20px;
        padding-left: 0;
    }
    .discussion li, .ai-answer li {
        margin: 8px 0;
        list-style-type: disc;
    }
    
    /* Sticky navigation container */
    .sticky-nav {
        position: sticky;
        top: 0;
        z-index: 999;
        background: white;
        padding: 16px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        border-radius: 8px;
    }
    
    /* Progress bar */
    .progress-bar-container {
        width: 100%;
        height: 4px;
        background: #e9ecef;
        border-radius: 2px;
        overflow: hidden;
        margin-top: 12px;
    }
    
    .progress-bar {
        height: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        transition: width 0.3s ease;
    }
    
    /* Button styling improvements */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
</style>
""", unsafe_allow_html=True)

# Initialize data directory
DATA_DIR = Path("exam_data")
DATA_DIR.mkdir(exist_ok=True)

def initialize_session_state():
    """Initialize session state variables"""
    if "current_page" not in st.session_state:
        st.session_state.current_page = "home"
    if "selected_exam" not in st.session_state:
        st.session_state.selected_exam = None
    if "current_question_index" not in st.session_state:
        st.session_state.current_question_index = 0
    if "show_answer" not in st.session_state:
        st.session_state.show_answer = {}
    if "authenticated_exams" not in st.session_state:
        st.session_state.authenticated_exams = []
    if "password_attempt" not in st.session_state:
        st.session_state.password_attempt = {}

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(input_password: str, stored_hash: str) -> bool:
    """Verify password against stored hash"""
    return hash_password(input_password) == stored_hash

def is_exam_authenticated(exam_name: str) -> bool:
    """Check if exam is authenticated in current session"""
    if "authenticated_exams" not in st.session_state:
        st.session_state.authenticated_exams = []
    return exam_name in st.session_state.authenticated_exams

def image_to_base64(image_path: str) -> str:
    """Convert image to base64 for embedding"""
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
            base64_data = base64.b64encode(image_data).decode('utf-8')
            ext = Path(image_path).suffix.lower()
            mime_types = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', 
                         '.png': 'image/png', '.gif': 'image/gif'}
            mime_type = mime_types.get(ext, 'image/jpeg')
            return f"{mime_type};base64,{base64_data}"
    except:
        return ""

def convert_html_images_to_base64(html_content: str, exam_name: str, folder_prefix: str = "") -> str:
    """Convert all image src in HTML to base64 data URIs"""
    if not html_content:
        return html_content
    
    soup = BeautifulSoup(html_content, 'html.parser')
    images = soup.find_all('img')
    
    for img in images:
        src = img.get('src', '')
        if src and not src.startswith(''):
            images_dir = DATA_DIR / exam_name / "images"
            img_path = None
            
            test_path = images_dir / src
            if test_path.exists():
                img_path = test_path
            elif folder_prefix:
                prefixed_name = f"{folder_prefix}_{src}"
                test_path = images_dir / prefixed_name
                if test_path.exists():
                    img_path = test_path
                else:
                    matching_files = list(images_dir.glob(f"*_{src}"))
                    if matching_files:
                        for match in matching_files:
                            if match.name.startswith(folder_prefix):
                                img_path = match
                                break
                        if not img_path:
                            img_path = matching_files[0]
            
            if img_path and img_path.exists():
                b64 = image_to_base64(str(img_path))
                if b64:
                    img['src'] = b64
    
    if hasattr(soup, 'decode_contents'):
        return soup.decode_contents()
    return str(soup)

def remove_duplicate_chunks(text: str, min_chunk_size: int = 150) -> str:
    """Remove duplicate text chunks from question text"""
    if not text or len(text) < min_chunk_size:
        return text
    
    markers = [
        "You have the following",
        "HOTSPOT -",
        "DRAG DROP -",
        "SIMULATION -",
        "You need to",
        "What should you",
        "Hot Area:"
    ]
    
    for marker in markers:
        if marker not in text:
            continue
            
        positions = []
        start = 0
        while True:
            pos = text.find(marker, start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + len(marker)
        
        if len(positions) >= 2:
            first_pos = positions[0]
            second_pos = positions[1]
            chunk_between = text[first_pos:second_pos].strip()
            
            if len(chunk_between) >= min_chunk_size:
                return text[:second_pos].strip()
    
    text_len = len(text)
    mid = text_len // 2
    
    for offset in range(-50, 51):
        split_point = mid + offset
        if split_point < min_chunk_size or split_point > text_len - min_chunk_size:
            continue
        
        first_half = text[:split_point].strip()
        second_half = text[split_point:].strip()
        
        if first_half == second_half and len(first_half) >= min_chunk_size:
            return first_half
    
    for chunk_size in range(int(text_len * 0.4), min_chunk_size, -30):
        for start in range(0, min(200, text_len - chunk_size)):
            chunk = text[start:start + chunk_size]
            next_pos = text.find(chunk, start + chunk_size)
            
            if next_pos != -1 and (next_pos - start) >= min_chunk_size:
                return text[:next_pos].strip()
    
    return text

def generate_offline_html(exam_name: str, exam_ Dict[str, Any]) -> str:
    """Generate self-contained HTML file for offline study with proper formatting"""
    questions = exam_data['questions']
    exam_title = exam_data.get('exam_name', exam_name)
    count = len(questions)
    
    html = f'''<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{exam_title} - Offline Study</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f5f7fa;padding:8px;line-height:1.6}}
.container{{max-width:900px;margin:0 auto;background:white;border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,0.08)}}
.header{{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;padding:24px;text-align:center;border-radius:12px 12px 0 0}}
.header h1{{font-size:26px;margin-bottom:8px}}
.nav{{background:#f8f9fa;padding:16px;display:flex;justify-content:space-between;align-items:center;gap:12px;position:sticky;top:0;z-index:100;flex-wrap:wrap}}
.btn{{padding:10px 18px;border:none;border-radius:8px;cursor:pointer;font-size:15px;font-weight:500;min-width:44px;min-height:44px}}
.btn-primary{{background:#667eea;color:white}}
.btn-secondary{{background:#6c757d;color:white}}
.btn:hover{{opacity:0.9}}
.btn:disabled{{opacity:0.5;cursor:not-allowed}}
.progress-bar{{height:4px;background:linear-gradient(90deg,#667eea 0%,#764ba2 100%);transition:width 0.3s}}
.question{{padding:24px}}
.question h3{{color:#667eea;margin-bottom:16px;font-size:20px}}
.question-text{{margin:16px 0;line-height:1.8;color:#2c3e50}}
.question-text p{{margin:12px 0}}
.question-text ul{{margin:12px 0 12px 24px;padding:0}}
.question-text li{{margin:8px 0;line-height:1.7}}
.option{{padding:14px;margin:12px 0;border:2px solid #e9ecef;border-radius:10px;cursor:pointer;transition:all 0.2s}}
.option:hover{{border-color:#667eea;background:#f8f9ff}}
.option.correct{{border-color:#28a745;background:#d4edda}}
.option.wrong{{border-color:#dc3545;background:#f8d7da}}
.answer{{margin-top:24px;padding:20px;background:#f8f9fa;border-radius:10px;border-left:4px solid #667eea}}
.answer h4{{color:#28a745;margin-bottom:16px}}
.answer-content{{margin:16px 0;padding:16px;background:white;border-radius:8px}}
.answer-content h5{{color:#2c3e50;margin-bottom:12px;font-size:16px}}
.answer-content p{{margin:10px 0;line-height:1.7}}
.answer-content ul{{margin:12px 0 12px 24px}}
.answer-content li{{margin:8px 0;line-height:1.7}}
.hidden{{display:none}}
img{{max-width:100%;height:auto;margin:16px 0;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.1)}}
@media (max-width:768px){{
body{{padding:4px}}
.header h1{{font-size:22px}}
.question{{padding:16px}}
.btn{{font-size:14px;padding:10px 14px}}
#counter{{width:100%;order:-1;margin-bottom:8px;text-align:center}}
}}
</style>
</head>
<body>
<div class="container">
<div class="header"><h1>📚 {exam_title}</h1><div>{count} Questions | Offline Mode</div></div>
<div class="nav">
<button class="btn btn-secondary" onclick="prev()" id="prev">◀ Prev</button>
<div id="counter">Q 1/{count}</div>
<button class="btn btn-secondary" onclick="next()" id="next">Next ▶</button>
<button class="btn btn-primary" onclick="toggle()" id="show">Show Answer</button>
</div>
<div style="height:4px;background:#e9ecef"><div class="progress-bar" id="prog" style="width:0%"></div></div>
<div id="qs">'''
    
    # Add questions (keeping existing logic)
    for i, q in enumerate(questions):
        topic = q.get('topic_index', 1)
        qnum = q.get('question_index', 1)
        text = q.get('question', 'No question')
        choices = q.get('choices', {})
        ans = q.get('suggested_answer', q.get('correct_answer', ''))

        text = remove_duplicate_chunks(text, min_chunk_size=150)
        formatted_text = text.replace('\n', '<br>')

        opts = ""
        if choices:
            for letter, choice in sorted(choices.items()):
                correct = "true" if letter == ans else "false"
                opts += f'<div class="option" data-opt="{letter}" data-cor="{correct}" onclick="sel(this,{i})"><b>{letter}.</b> {choice}</div>'

        imgs = ""
        for img_file in q.get('saved_images', []):
            img_path = DATA_DIR / exam_name / "images" / img_file
            if img_path.exists():
                b64 = image_to_base64(str(img_path))
                if b64:
                    imgs += f'<img src="{b64}">'
        
        answer_imgs = ""
        if q.get('answer_images'):
            for img_file in q['answer_images']:
                img_path = DATA_DIR / exam_name / "images" / img_file
                if img_path.exists():
                    b64 = image_to_base64(str(img_path))
                    if b64:
                        answer_imgs += f'<img src="{b64}">'
        
        answer_html = q.get('suggested_answer_html', '')
        disc_html = q.get('discussion_summary_html', '')
        ai_html = q.get('ai_recommendation_html', '')

        html += f'''
<div class="question" id="q{i}" style="display:{'block' if i==0 else 'none'}">
<h3>Topic {topic} - Question {qnum}</h3>
<div class="question-text">{formatted_text}</div>
{imgs}
<div>{opts}</div>
<div class="answer hidden" id="a{i}">'''
        
        if answer_html:
            soup = BeautifulSoup(answer_html, 'html.parser')
            for img_tag in soup.find_all('img'):
                img_tag.decompose()
            answer_html = str(soup).replace("Suggested Answer:", "")
            html += f'<div class="answer-content"><h5>✅ Suggested Answer</h5><div style="padding:10px">{answer_imgs}{answer_html}</div></div>'
        else:
            html += f'<h4>✅ Answer: {ans}</h4>'

        if disc_html:
            html += f'<div class="answer-content"><h5>💬 Discussion</h5><div style="padding:10px">{disc_html}</div></div>'
        if ai_html:
            html += f'<div class="answer-content"><h5>🤖 AI Recommendation</h5><div style="padding:10px">{ai_html}</div></div>'

        html += '</div>\n</div>\n'

    html += f'''
</div></div>
<script>
let c=0,t={count},ans={{}},s=false;
function load(){{let d=localStorage.getItem('e_{exam_name.replace(" ","_")}');if(d){{let p=JSON.parse(d);ans=p.a||{{}};c=p.c||0}}show(c)}}
function save(){{localStorage.setItem('e_{exam_name.replace(" ","_")}',JSON.stringify({{c:c,a:ans}}))}}
function show(i){{
document.querySelectorAll('.question').forEach(q=>q.style.display='none');
document.getElementById('q'+i).style.display='block';
document.getElementById('counter').textContent='Q '+(i+1)+'/'+t;
document.getElementById('prev').disabled=i===0;
document.getElementById('next').disabled=i===t-1;
document.getElementById('prog').style.width=((i+1)/t*100)+'%';
s=false;document.getElementById('a'+i).classList.add('hidden');
document.getElementById('show').textContent='Show Answer';
c=i;save();
}}
function next(){{if(c<t-1)show(c+1)}}
function prev(){{if(c>0)show(c-1)}}
function toggle(){{
let a=document.getElementById('a'+c),b=document.getElementById('show');
if(s){{a.classList.add('hidden');b.textContent='Show Answer'}}
else{{a.classList.remove('hidden');b.textContent='Hide Answer'}}
s=!s;
}}
function sel(e,q){{
e.parentElement.querySelectorAll('.option').forEach(o=>o.classList.remove('correct','wrong'));
let cor=e.getAttribute('data-cor')==='true';
e.classList.add(cor?'correct':'wrong');
if(!cor)e.parentElement.querySelector('[data-cor="true"]').classList.add('correct');
ans[q]=e.getAttribute('data-opt');save();
setTimeout(()=>{{if(!s)toggle()}},500);
}}
document.addEventListener('keydown',e=>{{
if(e.key==='ArrowRight')next();
else if(e.key==='ArrowLeft')prev();
else if(e.key===' '){{e.preventDefault();toggle()}}
}});
window.onload=load;
</script>
</body></html>'''
    
    return html

# [Keep all existing parsing and extraction functions...]
def parse_folder_name(folder_name: str) -> Dict[str, int]:
    """Extract topic and question index from folder name"""
    match = re.match(r'topic_(\d+)_question_(\d+)', folder_name)
    if match:
        return {
            'topic_index': int(match.group(1)),
            'question_index': int(match.group(2))
        }
    return None

def extract_html_content(html_content: str, content_type: str) -> Dict[str, Any]:
    """Extract content from HTML files using BeautifulSoup"""
    soup = BeautifulSoup(html_content, 'html.parser')
    result = {}
    
    for elem in soup.find_all(style=lambda v: v and 'display: none' in v.lower()):
        elem.decompose()
    
    if content_type == 'question':
        question_div = soup.find('div', class_='question')
        if question_div:
            question_text = question_div.get_text(separator='\n', strip=True)
            question_text = remove_duplicate_chunks(question_text, min_chunk_size=150)
            result['question'] = question_text
            
            images = question_div.find_all('img')
            result['question_images'] = [img.get('src', '') for img in images]
        
        choices = {}
        correct_answer = None
        
        choice_items = soup.find_all('li', class_='multi-choice-item')
        
        if choice_items:
            for item in choice_items:
                letter = None
                choice_text = None
                
                letter_span = item.find('span', class_='multi-choice-letter')
                if letter_span:
                    letter = letter_span.get('data-choice-letter', '')
                    choice_text = item.get_text(separator=' ', strip=True)
                    choice_text = choice_text.replace(f"{letter}.", "", 1).strip()
                    choice_text = ' '.join(choice_text.split())
                    choices[letter] = choice_text
                else:
                    first_span = item.find('span')
                    if first_span:
                        span_text = first_span.get_text(strip=True)
                        letter = span_text.strip().rstrip('.')
                        full_text = item.get_text(separator=' ', strip=True)
                        choice_text = full_text.replace(span_text, '', 1).strip()
                        choice_text = ' '.join(choice_text.split())
                        
                        if letter and choice_text:
                            choices[letter] = choice_text
                    else:
                        full_text = item.get_text(separator=' ', strip=True)
                        match = re.match(r'^([A-Z])\.\s*(.*)', full_text)
                        if match:
                            letter = match.group(1)
                            choice_text = match.group(2).strip()
                            choice_text = ' '.join(choice_text.split())
                            if letter and choice_text:
                                choices[letter] = choice_text
                
                if 'correct-hidden' in item.get('class', []) and letter:
                    correct_answer = letter
        
        if not choices:
            question_options_div = soup.find('div', class_='question-options')
            if question_options_div:
                option_items = question_options_div.find_all('li')
                for item in option_items:
                    full_text = item.get_text(separator=' ', strip=True)
                    match = re.match(r'^([A-Z])\.\s*(.*)', full_text)
                    if match:
                        letter = match.group(1)
                        choice_text = match.group(2).strip()
                        choice_text = ' '.join(choice_text.split())
                        if letter and choice_text:
                            choices[letter] = choice_text
        
        result['choices'] = choices
        if correct_answer:
            result['correct_answer'] = correct_answer
        
    elif content_type == 'answer':
        answer_div = soup.find('div', class_='answer')
        if answer_div:
            answer_html = answer_div.decode_contents()
            result['suggested_answer_html'] = str(answer_html)
            suggested_answer_text = answer_div.get_text(separator=' ', strip=True)
            
            match = re.search(r'Suggested Answer[:\s]+([A-Z])', suggested_answer_text)
            if match:
                result['suggested_answer'] = match.group(1)
            else:
                result['suggested_answer'] = 'See Discussion'
            
            images = answer_div.find_all('img')
            result['answer_images'] = [img.get('src', '') for img in images]
        
        discussion_div = soup.find('div', class_='discussion-summary')
        if discussion_div:
            header = discussion_div.find('h3')
            if header:
                header.decompose()
            result['discussion_summary_html'] = str(discussion_div)

        ai_div = soup.find('div', class_='ai-recommendation')
        if ai_div:
            for h3 in ai_div.find_all('h3'):
                if 'citation' in h3.get_text().lower():
                    citation_header = h3
                    citation_ul = citation_header.find_next_sibling('ul')
                    if citation_ul:
                        citation_ul.decompose()
                    citation_header.decompose()
                    break
            
            result['ai_recommendation_html'] = str(ai_div)
            
            citations = []
            citation_header = None
            for h3 in ai_div.find_all('h3'):
                if 'citation' in h3.get_text().lower():
                    citation_header = h3
                    break
            
            if citation_header:
                next_ul = citation_header.find_next_sibling('ul')
                if next_ul:
                    for li in next_ul.find_all('li'):
                        cit = li.get_text(separator=' ', strip=True)
                        cit = ' '.join(cit.split())
                        if cit:
                            citations.append(cit)
            
            if citations:
                result['ai_citations'] = citations
    
    return result

# [Keep all other existing helper functions: extract_zip_file, process_zip_file, save_exam, load_exam, list_exams, delete_exam...]

def save_exam(exam_name: str, questions: List[Dict[str, Any]], password: str = None):
    """Save exam data to JSON file with optional password"""
    exam_dir = DATA_DIR / exam_name
    exam_dir.mkdir(parents=True, exist_ok=True)

    exam_data = {
        'exam_name': exam_name,
        'created_at': datetime.now().isoformat(),
        'question_count': len(questions),
        'questions': questions
    }

    if password:
        exam_data['password_protected'] = True
        exam_data['password_hash'] = hash_password(password)
    else:
        exam_data['password_protected'] = False

    exam_file = exam_dir / "exam_data.json"
    with open(exam_file, 'w', encoding='utf-8') as f:
        json.dump(exam_data, f, indent=2, ensure_ascii=False)

def load_exam(exam_name: str) -> Dict[str, Any]:
    """Load exam data from JSON file"""
    exam_file = DATA_DIR / exam_name / "exam_data.json"
    if exam_file.exists():
        with open(exam_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def list_exams() -> List[str]:
    """List all available exams"""
    if not DATA_DIR.exists():
        return []
    return [d.name for d in DATA_DIR.iterdir() if d.is_dir() and (d / "exam_data.json").exists()]

def delete_exam(exam_name: str):
    """Delete an exam and its data"""
    exam_dir = DATA_DIR / exam_name
    if exam_dir.exists():
        shutil.rmtree(exam_dir)
        return True
    return False

# ============= ENHANCED STUDY PAGE WITH TOP NAVIGATION AND PAGE SELECTOR =============

def study_page():
    """Enhanced study page with sticky top navigation and page number selector"""
    if not st.session_state.selected_exam:
        st.error("No exam selected")
        if st.button("← Back to Home"):
            st.session_state.current_page = "home"
            st.rerun()
        return

    exam_name = st.session_state.selected_exam
    exam_data = load_exam(exam_name)

    if not exam_
        st.error("Exam not found")
        return

    questions = exam_data['questions']
    total_questions = len(questions)
    current_idx = st.session_state.current_question_index

    # Ensure index is within bounds
    if current_idx >= total_questions:
        st.session_state.current_question_index = 0
        current_idx = 0

    current_question = questions[current_idx]

    # ===== STICKY NAVIGATION AT THE TOP =====
    st.markdown('<div class="sticky-nav">', unsafe_allow_html=True)
    
    # Top row: Show Answer button (prominent position)
    show_answer_key = f"show_answer_{exam_name}_{current_idx}"
    if show_answer_key not in st.session_state.show_answer:
        st.session_state.show_answer[show_answer_key] = False
    
    col_show = st.columns([3, 1])[1]
    with col_show:
        if st.button(
            "👁️ Show Answer" if not st.session_state.show_answer[show_answer_key] else "🙈 Hide Answer",
            key=f"toggle_answer_{current_idx}",
            use_container_width=True,
            type="primary"
        ):
            st.session_state.show_answer[show_answer_key] = not st.session_state.show_answer[show_answer_key]
            st.rerun()
    
    st.markdown("---")
    
    # Navigation controls row
    nav_cols = st.columns([1, 2, 1.5, 1, 1])
    
    # Back to Home button
    with nav_cols[0]:
        if st.button("🏠 Home", key="home_btn", use_container_width=True):
            st.session_state.current_page = "home"
            st.rerun()
    
    # Question counter display
    with nav_cols[1]:
        st.markdown(f"### Question {current_idx + 1} of {total_questions}")
    
    # Page number selector (direct jump)
    with nav_cols[2]:
        selected_page = st.selectbox(
            "Jump to:",
            options=list(range(1, total_questions + 1)),
            index=current_idx,
            key="page_selector",
            label_visibility="collapsed",
            help="Select a question number to jump directly"
        )
        
        # Handle page change from selector
        if selected_page - 1 != current_idx:
            st.session_state.current_question_index = selected_page - 1
            st.rerun()
    
    # Previous button
    with nav_cols[3]:
        if st.button("◀️ Prev", key="prev_btn", disabled=(current_idx == 0), use_container_width=True):
            st.session_state.current_question_index = max(0, current_idx - 1)
            st.rerun()
    
    # Next button
    with nav_cols[4]:
        if st.button("Next ▶️", key="next_btn", disabled=(current_idx >= total_questions - 1), use_container_width=True):
            st.session_state.current_question_index = min(total_questions - 1, current_idx + 1)
            st.rerun()
    
    # Progress bar
    progress = (current_idx + 1) / total_questions
    st.markdown(f'''
        <div class="progress-bar-container">
            <div class="progress-bar" style="width: {progress * 100}%"></div>
        </div>
    ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ===== QUESTION CONTENT =====
    st.markdown('<div class="question-container">', unsafe_allow_html=True)
    
    # Question header
    topic = current_question.get('topic_index', 1)
    qnum = current_question.get('question_index', 1)
    st.markdown(f"### 📝 Topic {topic} - Question {qnum}")
    
    # Question text
    question_text = current_question.get('question', 'No question available')
    st.markdown(f'<div class="question-text">{question_text.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
    
    # Question images
    if current_question.get('saved_images'):
        for img_file in current_question['saved_images']:
            img_path = DATA_DIR / exam_name / "images" / img_file
            if img_path.exists():
                st.image(str(img_path), use_container_width=True)
    
    # Answer choices
    choices = current_question.get('choices', {})
    if choices:
        st.markdown("#### Answer Options:")
        for letter, choice_text in sorted(choices.items()):
            st.markdown(f"**{letter}.** {choice_text}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ===== ANSWER SECTION (conditionally shown) =====
    if st.session_state.show_answer[show_answer_key]:
        st.markdown("---")
        
        # Suggested Answer
        answer_html = current_question.get('suggested_answer_html', '')
        if answer_html:
            st.markdown("### ✅ Suggested Answer")
            
            # Display answer images
            if current_question.get('answer_images'):
                for img_file in current_question['answer_images']:
                    img_path = DATA_DIR / exam_name / "images" / img_file
                    if img_path.exists():
                        st.image(str(img_path), use_container_width=True)
            
            st.markdown(answer_html, unsafe_allow_html=True)
        else:
            suggested_ans = current_question.get('suggested_answer', 'N/A')
            st.success(f"✅ Answer: **{suggested_ans}**")
        
        # Discussion Summary
        disc_html = current_question.get('discussion_summary_html', '')
        if disc_html:
            st.markdown("### 💬 Discussion Summary")
            st.markdown(f'<div class="discussion">{disc_html}</div>', unsafe_allow_html=True)
        
        # AI Recommendation
        ai_html = current_question.get('ai_recommendation_html', '')
        if ai_html:
            st.markdown("### 🤖 AI Recommendation")
            st.markdown(f'<div class="ai-answer">{ai_html}</div>', unsafe_allow_html=True)

# ============= HOME PAGE =============

def home_page():
    """Display home page with exam list"""
    st.markdown('<h1 class="main-header">📚 NotJustExam Study Portal</h1>', unsafe_allow_html=True)
    st.markdown("### Your comprehensive exam preparation platform")

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("➕ Create New Exam", use_container_width=True):
            st.session_state.current_page = "create_exam"
            st.rerun()

    st.markdown("---")

    exams = list_exams()

    if not exams:
        st.info("📝 No exams found. Create your first exam to get started!")
    else:
        st.subheader(f"📖 Your Exams ({len(exams)})")

        for exam_name in exams:
            exam_data = load_exam(exam_name)
            if exam_
                is_protected = exam_data.get('password_protected', False)
                is_authenticated = is_exam_authenticated(exam_name)

                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        icon = "🔒" if is_protected and not is_authenticated else "📚"
                        st.markdown(f"### {icon} {exam_name}")
                        st.caption(f"{exam_data['question_count']} questions | Created: {exam_data.get('created_at', 'N/A')[:10]}")
                        if is_protected and is_authenticated:
                            st.caption("✅ Unlocked")

                    with col2:
                        if is_protected and not is_authenticated:
                            if st.button("🔓 Unlock", key=f"unlock_{exam_name}", use_container_width=True):
                                st.session_state.exam_to_unlock = exam_name
                                st.rerun()
                        else:
                            if st.button("📖 Study", key=f"study_{exam_name}", use_container_width=True):
                                st.session_state.selected_exam = exam_name
                                st.session_state.current_question_index = 0
                                st.session_state.current_page = "study"
                                st.rerun()
                    
                    with col3:
                        if st.button("💾 Download", key=f"download_{exam_name}", use_container_width=True):
                            html = generate_offline_html(exam_name, exam_data)
                            filename = f"{exam_name.replace(' ', '_')}_offline.html"
                            
                            st.download_button(
                                label="📥 Get File",
                                data=html,
                                file_name=filename,
                                mime="text/html",
                                key=f"dl_{exam_name}",
                                use_container_width=True
                            )
                
                st.markdown("---")

# Password unlock dialog
    if "exam_to_unlock" in st.session_state:
        exam_to_unlock = st.session_state.exam_to_unlock
        exam_data = load_exam(exam_to_unlock)

        if exam_data and exam_data.get('password_protected'):
            st.markdown("---")
            st.markdown(f"### 🔐 Unlock Exam: {exam_to_unlock}")

            with st.form(key=f"unlock_form_{exam_to_unlock}"):
                password = st.text_input("Enter Password", type="password")

                col1, col2 = st.columns(2)
                with col1:
                    submit = st.form_submit_button("🔓 Unlock", use_container_width=True)
                with col2:
                    cancel = st.form_submit_button("❌ Cancel", use_container_width=True)

                if cancel:
                    del st.session_state.exam_to_unlock
                    st.rerun()

                if submit:
                    if password:
                        stored_hash = exam_data.get('password_hash')
                        if verify_password(password, stored_hash):
                            if exam_to_unlock not in st.session_state.authenticated_exams:
                                st.session_state.authenticated_exams.append(exam_to_unlock)
                            
                            st.success("✅ Exam unlocked!")
                            del st.session_state.exam_to_unlock
                            st.rerun()
                        else:
                            st.error("❌ Incorrect password")
                    else:
                        st.warning("⚠️ Please enter a password")

# ============= MAIN APP =============

def main():
    """Main application entry point"""
    initialize_session_state()

    # Route to appropriate page
    if st.session_state.current_page == "home":
        home_page()
    elif st.session_state.current_page == "study":
        study_page()
    # Add other pages (create_exam, etc.) as needed

if __name__ == "__main__":
    main()
