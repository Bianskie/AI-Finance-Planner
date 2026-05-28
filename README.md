# 📈 AI-Powered Personal Finance Planner

An intelligent, web-based financial tracking application that integrates **Google Gemini 2.5 Flash** to provide automated financial analysis, insights, and cash flow visualization without relying on complex vector databases.

## ✨ Key Features
* **AI Financial Assistant:** A built-in chatbot capable of evaluating monthly cash flows, identifying wasteful spending, and providing personalized investment advice.
* **In-Context RAG Architecture:** Efficiently injects structured JSON tabular data directly into the LLM's context window, optimizing performance without the overhead of text-embedding or vector databases.
* **Interactive Dashboard:** Visualizes daily income and expenses, alongside current balances, using dynamic charts (Chart.js).
* **Dynamic Savings Goal Tracker:** Allows users to set flexible saving targets with a real-time progress bar.
* **Full CRUD Functionality:** Seamlessly add, view, and delete transaction records asynchronously via Fetch API (No page reloads).
* **Attachment Preview:** UI support for previewing receipt images/documents before sending them to the AI for processing.

## 🛠️ Tech Stack
* **Backend:** Python, Flask, Werkzeug
* **AI Integration:** Google Generative AI SDK (Gemini 2.5 Flash)
* **Frontend:** HTML5, CSS3, Vanilla JavaScript, Chart.js, FontAwesome
* **Database:** JSON-based local storage (Custom DB Manager)

## 🚀 How to Run Locally

1. Clone this repository:
   ```bash
   git clone [https://github.com/YOUR_GITHUB_USERNAME/AI-Finance-Planner.git](https://github.com/YOUR_GITHUB_USERNAME/AI-Finance-Planner.git)
   cd AI-Finance-Planner

2. Install the required dependencies:
pip install -r requirements.txt

3. Configure Environment Variables:
* Create a .env file in the root directory.
* Add your Google Gemini API Key:
 
 GEMINI_API_KEY="your_api_key_here"

4. Run the Flask server:
python app.py

5. Open your browser and navigate to python app.py



## 💡 Architecture & System Flow

> [!IMPORTANT]
> **Why No Vector Database?**
> This project demonstrates the effective use of **In-Context Learning (Context Stuffing)** for RAG. Since the personal financial data is structured (tabular) and relatively small in size, feeding the raw JSON directly into the context window of modern LLMs (like Gemini Flash) yields highly accurate aggregations. It completely avoids the unnecessary complexity, cost, and latency of traditional vector-embedding setups.

### 🏗️ Data Flow Architecture
```mermaid
graph TD
    A[User UI / Chat Input] -->|Fetch API| B(Flask Backend)
    C[(database.json)] -->|Retrieve All Records| B
    B -->|Context Stuffing| D[Prompt Construction]
    D -->|Send Prompt + Image| E((Gemini 2.5 Flash API))
    E -->|JSON/Text Response| B
    B -->|Render Data| F[Interactive Dashboard]
    
    style E fill:#4A69BD,stroke:#333,stroke-width:2px,color:#fff
    style C fill:#A4B0E5,stroke:#333,stroke-width:2px,color:#333