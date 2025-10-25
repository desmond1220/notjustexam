
# Create a deployment guide document
deployment_guide = '''# Streamlit Cloud Deployment Guide

## Quick Deployment Steps

### 1. Prepare GitHub Repository

Create a new GitHub repository with these files:
- `app.py` (renamed from notjustexam_app.py)
- `requirements.txt`
- `README.md`
- `.gitignore` (optional but recommended)

### 2. Create .gitignore (Optional)

Add this content to `.gitignore`:
```
exam_data/
__pycache__/
*.pyc
.DS_Store
*.log
```

### 3. Deploy to Streamlit Cloud

1. Visit: https://share.streamlit.io
2. Sign in with your GitHub account
3. Click "New app"
4. Fill in the deployment form:
   - **Repository**: Select your GitHub repo
   - **Branch**: main (or master)
   - **Main file path**: app.py
   - **App URL**: Choose a custom URL (optional)

5. Click "Deploy!" button

### 4. Wait for Deployment

- Initial deployment takes 2-5 minutes
- Watch the deployment logs for any errors
- Once complete, your app will be live!

## File Upload Instructions

When using the deployed app:

### Preparing Files for Upload

1. **Organize your question folders** locally:
```
your_exam_content/
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

2. **Create a ZIP file** (recommended for many folders):
   - Right-click on each folder
   - Add to ZIP archive
   - Or use command line: `zip -r exam_content.zip topic_*`

3. **Alternative**: Select all files manually
   - Navigate to your content directory
   - Press Ctrl+A (Windows) or Cmd+A (Mac)
   - Ensure file paths include folder names

### Uploading to the App

1. Click "➕ Create New Exam"
2. Enter exam name
3. Click "Upload all files from your question folders"
4. Select all files (HTML + images) from your folders
5. Click "🔄 Parse and Save Exam"

**Important**: When selecting files, ensure the folder structure is maintained in the filename path.

## Troubleshooting Deployment

### Error: "Module not found"
- Check `requirements.txt` has all dependencies
- Verify spelling and versions
- Try redeploying

### Error: "App not loading"
- Check Streamlit Cloud logs
- Verify `app.py` has no syntax errors
- Ensure all imports are in requirements.txt

### Error: "File upload fails"
- Check file size limits (Streamlit has 200MB limit)
- Verify file extensions (.html, .png, .jpg)
- Ensure folder structure in filenames

### Performance Issues
- Large number of questions may slow down
- Consider splitting into multiple exams
- Optimize image sizes

## Post-Deployment

### Updating Your App

1. Push changes to GitHub repository
2. Streamlit Cloud auto-deploys on push
3. Watch deployment logs
4. Test new changes

### Managing Data

- Data persists only during the session on Streamlit Cloud
- For permanent storage, consider:
  - GitHub repository for exam data
  - External database (PostgreSQL, MongoDB)
  - Cloud storage (S3, Google Cloud Storage)

### Monitoring

- Check app health in Streamlit Cloud dashboard
- Monitor resource usage
- Review error logs

## Best Practices

1. **Version Control**: Commit frequently to GitHub
2. **Testing**: Test locally before deploying
3. **Documentation**: Keep README.md updated
4. **Backup**: Keep backups of exam data
5. **Security**: Don't commit sensitive data

## Custom Domain (Optional)

To use a custom domain:

1. Go to Streamlit Cloud settings
2. Click on your app
3. Navigate to "Settings" → "General"
4. Add custom domain
5. Update DNS records as instructed

## Limitations

Streamlit Cloud Free Tier:
- 1 GB RAM
- 1 CPU core
- 1 app per account
- Limited to 3 apps total

For more resources, consider:
- Streamlit Cloud paid plans
- Self-hosting on AWS/Azure/GCP
- Docker deployment

## Support Resources

- Streamlit Documentation: https://docs.streamlit.io
- Streamlit Community: https://discuss.streamlit.io
- GitHub Issues: Your repository issues page

---

Good luck with your deployment! 🚀
'''

with open('DEPLOYMENT_GUIDE.md', 'w', encoding='utf-8') as f:
    f.write(deployment_guide)

print("✅ Created: DEPLOYMENT_GUIDE.md")

# Create a .gitignore file
gitignore = '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Streamlit
.streamlit/

# Data
exam_data/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log
'''

with open('.gitignore', 'w', encoding='utf-8') as f:
    f.write(gitignore)

print("✅ Created: .gitignore")
