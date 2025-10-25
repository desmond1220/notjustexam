# NotJustExam Project Structure

## 📁 Complete File Structure

```
notjustexam/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── README.md                       # Project documentation
├── DEPLOYMENT_GUIDE.md            # Deployment instructions
├── .gitignore                     # Git ignore rules
├── upload_helper.py               # File preparation utility
│
├── exam_data/                     # Created at runtime (gitignored)
│   ├── <exam_name_1>/
│   │   ├── exam_data.json        # Exam metadata and questions
│   │   └── images/               # Exam images
│   │       ├── topic_1_question_1_image_0.png
│   │       └── topic_1_question_2_image_0.png
│   │
│   └── <exam_name_2>/
│       ├── exam_data.json
│       └── images/
│
└── .streamlit/                    # Streamlit config (optional)
    └── config.toml               # App configuration
```

## 📄 File Descriptions

### Core Application Files

#### `app.py`
Main Streamlit application with:
- Home page with exam list
- Exam creation page with file upload
- Study page with question display
- Answer reveal functionality
- Navigation system
- Session state management

**Key Features:**
- BeautifulSoup HTML parsing
- Multiple file upload support
- Image handling and display
- JSON data persistence
- Responsive UI with custom CSS

#### `requirements.txt`
Python package dependencies:
```
streamlit==1.32.0
beautifulsoup4==4.12.3
Pillow==10.2.0
```

#### `README.md`
Complete project documentation including:
- Features overview
- Folder structure requirements
- Deployment instructions
- Usage guide
- Troubleshooting tips

#### `DEPLOYMENT_GUIDE.md`
Step-by-step deployment guide for:
- GitHub repository setup
- Streamlit Cloud deployment
- File upload instructions
- Post-deployment management

#### `.gitignore`
Excludes from version control:
- Python cache files
- Virtual environments
- Exam data directory
- IDE configuration
- OS-specific files

#### `upload_helper.py`
Utility script to:
- Prepare question folders for upload
- Validate folder structure
- Create upload packages
- Generate ZIP files

## 🎯 Question Folder Format

Each question must be in a folder following this structure:

```
topic_<topic_index>_question_<question_index>/
├── summary_question.html           # Required
├── summary_discussion_ai.html      # Required
├── image_0.png                     # Optional
├── image_1.png                     # Optional
└── image_N.png                     # Optional
```

### Folder Naming Convention
- Format: `topic_X_question_Y`
- X = Topic index (integer)
- Y = Question index (integer)
- Examples:
  - `topic_1_question_1`
  - `topic_1_question_2`
  - `topic_2_question_1`

### Required Files

#### `summary_question.html`
Contains:
- Question text with HTML formatting
- Multiple choice options (A, B, C, D)
- Image references (if applicable)
- Correct answer indicator (class="correct-hidden")

**Expected HTML Structure:**
```html
<div class="question">
    <p>Question text here...</p>
</div>
<div class="question-choices-container">
    <ul>
        <li class="multi-choice-item">
            <span class="multi-choice-letter" data-choice-letter="A">A.</span>
            Option A text
        </li>
        <li class="multi-choice-item correct-hidden">
            <span class="multi-choice-letter" data-choice-letter="B">B.</span>
            Option B text (correct answer)
        </li>
        <!-- More options... -->
    </ul>
</div>
```

#### `summary_discussion_ai.html`
Contains:
- Suggested answer
- Internet discussion summary
- AI recommended answer
- Explanation and reasoning
- References and citations

**Expected HTML Structure:**
```html
<div class="answer">
    <p><strong>Suggested Answer:</strong> B</p>
</div>
<div class="discussion-summary">
    <h3>Discussion Summary</h3>
    <p>Community discussion content...</p>
</div>
<div class="ai-recommendation">
    <h3>AI Recommended Answer</h3>
    <p>AI analysis and explanation...</p>
    <ul>
        <li>Citation 1</li>
        <li>Citation 2</li>
    </ul>
</div>
```

### Optional Files

#### `image_<index>.png`
- Image files referenced in questions
- Supported formats: PNG, JPG, JPEG
- Naming: `image_0.png`, `image_1.png`, etc.
- Index starts from 0

## 💾 Data Storage

### `exam_data.json` Format

```json
{
  "exam_name": "Azure AZ-104 Administrator",
  "created_at": "2024-01-15T10:30:00",
  "question_count": 50,
  "questions": [
    {
      "topic_index": 1,
      "question_index": 1,
      "question_name": "Topic 1 - Question 1",
      "question": "Question text...",
      "choices": {
        "A": "Option A text",
        "B": "Option B text",
        "C": "Option C text",
        "D": "Option D text"
      },
      "correct_answer": "B",
      "suggested_answer": "B",
      "discussion_summary": "Community discussion...",
      "ai_recommendation": "AI analysis...",
      "ai_citations": [
        "Reference 1",
        "Reference 2"
      ],
      "images": ["image_0.png"],
      "saved_images": ["topic_1_question_1_image_0.png"]
    }
  ]
}
```

## 🔧 Configuration (Optional)

Create `.streamlit/config.toml` for custom settings:

```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[server]
maxUploadSize = 200
enableCORS = false
enableXsrfProtection = true
```

## 🚀 Deployment Checklist

Before deploying:
- [ ] Rename `notjustexam_app.py` to `app.py`
- [ ] Verify all dependencies in `requirements.txt`
- [ ] Test locally with sample data
- [ ] Create GitHub repository
- [ ] Add `.gitignore` to exclude `exam_data/`
- [ ] Push code to GitHub
- [ ] Deploy to Streamlit Cloud
- [ ] Test file upload with actual data

## 📊 Data Flow

1. **Upload Phase:**
   ```
   User uploads files → Files grouped by folder → 
   HTML parsed by BeautifulSoup → Images saved → 
   Data stored in JSON
   ```

2. **Study Phase:**
   ```
   User selects exam → Load JSON data → 
   Display question → User clicks "Show Answer" → 
   Display answer sections
   ```

3. **Navigation:**
   ```
   Previous/Next buttons → Update question index → 
   Reload question data → Update display
   ```

## 🔐 Security Considerations

- No sensitive data stored in code
- Exam data stored locally in session
- No external API calls required
- File validation on upload
- Safe HTML parsing with BeautifulSoup

## 📈 Scalability

**Current Limitations:**
- Single-user session storage
- In-memory data (resets on restart)
- 200MB upload limit on Streamlit Cloud

**For Production:**
- Implement database (PostgreSQL, MongoDB)
- Add user authentication
- Use cloud storage (S3, Azure Blob)
- Implement caching
- Add progress tracking

## 🛠️ Maintenance

### Regular Tasks:
- Update dependencies in `requirements.txt`
- Monitor Streamlit Cloud logs
- Backup exam data
- Review and update documentation

### Troubleshooting:
- Check logs in Streamlit Cloud dashboard
- Verify file upload formats
- Validate HTML structure
- Test with different browsers

---

**Project Version:** 1.0.0  
**Last Updated:** 2024  
**Maintained by:** NotJustExam Team
