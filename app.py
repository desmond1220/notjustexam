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
    """Extract content from HTML files using BeautifulSoup with proper formatting"""
    soup = BeautifulSoup(html_content, 'html.parser')
    result = {}
    
    if content_type == 'question':
        # Extract question text with proper formatting
        question_div = soup.find('div', class_='question')
        if question_div:
            # Use separator to maintain paragraph structure
            result['question'] = question_div.get_text(separator='\n\n').strip()
            # Check for images
            images = question_div.find_all('img')
            result['images'] = [img.get('src', '') for img in images]
        
        # Extract choices
        choices = {}
        choice_items = soup.find_all('li', class_='multi-choice-item')
        for item in choice_items:
            letter_span = item.find('span', class_='multi-choice-letter')
            if letter_span:
                letter = letter_span.get('data-choice-letter', '')
                # Get choice text, preserving internal formatting
                choice_text = item.get_text(separator=' ').replace(letter + '.', '', 1).strip()
                choices[letter] = choice_text
                # Check if this is the correct answer
                if 'correct-hidden' in item.get('class', []):
                    result['correct_answer'] = letter
        result['choices'] = choices
        
    elif content_type == 'answer':
        # Extract suggested answer
        answer_div = soup.find('div', class_='answer')
        if answer_div:
            suggested_answer_text = answer_div.get_text(separator=' ').strip()
            # Extract the answer letter
            match = re.search(r'Suggested Answer:\s*([A-Z])', suggested_answer_text)
            if match:
                result['suggested_answer'] = match.group(1)
        
        # Extract discussion summary with proper formatting
        discussion_div = soup.find('div', class_='discussion-summary')
        if discussion_div:
            # Remove the header if present
            header = discussion_div.find('h3')
            if header:
                header.extract()
            
            # Get formatted text with paragraphs preserved
            discussion_text = discussion_div.get_text(separator='\n\n').strip()
            result['discussion_summary'] = discussion_text
        
        # Extract AI recommendation with proper formatting
        ai_div = soup.find('div', class_='ai-recommendation')
        if ai_div:
            # Remove the header if present
            header = ai_div.find('h3')
            if header:
                header.extract()
            
            # Extract main content preserving structure
            content_parts = []
            
            for elem in ai_div.children:
                if elem.name == 'p':
                    text = elem.get_text(separator=' ').strip()
                    if text:
                        content_parts.append(text)
                elif elem.name == 'ul':
                    # Extract list items with bullets
                    items = []
                    for li in elem.find_all('li'):
                        item_text = li.get_text(separator=' ').strip()
                        if item_text:
                            # Check if it's a citation (contains http)
                            if 'http' not in item_text:
                                items.append(f"  • {item_text}")
                            else:
                                items.append(f"  {item_text}")
                    if items:
                        content_parts.append('\n'.join(items))
            
            result['ai_recommendation'] = '\n\n'.join(content_parts)
            
            # Extract citations separately
            citations = []
            citation_uls = ai_div.find_all('ul')
            if citation_uls:
                # Last ul is usually citations
                for li in citation_uls[-1].find_all('li'):
                    citation_text = li.get_text(separator=' ').strip()
                    if citation_text:
                        citations.append(citation_text)
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

            # Save images
            image_files = [f for f in files.keys() if f.startswith('image_') and f.endswith(('.png', '.jpg', '.jpeg'))]
            if image_files:
                exam_images_dir = DATA_DIR / exam_name / "images"
                exam_images_dir.mkdir(parents=True, exist_ok=True)

                saved_images = []
                for img_file in image_files:
                    img_path = exam_images_dir / f"{folder_name}_{img_file}"
                    with open(img_path, 'wb') as f:
                        f.write(files[img_file])
                    saved_images.append(f"{folder_name}_{img_file}")
                question_data['saved_images'] = saved_images

            questions.append(question_data)

    # Sort questions by topic and question index
    questions.sort(key=lambda x: (x['topic_index'], x['question_index']))

    return questions

