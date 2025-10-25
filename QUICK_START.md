# 🚀 Quick Start Guide - NotJustExam

Get your exam study portal up and running in 10 minutes!

## ⚡ Super Quick Setup

### Prerequisites
- GitHub account
- Streamlit Cloud account (free at share.streamlit.io)
- Your exam content folders

### Step 1: Download Project Files (2 minutes)

Download these essential files:
1. `notjustexam_app.py` → Rename to `app.py`
2. `requirements.txt`
3. `README.md`
4. `.gitignore`

### Step 2: Create GitHub Repository (2 minutes)

1. Go to GitHub.com
2. Click "New repository"
3. Name it: `notjustexam` (or your choice)
4. Set to Public
5. Click "Create repository"

### Step 3: Upload Files to GitHub (2 minutes)

```bash
# Option A: Using Git command line
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/notjustexam.git
git push -u origin main

# Option B: Using GitHub web interface
# 1. Click "Add file" → "Upload files"
# 2. Drag and drop all files
# 3. Commit changes
```

### Step 4: Deploy to Streamlit (3 minutes)

1. Visit: https://share.streamlit.io
2. Sign in with GitHub
3. Click "New app"
4. Fill in:
   - **Repository**: your-username/notjustexam
   - **Branch**: main
   - **Main file path**: app.py
5. Click "Deploy!"

### Step 5: Upload Your Content (1 minute)

1. Once deployed, open your app
2. Click "➕ Create New Exam"
3. Enter exam name
4. Upload your question folders
5. Click "Parse and Save"

## 🎉 You're Done!

Your app is now live at: `https://your-app-name.streamlit.app`

---

## 📚 Preparing Your Question Content

### Required Folder Structure

```
your-exam-content/
├── topic_1_question_1/
│   ├── summary_question.html
│   ├── summary_discussion_ai.html
│   └── image_0.png
├── topic_1_question_2/
│   ├── summary_question.html
│   └── summary_discussion_ai.html
└── topic_2_question_1/
    ├── summary_question.html
    ├── summary_discussion_ai.html
    └── image_0.png
```

### File Upload Tips

**Method 1: Direct Upload (Recommended)**
1. Open all question folders
2. Select all HTML and image files
3. Ensure filenames include folder paths
4. Upload in one go

**Method 2: Using Upload Helper**
```bash
python upload_helper.py
# Choose option 1
# Enter your content directory path
# Creates organized upload package
```

---

## 🔧 Testing Locally First

Before deploying, test locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py

# Open browser to http://localhost:8501
```

---

## 📖 Example Workflow

### Creating Your First Exam

1. **Launch App** → Click "Create New Exam"
2. **Enter Name** → "Azure AZ-104 Administrator"
3. **Upload Files** → Select all from topic folders
4. **Parse** → Click "Parse and Save Exam"
5. **Study** → Click "Study" on home page

### Studying Questions

1. **Select Exam** → Click "Study" button
2. **Read Question** → Review question and options
3. **Show Answer** → Click "💡 Show Answer"
4. **Review** → Read suggested answer, discussion, and AI explanation
5. **Navigate** → Use Previous/Next buttons

---

## 🎯 Common Use Cases

### Use Case 1: IT Certification Exam Prep
**Example**: Microsoft Azure, AWS, CompTIA
- Upload vendor exam dumps
- Study with explanations
- Review community feedback

### Use Case 2: Academic Course Study
**Example**: University finals, entrance exams
- Organize by topics
- Include practice questions
- Reference materials included

### Use Case 3: Interview Preparation
**Example**: Technical interviews
- Curate common questions
- Add multiple solution approaches
- Include best practices

---

## ❓ Troubleshooting

### Problem: Files Not Uploading
**Solution**: 
- Check file paths include folder names
- Verify HTML format is correct
- Try smaller batches

### Problem: Images Not Showing
**Solution**:
- Ensure images are PNG/JPG
- Check image references in HTML
- Verify folder naming convention

### Problem: Questions Not Parsing
**Solution**:
- Validate HTML structure
- Check required div classes
- Use BeautifulSoup locally to test

### Problem: App Not Loading
**Solution**:
- Check Streamlit Cloud logs
- Verify requirements.txt
- Redeploy from GitHub

---

## 📞 Need Help?

1. **Documentation**: Read README.md for detailed info
2. **Structure Guide**: See PROJECT_STRUCTURE.md
3. **Deployment**: Check DEPLOYMENT_GUIDE.md
4. **GitHub Issues**: Create an issue for bugs

---

## 🎓 Pro Tips

### Tip 1: Organize Content Efficiently
- Use consistent naming: `topic_X_question_Y`
- Keep images optimized (< 500KB each)
- Group related questions by topic

### Tip 2: Enhance Your Content
- Add detailed explanations in AI section
- Include multiple references
- Update discussion summaries regularly

### Tip 3: Maintain Your App
- Regularly update dependencies
- Backup exam data to GitHub
- Monitor Streamlit Cloud usage

### Tip 4: Scale Your Platform
- Create multiple topic-specific exams
- Share with study groups
- Consider adding user accounts

---

## 📈 Next Steps

After basic setup:

1. **Customize Appearance**
   - Edit CSS in app.py
   - Modify colors and fonts
   - Add your branding

2. **Add More Features**
   - Progress tracking
   - Quiz mode with timer
   - Score calculation
   - Export results

3. **Expand Content**
   - Add more exams
   - Include video explanations
   - Link external resources

4. **Share Your Platform**
   - Share URL with friends
   - Create study groups
   - Collect feedback

---

## 🌟 Success Story Example

**Before**: Scattered PDF files, no organization
**After**: Centralized platform with 500+ questions, multiple exams, used by 50+ students

**Time Investment**: 1 hour setup + content upload
**Result**: Professional study portal accessible anywhere

---

## 🚀 Ready to Launch?

Follow the 5 steps above and you'll have your exam portal running in no time!

**Start now**: Create your GitHub repository and deploy your first exam!

Good luck with your studies! 📚✨

---

**NotJustExam Team**  
*Making exam preparation easier, one question at a time*
