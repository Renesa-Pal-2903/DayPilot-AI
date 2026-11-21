# 🌸 DayPilot AI – Smart Productivity & Task Management Assistant

DayPilot AI is a smart productivity and task management web application built using Python and Streamlit. It helps users organize their tasks, manage deadlines, track progress, and plan their daily activities efficiently.

The application includes an interactive AI Assistant that analyzes saved tasks and provides rule-based recommendations and personalized study schedules.

## ✨ Features

- **Dashboard:** View total tasks, pending tasks, completed tasks, and completion rate.
- **Task Management:** Add, view, complete, and delete tasks.
- **Priority Management:** Organize tasks based on High, Medium, and Low priorities.
- **Deadline Tracking:** Monitor upcoming deadlines and overdue tasks.
- **Daily Planner:** View tasks according to their scheduled dates.
- **AI Assistant:** Ask questions about tasks, deadlines, and productivity.
- **Smart Recommendations:** Get suggestions about which task to complete next.
- **Study Plan Generator:** Generate a time-based schedule using available time and pending tasks.
- **SQLite Database:** Store tasks persistently.

## 🛠️ Technologies Used

- Python
- Streamlit
- SQLite
- Pandas
- HTML
- CSS

## 📁 Project Structure

```text
DayPilot-AI/
│
├── app.py
│
├── database/
│   ├── db.py
│   └── daypilot.db
│
├── README.md
└── requirements.txt
```

*The database file is created automatically when the application initializes if it does not already exist.*

## ⚙️ Installation and Setup

### 1. Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

### 2. Navigate to the Project Folder

```bash
cd DayPilot-AI
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
python -m streamlit run app.py
```

The application will open in your browser at:

```text
http://localhost:8501
```

## 🤖 About the AI Assistant

The DayPilot AI Assistant uses rule-based logic to analyze task information stored in the database.

It can:
- Identify urgent and approaching deadlines.
- Recommend the next task based on priority and urgency.
- Generate study schedules according to available time.
- Display pending and completed tasks.
- Provide productivity summaries.

## 🎯 Project Objective

The main objective of DayPilot AI is to make task management easier and help students and individuals improve their productivity through structured planning, deadline awareness, and intelligent task recommendations.

## 👩‍💻 Developed With

Python | Streamlit | SQLite

**DayPilot AI – Plan Smart. Stay Focused. Get Things Done.** 🌸