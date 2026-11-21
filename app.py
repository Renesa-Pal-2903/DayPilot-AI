
import streamlit as st
import re

from datetime import datetime, date, time, timedelta

from database.db import (
    initialize_database,
    add_task,
    get_tasks,
    complete_task,
    delete_task
)


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="DayPilot AI",
    page_icon="🌸",
    layout="wide"
)

initialize_database()


# ==================================================
# TASK ANALYSIS
# ==================================================

def parse_deadline(task):

    deadline = task.get("deadline")

    if not deadline:
        return None

    try:
        return datetime.strptime(deadline, "%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return None


def analyze_task_urgency(task):

    deadline = parse_deadline(task)

    if deadline is None:
        return "No deadline"

    now = datetime.now()

    if deadline < now:
        return "Overdue"

    if deadline.date() == now.date():
        return "Due today"

    if deadline.date() == (now + timedelta(days=1)).date():
        return "Due tomorrow"

    if deadline <= now + timedelta(days=7):
        return "Approaching"

    return "Upcoming"


# ==================================================
# SMART TASK RECOMMENDATIONS
# ==================================================

def get_task_recommendations(tasks):

    pending = [
        task for task in tasks
        if task.get("status") == "Pending"
    ]

    urgency_scores = {
        "Overdue": 0,
        "Due today": 1,
        "Due tomorrow": 2,
        "Approaching": 3,
        "Upcoming": 4,
        "No deadline": 5
    }

    priority_scores = {
        "High": 0,
        "Medium": 1,
        "Low": 2
    }

    def score(task):

        return (
            urgency_scores[analyze_task_urgency(task)],
            priority_scores.get(task.get("priority"), 1),
            parse_deadline(task) or datetime.max,
            task.get("estimated_minutes") or 60
        )

    return sorted(pending, key=score)


def get_next_recommendation(tasks, skip_first=False):

    recommendations = get_task_recommendations(tasks)

    if skip_first and recommendations:
        recommendations = recommendations[1:]

    return recommendations


# ==================================================
# RECOMMENDATION EXPLANATION
# ==================================================

def explain_recommendation(tasks):

    recommendations = get_task_recommendations(tasks)

    if not recommendations:

        return (
            "🎉 You currently have no pending tasks!\n\n"
            "You've completed everything in your task list. "
            "Enjoy your free time or add a new goal."
        )

    task = recommendations[0]

    deadline = parse_deadline(task)
    urgency = analyze_task_urgency(task)

    reasons = []

    reasons.append(
        f"It has **{task['priority']} priority**."
    )

    reasons.append(
        f"Its current urgency is **{urgency}**."
    )

    duration = task.get("estimated_minutes") or 60

    deadline_text = (
        deadline.strftime("%d %B %Y at %I:%M %p")
        if deadline else "Not specified"
    )

    response = (
        "🌟 **Here's why I recommended this task:**\n\n"
        f"My recommended task is **{task['title']}**.\n\n"
        "**Reasons:**\n\n"
    )

    for reason in reasons:
        response += f"- {reason}\n"

    response += (
        f"\n- **Estimated duration:** {duration} minutes\n"
        f"- **Deadline:** {deadline_text}\n"
        f"- **Current status:** {task['status']}\n\n"
        "**My suggestion:** Start working on this task first. "
        "Completing it early will help you avoid last-minute stress. 💜"
    )

    return response


# ==================================================
# AVAILABLE TIME DETECTION
# ==================================================

def extract_available_minutes(query):

    patterns = [
        (r"(\d+(?:\.\d+)?)\s*hours?", 60),
        (r"(\d+)\s*minutes?", 1),
        (r"(\d+)\s*mins?", 1)
    ]

    for pattern, multiplier in patterns:

        match = re.search(pattern, query)

        if match:
            return int(float(match.group(1)) * multiplier)

    return 180


# ==================================================
# SMART STUDY PLAN
# ==================================================

def create_study_plan(tasks, available_minutes):

    recommendations = get_task_recommendations(tasks)

    if not recommendations:

        return (
            "🎉 You have no pending tasks!\n\n"
            "You've completed everything. "
            "Enjoy your free time!"
        )

    if available_minutes <= 0:
        return "Please provide a valid available time."

    remaining = available_minutes
    current_time = datetime.now()

    response = (
        "📚 **Your Smart Study Plan**\n\n"
        f"**Available time:** {available_minutes} minutes\n"
        f"**Starting time:** {current_time.strftime('%I:%M %p')}\n\n"
        "Here is your recommended schedule:\n\n"
    )

    scheduled_count = 0
    completed_schedule_minutes = 0

    for task in recommendations:

        if remaining <= 0:
            break

        duration = max(
            5,
            int(task.get("estimated_minutes") or 60)
        )

        allocated = min(duration, remaining)

        start_time = current_time
        end_time = start_time + timedelta(minutes=allocated)

        scheduled_count += 1
        completed_schedule_minutes += allocated

        deadline = parse_deadline(task)

        response += (
            f"**{scheduled_count}. {task['title']}**\n"
            f"- Time: {start_time.strftime('%I:%M %p')} "
            f"to {end_time.strftime('%I:%M %p')}\n"
            f"- Allocated: {allocated} minutes\n"
            f"- Priority: {task['priority']}\n"
            f"- Urgency: {analyze_task_urgency(task)}\n"
        )

        if allocated < duration:

            response += (
                f"- Remaining work: {duration - allocated} minutes\n"
                "- Status: Partial work session\n"
            )

        else:
            response += "- Status: Full estimated work session\n"

        if deadline:
            response += (
                f"- Deadline: {deadline.strftime('%d %b, %I:%M %p')}\n"
            )

        response += "\n"

        remaining -= allocated
        current_time = end_time

        # Add a five-minute break between work sessions.
        if remaining > 0 and scheduled_count < len(recommendations):

            break_time = min(5, remaining)

            if break_time == 5:

                response += (
                    "☕ **Short Break** — 5 minutes\n\n"
                )

                current_time += timedelta(minutes=5)
                remaining -= 5
                completed_schedule_minutes += 5

    response += (
        "---\n\n"
        f"**Total scheduled time:** "
        f"{completed_schedule_minutes} minutes\n"
        f"**Unused time:** {remaining} minutes\n\n"
        "**My advice:** Follow this schedule one task at a time. "
        "Avoid multitasking and take short breaks. 💜"
    )

    return response


# ==================================================
# AI ASSISTANT
# ==================================================

def generate_ai_response(message, tasks):

    query = message.lower().strip()

    pending = [
        task for task in tasks
        if task["status"] == "Pending"
    ]

    completed = [
        task for task in tasks
        if task["status"] == "Completed"
    ]

    overdue = [
        task for task in pending
        if analyze_task_urgency(task) == "Overdue"
    ]

    due_today = [
        task for task in pending
        if analyze_task_urgency(task) == "Due today"
    ]

    due_tomorrow = [
        task for task in pending
        if analyze_task_urgency(task) == "Due tomorrow"
    ]

    approaching = [
        task for task in pending
        if analyze_task_urgency(task) == "Approaching"
    ]

    total = len(tasks)

    progress = (
        len(completed) / total * 100
        if total else 0
    )

    # GREETING

    if any(word in query.split() for word in
           ["hello", "hi", "hey", "hii", "goodmorning"]):

        return (
            "Hello! 🌸 I'm your DayPilot AI Assistant.\n\n"
            "I can analyse your saved tasks, identify urgent deadlines, "
            "create study plans and recommend what to work on next.\n\n"
            "How can I help you today?"
        )

    # HELP

    if "help" in query or "what can you do" in query:

        return (
            "Here's what I can help you with! 💜\n\n"
            "- Check pending and completed tasks.\n"
            "- Identify overdue tasks.\n"
            "- Find tasks due today or tomorrow.\n"
            "- Analyse approaching deadlines.\n"
            "- Recommend your next task.\n"
            "- Explain my recommendations.\n"
            "- Generate time-based study plans.\n"
            "- Recommend tasks based on available hours.\n"
            "- Track productivity and completion progress.\n\n"
            "**Try asking:**\n"
            "- Create a study plan for today.\n"
            "- I have only 2 hours available. What should I work on?\n"
            "- What should I do after completing my highest-priority task?"
        )

    # STUDY PLAN / AVAILABLE TIME

    study_keywords = [
        "study plan",
        "create a plan",
        "make a plan",
        "plan for today",
        "schedule my tasks",
        "schedule for today",
        "available",
        "only have",
        "hours left",
        "minutes left"
    ]

    if any(word in query for word in study_keywords):

        available_minutes = extract_available_minutes(query)

        return create_study_plan(
            tasks,
            available_minutes
        )

    # EXPLAIN RECOMMENDATION

    explanation_phrases = [
        "why should",
        "why did you",
        "why do you recommend",
        "why this task",
        "explain your recommendation",
        "explain the recommendation",
        "explain why",
        "why recommend",
        "why complete",
        "why is this task",
        "why is this important",
        "reason for recommendation",
        "reason for choosing",
        "justify your recommendation"
    ]

    if (
        any(phrase in query for phrase in explanation_phrases)
        or "complete this task first" in query
        or "finish this task first" in query
    ):

        return explain_recommendation(tasks)

    # NEXT TASK AFTER COMPLETING THE FIRST TASK

    after_completion = (
        "after completing" in query
        or "after finishing" in query
        or "once i complete" in query
        or "once i finish" in query
        or "after my highest" in query
    )

    if after_completion:

        recommendations = get_next_recommendation(
            tasks,
            skip_first=True
        )

        if not recommendations:

            return (
                "🎉 Excellent! Assuming you've completed your "
                "highest-priority task, there are no other pending "
                "tasks to recommend.\n\n"
                "Enjoy your free time or add a new goal!"
            )

        task = recommendations[0]

        deadline = parse_deadline(task)

        return (
            "🌟 **Your Next Smart Task Recommendation**\n\n"
            f"### {task['title']}\n\n"
            "Assuming you've completed your previous highest-priority "
            "task, this is the next task I recommend.\n\n"
            f"- **Priority:** {task['priority']}\n"
            f"- **Urgency:** {analyze_task_urgency(task)}\n"
            f"- **Estimated duration:** "
            f"{task.get('estimated_minutes') or 60} minutes\n"
            f"- **Deadline:** "
            f"{deadline.strftime('%d %b %Y, %I:%M %p') if deadline else 'Not specified'}\n\n"
            "**My advice:** Start this task next. 💜"
        )

    # OVERDUE TASKS

    if any(word in query for word in
           ["overdue", "past deadline", "missed deadline", "late tasks"]):

        if not overdue:
            return "🎉 Great news! You currently have no overdue pending tasks."

        response = f"⚠️ **You have {len(overdue)} overdue tasks:**\n\n"

        for task in overdue:

            deadline = parse_deadline(task)

            response += (
                f"- **{task['title']}**\n"
                f"  - Priority: {task['priority']}\n"
                f"  - Deadline: {deadline.strftime('%d %b, %I:%M %p')}\n"
                f"  - Duration: {task['estimated_minutes']} minutes\n\n"
            )

        return response

    # TASKS DUE TODAY

    if any(phrase in query for phrase in
           ["due today", "today's tasks", "tasks today", "today deadline"]):

        if not due_today:
            return "You have no pending tasks due today. 🌸"

        response = f"📅 **You have {len(due_today)} tasks due today:**\n\n"

        for task in due_today:

            deadline = parse_deadline(task)

            response += (
                f"- **{task['title']}**\n"
                f"  - Deadline: {deadline.strftime('%I:%M %p')}\n"
                f"  - Priority: {task['priority']}\n"
                f"  - Duration: {task['estimated_minutes']} minutes\n\n"
            )

        return response

    # TASKS DUE TOMORROW

    if "tomorrow" in query:

        if not due_tomorrow:
            return "You have no pending tasks due tomorrow."

        response = "**📅 Tasks due tomorrow:**\n\n"

        for task in due_tomorrow:

            deadline = parse_deadline(task)

            response += (
                f"- **{task['title']}** "
                f"at {deadline.strftime('%I:%M %p')} "
                f"(Priority: {task['priority']})\n"
            )

        return response

    # APPROACHING DEADLINES

    if any(word in query for word in
           ["approaching", "upcoming deadline", "deadlines soon"]):

        if not approaching and not due_tomorrow:
            return "You have no pending deadlines approaching within seven days."

        response = "⏰ **Your approaching deadlines:**\n\n"

        for task in due_tomorrow + approaching:

            deadline = parse_deadline(task)

            response += (
                f"- **{task['title']}** — "
                f"{deadline.strftime('%d %b, %I:%M %p')}\n"
            )

        return response

    # SMART RECOMMENDATIONS

    if any(phrase in query for phrase in
           ["what should", "next task", "work on next",
            "recommend", "suggest a task", "start with",
            "smart recommendation"]):

        recommendations = get_task_recommendations(tasks)

        if not recommendations:
            return "🎉 You have completed all your tasks! Enjoy your free time."

        recommended = recommendations[0]

        deadline = parse_deadline(recommended)

        response = (
            "🌟 **Your Smart Task Recommendation**\n\n"
            f"### {recommended['title']}\n\n"
            f"**Why this task?** It has "
            f"{analyze_task_urgency(recommended)} urgency and "
            f"{recommended['priority']} priority.\n\n"
            f"- Priority: {recommended['priority']}\n"
            f"- Urgency: {analyze_task_urgency(recommended)}\n"
            f"- Estimated duration: "
            f"{recommended.get('estimated_minutes') or 60} minutes\n"
            f"- Deadline: "
            f"{deadline.strftime('%d %b %Y, %I:%M %p') if deadline else 'Not specified'}\n\n"
            "**My advice:** Focus on this task first."
        )

        if len(recommendations) > 1:

            response += "\n\n**Other recommended tasks:**\n"

            for task in recommendations[1:4]:

                response += (
                    f"- **{task['title']}** "
                    f"({task['priority']} priority, "
                    f"{analyze_task_urgency(task)})\n"
                )

        return response

    # HIGH PRIORITY TASKS

    if "high priority" in query or "urgent" in query:

        high_tasks = [
            task for task in pending
            if task["priority"] == "High"
        ]

        if not high_tasks:
            return "You currently have no pending high-priority tasks."

        response = "⚡ **Your high-priority tasks:**\n\n"

        for task in high_tasks:

            response += (
                f"- **{task['title']}** "
                f"({analyze_task_urgency(task)})\n"
            )

        return response

    # PRODUCTIVITY REPORT

    if any(word in query for word in
           ["progress", "productive", "productivity",
            "statistics", "performance", "summary",
            "how am i doing"]):

        return (
            "📊 **Your Productivity Report**\n\n"
            f"- Total tasks: **{total}**\n"
            f"- Completed: **{len(completed)}**\n"
            f"- Pending: **{len(pending)}**\n"
            f"- Overdue: **{len(overdue)}**\n"
            f"- Due today: **{len(due_today)}**\n"
            f"- Completion rate: **{progress:.1f}%**\n\n"
            + (
                "Excellent progress! Keep it up! 🌸"
                if progress >= 70
                else "Keep working consistently. Every small step counts! 💜"
            )
        )

    # COMPLETED TASKS

    if any(word in query for word in
           ["completed", "finished", "done"]):

        if not completed:
            return "You haven't completed any tasks yet. Let's get started! 🌷"

        response = (
            f"🎉 **You have completed {len(completed)} tasks:**\n\n"
        )

        for task in completed:
            response += f"- {task['title']}\n"

        return response

    # PENDING TASKS

    if any(word in query for word in
           ["pending", "remaining", "incomplete", "unfinished"]):

        if not pending:
            return "Amazing! You have no pending tasks. 🎉"

        response = (
            f"**You currently have {len(pending)} pending tasks:**\n\n"
        )

        for task in pending:

            response += (
                f"- **{task['title']}** "
                f"— {task['priority']} priority "
                f"({analyze_task_urgency(task)})\n"
            )

        return response

    # ALL TASKS

    if any(phrase in query for phrase in
           ["show all", "list all", "my tasks", "all tasks"]):

        if not tasks:
            return "You haven't created any tasks yet."

        response = "**Here are all your tasks:**\n\n"

        for task in tasks:

            symbol = (
                "✅" if task["status"] == "Completed" else "⏳"
            )

            response += (
                f"- {symbol} **{task['title']}** "
                f"({task['priority']})\n"
            )

        return response

    # TODAY'S SCHEDULE

    if "today" in query:

        today_tasks = [
            task for task in tasks
            if parse_deadline(task)
            and parse_deadline(task).date() == date.today()
        ]

        if not today_tasks:
            return "You have no tasks scheduled for today. 🌸"

        response = "**Your schedule for today:**\n\n"

        for task in today_tasks:

            deadline = parse_deadline(task)

            status = (
                "✅" if task["status"] == "Completed" else "⏳"
            )

            response += (
                f"- {status} **{task['title']}** "
                f"at {deadline.strftime('%I:%M %p')}\n"
            )

        return response

    # PRODUCTIVITY TIPS

    if any(word in query for word in
           ["tip", "advice", "motivate", "motivation", "focus"]):

        return (
            "🌷 **A productivity tip for you:**\n\n"
            "1. Start with your most urgent task.\n"
            "2. Break large tasks into smaller steps.\n"
            "3. Try the Pomodoro technique: 25 minutes of focused work "
            "followed by a 5-minute break.\n"
            "4. Avoid multitasking.\n"
            "5. Celebrate small achievements.\n\n"
            "Remember: Consistency is more important than perfection! 💜"
        )

    # DEFAULT RESPONSE

    return (
        "I'm still learning to understand different requests! 🌸\n\n"
        "Try asking me about overdue tasks, deadlines, productivity "
        "progress, study plans, or smart recommendations.\n\n"
        "Type **Help** to see what I can do."
    )


# ==================================================
# CUSTOM CSS
# ==================================================

st.markdown("""
<style>

.stApp {
    background-color: #F7F7FC;
}

.main .block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
}

h1, h2, h3 {
    color: #39345C;
}

p, label, span {
    color: #55536B;
}

div[data-testid="stMetric"] {
    background: white;
    border: 1px solid #E8E4F5;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0 3px 12px rgba(80, 60, 120, 0.05);
}

div[data-testid="stMetricLabel"] {
    color: #77718F;
}

div[data-testid="stMetricValue"] {
    color: #6554A4;
}

.stButton > button {
    border-radius: 10px;
    border: 1px solid #D9D0F0;
    background-color: #EEEAF9;
    color: #51418B;
    font-weight: 600;
}

.stButton > button:hover {
    background-color: #DCD3F4;
    border-color: #BBADE5;
    color: #39345C;
}

.stForm {
    background-color: white;
    padding: 20px;
    border: 1px solid #E8E4F5;
    border-radius: 15px;
}

div[data-testid="stSidebar"] {
    background-color: #F0EDFA;
}

</style>
""", unsafe_allow_html=True)


# ==================================================
# HEADER
# ==================================================

st.title("🌸 DayPilot AI")

st.markdown("### Your personal productivity companion")

st.caption(
    "Plan your day, organize your tasks, and stay focused."
)

st.divider()


# ==================================================
# LOAD TASKS
# ==================================================

tasks = get_tasks()

pending_tasks = [
    task for task in tasks
    if task["status"] == "Pending"
]

completed_tasks = [
    task for task in tasks
    if task["status"] == "Completed"
]

total_tasks = len(tasks)
pending_count = len(pending_tasks)
completed_count = len(completed_tasks)

completion_rate = (
    completed_count / total_tasks * 100
    if total_tasks else 0
)


# ==================================================
# SIDEBAR
# ==================================================

st.sidebar.title("🌷 DayPilot Menu")

page = st.sidebar.radio(
    "Navigate",
    [
        "Dashboard",
        "AI Assistant",
        "Add New Task",
        "My Tasks",
        "Daily Planner"
    ]
)


# ==================================================
# DASHBOARD
# ==================================================

if page == "Dashboard":

    st.subheader("✨ Welcome to your workspace!")

    st.write(
        "Keep track of your goals and make every day productive."
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Tasks", total_tasks)
    col2.metric("Pending Tasks", pending_count)
    col3.metric("Completed Tasks", completed_count)
    col4.metric("Completion Rate", f"{completion_rate:.1f}%")

    st.divider()

    st.markdown("#### 📌 Recent Tasks")

    if tasks:

        for task in tasks[:5]:

            with st.container(border=True):

                col1, col2 = st.columns([4, 1])

                with col1:

                    st.markdown(f"**{task['title']}**")

                    st.caption(
                        task["description"] or "No description provided."
                    )

                with col2:

                    if task["status"] == "Completed":
                        st.success("Completed")
                    else:
                        st.warning("Pending")

    else:
        st.info("Start by adding your first task!")

    st.markdown("#### 📈 Overall Progress")

    st.progress(int(completion_rate))

    st.write(
        f"You have completed {completion_rate:.1f}% of your tasks."
    )

    st.divider()

    st.markdown("#### 💡 Productivity Reminder")

    st.info(
        "Break your work into smaller tasks, set realistic deadlines, "
        "and celebrate your progress!"
    )


# ==================================================
# AI ASSISTANT
# ==================================================

elif page == "AI Assistant":

    st.subheader("🤖 Meet Your AI Assistant")

    st.write(
        "Ask me about your tasks, deadlines, and productivity."
    )

    st.info(
        "I can analyse your saved tasks, identify urgent deadlines, "
        "create study plans, and recommend what to work on next."
    )

    if "chat_history" not in st.session_state:

        st.session_state.chat_history = [
            {
                "role": "assistant",
                "content": (
                    "Hello! 🌸 I'm your DayPilot AI Assistant. "
                    "How can I help you today?"
                )
            }
        ]

    for message in st.session_state.chat_history:

        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_input = st.chat_input(
        "Ask me something about your productivity..."
    )

    if user_input:

        st.session_state.chat_history.append(
            {
                "role": "user",
                "content": user_input
            }
        )

        response = generate_ai_response(
            user_input,
            get_tasks()
        )

        st.session_state.chat_history.append(
            {
                "role": "assistant",
                "content": response
            }
        )

        st.rerun()

    if st.button("🗑️ Clear Chat"):

        st.session_state.chat_history = [
            {
                "role": "assistant",
                "content": "Hello! 🌸 How can I help you today?"
            }
        ]

        st.rerun()


# ==================================================
# ADD NEW TASK
# ==================================================

elif page == "Add New Task":

    st.subheader("➕ Create a New Task")

    with st.form("add_task_form", clear_on_submit=True):

        title = st.text_input(
            "Task Title",
            placeholder="e.g. Complete Python Assignment"
        )

        description = st.text_area(
            "Task Description",
            placeholder="Enter task details..."
        )

        col1, col2 = st.columns(2)

        with col1:

            deadline_date = st.date_input(
                "Deadline",
                value=date.today(),
                min_value=date.today()
            )

            priority = st.selectbox(
                "Priority",
                ["Low", "Medium", "High"]
            )

        with col2:

            deadline_time = st.time_input(
                "Deadline Time",
                value=time(23, 59)
            )

            estimated_minutes = st.number_input(
                "Estimated Duration (minutes)",
                min_value=5,
                max_value=1440,
                value=60,
                step=5
            )

        submitted = st.form_submit_button(
            "🌸 Add Task",
            use_container_width=True
        )

        if submitted:

            if not title.strip():

                st.error("Please enter a task title.")

            else:

                deadline = datetime.combine(
                    deadline_date,
                    deadline_time
                ).strftime("%Y-%m-%d %H:%M")

                add_task(
                    title.strip(),
                    description.strip(),
                    deadline,
                    priority,
                    int(estimated_minutes)
                )

                st.success("Your task has been added successfully! 🎉")

                st.rerun()


# ==================================================
# MY TASKS
# ==================================================

elif page == "My Tasks":

    st.subheader("📝 Manage Your Tasks")

    filter_option = st.selectbox(
        "Filter Tasks",
        ["All Tasks", "Pending", "Completed"]
    )

    if filter_option == "Pending":
        filtered_tasks = pending_tasks

    elif filter_option == "Completed":
        filtered_tasks = completed_tasks

    else:
        filtered_tasks = tasks

    if not filtered_tasks:

        st.info("No tasks found in this category.")

    else:

        for task in filtered_tasks:

            with st.container(border=True):

                col1, col2 = st.columns([4, 1])

                with col1:

                    st.markdown(f"### {task['title']}")

                    st.write(
                        task["description"] or "No description provided."
                    )

                    st.caption(
                        f"Priority: {task['priority']} | "
                        f"Estimated time: {task['estimated_minutes']} minutes"
                    )

                    st.caption(
                        f"Deadline: {task['deadline'] or 'Not specified'}"
                    )

                    if task["status"] == "Completed":
                        st.success("✓ Completed")
                    else:
                        st.warning("⏳ Pending")

                with col2:

                    if task["status"] == "Pending":

                        if st.button(
                            "Complete",
                            key=f"complete_{task['id']}"
                        ):

                            complete_task(task["id"])

                            st.success(
                                f"{task['title']} marked as completed!"
                            )

                            st.rerun()

                    if st.button(
                        "Delete",
                        key=f"delete_{task['id']}"
                    ):

                        delete_task(task["id"])
                        st.rerun()


# ==================================================
# DAILY PLANNER
# ==================================================

elif page == "Daily Planner":

    st.subheader("📅 Your Daily Planner")

    selected_date = st.date_input(
        "Select a date",
        value=date.today()
    )

    st.write(
        f"### Schedule for {selected_date.strftime('%d %B %Y')}"
    )

    scheduled_tasks = []

    for task in tasks:

        deadline = parse_deadline(task)

        if deadline and deadline.date() == selected_date:
            scheduled_tasks.append(task)

    if scheduled_tasks:

        scheduled_tasks.sort(
            key=lambda task: task["deadline"]
        )

        for task in scheduled_tasks:

            deadline = parse_deadline(task)

            with st.container(border=True):

                st.markdown(
                    f"**🕒 {deadline.strftime('%I:%M %p')} — "
                    f"{task['title']}**"
                )

                st.caption(
                    f"Priority: {task['priority']} | "
                    f"Duration: {task['estimated_minutes']} minutes"
                )

                if task["status"] == "Completed":
                    st.success("Completed")
                else:
                    st.warning("Pending")

    else:

        st.info(
            "No tasks scheduled for this date. "
            "Add a task with this deadline to see it here."
        )

    st.divider()

    st.markdown("#### 📊 Daily Summary")

    daily_total = len(scheduled_tasks)

    daily_completed = sum(
        1 for task in scheduled_tasks
        if task["status"] == "Completed"
    )

    daily_pending = daily_total - daily_completed

    col1, col2, col3 = st.columns(3)

    col1.metric("Scheduled Tasks", daily_total)
    col2.metric("Completed", daily_completed)
    col3.metric("Remaining", daily_pending)


# ==================================================
# FOOTER
# ==================================================

st.divider()

st.markdown(
    "<center style='color:#9991B2;'>"
    "Made with 💜 | DayPilot AI — Your Day, Your Way"
    "</center>",
    unsafe_allow_html=True
)
