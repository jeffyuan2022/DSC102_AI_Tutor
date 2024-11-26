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

st.title("MentorAI 🤖")

# Prompt the user for their student code
if 'student_code' not in st.session_state:
    st.session_state.student_code = None

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

# Create three columns for the buttons
col1, col2, col3, col4 = st.columns(4)

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
error_description = ""
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




else:
    # Default content when no button is clicked
    st.write("""
    Welcome to MentorAI! Click any of the buttons above to learn more about the features of this application.
    """)
