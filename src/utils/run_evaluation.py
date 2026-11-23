from keyword_evaluator import evaluate_keywords_and_generate_report

# Replace this list with your actual extracted keywords
llm_keywords = ["hypertension", "blood pressure", "metabolite", "antihypertensive"]

# Run the evaluation
evaluate_keywords_and_generate_report(llm_keywords, "evaluation_report.md")

print("Evaluation complete!")