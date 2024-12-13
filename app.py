import streamlit as st
import requests
import openai
import json
import os
import boto3
import matplotlib.pyplot as plt
from collections import defaultdict
import pandas as pd
import re
import ast
from dotenv import load_dotenv

# """
# Project Credits
# ---------------
# This application project is a collaborative effort by the following team members
# (listed in alphabetical order by last name):
# - Jason Dai
# - Yuhe Tian
# - Andrew Zhao
# - Yiheng Yuan

# We acknowledge the invaluable assistance provided by large language models (LLMs); we have used ChatGPT to help us write those two load course materials functions, load user materials from s3 function, and the donut chart data visualization function, and we have also used ChatGPT to help us in the Generate Quiz and View Your Question History UI functions, but we changed the code because the code provided by ChatGPT did not work at the start. 
# the resources made available through the UCSD DSC 102 course website, and the insightful 
# feedback from the course teaching assistants. Additional external resources also 
# contributed to the development of this project.
# """

load_dotenv()

s3 = boto3.client('s3')
BUCKET_NAME = "lign167project" # change to your own Bucket Name from AWS

os.environ['AWS_ACCESS_KEY_ID'] = os.getenv('AWS_ACCESS_KEY_ID')
os.environ['AWS_SECRET_ACCESS_KEY'] = os.getenv('AWS_SECRET_ACCESS_KEY')

openai.api_key = os.getenv('OPENAI_API_KEY')

def load_course_material_by_weeks(weeks):
    materials = []
    for week in weeks:
        file_name = f"data/week_{week}.txt"
        try:
            with open(file_name, "r", encoding="utf-8") as file:
                materials.append(file.read())
        except FileNotFoundError:
            st.error(f"Error: {file_name} not found.")
    return "\n".join(materials)

def load_course_material_by_concepts(concepts):
    materials = []
    for concept in concepts:
        file_name = f"data/{concept.replace(' ', '_')}.txt"
        try:
            with open(file_name, "r", encoding="utf-8") as file:
                materials.append(file.read())
        except FileNotFoundError:
            st.error(f"Error: {file_name} not found.")
    return "\n".join(materials)

def generate_quiz_questions(materials, num_questions):
    prompt = f"""
    You are an educational content generator. Based on the following course material, create {num_questions} quiz questions.

    Course Material:
    {materials}

    Instructions:
    - Provide {num_questions} questions as output.
    - Use the following format:
        1. Question 1
        2. Question 2
        3. Question 3
        ...
    - Only output the questions; do not include any explanations or answers.
    """
    
    completion = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response = completion.choices[0].message.content.strip()
    return response

def grade_quiz_questions(answers, material):
    prompt = f"""
    You are an assistant that evaluates answers to quiz questions. The user has provided answers to a set of questions {answers}.

    Additionally, you have the following course material to reference:
    {material}
    
    Rules:
    1. Evaluate each question's answer for correctness.
    2. If the user's answer is correct, set the label to "1" and include the user's answer as the correct_answer_or_user_answer.
    3. If the user's answer is incorrect, set the label to "0" and provide the correct answer in the correct_answer_or_user_answer field.
    
    Format:
    For each question, output the following in a list format:
    [(question_number, question_text, user_answer, label (1/0), correct_answer_or_user_answer), ...].
    
    Ensure the output is a valid Python list with tuples for each question. Do not include any explanations or extra text.
    """

    completion = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    response = completion.choices[0].message.content.strip()

    match = re.search(r"\[.*\]", response, re.DOTALL)
    if match:
        extracted_content = ast.literal_eval(match.group(0))

    return extracted_content

def attribute_error_to_topic(error):
    dsc102_topics = [
    "Hardware and Software Basics", 
    "Data Representation and Abstraction", 
    "Processors and Memory Hierarchy", 
    "Operating Systems and Virtualization", 
    "Data Structures", 
    "File Systems and Databases", 
    "Distributed Computing and Parallelism", 
    "Cloud Computing and Scalability", 
    "Feature Engineering in ML"
    ]
    prompt = f"""
    Here is the correct answer of a student's mistake on a question: {error}, please attribute this mistake to a type of error in this list: {', '.join(dsc102_topics)}. Please make sure you only output a single type of error in this format [[your_answer]]. You MUST output one category from the list.
    """

    completion = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    concept_category = completion.choices[0].message.content.strip()
    if concept_category.startswith("[[") and concept_category.endswith("]]"):
        concept_category = concept_category[2:-2] 

    return concept_category

