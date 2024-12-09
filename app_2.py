import streamlit as st
import requests
import openai
import json
import os
import boto3
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from collections import defaultdict
import pandas as pd
import re
import ast

# Initialize S3 client
s3 = boto3.client('s3')
BUCKET_NAME = "lign167project"

os.environ['AWS_ACCESS_KEY_ID'] = "AKIAR3HUODFIYESUR3IY"
os.environ['AWS_SECRET_ACCESS_KEY'] = "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"

# Set up OpenAI API key
openai.api_key = "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"

# Function to load course materials
def load_course_material_by_weeks(weeks):
    """Load and concatenate course materials from selected weeks."""
    materials = []
    for week in weeks:
        file_name = f"week_{week}.txt"
        try:
            with open(file_name, "r", encoding="utf-8") as file:
                materials.append(file.read())
        except FileNotFoundError:
            st.error(f"Error: {file_name} not found.")
    return "\n".join(materials)


def load_course_material_by_concepts(concepts):
    """Load and concatenate course materials from selected weeks."""
    materials = []
    for concept in concepts:
        file_name = f"{concept.replace(' ', '_')}.txt"
        try:
            with open(file_name, "r", encoding="utf-8") as file:
                materials.append(file.read())
        except FileNotFoundError:
            st.error(f"Error: {file_name} not found.")
    return "\n".join(materials)

# Function to generate quiz questions
def generate_quiz_questions(materials, num_questions):
    """Generate quiz questions using OpenAI."""
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

def grade_quiz_questions(answers):
    prompt = f"""
    You are an assistant that evaluates answers to quiz questions. The user has provided answers to a set of questions{answers}. Do not output any other things rather than the one specified later, you must include [] signs in your output. Your task is to judge the correctness of user's answer. You only need to tell user about questions they made mistakes on. You should put all mistakes and its correct answer in a list and output in this way: [(mistaken_question_number, correct_answer), (mistaken_question_number, correct_answer), ......]
    """

    completion = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response = completion.choices[0].message.content.strip()
    return response

def grade_quiz_questions_2(answers):
    prompt = f"""
    You are an assistant that evaluates answers to quiz questions. The user has provided answers to a set of questions{answers}. Do not output any other information than specified below. Your task is to judge the correctness of the user's answers and provide a review of each question. You must include [] signs in your output. 

    Rules:
    1. If the user's answer is correct, set the label to "1" and include the user's answer as the correct_answer_or_user_answer.
    2. If the user's answer is incorrect, set the label to "0" and provide the correct answer in the correct_answer_or_user_answer field.

    For each question, output the following in a list format:
    [(question_text, user_answer, label (1/0), correct_answer_or_user_answer), (question_text, user_answer, label (1/0), correct_answer_or_user_answer), ......].

    Ensure the output is a valid Python list with tuples for each question. Do not include any explanations or extra text outside the specified format.
    """

    completion = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response = completion.choices[0].message.content.strip()
    return response

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

    # Remove brackets [[ ]] from the output
    concept_category = completion.choices[0].message.content.strip()
    if concept_category.startswith("[[") and concept_category.endswith("]]"):
        concept_category = concept_category[2:-2]  # Remove the outer [[ ]]

    return concept_category


# Directory to store student data
STUDENT_DATA_DIR = "student_data"

# Ensure the directory exists
os.makedirs(STUDENT_DATA_DIR, exist_ok=True)

def get_student_file(student_id):
    """Get the file path for a student's data file."""
    return os.path.join(STUDENT_DATA_DIR, f"{student_id}.json")

def load_student_data(student_id):
    """Load mistake history for a specific student."""
    file_path = get_student_file(student_id)
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            return json.load(file)
    else:
        # Initialize new data for the student if file doesn't exist
        return {"tracked_errors": [], "error_frequencies": defaultdict(int)}

def save_student_data(student_id, student_data):
    """Save mistake history for a specific student."""
    file_path = get_student_file(student_id)
    with open(file_path, "w") as file:
        # Convert defaultdict to a regular dict before saving
        student_data["error_frequencies"] = dict(student_data["error_frequencies"])
        json.dump(student_data, file, indent=4)

