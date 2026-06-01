# 📈 AI-Powered Personal Finance Planner

An intelligent, web-based financial tracking application that integrates **Google Gemini 2.5 Flash** with a **Local Vector Database** to provide automated financial analysis, semantic insights, and cash flow visualization.

## ✨ Key Features
* **AI Financial Assistant:** A built-in chatbot capable of evaluating monthly cash flows, identifying wasteful spending, and providing personalized investment advice.
* **Vector-Embedded RAG Architecture:** Utilizes local embeddings (`vector_db.py`) to semantically search and retrieve relevant financial history, connecting `memory.json` and `database.json` to the Gemini LLM for highly accurate and contextual responses.
* **Interactive Dashboard:** Visualizes daily income and expenses, alongside current balances, using dynamic charts (Chart.js).
* **Dynamic Savings Goal Tracker:** Allows users to set flexible saving targets with a real-time progress bar.
* **Full CRUD Functionality:** Seamlessly add, view, and delete transaction records asynchronously via Fetch API (No page reloads).
* **Attachment Preview:** UI support for previewing receipt images/documents before sending them to the AI for processing.

## 🛠️ Tech Stack
* **Backend:** Python, Flask, Werkzeug
* **AI Integration:** Google Generative AI SDK (Gemini 2.5 Flash)
* **Frontend:** HTML5, CSS3, Vanilla JavaScript, Chart.js, FontAwesome
* **Database:** JSON-based local storage (Custom DB Manager) & Local Vector DB

## 🚀 How to Run Locally

1. Clone this repository:
```bash
   git clone [https://github.com/YOUR_GITHUB_USERNAME/AI-Finance-Planner.git](https://github.com/YOUR_GITHUB_USERNAME/AI-Finance-Planner.git)
   cd AI-Finance-Planner
Install the required dependencies:

Bash
   pip install -r requirements.txt
Configure Environment Variables:

Create a .env file in the root directory.

Add your Google Gemini API Key:

4. Run the Flask server:
   bash
   python app.py
Open your browser and navigate to http://127.0.0.1:5000

💡 Architecture & System Flow
[!IMPORTANT]
Why Local Embeddings?
As financial data grows, stuffing everything into the LLM context window becomes inefficient and costly. This project implements a Local Vector Database (vector_db.py). By converting transactions and goals into embeddings, the system performs semantic searches to pull only the most relevant financial context. This ensures Gemini 2.5 Flash provides laser-accurate advice without unnecessary token overhead or exposing data to external cloud databases.

🏗️ Data Flow Architecture
Cuplikan kode
graph TD
    A[User UI / Chat Input] -->|Fetch API| B(Flask Backend)
    C[(JSON Databases)] -->|Load Data| V[(Local Vector DB)]
    V -->|Semantic Search| B
    B -->|Inject Relevant Context| D[Prompt Construction]
    D -->|Send Prompt + Image| E((Gemini 2.5 Flash API))
    E -->|JSON/Text Response| B
    B -->|Render Data| F[Interactive Dashboard]
    
    style E fill:#4A69BD,stroke:#333,stroke-width:2px,color:#fff
    style C fill:#A4B0E5,stroke:#333,stroke-width:2px,color:#333
    style V fill:#ff9f43,stroke:#333,stroke-width:2px,color:#333