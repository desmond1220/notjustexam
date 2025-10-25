
# Create optional Streamlit configuration
streamlit_config = '''[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[server]
maxUploadSize = 200
enableCORS = false
enableXsrfProtection = true
headless = true

[browser]
gatherUsageStats = false
serverAddress = "localhost"
serverPort = 8501
'''

# Create .streamlit directory structure
os.makedirs('.streamlit', exist_ok=True)
with open('.streamlit/config.toml', 'w', encoding='utf-8') as f:
    f.write(streamlit_config)

print("✅ Created: .streamlit/config.toml")