STUDENT_DATA_DIR = "student_data"
os.makedirs(STUDENT_DATA_DIR, exist_ok=True)

def get_student_file(student_id):
    return os.path.join(STUDENT_DATA_DIR, f"{student_id}.json")

def load_student_data(student_id):
    file_path = get_student_file(student_id)
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            return json.load(file)
    else:
        return {"tracked_errors": [], "error_frequencies": defaultdict(int)}

def save_student_data(student_id, student_data):
    file_path = get_student_file(student_id)
    with open(file_path, "w") as file:
        student_data["error_frequencies"] = dict(student_data["error_frequencies"])
        json.dump(student_data, file, indent=4)

def visualize_error_history(student_data):
    topics = list(student_data.keys())
    frequencies = [value for value in student_data.values() if isinstance(value, (int, float)) and value > 0]
    if not topics or not frequencies:
        st.warning("No valid error data available to visualize.")
        return
    if len(topics) != len(frequencies):
        st.warning("Mismatch between topics and frequencies. Please check your data.")
        return
    cmap = plt.get_cmap("tab20c")
    colors = [cmap(i / len(frequencies)) for i in range(len(frequencies))]

    fig, ax = plt.subplots(figsize=(8, 8))
    wedges, texts, autotexts = ax.pie(
        frequencies,
        autopct="%1.1f%%",
        startangle=90,
        wedgeprops={"edgecolor": "white"},
        colors=colors,
        pctdistance=0.8
    )
    center_circle = plt.Circle((0, 0), 0.60, fc="white")
    fig.gca().add_artist(center_circle)
    ax.axis("equal")
    plt.setp(autotexts, size=10, weight="bold", color="black")
    plt.setp(texts, size=8)
    plt.text(0, 0, "Error History", ha="center", va="center", fontsize=12, weight="bold")
    fig.legend(
        wedges,
        topics,
        title="Topics",
        loc="lower center",
        bbox_to_anchor=(0.5, -0.1),
        ncol=2, 
        fontsize=9
    )
    plt.tight_layout()
    st.pyplot(fig)

def update_user_errors_in_s3(bucket_name, student_code, data):
    file_name = f"errors_{student_code}.json"
    json_data = json.dumps(data)
    s3.put_object(Bucket=bucket_name, Key=file_name, Body=json_data, ContentType="application/json")
    
def load_user_errors_from_s3(bucket_name, student_code):
    file_name = f"errors_{student_code}.json"
    try:
        response = s3.get_object(Bucket=bucket_name, Key=file_name)
        data = json.loads(response['Body'].read().decode('utf-8'))
        if "right_wrong_history" in student_code:
            return data if isinstance(data, list) else []
        else:
            return data if isinstance(data, dict) else {}
    except s3.exceptions.NoSuchKey:
        if "right_wrong_history" in student_code:
            return []
        else:
            return {}

def search_concept_links(concept):
    api_key = os.getenv('SERPAPI_API_KEY')
    search_url = "https://serpapi.com/search.json"
    
    params = {
        "q": concept,  
        "hl": "en",    
        "num": 5,     
        "api_key": api_key
    }
    
    response = requests.get(search_url, params=params)
    if response.status_code == 200:
        search_results = response.json().get("organic_results", [])
        links = [f"{result['title']}: {result['link']}" for result in search_results]
        return links
    else:
        return ["Unable to fetch resources. Please try again later."]

st.title("DSC102 AI Tutor 🤖")

if "student_id" not in st.session_state:
    student_id = st.text_input("Enter your Student ID:")
    if student_id:
        st.session_state["student_id"] = student_id
        st.session_state["student_data"] = load_user_errors_from_s3(BUCKET_NAME, student_id)
        st.session_state["graded_2"] = load_user_errors_from_s3(BUCKET_NAME, student_id + "right_wrong_history")
        st.rerun() 