def visualize_error_history(student_data):
    """
    Visualize the student's error history as a donut chart with the legend positioned below.
    """

    # Prepare data for visualization
    topics = list(student_data.keys())
    frequencies = [value for value in student_data.values() if isinstance(value, (int, float)) and value > 0]

    # Check for empty or invalid data
    if not topics or not frequencies:
        st.warning("No valid error data available to visualize.")
        return

    if len(topics) != len(frequencies):
        st.warning("Mismatch between topics and frequencies. Please check your data.")
        return

    # Normalize frequencies for dynamic color assignment
    cmap = cm.get_cmap("tab20c")  # Change to your preferred colormap
    colors = [cmap(i / len(frequencies)) for i in range(len(frequencies))]

    # Create a donut chart
    fig, ax = plt.subplots(figsize=(8, 8))
    wedges, texts, autotexts = ax.pie(
        frequencies,
        autopct="%1.1f%%",
        startangle=90,
        wedgeprops={"edgecolor": "white"},
        colors=colors,
        pctdistance=0.8
    )

    # Add a center circle to make it a donut chart
    center_circle = plt.Circle((0, 0), 0.60, fc="white")
    fig.gca().add_artist(center_circle)

    # Equal aspect ratio ensures that pie is drawn as a circle
    ax.axis("equal")
    plt.setp(autotexts, size=10, weight="bold", color="black")
    plt.setp(texts, size=8)

    # Title in the center of the donut
    plt.text(0, 0, "Error History", ha="center", va="center", fontsize=12, weight="bold")

    # Add a legend below the chart
    fig.legend(
        wedges,
        topics,
        title="Topics",
        loc="lower center",
        bbox_to_anchor=(0.5, -0.1),
        ncol=2,  # Display legend in two columns
        fontsize=9
    )

    # Adjust layout to make room for the legend
    plt.tight_layout()
    st.pyplot(fig)


def update_user_errors_in_s3(bucket_name, student_code, data):
    """
    Update the user's error data in S3.
    
    Args:
        bucket_name (str): The S3 bucket name.
        student_code (str): The student's ID.
        data (dict): The error data to save.
    """
    file_name = f"errors_{student_code}.json"
    json_data = json.dumps(data)
    s3.put_object(Bucket=bucket_name, Key=file_name, Body=json_data, ContentType="application/json")

def load_user_errors_from_s3(bucket_name, student_code):
    """
    Load the user's error data from S3.
    
    Args:
        bucket_name (str): The S3 bucket name.
        student_code (str): The student's ID.
    
    Returns:
        dict: The user's error data, or an empty dictionary if the file doesn't exist.
    """
    file_name = f"errors_{student_code}.json"
    try:
        response = s3.get_object(Bucket=bucket_name, Key=file_name)
        data = json.loads(response['Body'].read().decode('utf-8'))
        return data  # Return the dictionary directly
    except s3.exceptions.NoSuchKey:
        return {}  # Return an empty dictionary if the file doesn't exist

def search_concept_links(concept):
    """
    Search for course-specific study resources related to a concept using SerpApi.
    """
    api_key = "9809cdc19c68cb1f3379fca7d5c227eb52f5e8cd4e9c70ae9bfb02ed31792bf8"
    search_url = "https://serpapi.com/search.json"
    
    params = {
        "q": concept,  # Focus on course-specific resources
        "hl": "en",    # Language
        "num": 5,      # Number of results
        "api_key": api_key
    }
    
    response = requests.get(search_url, params=params)
    if response.status_code == 200:
        search_results = response.json().get("organic_results", [])
        links = [f"{result['title']}: {result['link']}" for result in search_results]
        return links
    else:
        return ["Unable to fetch resources. Please try again later."]

# Streamlit App
st.title("DSC102 AI Tutor 🤖")

# Ask for Student ID once
if "student_id" not in st.session_state:
    student_id = st.text_input("Enter your Student ID:")
    if student_id:
        st.session_state["student_id"] = student_id
        st.session_state["student_data"] = load_user_errors_from_s3(BUCKET_NAME, student_id)
        st.session_state["graded_2"] = load_user_errors_from_s3(BUCKET_NAME, student_id + "right_wrong_history")
        st.rerun()  # Reload the app after ID is entered
