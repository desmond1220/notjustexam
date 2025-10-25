
# Create requirements.txt for Streamlit deployment
requirements = '''streamlit==1.32.0
beautifulsoup4==4.12.3
Pillow==10.2.0
'''

with open('requirements.txt', 'w', encoding='utf-8') as f:
    f.write(requirements)

print("✅ Created: requirements.txt")

# Create README.md with deployment instructions
readme = '''# NotJustExam - Streamlit Study Portal

A comprehensive exam preparation platform for managing and studying exam dumps with AI-powered explanations and community discussions.

## Features

✨ **Key Features:**
- 📚 Create and manage multiple exams
- 📂 Upload question folders with structured content
- 💡 View suggested answers with explanations
- 💬 Access internet discussion summaries
- 🤖 Get AI-recommended answers with references
- 📷 Support for images and diagrams
- 📊 Clean and intuitive user interface

## Question Folder Structure

Each question should be in a folder with this naming format:
```
topic_<topic_index>_question_<question_index>
```

### Required Files in Each Folder:

1. **summary_question.html** - Contains:
   - Question text
   - Answer options (A, B, C, D)
   - Associated images (optional)

2. **summary_discussion_ai.html** - Contains:
   - Suggested answer
   - Internet discussion summary
   - AI recommended answer
   - References and citations

3. **image_<index>.png** - Optional image files

### Example Folder Structure:
```
topic_1_question_1/
├── summary_question.html
├── summary_discussion_ai.html
├── image_0.png
└── image_1.png

topic_1_question_2/
├── summary_question.html
└── summary_discussion_ai.html

topic_2_question_1/
├── summary_question.html
├── summary_discussion_ai.html
└── image_0.png
```

## Deployment to Streamlit Cloud

### Step 1: Prepare Your Repository

1. Create a new GitHub repository
2. Upload these files:
   - `notjustexam_app.py` (rename to `app.py`)
   - `requirements.txt`
   - `README.md`

### Step 2: Deploy to Streamlit

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click "New app"
4. Select your repository
5. Set the main file path to `app.py`
6. Click "Deploy"

### Step 3: Upload Your Exam Content

1. When uploading files, maintain the folder structure in filenames:
   - Format: `topic_X_question_Y/filename.html`
   - Example: `topic_1_question_1/summary_question.html`

2. You can upload multiple folders at once
3. The app will automatically parse and organize your questions

## Local Development

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd notjustexam
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run app.py
```

4. Open your browser to `http://localhost:8501`

## Usage Guide

### Creating a New Exam

1. Click "➕ Create New Exam" on the home page
2. Enter a unique exam name (e.g., "Azure AZ-104 Administrator")
3. Upload all HTML and image files from your question folders
4. Click "🔄 Parse and Save Exam"
5. Wait for processing to complete

### Studying an Exam

1. From the home page, click "📖 Study" on any exam
2. Navigate through questions using Previous/Next buttons
3. Click "💡 Show Answer" to reveal:
   - Suggested answer
   - Internet discussion summary
   - AI recommended answer with references
4. Use "🔒 Hide Answer" to hide the answer section

### Managing Exams

- **Delete**: Click "🗑️ Delete" to remove an exam
- **Home**: Click "🏠 Home" to return to the exam list

## File Upload Tips

When preparing files for upload:

1. **Maintain folder structure in filenames**:
   - Good: `topic_1_question_1/summary_question.html`
   - Bad: `summary_question.html`

2. **Select all files at once**:
   - Use Ctrl+A (Windows) or Cmd+A (Mac) to select all files
   - The app supports multiple file uploads

3. **Supported file types**:
   - HTML files: `.html`
   - Images: `.png`, `.jpg`, `.jpeg`

## Data Storage

- All exam data is stored in the `exam_data/` directory
- Each exam has its own folder containing:
  - `exam_data.json` - Question metadata and content
  - `images/` - Associated images

## Troubleshooting

### Files not uploading correctly
- Ensure filenames include the folder path (e.g., `topic_1_question_1/summary_question.html`)
- Check that HTML files are properly formatted
- Verify image files are in PNG or JPEG format

### Questions not parsing
- Verify HTML structure matches the expected format
- Check that folder names follow the `topic_X_question_Y` pattern
- Ensure required files (`summary_question.html` and `summary_discussion_ai.html`) are present

### Images not displaying
- Confirm image files are uploaded with correct folder prefix
- Check image file extensions (`.png`, `.jpg`, `.jpeg`)
- Verify images are referenced correctly in HTML files

## Technical Details

### Dependencies
- **Streamlit**: Web application framework
- **BeautifulSoup4**: HTML parsing
- **Pillow**: Image processing

### Browser Support
- Chrome (recommended)
- Firefox
- Safari
- Edge

## License

This project is provided as-is for educational purposes.

## Support

For issues or questions, please create an issue in the GitHub repository.

---

**NotJustExam** - Your comprehensive exam preparation solution 📚✨
'''

with open('README.md', 'w', encoding='utf-8') as f:
    f.write(readme)

print("✅ Created: README.md")
