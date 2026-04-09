import json
import os
from datetime import date
import pandas as pd
import streamlit as st
from agents import route_query
from utils import calculate_bmi
from llm import get_response
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def generate_insights(weight_data):
    if len(weight_data) < 2:
        return "Not enough data to analyze."

    weights = [entry["weight"] for entry in weight_data]

    start = weights[0]
    end = weights[-1]
    diff = end - start

    insights = []

    # Trend
    if diff < 0:
        insights.append(f"You lost {abs(diff)} kg overall. Good progress!")
    elif diff > 0:
        insights.append(f"You gained {diff} kg. Review your diet.")
    else:
        insights.append("No change in weight.")

    # Plateau detection
    if len(set(weights[-3:])) == 1:
        insights.append("⚠️ Plateau detected in last 3 entries.")

    # Speed check
    if abs(diff) >= 3:
        insights.append("⚠️ Rapid weight change — ensure it's healthy.")

    return "\n".join(insights)
# ===== PDF FUNCTION =====
def generate_pdf(name, age, weight, height, goal, weight_data, weekly_plan, review):
    doc = SimpleDocTemplate("wellness_report.pdf")
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("AI Wellness Report", styles['Title']))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"Name: {name}", styles['Normal']))
    elements.append(Paragraph(f"Age: {age}", styles['Normal']))
    elements.append(Paragraph(f"Height: {height} cm", styles['Normal']))
    elements.append(Paragraph(f"Weight: {weight} kg", styles['Normal']))
    elements.append(Paragraph(f"Goal: {goal}", styles['Normal']))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Weight History:", styles['Heading2']))
    if weight_data:
        for entry in weight_data:
            elements.append(Paragraph(f"• {entry['date']} - {entry['weight']} kg", styles['Normal']))
    else:
        elements.append(Paragraph("No data available", styles['Normal']))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("AI Weekly Review:", styles['Heading2']))
    if review:
        for line in review.split("\n"):
            if line.strip():
                elements.append(Paragraph(f"• {line}", styles['Normal']))
    else:
        elements.append(Paragraph("No review generated", styles['Normal']))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Weekly Plan:", styles['Heading2']))
    if weekly_plan:
        for line in weekly_plan.split("\n"):
            if line.strip():
                elements.append(Paragraph(f"• {line}", styles['Normal']))
    else:
        elements.append(Paragraph("No plan generated", styles['Normal']))

    doc.build(elements)


# ===== APP START =====
st.set_page_config(page_title="AI Wellness Coach")
st.title("💪 AI Wellness Coach")

# ===== SESSION STORAGE =====
if "messages" not in st.session_state:
    st.session_state.messages = []

if "weekly_plan" not in st.session_state:
    st.session_state.weekly_plan = None

if "review" not in st.session_state:
    st.session_state.review = None

# ===== LOAD DATA =====
if "weight_data" not in st.session_state:
    if os.path.exists("weight_data.json"):
        with open("weight_data.json", "r") as f:
            st.session_state.weight_data = json.load(f)
    else:
        st.session_state.weight_data = []

# ===== SIDEBAR =====
with st.sidebar:
    st.header("User Profile")

    name = st.text_input("Full Name")
    age = st.number_input("Age", 10, 100, 22)
    weight = st.number_input("Weight (kg)", 30, 200, 65)
    height = st.number_input("Height (cm)", 100, 220, 170)
    goal = st.selectbox("Goal", ["Fat Loss", "Muscle Gain", "Maintain"])

    bmi = calculate_bmi(weight, height)
    st.subheader("📊 Health Insights")
    st.write(f"BMI: {bmi}")

# ===== USER DATA =====
user_data = f"Name: {name}, Age: {age}, Weight: {weight}, Height: {height}, Goal: {goal}"

# ===== CHAT =====
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_input = st.chat_input("Ask your question...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.write(user_input)

    response = route_query(user_input, user_data, st.session_state.messages)

    st.session_state.messages.append({"role": "assistant", "content": response})

    with st.chat_message("assistant"):
        st.write(response)

# ===== PLAN & REVIEW BUTTONS (FIXED) =====
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    if st.button("📅 Generate Weekly Plan"):
        st.session_state.weekly_plan = get_response(f"Create weekly plan for {user_data}")

with col2:
    if st.button("📊 Generate Weekly Review"):
        if st.session_state.weight_data:
            st.session_state.review = get_response(f"Analyze: {st.session_state.weight_data}")
        else:
            st.warning("Add weight data first!")

# ===== ALWAYS SHOW (FIXED) =====
if st.session_state.weekly_plan:
    st.subheader("📅 Weekly Fitness & Diet Plan")
    st.write(st.session_state.weekly_plan)

if st.session_state.review:
    st.subheader("📊 Weekly AI Review")
    st.write(st.session_state.review)

# ===== PROGRESS DASHBOARD =====
st.markdown("## 📊 Progress Dashboard")
st.markdown("---")

selected_date = st.date_input("Select Date", value=date.today())
daily_weight = st.number_input("Enter Weight (kg)", 30.0, 200.0, float(weight))

if st.button("➕ Save / Update Weight"):
    selected_date_str = str(selected_date)

    found = False
    for entry in st.session_state.weight_data:
        if entry["date"] == selected_date_str:
            entry["weight"] = daily_weight
            found = True
            break

    if not found:
        st.session_state.weight_data.append({
            "date": selected_date_str,
            "weight": daily_weight
        })

    with open("weight_data.json", "w") as f:
        json.dump(st.session_state.weight_data, f)

    st.success("Weight saved!")


# ===== CHART + DATA MANAGEMENT =====
if st.session_state.weight_data:
    df = pd.DataFrame(st.session_state.weight_data)

    df["date"] = pd.to_datetime(df["date"]).dt.date
    df = df.sort_values("date")

    df["3_day_avg"] = df["weight"].rolling(window=3).mean()
    df = df.set_index("date")

    st.markdown("### 📈 Weight Trend")
    st.line_chart(df)

    

    # ===== SMART INSIGHTS =====
if st.session_state.weight_data:
    st.markdown("### 🧠 Smart Insights")

    insights = generate_insights(st.session_state.weight_data)

    st.info(insights)

    # ===== SHOW ENTRIES =====
    st.markdown("### 📅 Logged Data")

    for i, entry in enumerate(st.session_state.weight_data):
        col1, col2 = st.columns([4, 1])

        with col1:
            st.markdown(f"**📅 {entry['date']}** — {entry['weight']} kg")

        with col2:
            if st.button("❌", key=f"delete_{i}"):
                st.session_state.weight_data.pop(i)

                with open("weight_data.json", "w") as f:
                    json.dump(st.session_state.weight_data, f)

                st.rerun()

    # ===== CLEAR ALL =====
    if st.button("🗑️ Clear All Data"):
        st.session_state.weight_data = []

        with open("weight_data.json", "w") as f:
            json.dump([], f)

        st.rerun()
    
# ===== PDF DOWNLOAD =====
st.markdown("---")
st.subheader("📄 Download Report")

if st.button("📥 Generate PDF Report"):

    if not st.session_state.weekly_plan or not st.session_state.review:
        st.warning("⚠️ Generate Weekly Plan & Review first!")
    else:
        generate_pdf(
            name,
            age,
            weight,
            height,
            goal,
            st.session_state.weight_data,
            st.session_state.weekly_plan,
            st.session_state.review
        )

        with open("wellness_report.pdf", "rb") as file:
            st.download_button(
                label="⬇️ Download PDF",
                data=file,
                file_name="wellness_report.pdf",
                mime="application/pdf"
            )