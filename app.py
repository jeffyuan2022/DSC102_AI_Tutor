import streamlit as st
import openai
import json
import os

# Set up OpenAI API key
openai.api_key = "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"

def get_error_file(student_code):
    """Generate the filename for storing a user's errors."""
    return f"errors_{student_code}.json"

def load_user_errors(student_code):
    """Load the error patterns and frequencies for a specific student."""
    file_name = get_error_file(student_code)
    if os.path.exists(file_name):
        with open(file_name, "r") as file:
            data = json.load(file)
            return data.get("tracked_errors", []), data.get("error_frequencies", {})
    return [], {}  # Default to empty data if file doesn't exist

def save_user_errors(student_code, data):
    """Save the error patterns and frequencies for a specific student."""
    file_name = get_error_file(student_code)
    with open(file_name, "w") as file:
        json.dump(data, file)

def get_error_specific_hint(code):
    """
    Uses OpenAI API to analyze code errors and provide hints.
    """
    completion = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": f"Analyze the following code for errors and suggest hints:\n\n{code}"}
        ]
    )
    return completion.choices[0].message.content

def get_related_concepts(code):
    """
    Suggest related concepts based on the student's code.
    """
    completion = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": f"Identify programming concepts related to this code snippet:\n\n{code}"}
        ]
    )
    return completion.choices[0].message.content

def generate_pseudocode_outline(code):
    """
    Generate a pseudocode outline for the student's code.
    """
    completion = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": f"Create a pseudocode outline for the following code:\n\n{code}"}
        ]
    )
    return completion.choices[0].message.content

def error_tracking(code):
    completion = openai.chat.completions.create(
        model = "gpt-4o",
        messages=[
            {"role": "user", "content": f"Here is the student's code: {code}, would you please attribute the code to one of the following category:[Algorithm, Data Structure, String Manipulation, Array and Matrix operation, Mathematical and Logical, Recursion and Backtracking, Searching and Sorting, Dynamic Programming, System Design, Object-Oriented Programming, Database and SQL, Real-World Simulation, Problem-Solving with APIs, Optimization] and output your answer in this format: [[your_answer]]? You MUST output one category in the list"}
        ]
    )
    return completion.choices[0].message.content

def generate_practice_questions_artistic(error_type, code):
    """
    Generate 2-3 artistic and engaging practice questions based on the error type using the LLM.
    """
    try:
        prompt = f"""You are an exercise programming question designer, and the student is struggling with this type of question{error_type}, and here is the code student provided, which contains the error: {code}, Please just output the question you design to help students practice this knowledge. Do not output any other things.
        
        """
        completion = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        response = completion.choices[0].message.content.strip()
        return response.split("\n")  # Split response into separate questions
    except Exception as e:
        return [f"An error occurred while generating questions: {e}"]

def get_concept_suggestions(question):
    """
    Get suggested concepts to explore based on the student's question.
    """
    completion = openai.chat.completions.create(
        model="gpt-4",  # Note: Changed from "gpt-4o" to "gpt-4"
        messages=[
            {"role": "user", "content": f"""
            Based on this programming question: {question}
            
            1. Identify the main programming concepts involved
            2. Suggest 3-5 related concepts that would be valuable to explore
            3. Provide a brief explanation of why these concepts are related
            
            Format the response as:
            Main Concept: [concept]
            Related Concepts:
            - [concept 1]: [brief explanation]
            - [concept 2]: [brief explanation]
            - [concept 3]: [brief explanation]
            """}
        ]
    )
    return completion.choices[0].message.content.strip()

st.title("MentorAI 🤖")

error_description = ""
hint = ""

# Prompt the user for their student code
if 'student_code' not in st.session_state:
    st.session_state.student_code = None

if 'round' not in st.session_state:
    st.session_state.round = 0

if not st.session_state.student_code:
    st.session_state.student_code = st.text_input("Enter your student code:", "")
    
    if st.session_state.student_code:
        # Load errors and frequencies for this user
        tracked_errors, error_frequencies = load_user_errors(st.session_state.student_code)
        st.session_state.tracked_errors = tracked_errors
        st.session_state.error_frequencies = error_frequencies
        st.success(f"Welcome, student {st.session_state.student_code}! Your error history is loaded.")
    else:
        st.stop()  # Stop the app until a valid student code is entered



if 'active_feature' not in st.session_state:
    st.session_state.active_feature = None

if 'show_practice_popup' not in st.session_state:
    st.session_state.show_practice_popup = True

# Create three columns for the buttons
col1, col2, col3, col4, col5 = st.columns(5)

# Place buttons in separate columns to arrange them horizontally
with col1:
    if st.button("🛠️Error-Specific Guidance and Hints"):
        st.session_state.active_feature = 'error_guidance'
with col2:
    if st.button("📘Pesudo Answer Generation Ground"):
        st.session_state.active_feature = 'Pesudo Answer Generation'
with col3:
    if st.button("🔗Concept Links and Related Resources"):
        st.session_state.active_feature = 'concept_links'
with col4:  # Add this under the existing buttons
    if st.button("📊Error Tracking"):
        st.session_state.active_feature = 'error_tracking'
with col5:
    if st.button("🔍 Concept Explorer"):
        st.session_state.active_feature = 'concept_explorer'
