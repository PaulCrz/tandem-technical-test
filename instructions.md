# Tandem - Full-Stack Engineer Technical Test

# **Overview**

You are a software engineer working on a product aimed at providing actionable UX insights for Product Managers. Your task is to build a script that processes a large JSON file of user events and produces a report.

The report should include:

- **Meaningful User Flows:** A list of the most significant paths (flows) users take through the product.
- **Anomalies:** A focus on anomalies — whether technical glitches, unexpected behavior, or UX issues — so that PMs can quickly identify what areas may need attention.

## **Data Source**

The JSON file is available at:

https://s3.eu-central-1.amazonaws.com/public.prod.usetandem.ai/sessions.json

The file is formatted in [JSON Lines](https://jsonlines.org/) (each line is a separate JSON object).

# **Requirements**

## **Data Processing**

- Read and process the session events from the provided JSON Lines file.

## **Report Generation**

- **User Flows:** Identify and list the most meaningful flows (common paths or sequences of events) through the application, and generate for each flow a title and a description.
- **Anomalies:** Detect and emphasize anomalies in the data. These anomalies could be technical errors (e.g., timeouts, error messages) or unexpected UX issues (e.g., user confusion, navigation issues).

## **Output Format**

- You are free to choose the output format (e.g., a text summary, an HTML report, a JSON digest, etc.). Make sure that the output is clear and can be easily interpreted by a PM.

## **Scalability & Industrialization**

- In your submission, include a brief explanation of how you would scale and industrialize your solution to work in production on millions of events. Consider aspects such as performance, cost, and maintainability.
- Assume the solution will eventually need to handle millions of events, so design your approach with scalability in mind.

## **Tools & Language**

- You may use any programming language and libraries/tools of your choice.

# **Deliverables**

## **Script**

A working script that processes the JSON file and produces the digest report.

## **Documentation**

A brief explanation (no more than 1 page) covering:

- Your overall approach to processing the data.
- How you identified and summarized meaningful flows.
- How you detected anomalies.
- Your strategy for scaling and industrializing the solution.

# **Time Allocation**

You are expected to spend **2 hours** on this test.

This test includes a lot to tackle in a limited time, and it is possible that you will struggle to complete everything. Don’t worry: the goal is not just to assess the final result but to understand how you manage short timelines, where you choose to focus your efforts, how you prioritize tasks, and how you allocate your energy to deliver the most valuable outcomes.

# **Additional Notes**

- This is an open-ended challenge. We’re more interested in your thought process, design decisions, and your approach to solving the problem than in a fully production-ready tool.
- Please document any assumptions you make.
- Remember that this test simulates real-world scenarios where you need to balance quick prototyping with scalable design.

Good luck!
