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

## Future improvements

### User interaction

"one thing that I really like about the OpenAI deep research is that it always comes back with exactly 1 round of clarifying questions before running, which I believe significantly improves the result for the desired context" -- brkrabach

Or when running in an MCP, maybe make the tool description:

"If you feel it is appropriate to use this tool, express this intent and then make exactly one request of the user for specific details that may make this research request more on target with their ask. Include 4-6 clarifying questions. If you have already done this step, please make sure to include the user's answers in your request for this tool"

### Routine improvements

"Based on my analysis of the current Web Research routine and the feedback received, here are several structural changes I would recommend:
Recommended Structural Changes to the Research Routine" -- Claude 3.7 Sonnet

Add a Source Evaluation Step

Create a new routine (research2.evaluate_sources) that runs after visiting pages
This would assess the reliability and relevance of each source, flagging potential biases or SEO-optimized content
Could assign confidence ratings to different sources

Implement Iterative Fact Verification

Add a dedicated verification step (research2.verify_facts) that cross-checks facts across multiple sources
This would help identify and flag contradictions or unverified claims
Could implement a consensus mechanism for conflicting information

Create a Progressive Summary

Instead of waiting until the end, maintain a running summary (research2.progressive_summary)
Update this summary after each research iteration
This would help identify gaps more clearly as the research progresses

Add Information Classification

Create a routine to classify information by type (e.g., research2.classify_info)
Categories could include: technical specs, expert opinions, user experiences, statistical data
This would help organize the final report and highlight the diversity of information types

Implement a Counterpoint Search

Add a dedicated step (research2.find_counterpoints) to search specifically for contradictory information
This would deliberately look for opposing viewpoints or contradictions to current findings
Could help address confirmation bias in the research process

Create a Confidence Scoring System

Implement a numerical confidence score for each fact (research2.score_confidence)
Based on source reliability, number of corroborating sources, and consistency
Would make uncertainty more transparent in the final report

Add Early Termination Criteria

Implement more sophisticated criteria for when research is complete
Consider both coverage of topics and confidence levels in determining completion
Could prevent unnecessary searches when sufficient reliable information has been found