else:
    student_id = st.session_state["student_id"]
    student_data = st.session_state["student_data"]
    graded_2 = st.session_state["graded_2"]

    st.sidebar.success(f"Logged in as: {student_id}")

    if student_id:
        # Initialize student_data in session state if not already initialized
        if f"student_data_" not in st.session_state:
            holder = {}
            st.session_state.student_data = load_user_errors_from_s3(BUCKET_NAME, student_id)
            for key, value in st.session_state.student_data.items():
                holder[key] = value
            st.session_state.student_data = holder
        if f"graded_2_" not in st.session_state:
            holder_2 = {}
            st.session_state.graded_2 = load_user_errors_from_s3(BUCKET_NAME, student_id + "right_wrong_history")

    # Load or initialize session state
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

    # Main navigation
    st.sidebar.title("Features")
    selected_feature = st.sidebar.radio(
        "Select a Feature:",
        ["📋 Generate Quiz", "📊 Concept Self Tracking", "📋 View Your Question History", "🔗 Concept Self-Study Links"]
    )

    if selected_feature == "📋 Generate Quiz":
        st.subheader("Generate Quiz Questions")

        # Initial selection: choose quiz generation method
        quiz_type = st.radio(
            "How would you like to generate the quiz?",
            options=["Course Materials by Weeks", "Concepts You Got Wrong Before"]
        )

        # Option 1: Generate quiz based on course materials (weeks)
        if quiz_type == "Course Materials by Weeks":
            weeks = st.multiselect("Select Course Materials (Weeks):", [str(i) for i in range(1, 11)])
            if weeks:
                materials = load_course_material_by_weeks(weeks)
            else:
                st.error("Please select at least one week.")

        # Option 2: Generate quiz based on concepts user got wrong
        elif quiz_type == "Concepts You Got Wrong Before":
            # Fetch user's error data (replace this with your actual method to fetch data)
            student_data = load_user_errors_from_s3(BUCKET_NAME, student_id)
            
            # If error data exists, let the user select from wrong concepts
            if student_data:
                concepts = list(student_data.keys())
                selected_concepts = st.multiselect("Select Concepts to Include in Quiz:", concepts)
                if selected_concepts:
                    materials = load_course_material_by_concepts(selected_concepts)
                else:
                    st.error("Please select at least one concept.")
            else:
                st.warning("No data available on your past mistakes.")

        # Number of questions
        num_questions = st.number_input("Number of Questions:", min_value=1, max_value=20, step=1, value=5)

        if st.button("Generate Quiz"):
            questions_text = generate_quiz_questions(materials, num_questions)

            # Parse the questions from the numbered list format
            st.session_state.quiz_questions = [q.strip() for q in questions_text.split("\n") if q.strip()]
            st.session_state.quiz_materials = materials
            # Initialize user_answers in session_state
            st.session_state.user_answers = [""] * len(st.session_state.quiz_questions)  # One answer per question
            # Initialize quiz_answers to store user answers
            st.session_state.quiz_answers = {}
            st.success("Quiz Generated! Scroll down to take the quiz.")

        # Display quiz questions with text boxes
        counter = 0
        if "quiz_questions" in st.session_state and st.session_state.quiz_questions:
            for i in st.session_state.quiz_questions:
                st.write(i)
                user_answer = st.text_area(f"Answer for question {counter+1}:", key=f"answer_{counter}", max_chars = 500, height=100)
                if user_answer:  # Only store if the user has typed something
                    st.session_state.quiz_answers[i] = user_answer
                counter += 1

            agree = st.checkbox("I confirm all answers are filled (even if unsure).")
            if st.button("Submit Answer") and agree:
                st.write(st.session_state.quiz_answers)
                graded = grade_quiz_questions(st.session_state.quiz_answers)
                placeholder = grade_quiz_questions_2(st.session_state.quiz_answers)
                st.write("Incorrect Questions question number , Explanation:")
                # st.write(graded)
                for i in graded.strip('[]').split("), ("):
                    st.write(i)
                    topic = attribute_error_to_topic(i[3:])
                    # st.write(attribute_error_to_topic(i[3:]))

                    # Increment the topic frequency in the student's data
                    if topic not in st.session_state.student_data:
                        st.session_state.student_data[topic] = 1
                    else: 
                        st.session_state.student_data[topic] += 1
                
                match = re.search(r"\[.*\]", placeholder, re.DOTALL)
                if match:
                    extracted_content = match.group(0)

                st.session_state.graded_2 = st.session_state.graded_2 + ast.literal_eval(extracted_content)

                # Save the updated data back to the student's file
                update_user_errors_in_s3(BUCKET_NAME, student_id, st.session_state.student_data)
                update_user_errors_in_s3(BUCKET_NAME, student_id + "right_wrong_history", st.session_state.graded_2)

                st.success("Error frequencies updated!")

    elif selected_feature == "📋 View Your Question History":
        st.subheader("📋 View Your Question History")
        # Load question history from S3 (or local session state)
        history_file_name = f"errors_{student_id}right_wrong_history.json"
        try:
            response = s3.get_object(Bucket=BUCKET_NAME, Key=history_file_name)
            question_history = json.loads(response['Body'].read().decode('utf-8'))
        except s3.exceptions.NoSuchKey:
            st.warning("No question history found. Try answering some questions first with ***Generate Quiz*** feature!")
            question_history = []
        # Options for filtering
        filter_option = st.radio(
            "Select the type of questions to display:",
            options=["All Questions", "Right", "Wrong"]
        )

        # Filter questions based on the selected option
        filtered_questions = []
        if filter_option == "All Questions":
            filtered_questions = question_history
        elif filter_option == "Right":
            filtered_questions = [q for q in question_history if q[2] == 1]
        elif filter_option == "Wrong":
            filtered_questions = [q for q in question_history if q[2] == 0]

        # Display the filtered questions
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


    # Concept Links Feature
    elif selected_feature == "🔗 Concept Self-Study Links":

        student_data = load_user_errors_from_s3(BUCKET_NAME, student_id)

        st.subheader("Concept Links and Related Resources")
        st.write("""
        Explore topics you need to improve on and find related resources to deepen your understanding.
        Each topic includes links to external tutorials or resources, and you can track which concepts you want to revisit.
        """)
        if student_data:
            # Combine concepts with their frequencies for display
            concept_options = [
                f"{concept} (Occurrences: {frequency})"
                for concept, frequency in student_data.items()
            ]
            st.write("Tracked Concepts (Select a topic to explore):")
            selected_option = st.selectbox("Choose a concept", concept_options)

            # Extract the concept name from the selected option
            concept = selected_option.split(" (")[0]
        else:
            st.info("No concepts tracked yet. Start practice with ***Generate Quiz*** to build your weakness concept history.")
            concept = None

        # Provide study links for the selected concept
        if concept and st.button("Get Study Links"):
            st.write(f"Fetching study links for concept: **{concept}**")
            links = search_concept_links(concept)
            st.write("### Study Resources")
            if links:
                for link in links:
                    st.write(f"- {link}")
            else:
                st.write("No resources found for this concept. Try a different topic or check back later.")

    # Concept Tracking Feature
    elif selected_feature == "📊 Concept Self Tracking":

        student_data = load_user_errors_from_s3(BUCKET_NAME, student_id)

        holder = {}
        
        if student_data:
            # Display Error History with Enhanced Formatting
            st.subheader("Your Error History")
            st.write("Below is a summary of your tracked errors. Topics with higher frequencies indicate areas to focus on.")
            
            # Create a DataFrame for a more structured display
            error_data = pd.DataFrame({
                "Concept": list(student_data.keys()),
                "Frequency": list(student_data.values())
            })

            # Filter out invalid topics and sort by frequency
            error_data = error_data[~error_data["Concept"].str.contains("_")].sort_values(by="Frequency", ascending=False).reset_index(drop=True)
            holder = dict(zip(error_data["Concept"], error_data["Frequency"]))

            # Display as a table with highlighted frequencies
            st.dataframe(error_data.style.background_gradient(cmap="Blues", subset=["Frequency"]))
            
            # Visualization of Error History
            st.subheader("Error History Visualization")
            visualize_error_history(holder)

        else:
            st.info("No concepts tracked yet. Start practice with ***Generate Quiz*** to build your weakness concept history.")