def save_exam(exam_name: str, questions: List[Dict[str, Any]]):
    """Save exam data to JSON file"""
    exam_dir = DATA_DIR / exam_name
    exam_dir.mkdir(parents=True, exist_ok=True)

    exam_file = exam_dir / "exam_data.json"
    with open(exam_file, 'w', encoding='utf-8') as f:
        json.dump({
            'exam_name': exam_name,
            'created_at': datetime.now().isoformat(),
            'question_count': len(questions),
            'questions': questions
        }, f, indent=2, ensure_ascii=False)

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
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        st.markdown(f"### 📚 {exam_name}")
                        st.caption(f"{exam_data['question_count']} questions | Created: {exam_data.get('created_at', 'N/A')[:10]}")

                    with col2:
                        if st.button("📖 Study", key=f"study_{exam_name}", use_container_width=True):
                            st.session_state.selected_exam = exam_name
                            st.session_state.current_page = "study_exam"
                            st.session_state.current_question_index = 0
                            st.session_state.show_answer = {}
                            st.rerun()

                    with col3:
                        if st.button("🗑️ Delete", key=f"delete_{exam_name}", use_container_width=True):
                            if delete_exam(exam_name):
                                st.success(f"Deleted exam: {exam_name}")
                                st.rerun()
                            else:
                                st.error("Failed to delete exam")

                    st.markdown("---")

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
            with st.spinner("Processing uploaded files... Please wait."):
                try:
                    questions = []

                    # Process based on upload method
                    if uploaded_zip:
                        questions = process_zip_file(uploaded_zip, exam_name)
                    elif uploaded_files:
                        questions = process_uploaded_folders(uploaded_files, exam_name)

                    if questions:
                        # Save exam
                        save_exam(exam_name, questions)

                        st.success(f"✅ Successfully created exam: {exam_name}")
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
                        st.error("❌ No valid questions found in uploaded files. Please check the folder structure and file naming.")

                except Exception as e:
                    st.error(f"❌ Error processing files: {str(e)}")
                    import traceback
                    with st.expander("View error details"):
                        st.code(traceback.format_exc())

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

    # Display current question
    question = questions[current_idx]
    question_id = f"q_{question['topic_index']}_{question['question_index']}"

    st.markdown(f"## {question['question_name']}")

    # Question content
    with st.container():
        st.markdown('<div class="question-container">', unsafe_allow_html=True)

        st.markdown("### Question")
        st.markdown(question.get('question', 'No question text available'))

        # Display images if available
        if 'saved_images' in question and question['saved_images']:
            st.markdown("### 📷 Images")
            img_cols = st.columns(min(len(question['saved_images']), 3))
            for idx, img_file in enumerate(question['saved_images']):
                img_path = DATA_DIR / exam_name / "images" / img_file
                if img_path.exists():
                    with img_cols[idx % 3]:
                        st.image(str(img_path), use_container_width=True)

        # Choices
        if 'choices' in question and question['choices']:
            st.markdown("### Answer Options")
            for letter, choice_text in sorted(question['choices'].items()):
                st.markdown(f"**{letter}.** {choice_text}")

        st.markdown('</div>', unsafe_allow_html=True)

    # Show answer section
    st.markdown("---")

    if question_id not in st.session_state.show_answer:
        st.session_state.show_answer[question_id] = False

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if not st.session_state.show_answer[question_id]:
            if st.button("💡 Show Answer", key=f"show_{question_id}", use_container_width=True):
                st.session_state.show_answer[question_id] = True
                st.rerun()
        else:
            if st.button("🔒 Hide Answer", key=f"hide_{question_id}", use_container_width=True):
                st.session_state.show_answer[question_id] = False
                st.rerun()

    # Display answer if shown
    if st.session_state.show_answer.get(question_id, False):
        st.markdown("### Answer Section")

        # Suggested Answer
        if 'suggested_answer' in question or 'correct_answer' in question:
            st.markdown("#### ✅ Suggested Answer")
            answer = question.get('suggested_answer') or question.get('correct_answer')
            st.markdown(f"**Answer: {answer}**")
            if answer in question.get('choices', {}):
                st.markdown(f"*{question['choices'][answer]}*")

        # Discussion Summary
        if 'discussion_summary' in question:
            st.markdown("#### 💬 Internet Discussion Summary")
            st.markdown(question['discussion_summary'])

        # AI Recommendation
        if 'ai_recommendation' in question:
            st.markdown("#### 🤖 AI Recommended Answer")
            st.markdown(question['ai_recommendation'])

            # Citations
            if 'ai_citations' in question and question['ai_citations']:
                st.markdown("**References:**")
                for citation in question['ai_citations']:
                    st.markdown(f"- {citation}")

    # Navigation
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if current_idx > 0:
            if st.button("⬅️ Previous", use_container_width=True):
                st.session_state.current_question_index -= 1
                st.rerun()

    with col3:
        if current_idx < len(questions) - 1:
            if st.button("Next ➡️", use_container_width=True):
                st.session_state.current_question_index += 1
                st.rerun()
        else:
            if st.button("🎉 Finish", use_container_width=True, type="primary"):
                st.success("🎉 Congratulations! You've completed all questions!")
                st.balloons()

# ============= MAIN APPLICATION =============

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
