"""
NotJustExam - Exam Study Portal
A Streamlit application for managing and studying exam dumps
Enhanced with ZIP file upload support
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
import base64  # ADD THIS



# Page configuration
st.set_page_config(
    page_title="NotJustExam Study Portal",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS (keeping minimal for brevity)
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
    if "authenticated_exams" not in st.session_state:  # NEW
        st.session_state.authenticated_exams = []
    if "password_attempt" not in st.session_state:  # NEW
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
            return f"data:{mime_type};base64,{base64_data}"
    except:
        return ""


def convert_html_images_to_base64(html_content: str, exam_name: str, folder_prefix: str = "") -> str:
    """Convert all image src in HTML to base64 data URIs
    
    Args:
        html_content: HTML string containing images
        exam_name: Name of the exam
        folder_prefix: The folder prefix (e.g., 'topic_1_question_5') to find correct images
    """
    if not html_content:
        return html_content
    
    # Parse without adding html/body wrapper tags
    soup = BeautifulSoup(html_content, 'html.parser')
    images = soup.find_all('img')
    
    for img in images:
        src = img.get('src', '')
        if src and not src.startswith('data:'):  # Skip if already base64
            images_dir = DATA_DIR / exam_name / "images"
            img_path = None
            
            # Try exact match first
            test_path = images_dir / src
            if test_path.exists():
                img_path = test_path
            elif folder_prefix:
                # Try with the specific folder prefix for this question
                prefixed_name = f"{folder_prefix}_{src}"
                test_path = images_dir / prefixed_name
                if test_path.exists():
                    img_path = test_path
                else:
                    # Last resort: try glob pattern to find any match
                    matching_files = list(images_dir.glob(f"*_{src}"))
                    if matching_files:
                        # Prefer files with the correct folder prefix
                        for match in matching_files:
                            if match.name.startswith(folder_prefix):
                                img_path = match
                                break
                        # If no exact prefix match, use first match
                        if not img_path:
                            img_path = matching_files[0]
            
            if img_path and img_path.exists():
                # Convert to base64
                b64 = image_to_base64(str(img_path))
                if b64:
                    img['src'] = b64
    
    # Return decoded content to preserve original HTML structure
    # Use decode_contents() for fragments or str() for complete documents
    if hasattr(soup, 'decode_contents'):
        return soup.decode_contents()
    return str(soup)


def remove_duplicate_chunks(text: str, min_chunk_size: int = 150) -> str:
    """
    Remove duplicate text chunks from question text.
    Handles cases where text is duplicated but has additional content after.
    
    Args:
        text: The text to deduplicate
        min_chunk_size: Minimum length of duplicate chunks to remove (default 150)
    
    Returns:
        Deduplicated text
    """
    if not text or len(text) < min_chunk_size:
        return text
    
    # METHOD 1: Find repeating question markers
    # Common markers that indicate duplicate questions
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
            
        # Find all occurrences of this marker
        positions = []
        start = 0
        while True:
            pos = text.find(marker, start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + len(marker)
        
        # If we found 2+ occurrences, we likely have a duplicate
        if len(positions) >= 2:
            first_pos = positions[0]
            second_pos = positions[1]
            
            # Extract the chunk between first and second occurrence
            chunk_between = text[first_pos:second_pos].strip()
            
            # If this chunk is substantial, assume duplication
            if len(chunk_between) >= min_chunk_size:
                # Return everything from start to second occurrence
                return text[:second_pos].strip()
    
    # METHOD 2: Check for 50/50 duplicates
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
    
    # METHOD 3: Sliding window for large duplicates
    # Look for any large chunk that repeats
    for chunk_size in range(int(text_len * 0.4), min_chunk_size, -30):
        for start in range(0, min(200, text_len - chunk_size)):
            chunk = text[start:start + chunk_size]
            # Find if this chunk appears later
            next_pos = text.find(chunk, start + chunk_size)
            
            if next_pos != -1 and (next_pos - start) >= min_chunk_size:
                # Found duplicate - return text up to second occurrence
                return text[:next_pos].strip()
    
    return text



def generate_offline_html(exam_name: str, exam_data: Dict[str, Any]) -> str:
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
    
    # Add questions
    for i, q in enumerate(questions):
        topic = q.get('topic_index', 1)
        qnum = q.get('question_index', 1)
        text = q.get('question', 'No question')
        choices = q.get('choices', {})
        ans = q.get('suggested_answer', q.get('correct_answer', ''))

        # Remove duplicate chunks (if text was accidentally duplicated)
        text = remove_duplicate_chunks(text, min_chunk_size=150)
        # Just use text as-is with basic line break formatting
        import html as html_lib
        formatted_text = html_lib.escape(text).replace('\n', '<br>')

        # Build choices
        opts = ""
        if choices:
            for letter, choice in sorted(choices.items()):
                correct = "true" if letter == ans else "false"
                opts += f'<div class="option" data-opt="{letter}" data-cor="{correct}" onclick="sel(this,{i})"><b>{letter}.</b> {choice}</div>'
        # elif q.get('question_type') == 'hotspot':
        #     opts = '<div style="padding:16px;background:#fff3cd;border:1px solid #ffc107;border-radius:8px">⚠️ This is a HOTSPOT/Hot Area question. View the answer below for the solution.</div>'
        # else:
        #     opts = '<div style="padding:16px;background:#f8d7da;border:1px solid #dc3545;border-radius:8px">⚠️ No answer options available for this question.</div>'

        # Embed question images (same as Streamlit)
        imgs = ""
        for img_file in q.get('saved_images', []):
            img_path = DATA_DIR / exam_name / "images" / img_file
            if img_path.exists():
                b64 = image_to_base64(str(img_path))
                if b64:
                    imgs += f'<img src="{b64}">'
        
        # Embed answer images (same mechanism as Streamlit - use answer_images)
        answer_imgs = ""
        if q.get('answer_images'):
            for img_file in q['answer_images']:
                img_path = DATA_DIR / exam_name / "images" / img_file
                if img_path.exists():
                    b64 = image_to_base64(str(img_path))
                    if b64:
                        answer_imgs += f'<img src="{b64}">'
        
        # Get HTML content (no conversion needed - images are separate)
        answer_html = q.get('suggested_answer_html', '')
        disc_html = q.get('discussion_summary_html', '')
        ai_html = q.get('ai_recommendation_html', '')


        html += f'''
<div class="question" id="q{i}" style="display:{'block' if i==0 else 'none'}; overflow: auto;">
    <h3>Topic {topic} - Question {qnum}</h3>
    <div class="question-text">
        {formatted_text}
    </div>
    {imgs}
    <div>{opts}</div>
<div class="answer hidden" id="a{i}">'''
        
        # If we have HTML answer with detailed content, use that instead of just the letter
        if answer_html:
            soup = BeautifulSoup(answer_html, 'html.parser')
            # Find and remove all img tags
            for img_tag in soup.find_all('img'):
                img_tag.decompose()  # Remove the tag completely
            answer_html = str(soup).replace("Suggested Answer:", "")
            html += f'<div class="answer-content"><h5>✅ Suggested Answer</h5><div style="padding:10px">{answer_imgs}{answer_html}</div></div>'
        else:
            # Fallback to simple answer letter if no HTML
            html += f'<h4>✅ Answer: {ans}</h4>'

        # Add discussion and AI sections
        if disc_html:
            html += f'<div class="answer-content"><h5>💬 Discussion</h5><div style="padding:10px">{disc_html}</div></div>'
        if ai_html:
            html += f'<div class="answer-content"><h5>🤖 AI Recommendation</h5><div style="padding:10px">{ai_html}</div></div>'

        # html += '</div>\n</div>\n'
        html += '</div>'

    # Add JavaScript
    html += f'''
</div></div>
<script>
let c=0,t={count},ans={{}},s=false;
function load(){{
    try {{
        let d=localStorage.getItem('e_{exam_name.replace(" ","_")}');
        if(d){{
            let p=JSON.parse(d);
            ans=p.a||{{}};
            c=p.c||0;
        }}
    }} catch(e) {{
        console.error('Error loading progress:', e);
        c = 0; // Fallback to start
    }}
    // Ensure c is within bounds
    if(c < 0 || c >= t) c = 0;
    show(c);
}}
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
window.onload = load;
</script>
</body></html>'''
    
    return html



def download_exam_handler(exam_name: str):
    """Handle offline download for home page"""
    exam_data = load_exam(exam_name)
    if not exam_data:
        st.error("Exam not found")
        return
    
    try:
        html = generate_offline_html(exam_name, exam_data)
        filename = f"{exam_name.replace(' ', '_')}_offline.html"
        
        st.download_button(
            label="💾 Click to Download",
            data=html,
            file_name=filename,
            mime="text/html",
            key=f"dl_{exam_name}",
            help="Download for offline study"
        )
        st.success("✅ Ready to download!")
        st.info("📱 Works on all devices - mobile, tablet, desktop")
    except Exception as e:
        st.error(f"Error: {str(e)}")



def parse_folder_name(folder_name: str) -> Dict[str, int]:
    """Extract topic and question index from folder name"""
    # Format: topic_<topic_index>_question_<question_index>
    match = re.match(r'topic_(\d+)_question_(\d+)', folder_name)
    if match:
        return {
            'topic_index': int(match.group(1)),
            'question_index': int(match.group(2))
        }
    return None

def extract_html_content(html_content: str, content_type: str) -> Dict[str, Any]:
    """Extract content from HTML files using BeautifulSoup with support for multiple choice formats"""
    soup = BeautifulSoup(html_content, 'html.parser')
    result = {}
    
    # Remove display:none elements
    for elem in soup.find_all(style=lambda v: v and 'display: none' in v.lower()):
        elem.decompose()
    
    if content_type == 'question':
        # Extract question text
        question_div = soup.find('div', class_='question')
        if question_div:
            question_text = question_div.get_text(separator='\n', strip=True)
            # Remove duplicate chunks from question text
            question_text = remove_duplicate_chunks(question_text, min_chunk_size=150)
            result['question'] = question_text
            
            # Extract images from QUESTION HTML only
            images = question_div.find_all('img')
            result['question_images'] = [img.get('src', '') for img in images]
        
        # Extract choices - Try multiple formats
        choices = {}
        correct_answer = None
        
        # FORMAT 1: multi-choice-item (existing format)
        choice_items = soup.find_all('li', class_='multi-choice-item')
        
        if choice_items:
            for item in choice_items:
                letter = None
                choice_text = None
                
                # Try Format 1: <span class="multi-choice-letter" data-choice-letter="A">
                letter_span = item.find('span', class_='multi-choice-letter')
                if letter_span:
                    letter = letter_span.get('data-choice-letter', '')
                    choice_text = item.get_text(separator=' ', strip=True)
                    choice_text = choice_text.replace(f"{letter}.", "", 1).strip()
                    choice_text = ' '.join(choice_text.split())
                    choices[letter] = choice_text
                else:
                    # Try Format 2: <span> with letter as text content
                    first_span = item.find('span')
                    if first_span:
                        # Get the letter from span text
                        span_text = first_span.get_text(strip=True)
                        # Extract letter (A, B, C, D, etc.) - remove any dots or whitespace
                        letter = span_text.strip().rstrip('.')
                        
                        # Get the full choice text and remove the letter part
                        full_text = item.get_text(separator=' ', strip=True)
                        # Remove the letter from the beginning
                        choice_text = full_text.replace(span_text, '', 1).strip()
                        choice_text = ' '.join(choice_text.split())
                        
                        if letter and choice_text:
                            choices[letter] = choice_text
                    else:
                        # Try Format 3: No span, letter is direct text (e.g., "A. Choice text")
                        full_text = item.get_text(separator=' ', strip=True)
                        # Match pattern: "A. text" or "A. text"
                        match = re.match(r'^([A-Z])\.\\s*(.*)', full_text)
                        if match:
                            letter = match.group(1)
                            choice_text = match.group(2).strip()
                            choice_text = ' '.join(choice_text.split())
                            if letter and choice_text:
                                choices[letter] = choice_text
                
                # Check if this is the correct answer
                if 'correct-hidden' in item.get('class', []) and letter:
                    correct_answer = letter
                    # Get the letter for this item
                    if letter_span:
                        correct_answer = letter_span.get('data-choice-letter', '')
                    elif first_span:
                        correct_answer = first_span.get_text(strip=True).rstrip('.')
        
        # FORMAT 2: question-options (NEW - handles your HTML format)
        # If no multi-choice-item found, try question-options format
        if not choices:
            question_options_div = soup.find('div', class_='question-options')
            if question_options_div:
                # Find all list items with letter prefix
                option_items = question_options_div.find_all('li')
                for item in option_items:
                    letter = None
                    choice_text = None
                    
                    # Strategy 1: Check for span containing the letter (e.g., <span>A.</span>)
                    letter_span = item.find('span')
                    if letter_span:
                        span_text = letter_span.get_text(strip=True).rstrip('.')
                        if len(span_text) == 1 and span_text.isalpha():
                            letter = span_text
                            # Remove the span to get the rest of the text clean
                            letter_span.decompose()
                            choice_text = item.get_text(separator=' ', strip=True)
                    
                    # Strategy 2: Fallback to regex on full text if no valid span found
                    if not letter:
                        full_text = item.get_text(separator=' ', strip=True)
                        # Matches "A. Text", "A) Text", or just "A Text" if clear
                        match = re.match(r'^([A-Z])[\.\)\s]\s*(.*)', full_text)
                        if match:
                            letter = match.group(1)
                            choice_text = match.group(2)

                    if letter and choice_text:
                        # Clean up the text
                        choice_text = ' '.join(choice_text.split())
                        choices[letter] = choice_text
        
        result['choices'] = choices
        if correct_answer:
            result['correct_answer'] = correct_answer
        
    elif content_type == 'answer':
        # Extract suggested answer
        answer_div = soup.find('div', class_='answer')
        if answer_div:
            # Keep HTML format
            answer_html = answer_div.decode_contents()  # Gets content WITHOUT the div wrapper
            html_str = str(answer_html).strip()
            # FIX: Remove stray closing div tags if they were captured
            if html_str.endswith('</div>'):
                html_str = html_str[:-6].strip()

            result['suggested_answer_html'] = html_str

            suggested_answer_text = answer_div.get_text(separator=' ', strip=True)
            
            # Try to find answer letter
            match = re.search(r'Suggested Answer[:\\s]+([A-Z])', suggested_answer_text)
            if match:
                result['suggested_answer'] = match.group(1)
            else:
                # For HOTSPOT questions, the answer might be descriptive
                result['suggested_answer'] = 'See Discussion'
            
            # Extract images from ANSWER HTML only  
            images = answer_div.find_all('img')
            result['answer_images'] = [img.get('src', '') for img in images]
        
        # Extract discussion summary - KEEP AS HTML
        discussion_div = soup.find('div', class_='discussion-summary')
        if discussion_div:
            header = discussion_div.find('h3')
            if header:
                header.decompose()
            
            # Keep HTML format
            result['discussion_summary_html'] = str(discussion_div)

        # Extract AI recommendation - KEEP AS HTML
        ai_div = soup.find('div', class_='ai-recommendation')
        if ai_div:
            # Remove citation section
            for h3 in ai_div.find_all('h3'):
                if 'citation' in h3.get_text().lower():
                    citation_header = h3
                    citation_ul = citation_header.find_next_sibling('ul')
                    if citation_ul:
                        citation_ul.decompose()
                    citation_header.decompose()
                    break
            
            # Keep HTML format
            result['ai_recommendation_html'] = str(ai_div)

            
            # Extract citations
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


def extract_zip_file(zip_file, temp_dir: Path) -> Dict[str, Dict[str, bytes]]:
    """
    Extract ZIP file contents and organize by folder structure

    Returns:
        Dict mapping folder names to files (name -> content bytes)
    """
    folders = {}

    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        for file_info in zip_ref.filelist:
            # Skip directories and hidden files
            if file_info.is_dir() or file_info.filename.startswith('__MACOSX'):
                continue

            # Extract folder and file name
            parts = Path(file_info.filename).parts
            if len(parts) >= 2:
                folder_name = parts[0]
                file_basename = parts[-1]

                if folder_name not in folders:
                    folders[folder_name] = {}

                # Read file content
                folders[folder_name][file_basename] = zip_ref.read(file_info.filename)

    return folders

def process_uploaded_folders(uploaded_files: List, exam_name: str) -> List[Dict[str, Any]]:
    """Process uploaded folders and extract question data"""
    questions = []

    # Create temporary directory to extract files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Group files by folder name
        folders = {}
        for uploaded_file in uploaded_files:
            file_name = uploaded_file.name
            # Extract folder name (everything before the last /)
            parts = file_name.split('/')
            if len(parts) >= 2:
                folder_name = parts[0]
                file_basename = parts[-1]

                if folder_name not in folders:
                    folders[folder_name] = {}
                folders[folder_name][file_basename] = uploaded_file

        # Process each folder
        for folder_name, files in folders.items():
            folder_info = parse_folder_name(folder_name)
            if not folder_info:
                continue

            question_data = {
                'topic_index': folder_info['topic_index'],
                'question_index': folder_info['question_index'],
                'question_name': f"Topic {folder_info['topic_index']} - Question {folder_info['question_index']}"
            }

            # Process summary_question.html
            if 'summary_question.html' in files:
                content = files['summary_question.html'].read().decode('utf-8')
                question_content = extract_html_content(content, 'question')
                question_data.update(question_content)

            # Process summary_discussion_ai.html
            if 'summary_discussion_ai.html' in files:
                content = files['summary_discussion_ai.html'].read().decode('utf-8')
                answer_content = extract_html_content(content, 'answer')
                question_data.update(answer_content)

            # Save images
            image_files = [f for f in files.keys() if f.startswith('image_') and f.endswith(('.png', '.jpg', '.jpeg'))]
            if image_files:
                exam_images_dir = DATA_DIR / exam_name / "images"
                exam_images_dir.mkdir(parents=True, exist_ok=True)

                saved_images = []
                for img_file in image_files:
                    img_path = exam_images_dir / f"{folder_name}_{img_file}"
                    content = files[img_file].read() if hasattr(files[img_file], 'read') else files[img_file]
                    with open(img_path, 'wb') as f:
                        f.write(content)
                    saved_images.append(f"{folder_name}_{img_file}")
                question_data['saved_images'] = saved_images

            questions.append(question_data)

    # Sort questions by topic and question index
    questions.sort(key=lambda x: (x['topic_index'], x['question_index']))

    return questions

def process_zip_file(zip_file, exam_name: str) -> List[Dict[str, Any]]:
    """Process uploaded ZIP file and extract question data"""
    questions = []

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Extract ZIP contents
        folders = extract_zip_file(zip_file, temp_path)

        # Process each folder
        for folder_name, files in folders.items():
            folder_info = parse_folder_name(folder_name)
            if not folder_info:
                continue

            question_data = {
                'topic_index': folder_info['topic_index'],
                'question_index': folder_info['question_index'],
                'question_name': f"Topic {folder_info['topic_index']} - Question {folder_info['question_index']}"
            }

            # Process summary_question.html
            if 'summary_question.html' in files:
                content = files['summary_question.html'].decode('utf-8')
                question_content = extract_html_content(content, 'question')
                question_data.update(question_content)

            # Process summary_discussion_ai.html
            if 'summary_discussion_ai.html' in files:
                content = files['summary_discussion_ai.html'].decode('utf-8')
                answer_content = extract_html_content(content, 'answer')
                question_data.update(answer_content)

            # Save images - NOW SEPARATE THEM
            image_files = [f for f in files.keys() if f.startswith('image_') and f.endswith(('.png', '.jpg', '.jpeg'))]
            if image_files:
                exam_images_dir = DATA_DIR / exam_name / "images"
                exam_images_dir.mkdir(parents=True, exist_ok=True)
                
                # Save all image files
                saved_images = []
                for img_file in image_files:
                    img_path = exam_images_dir / f"{folder_name}_{img_file}"
                    content = files[img_file].read() if hasattr(files[img_file], 'read') else files[img_file]
                    with open(img_path, 'wb') as f:
                        f.write(content)
                    saved_images.append(f"{folder_name}_{img_file}")
                
                # Determine which images are for question vs answer based on extracted image references
                question_images = []
                answer_images = []
                
                # If we have image references from HTML, use those to determine placement
                question_img_refs = question_data.get('question_images', [])
                answer_img_refs = question_data.get('answer_images', [])
                
                for img_file in saved_images:
                    # Check if image is referenced in question or answer HTML
                    # If no explicit reference, put in question by default for backward compatibility
                    if any(ref in img_file for ref in question_img_refs) or not answer_img_refs:
                        question_images.append(img_file)
                    if any(ref in img_file for ref in answer_img_refs):
                        answer_images.append(img_file)
                
                question_data['saved_images'] = question_images
                question_data['answer_images'] = answer_images

            questions.append(question_data)

    # Sort questions by topic and question index
    questions.sort(key=lambda x: (x['topic_index'], x['question_index']))

    return questions

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

    # Add password protection if provided
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

def unlock_exam_dialog(exam_name: str):
    """Show password dialog to unlock exam"""
    exam_data = load_exam(exam_name)

    if not exam_data or not exam_data.get('password_protected'):
        del st.session_state.exam_to_unlock
        return

    st.markdown("---")
    st.markdown(f"### 🔐 Unlock Exam: {exam_name}")

    with st.form(key=f"unlock_form_{exam_name}"):
        password = st.text_input(
            "Enter Password",
            type="password",
            help="Enter the password to access this exam"
        )

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
                    # Add to authenticated exams
                    if exam_name not in st.session_state.authenticated_exams:
                        st.session_state.authenticated_exams.append(exam_name)
                    
                    st.success("✅ Exam unlocked successfully!")
                    del st.session_state.exam_to_unlock
                    
                    # Stay on home page to show unlocked view (don't redirect to study)
                    st.rerun()
                else:
                    st.error("❌ Incorrect password. Please try again.")
            else:
                st.warning("⚠️ Please enter a password")


# ============= PAGE FUNCTIONS =============

def home_page():
    """Display home page with exam list"""
    st.markdown('<h1 class="main-header">📚 NotJustExam Study Portal</h1>', unsafe_allow_html=True)
    st.markdown("### Your comprehensive exam preparation platform")

    # Create new exam button
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("➕ Create New Exam", use_container_width=True):
            st.session_state.current_page = "create_exam"
            st.rerun()

    st.markdown("---")

    # List existing exams
    exams = list_exams()

    if not exams:
        st.info("📝 No exams found. Create your first exam to get started!")
    else:
        st.subheader(f"📖 Your Exams ({len(exams)})")

        for exam_name in exams:
            exam_data = load_exam(exam_name)
            if exam_data:
                is_protected = exam_data.get('password_protected', False)
                is_authenticated = is_exam_authenticated(exam_name)

                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        # Show lock icon if protected
                        icon = "🔒" if is_protected and not is_authenticated else "📚"
                        st.markdown(f"### {icon} {exam_name}")
                        st.caption(f"{exam_data['question_count']} questions | Created: {exam_data.get('created_at', 'N/A')[:10]}")
                        if is_protected and is_authenticated:
                            st.caption("✅ Unlocked")

                    with col2:
                        # Show Unlock or Study button
                        if is_protected and not is_authenticated:
                            if st.button("🔓 Unlock", key=f"unlock_{exam_name}", use_container_width=True):
                                st.session_state.exam_to_unlock = exam_name
                                st.rerun()
                        else:
                            if st.button("📖 Study", key=f"study_{exam_name}", use_container_width=True):
                                st.session_state.selected_exam = exam_name
                                st.session_state.current_page = "study_exam"
                                st.session_state.current_question_index = 0
                                st.session_state.show_answer = {}
                                st.rerun()

                    with col3:
                        if st.button("🗑️ Delete", key=f"delete_{exam_name}", use_container_width=True):
                            if delete_exam(exam_name):
                                # Remove from authenticated list if present
                                if exam_name in st.session_state.get('authenticated_exams', []):
                                    st.session_state.authenticated_exams.remove(exam_name)
                                st.success(f"Deleted exam: {exam_name}")
                                st.rerun()
                            else:
                                st.error("Failed to delete exam")

                    # ADD DOWNLOAD BUTTON - Only show if exam is unlocked or not protected
                    if not is_protected or is_authenticated:
                        with st.container():
                            if st.button("📥 Download Offline", key=f"download_{exam_name}", use_container_width=True):
                                download_exam_handler(exam_name)

                    st.markdown("---")


        # Password unlock dialog
        if "exam_to_unlock" in st.session_state and st.session_state.exam_to_unlock:
            unlock_exam_dialog(st.session_state.exam_to_unlock)


def create_exam_page():
    """Page for creating a new exam"""
    st.title("➕ Create New Exam")

    if st.button("⬅️ Back to Home"):
        st.session_state.current_page = "home"
        st.rerun()

    st.markdown("---")

    # Instructions
    st.markdown("""
    ### 📋 Instructions
    1. Enter a unique name for your exam
    2. **Choose upload method:** ZIP file (recommended) or individual files
    3. Each folder should have the format: `topic_<topic_index>_question_<question_index>`
    4. Each folder must contain:
        - `summary_question.html` - The question content
        - `summary_discussion_ai.html` - Discussion and AI recommended answer
        - `image_<index>.png` - Any associated images (optional)
    """)

    st.markdown("---")

    # Exam name input
    exam_name = st.text_input(
        "Exam Name *",
        placeholder="e.g., Azure AZ-104 Administrator",
        help="Enter a unique name for this exam"
    )

    # Check if exam already exists
    if exam_name and exam_name in list_exams():
        st.warning(f"⚠️ Exam '{exam_name}' already exists. Creating it will replace the existing exam.")

    st.markdown("### Choose Upload Method")

    # Upload method selector
    upload_method = st.radio(
        "Select how you want to upload your content:",
        ["📦 Upload ZIP File (Recommended)", "📁 Upload Individual Files"],
        horizontal=True
    )

    uploaded_zip = None
    uploaded_files = None

    if upload_method == "📦 Upload ZIP File (Recommended)":
        st.markdown("""
        #### 📦 ZIP File Upload
        Upload a single ZIP file containing all your question folders.

        **ZIP Structure Example:**
        ```
        exam_content.zip
        ├── topic_1_question_1/
        │   ├── summary_question.html
        │   ├── summary_discussion_ai.html
        │   └── image_0.png
        ├── topic_1_question_2/
        │   ├── summary_question.html
        │   └── summary_discussion_ai.html
        └── topic_2_question_1/
            └── ...
        ```
        """)

        # Password protection section
        st.markdown("---")
        st.markdown("### 🔒 Password Protection (Optional)")

        enable_password = st.checkbox(
            "Password protect this exam",
            help="Require a password to access this exam content"
        )

        exam_password = None
        exam_password_confirm = None

        if enable_password:
            col1, col2 = st.columns(2)
            with col1:
                exam_password = st.text_input(
                    "Set Password",
                    type="password",
                    help="Minimum 4 characters",
                    key="exam_password"
                )
            with col2:
                exam_password_confirm = st.text_input(
                    "Confirm Password",
                    type="password",
                    key="exam_password_confirm"
                )

            # Validate passwords
            if exam_password and exam_password_confirm:
                if exam_password != exam_password_confirm:
                    st.error("❌ Passwords do not match!")
                elif len(exam_password) < 4:
                    st.warning("⚠️ Password should be at least 4 characters")
                else:
                    st.success("✅ Password set successfully")

        st.markdown("---")

        uploaded_zip = st.file_uploader(
            "Upload ZIP file containing all question folders",
            type=['zip'],
            help="Upload a ZIP file with all your exam content"
        )

        if uploaded_zip:
            st.success(f"✅ ZIP file uploaded: {uploaded_zip.name} ({uploaded_zip.size / 1024:.1f} KB)")

            # Preview ZIP contents
            with st.expander("📂 View ZIP contents"):
                try:
                    with zipfile.ZipFile(uploaded_zip, 'r') as zip_ref:
                        file_list = zip_ref.namelist()
                        folders_preview = {}

                        for file_path in file_list:
                            if not file_path.endswith('/') and not '__MACOSX' in file_path:
                                parts = Path(file_path).parts
                                if len(parts) >= 2:
                                    folder = parts[0]
                                    if folder not in folders_preview:
                                        folders_preview[folder] = []
                                    folders_preview[folder].append(parts[-1])

                        for folder, files in folders_preview.items():
                            st.write(f"**{folder}/**")
                            for file in files:
                                st.write(f"  - {file}")

                    # Reset file pointer
                    uploaded_zip.seek(0)
                except Exception as e:
                    st.error(f"Error reading ZIP file: {str(e)}")

    else:  # Individual files upload
        st.markdown("""
        #### 📁 Individual Files Upload
        Select all HTML and image files from your question folders.
        Make sure files maintain their folder structure in the filename.
        """)

        uploaded_files = st.file_uploader(
            "Upload all files from your question folders",
            type=['html', 'png', 'jpg', 'jpeg'],
            accept_multiple_files=True,
            help="Select all HTML and image files. File paths should include folder names (e.g., topic_1_question_1/summary_question.html)"
        )

        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} files uploaded")

            # Preview uploaded files structure
            with st.expander("📂 View uploaded files structure"):
                folders_preview = {}
                for f in uploaded_files:
                    parts = f.name.split('/')
                    if len(parts) >= 2:
                        folder = parts[0]
                        if folder not in folders_preview:
                            folders_preview[folder] = []
                        folders_preview[folder].append(parts[-1])

                for folder, files in folders_preview.items():
                    st.write(f"**{folder}/**")
                    for file in files:
                        st.write(f"  - {file}")

    # Parse and save button
    st.markdown("---")
    can_process = exam_name and (uploaded_zip is not None or (uploaded_files is not None and len(uploaded_files) > 0))

    if st.button("🔄 Parse and Save Exam", type="primary", disabled=not can_process):
        if exam_name:
            # Validate password if enabled
            if enable_password:
                if not exam_password or not exam_password_confirm:
                    st.error("❌ Please enter and confirm password")
                    st.stop()
                elif exam_password != exam_password_confirm:
                    st.error("❌ Passwords do not match!")
                    st.stop()
                elif len(exam_password) < 4:
                    st.error("❌ Password must be at least 4 characters")
                    st.stop()

            with st.spinner("Processing uploaded files... Please wait."):
                try:
                    questions = []

                    # Process based on upload method
                    if uploaded_zip:
                        questions = process_zip_file(uploaded_zip, exam_name)
                    elif uploaded_files:
                        questions = process_uploaded_folders(uploaded_files, exam_name)

                    if questions:
                        # Save exam with password if provided
                        password_to_save = exam_password if enable_password else None
                        save_exam(exam_name, questions, password=password_to_save)

                        st.success(f"✅ Successfully created exam: {exam_name}")
                        if enable_password:
                            st.info("🔒 This exam is password protected")
                        st.balloons()

                        # Show summary
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Questions", len(questions))
                        with col2:
                            topics = len(set(q['topic_index'] for q in questions))
                            st.metric("Topics", topics)
                        with col3:
                            images = sum(len(q.get('saved_images', [])) for q in questions)
                            st.metric("Images", images)

                        st.info("👉 Go back to home to start studying!")
                    else:
                        st.error("❌ No valid questions found")

                except Exception as e:
                    st.error(f"❌ Error processing files: {str(e)}")


def study_exam_page():
    """Page for studying an exam"""
    exam_name = st.session_state.selected_exam
    exam_data = load_exam(exam_name)

    if not exam_data:
        st.error("Exam not found")
        if st.button("⬅️ Back to Home"):
            st.session_state.current_page = "home"
            st.rerun()
        return

    # Check if exam is password protected and not authenticated
    if exam_data.get('password_protected', False) and not is_exam_authenticated(exam_name):
        st.warning("🔒 This exam is password protected")
        st.info("Please unlock the exam from the home page first")
        if st.button("⬅️ Back to Home"):
            st.session_state.current_page = "home"
            st.rerun()
        return

    # Continue with normal study page logic...
    questions = exam_data['questions']
    current_idx = st.session_state.current_question_index

    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title(f"📖 {exam_name}")
    with col2:
        if st.button("🏠 Exit to Home"):
            st.session_state.current_page = "home"
            st.rerun()

    # Progress
    st.progress((current_idx + 1) / len(questions))
    st.caption(f"Question {current_idx + 1} of {len(questions)}")

    st.markdown("---")

    # ENHANCED: Navigation, Question Selector, and Answer Toggle Buttons at TOP
    question = questions[current_idx]
    question_id = f"q_{question['topic_index']}_{question['question_index']}"

    # Initialize show_answer state for this question
    if question_id not in st.session_state.show_answer:
        st.session_state.show_answer[question_id] = False

    # Top button row with 5 columns (added question selector)
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1.2, 1, 0.8])

    with col1:
        if current_idx > 0:
            if st.button("⬅️ Previous", key=f"prev_top_{question_id}", use_container_width=True):
                st.session_state.current_question_index -= 1
                st.rerun()
        else:
            st.button("⬅️ Previous", key=f"prev_top_disabled_{question_id}", use_container_width=True, disabled=True)

    with col2:
        if current_idx < len(questions) - 1:
            if st.button("Next ➡️", key=f"next_top_{question_id}", use_container_width=True):
                st.session_state.current_question_index += 1
                st.rerun()
        else:
            if st.button("🎉 Finish", key=f"finish_top_{question_id}", use_container_width=True, type="primary"):
                st.success("🎉 Congratulations! You've completed all questions!")
                st.balloons()

    with col3:
        # Question selector - allows jumping to any question
        selected_question = st.selectbox(
            "Jump to Question:",
            options=list(range(1, len(questions) + 1)),
            index=current_idx,
            key=f"question_selector_{question_id}",
            label_visibility="collapsed",
            help="Select a question number to jump directly to it"
        )
        if selected_question - 1 != current_idx:
            st.session_state.current_question_index = selected_question - 1
            st.rerun()

    with col4:
        if not st.session_state.show_answer[question_id]:
            if st.button("💡 Show Answer", key=f"show_top_{question_id}", use_container_width=True):
                st.session_state.show_answer[question_id] = True
                st.rerun()
        else:
            if st.button("🔒 Hide Answer", key=f"hide_top_{question_id}", use_container_width=True):
                st.session_state.show_answer[question_id] = False
                st.rerun()

    with col5:
        # Empty column for spacing or future use
        st.write("")

    st.markdown("---")

    # Display current question
    st.markdown(f"## {question['question_name']}")

    # Question content
    with st.container():
        # Get and deduplicate question text
        question_text = question.get('question', 'No question text available')
        question_text = remove_duplicate_chunks(question_text)

        # Convert to HTML with line breaks
        question_html = question_text.replace('\n', '<br>')

        # Display question with clean styled HTML (white background, colored border)
        styled_question = f"""
        <div class="question-text" style="
            padding: 20px;
            background: white;
            border-left: 4px solid #667eea;
            border-radius: 8px;
            margin: 16px 0;
            line-height: 1.8;
            box-shadow: 0 2px 4px rgba(0,0,0,0.08);
        ">
            {question_html}
        </div>
        """
        st.markdown(styled_question, unsafe_allow_html=True)

        # Display question images only
        if question.get('saved_images'):
            for img_file in question['saved_images']:
                img_path = DATA_DIR / st.session_state.selected_exam / "images" / img_file
                if img_path.exists():
                    st.image(str(img_path))

        # Display answer choices if they exist with HTML styling
        if question.get('choices'):
            st.markdown("### Answer Options:")

            # Create styled options HTML
            for letter, text in sorted(question['choices'].items()):
                is_correct = (letter == question.get('suggested_answer') or 
                             letter == question.get('correct_answer'))

                # Show correct answer with green styling when answer is shown
                if st.session_state.show_answer.get(question_id, False) and is_correct:
                    option_html = f"""
                    <div style="
                        padding: 16px;
                        margin: 12px 0;
                        border: 2px solid #28a745;
                        background: #d4edda;
                        border-radius: 10px;
                        font-weight: 500;
                    ">
                        <strong>{letter}.</strong> {text}
                    </div>
                    """
                else:
                    option_html = f"""
                    <div style="
                        padding: 16px;
                        margin: 12px 0;
                        border: 2px solid #e9ecef;
                        background: white;
                        border-radius: 10px;
                    ">
                        <strong>{letter}.</strong> {text}
                    </div>
                    """
                st.markdown(option_html, unsafe_allow_html=True)

    # Display answer if shown
    if st.session_state.show_answer.get(question_id, False):
        with st.container():
            # # Show answer images only here
            # if question.get('answer_images'):
            #     for img_file in question['answer_images']:
            #         img_path = DATA_DIR / st.session_state.selected_exam / "images" / img_file
            #         if img_path.exists():
            #             st.image(str(img_path))

            # Suggested Answer with HTML support
            if question.get('suggested_answer_html'):
                st.markdown("### ✅ Suggested Answer")

                # Convert HTML images to base64
                folder_prefix = f"topic_{question['topic_index']}_question_{question['question_index']}"
                answer_html_converted = convert_html_images_to_base64(
                    question['suggested_answer_html'], 
                    exam_name, 
                    folder_prefix
                )

                answer_styled = f"""
                <div class="answer" style="
                    margin-top: 24px;
                    padding: 20px;
                    background: #f8f9fa;
                    border-radius: 10px;
                    border-left: 4px solid #28a745;
                ">
                    {answer_html_converted}
                </div>
                """
                st.markdown(answer_styled, unsafe_allow_html=True)
            elif question.get('suggested_answer'):
                st.success(f"**Answer:** {question['suggested_answer']}")

            # Discussion Summary with HTML support
            if question.get('discussion_summary_html'):
                st.markdown("### 💬 Discussion")

                # Convert HTML images to base64
                discussion_html_converted = convert_html_images_to_base64(
                    question['discussion_summary_html'], 
                    exam_name, 
                    folder_prefix
                )

                discussion_styled = f"""
                <div class="discussion" style="
                    margin: 16px 0;
                    padding: 20px;
                    background: white;
                    border-radius: 10px;
                    border-left: 4px solid #667eea;
                    line-height: 1.7;
                ">
                    {discussion_html_converted}
                </div>
                """
                st.markdown(discussion_styled, unsafe_allow_html=True)

            # AI Recommendation with HTML support
            if question.get('ai_recommendation_html'):
                st.markdown("### 🤖 AI Recommendation")

                # Convert HTML images to base64
                ai_html_converted = convert_html_images_to_base64(
                    question['ai_recommendation_html'], 
                    exam_name, 
                    folder_prefix
                )

                ai_styled = f"""
                <div class="ai-answer" style="
                    margin: 16px 0;
                    padding: 20px;
                    background: white;
                    border-radius: 10px;
                    border-left: 4px solid #764ba2;
                    line-height: 1.7;
                ">
                    {ai_html_converted}
                </div>
                """
                st.markdown(ai_styled, unsafe_allow_html=True)


def main():
    """Main application entry point"""
    initialize_session_state()

    # Sidebar
    with st.sidebar:
        st.markdown("# 🎓 NotJustExam")
        st.markdown("### Premium Exam Dumps & Study Materials")
        st.markdown("---")

        # Navigation
        if st.session_state.current_page != "home":
            if st.button("🏠 Home", use_container_width=True):
                st.session_state.current_page = "home"
                st.rerun()

        st.markdown("---")

        # Current exam info
        if st.session_state.selected_exam:
            st.markdown("**Current Exam:**")
            st.info(st.session_state.selected_exam)
            exam_data = load_exam(st.session_state.selected_exam)
            if exam_data:
                st.caption(f"{exam_data['question_count']} questions")

        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        NotJustExam provides comprehensive exam preparation materials featuring:
        - ✅ Verified exam questions
        - 💬 Community discussions
        - 🤖 AI-powered explanations
        - 📚 Detailed references
        """)

    # Route to appropriate page
    if st.session_state.current_page == "home":
        home_page()
    elif st.session_state.current_page == "create_exam":
        create_exam_page()
    elif st.session_state.current_page == "study_exam":
        study_exam_page()
    else:
        home_page()

if __name__ == "__main__":
    main()
