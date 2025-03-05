# Research skill

## Web Research [web_researcy.py](./routines/web_research.py)

This routine conducts thorough research on a given topic, interacts with the
user to refine the research plan, gathers information from web searches,
evaluates answers, and generates a structured research report. Here's how it
works:

1. **Generate a Research Plan:**
   - The program starts by running a routine (`research.generate_research_plan`)
     to create a research plan based on the given topic.
   - The plan is then saved to a file (`plan_name.txt`).

2. **User Review & Refinement:**
   - The user is asked if the plan looks good or needs modifications.
   - If the user wants updates, the plan is read from the file and refined
     (`research.update_research_plan`).
   - This loop continues until the user confirms the plan or chooses to exit.

3. **Execute the Research Plan:**
   - If the user exits, the temporary research plan file is deleted.
   - Otherwise, the research begins, and a results file
     (`plan_name_research_answers.md`) is created with a header.

4. **Web Search & Answer Collection:**
   - For each research question in the plan:
     - The system searches the web for relevant information
       (`research.web_search`).
     - It generates an answer using the retrieved content
       (`research.answer_question_about_content`).
     - The answer is evaluated for accuracy (`research.evaluate_answer`).
     - If the answer is good, it is appended to the results file.
     - If the answer is not satisfactory, the system refines its search based on
       previous attempts.

5. **Summarize & Report Generation:**
   - After answering all research questions, the collected information is read
     from the file.
   - A summary of the research is generated (`common.summarize`).
   - The final research report is saved as `plan_name_research_report.txt`.
   - The program prints a completion message and returns the report.

### Key Features

- **Iterative refinement** with user feedback before executing research.
- **Automated web searching** to gather relevant information.
- **Evaluation of answers** to ensure quality before adding them to the report.
- **Final summarization** for a concise, structured research report.

This routine is designed to **automate and streamline** the process of
conducting detailed web-based research, reducing manual effort while maintaining
quality through user interaction and validation steps.
