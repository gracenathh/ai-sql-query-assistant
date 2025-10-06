# 🧠 AI SQL Query Assistant

A simple Flask web app that lets users ask natural language questions about a database and automatically generates SQL queries using AI.
Built with a mix of curiosity, caffeine, and what I like to call vibe coding ☕💻

## 🚀 Features
- 🗄 Upload your own SQLite database
- 💬 Ask questions in plain English
- 🤖 AI generates SQL for you
- 📊 View the query result instantly
- 🧩 Schema preview panel

## 💫 What Is “Vibe Coding”?
“Vibe coding” is how I describe my learning approach — instead of overthinking syntax or spending hours stuck on setup, I vibe with AI tools to explore, build, and learn faster.

Basically:
- I tell AI what I want to achieve 💭
- It suggests how to do it 🧠
- I read, tweak, and learn along the way 👩‍💻

This project was co-generated with AI, meaning I didn’t just copy code — I used AI to understand why things work and how all the pieces connect. It’s learning by building together.

## ⚙️ How It Works
1. Upload a database
2. The app reads its schema
3. You ask a question (e.g. “Which artist has the most albums?”)
4. AI → generates SQL → runs it → shows the table results

## 💻 Tech Stack
- Python (Flask)
- SQLite
- OpenAI API (LLM for SQL generation)
- Bootstrap for UI

## 🔍 Example Use
```
Q: What’s the average invoice total by country?
SQL: SELECT BillingCountry, AVG(Total) FROM invoices GROUP BY BillingCountry;
```

## 🎥 Demo
<video src="https://raw.githubusercontent.com/gracenathh/ai-sql-query-assistant/main/DEMO.mp4" width="600" controls></video>

## ⚠️ Current Limitations
1. ❌ No conversation memory, thus each question is independent
2. ⚡ No caching which requires SQL to be regenerated every time
3. 🧮 Works best with smaller databases (since schema excerpt is limited)
4. 🔒 API key must be manually entered each session

## 🧠 Learnings
- Reinforced concepts of database schema parsing
- Understood Flask routing and session logic
- Learned to safely handle SQL execution
- Learned to use AI as a pair programmer + tutor

## 🔗 Future Improvements
- Add follow-up question support (session memory)
- Implement SQL caching for performance
- Support multiple database types (Postgres, MySQL)

## 🧑‍💻 Run Locally
```
git clone https://github.com/gracenathh/ai-sql-query-assistant.git
cd ai-sql-query-assistant
pip install -r requirements.txt
flask run
```