else:
    student_id = st.session_state["student_id"]
    student_data = st.session_state["student_data"]
    graded_2 = st.session_state["graded_2"]

    st.sidebar.success(f"Logged in as: {student_id}")

    if student_id:
        if f"student_data_" not in st.session_state:
            holder = {}
            st.session_state.student_data = load_user_errors_from_s3(BUCKET_NAME, student_id)
            for key, value in st.session_state.student_data.items():
                holder[key] = value
            st.session_state.student_data = holder
        if f"graded_2_" not in st.session_state:
            holder_2 = {}
            st.session_state.graded_2 = load_user_errors_from_s3(BUCKET_NAME, student_id + "right_wrong_history")

    if 'errors' not in st.session_state:
        st.session_state.errors = {}

    if 'quiz_questions' not in st.session_state:
        st.session_state.quiz_questions = []

    if "quiz_answers" not in st.session_state:
        st.session_state.quiz_answers = {}

    if 'quiz_materials' not in st.session_state:
        st.session_state.quiz_materials = []

    if 'error_tracking' not in st.session_state:
        st.session_state.error_tracking = {}

    st.sidebar.title("Features")
    selected_feature = st.sidebar.radio(
        "Select a Feature:",
        ["📋 Generate Quiz", "📊 Concept Self Tracking", "👀 View Your Question History", "🔗 Concept Self-Study Links"]
    )

    if selected_feature == "📋 Generate Quiz":
        st.subheader("Generate Quiz Questions")

        quiz_type = st.radio(
            "How would you like to generate the quiz?",
            options=["Course Materials by Weeks", "Concepts You Got Wrong Before"]
        )

        if quiz_type == "Course Materials by Weeks":
            weeks = st.multiselect("Select Course Materials (Weeks):", [str(i) for i in range(1, 11)])
            if weeks:
                materials = load_course_material_by_weeks(weeks)
            else:
                st.error("Please select at least one week.")

        elif quiz_type == "Concepts You Got Wrong Before":
            student_data = load_user_errors_from_s3(BUCKET_NAME, student_id)
            
            if student_data:
                concepts = list(student_data.keys())
                selected_concepts = st.multiselect("Select Concepts to Include in Quiz:", concepts)
                if selected_concepts:
                    materials = load_course_material_by_concepts(selected_concepts)
                else:
                    st.error("Please select at least one concept.")
            else:
                st.warning("No data available on your past mistakes.")

        num_questions = st.number_input("Number of Questions: (From 1 to 20)", min_value=1, max_value=20, step=1, value=5)

        if st.button("Generate Quiz"):
            questions_text = generate_quiz_questions(materials, num_questions)
            st.session_state.quiz_questions = [q.strip() for q in questions_text.split("\n") if q.strip()]
            st.session_state.quiz_materials = materials
            st.session_state.user_answers = [""] * len(st.session_state.quiz_questions) 
            st.session_state.quiz_answers = {}
            st.success("Quiz Generated! Scroll down to take the quiz.")

        counter = 0
        if "quiz_questions" in st.session_state and st.session_state.quiz_questions:
            for i in st.session_state.quiz_questions:
                st.write(i)
                user_answer = st.text_area(f"Answer for question {counter+1}:", key=f"answer_{counter}", max_chars = 500, height=100)
                # st.write(user_answer)
                if user_answer: 
                    st.session_state.quiz_answers[i] = user_answer
                counter += 1

            agree = st.checkbox("I confirm all answers are filled (even if unsure).")
            if st.button("Submit Answer") and agree:
                full_results = grade_quiz_questions(st.session_state.quiz_answers, materials)
                graded_output = [
                    (item[0], item[4])  
                    for item in full_results if item[3] == 0
                ]
                store_result = [(item[1],item[2],item[3],item[4]) for item in full_results]
                st.write("Incorrect Questions (question number, Correct Answer):")
                for mistake in graded_output:
                    st.write(str(mistake))
                    topic = attribute_error_to_topic(mistake[1]) 

                    if topic not in st.session_state.student_data:
                        st.session_state.student_data[topic] = 1
                    else: 
                        st.session_state.student_data[topic] += 1

                st.session_state.graded_2 = st.session_state.graded_2 + store_result
                update_user_errors_in_s3(BUCKET_NAME, student_id, st.session_state.student_data)
                update_user_errors_in_s3(BUCKET_NAME, student_id + "right_wrong_history", st.session_state.graded_2)
                st.success("Error frequencies updated!")

    elif selected_feature == "👀 View Your Question History":
        st.subheader("📋 View Your Question History")
        history_file_name = f"errors_{student_id}right_wrong_history.json"
        try:
            response = s3.get_object(Bucket=BUCKET_NAME, Key=history_file_name)
            question_history = json.loads(response['Body'].read().decode('utf-8'))
        except s3.exceptions.NoSuchKey:
            st.warning("No question history found. Try answering some questions first with ***Generate Quiz*** feature!")
            question_history = []
        filter_option = st.radio(
            "Select the type of questions to display:",
            options=["All", "Right", "Wrong"]
        )
        filtered_questions = []
        if filter_option == "All":
            filtered_questions = question_history
        elif filter_option == "Right":
            filtered_questions = [q for q in question_history if q[2] == 1]
        elif filter_option == "Wrong":
            filtered_questions = [q for q in question_history if q[2] == 0]

        if filtered_questions:
            st.write(f"### Showing {filter_option.lower()} questions:")
            for idx, record in enumerate(filtered_questions, start=1):
                question, user_answer, correctness, correct_answer = record
                st.write(f"**{idx}. Question:** {question}")
                st.write(f"**Your Answer:** {user_answer}")
                st.write(f"**Correct Answer:** {correct_answer}")
                st.write(f"**Result:** {'✅ Correct' if correctness == 1 else '❌ Incorrect'}")
                st.markdown("---")
        else:
            st.info("No questions found for the selected category.")

    elif selected_feature == "🔗 Concept Self-Study Links":

        student_data = load_user_errors_from_s3(BUCKET_NAME, student_id)

        st.subheader("Concept Links and Related Resources")
        st.write("""
        Explore topics you need to improve on and find related resources to deepen your understanding.
        Each topic includes links to external tutorials or resources, and you can track which concepts you want to revisit.
        """)
        if student_data:
            concept_options = [
                f"{concept} (Occurrences: {frequency})"
                for concept, frequency in student_data.items()
            ]
            st.write("Tracked Concepts (Select a topic to explore):")
            selected_option = st.selectbox("Choose a concept", concept_options)
            concept = selected_option.split(" (")[0]
        else:
            st.info("No concepts tracked yet. Start practice with ***Generate Quiz*** to build your weakness concept history.")
            concept = None

        if concept and st.button("Get Study Links"):
            st.write(f"Fetching study links for concept: **{concept}**")
            links = search_concept_links(concept)
            st.write("### Study Resources")
            if links:
                for link in links:
                    st.write(f"- {link}")
            else:
                st.write("No resources found for this concept. Try a different topic or check back later.")

    elif selected_feature == "📊 Concept Self Tracking":

        student_data = load_user_errors_from_s3(BUCKET_NAME, student_id)

        holder = {}
        
        if student_data:
            st.subheader("Your Error History")
            st.write("Below is a summary of your tracked errors. Topics with higher frequencies indicate areas to focus on.")
            error_data = pd.DataFrame({
                "Concept": list(student_data.keys()),
                "Frequency": list(student_data.values())
            })
            error_data = error_data[~error_data["Concept"].str.contains("_")].sort_values(by="Frequency", ascending=False).reset_index(drop=True)
            holder = dict(zip(error_data["Concept"], error_data["Frequency"]))
            st.dataframe(error_data.style.background_gradient(cmap="Blues", subset=["Frequency"]))
            st.subheader("Error History Visualization")
            visualize_error_history(holder)
        else:
            st.info("No concepts tracked yet. Start practice with ***Generate Quiz*** to build your weakness concept history.")