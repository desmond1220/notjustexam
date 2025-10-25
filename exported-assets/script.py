
# Let me read the HTML files to understand their exact structure
with open('summary_question.html', 'r', encoding='utf-8') as f:
    question_html = f.read()
    
with open('summary_discussion_ai.html', 'r', encoding='utf-8') as f:
    discussion_ai_html = f.read()

print("=== QUESTION HTML ===")
print(question_html)
print("\n\n=== DISCUSSION/AI HTML ===")
print(discussion_ai_html)