# error_description = ""
# Define behavior based on the button clicked
# Define behavior based on the button clicked
if st.session_state.active_feature == 'error_guidance':
    # Display content for Error-Specific Guidance and Hints
    st.subheader("Error-Specific Guidance and Hints")
    st.write("""
    This feature allows students to input their code and receive hints based on the specific errors found.
    The hints start with general guidance and become more specific as needed, helping students solve issues
    on their own while learning from the process.
    """)
    code_input = st.text_area("Paste your code snippet here:", height=200)

    if st.button("Analyze Code"):
        if code_input.strip():
            with st.spinner("Analyzing your code..."):
                try:
                    hint = get_error_specific_hint(code_input)
                    error_description = error_tracking(code_input)
                    # Track the error
                    if 'tracked_errors' not in st.session_state:
                        st.session_state.tracked_errors = []
                    # Track frequency of this error
                    if 'error_frequencies' not in st.session_state:
                        st.session_state.error_frequencies = {}
                    
                    # Increment the frequency of the current error
                    if error_description in st.session_state.error_frequencies:
                        st.session_state.error_frequencies[error_description] += 1
                    else:
                        st.session_state.error_frequencies[error_description] = 1
                    
                    st.session_state.tracked_errors.append(error_description)
                    st.write("Hint: " + hint)
                    # Notify if this error has been repeated multiple times
                    if st.session_state.error_frequencies[error_description] >= 3:
                        st.warning(f"You've encountered this type of error: {error_description} multiple times ({st.session_state.error_frequencies[error_description]} times). Consider revisiting this topic to strengthen your understanding.")
                        # print("hey")
                        st.session_state.show_practice_popup = True
                        st.session_state.round += 1
                        # Add a button to trigger the pop-up
                        # Check if the pop-up should be displayed
                    if st.session_state.get("show_practice_popup", True) and st.session_state.round > 0:
                        st.title("Practice Questions")
                        st.markdown("### Practice Questions")
                        st.write("Here are some practice questions based on your repeated errors:")

                        # Generate practice questions
                        with st.spinner("Creating practice questions..."):
                            practice_questions = generate_practice_questions_artistic(error_description, code_input)
                            st.write(practice_questions)

                        # Add a button to close the pop-up
                        if st.button("Close"):
                            st.session_state.show_practice_popup = False  # Reset the flag
                        st.stop()  # Prevent further execution

                    # Save errors and frequencies to the user's file
                    save_user_errors(
                        st.session_state.student_code, 
                        {
                            "tracked_errors": st.session_state.tracked_errors,
                            "error_frequencies": st.session_state.error_frequencies,
                        }
                    )

                except Exception as e:
                    st.error(f"An error occurred: {e}")
        else:
            st.error("Please paste a valid code snippet.")
            st.session_state.round += 1


elif st.session_state.active_feature == 'Pesudo Answer Generation':
    # Display content for Pattern Detection for Repeated Mistakes
    st.subheader("Pseudo answer generation for students' programming question")
    st.write("""
    This feature provides student a start place on their programming problem.
    """)
    user_id = st.text_input("Enter your user ID:")
    code_input = st.text_area("Paste your code snippet here:", height=200)

    if st.button("Get Pesudo Answer"):
        result = generate_pseudocode_outline(code_input)
        st.write(result)

elif st.session_state.active_feature == 'concept_links':
    # Display content for Concept Links and Related Resources
    st.subheader("Concept Links and Related Resources")
    st.write("""
    Each hint includes links to external resources that help explain foundational programming concepts.
    For example, if you're struggling with recursion, you will receive a link to a tutorial on base cases and recursion.
    """)
    code_input = st.text_area("Paste your code snippet here:", height=200)

    if st.button("Get Related Concepts"):
        related_concept = get_related_concepts(code_input)
        st.write("Related Concepts: " + related_concept)

elif st.session_state.active_feature == 'error_tracking':
    st.subheader("📊 Error Tracking")
    st.write(f"Student Code: {st.session_state.student_code}")
    st.write("""
    This feature tracks all errors detected during the Error-Specific Guidance sessions.
    Below is a summary of your errors categorized by type.
    """)

    # Load errors and frequencies from the file to ensure the latest data
    st.session_state.tracked_errors = load_user_errors(st.session_state.student_code)[0]
    st.session_state.error_frequencies = load_user_errors(st.session_state.student_code)[1]

    # Display summary of error frequencies
    if st.session_state.error_frequencies:
        st.write("### Error Summary:")
        for idx, (error_type, count) in enumerate(st.session_state.error_frequencies.items(), start=1):
            st.write(f"**{idx}. {error_type}: {count}**")
    else:
        st.write("No errors tracked yet. Use the **Error-Specific Guidance** feature to analyze code.")

    # Optional: Clear error history for the current user
    if st.button("Clear Error History"):
        st.session_state.tracked_errors = []
        st.session_state.error_frequencies = {}
        save_user_errors(st.session_state.student_code, {"tracked_errors": [], "error_frequencies": {}})
        st.success("Error history cleared.")

elif st.session_state.active_feature == 'concept_explorer':
    st.subheader("🔍 Concept Explorer")
    st.write("""
    This feature helps you discover related programming concepts based on your question.
    Input your programming question to see what other topics you might want to explore!
    """)
    
    question = st.text_area("Enter your programming question:", height=100)
    
    if st.button("Explore Related Concepts"):
        if question.strip():
            with st.spinner("Finding related concepts..."):
                try:
                    concepts = get_concept_suggestions(question)
                    st.write(concepts)
                    
                except Exception as e:
                    st.error(f"An error occurred: {e}")
        else:
            st.error("Please enter a question first.")




else:
    # Default content when no button is clicked
    st.write("""
    Welcome to MentorAI! Click any of the buttons above to learn more about the features of this application.
    """)
