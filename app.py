import streamlit as st
import requests
import openai
import json
import os
import boto3
import matplotlib.pyplot as plt

# Initialize S3 client
s3 = boto3.client('s3')
BUCKET_NAME = "lign167project"

os.environ['AWS_ACCESS_KEY_ID'] = "AKIAR3HUODFIYESUR3IY"
os.environ['AWS_SECRET_ACCESS_KEY'] = "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"

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

def get_error_specific_hint(code, hint_level):
    """
    Uses OpenAI API to analyze code errors and provide hints based on the level.
    """
    hint_descriptions = {
        1: "Provide a very general and high-level hint to guide the user.",
        2: "Provide a slightly specific hint that gives some direction but remains general.",
        3: "Provide a moderately detailed hint, focusing on the error or problem area.",
        4: "Provide a detailed hint, explaining the error and how to resolve it.",
        5: "Provide a comprehensive and detailed explanation, almost solving the issue."
    }

    prompt = f"""
    Analyze the following code and provide a hint based on the user's selected level of guidance. 
    The levels are defined as follows:
    Level 1: {hint_descriptions[1]}
    Level 2: {hint_descriptions[2]}
    Level 3: {hint_descriptions[3]}
    Level 4: {hint_descriptions[4]}
    Level 5: {hint_descriptions[5]}
    
    Hint Level: {hint_level}
    
    Code:
    ```
    {code}
    ```
    
    Provide a hint at Level {hint_level}.
    """

    completion = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message.content

# def get_related_concepts(code):
#     """
#     Suggest related concepts based on the student's code.
#     """
#     completion = openai.chat.completions.create(
#         model="gpt-4o",
#         messages=[
#             {"role": "user", "content": f"Identify programming concepts related to this code snippet:\n\n{code}"}
#         ]
#     )
#     return completion.choices[0].message.content

################################################### Yiheng Testing ###################################################
def search_concept_links(concept):
    """
    Search for study resources related to a concept using SerpApi.
    """
    api_key = "9809cdc19c68cb1f3379fca7d5c227eb52f5e8cd4e9c70ae9bfb02ed31792bf8"
    search_url = "https://serpapi.com/search.json"
    
    params = {
        "q": concept,  # Search query
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
################################################### Yiheng Testing ###################################################

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

# Build the conversation history to provide context to MentorAI
    conversation_history = ""
    for turn in st.session_state.conversation_history:
        conversation_history += f"User's Code: {turn['user']}\nError Type: {turn['error_type']}\n"

    # Create the prompt for the error categorization
    prompt = f"""
    Here is the student's current code: {code}
    
    Here are all previous questions the user has asked and the corresponding error types:
    {conversation_history}

    If you think the current question's error type is similar to that of a previous one, please attribute the current input's error type to that of the previous one.

    Otherwise, please attribute the current code to one of the following categories:
    [Algorithm, Data Structure, String Manipulation, Array and Matrix operation, Mathematical and Logical, Recursion and Backtracking, Searching and Sorting, Dynamic Programming, System Design, Object-Oriented Programming, Database and SQL, Real-World Simulation, Problem-Solving with APIs, Optimization].

    Output your answer in this format: [[your_answer]]. You MUST output one category from the list.
    """

    completion = openai.chat.completions.create(
        model = "gpt-4o",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    # Remove brackets [[ ]] from the output
    error_category = completion.choices[0].message.content.strip()
    if error_category.startswith("[[") and error_category.endswith("]]"):
        error_category = error_category[2:-2]  # Remove the outer [[ ]]
    return error_category

def generate_practice_questions_artistic(error_type, code):
    """
    Generate 2-3 artistic and engaging practice questions based on the error type using the LLM.
    """
    try:
        prompt = f"""You are an exercise programming question designer, and the student is struggling with this type of question{error_type}, and here is the code student provided, which contains the error: {code}, Please just output the question you design to help students practice this knowledge. Do not output any other things. Output as a .txt file format.
        """
        completion = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        response = completion.choices[0].message.content.strip()
        return response
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

def visualize_error_types_donut(error_frequencies):
    labels = list(error_frequencies.keys())
    sizes = list(error_frequencies.values())

    # Creating the donut chart
    fig, ax = plt.subplots()
    wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, wedgeprops={'edgecolor': 'white'})
    
    # Draw a circle at the center to make it a donut
    center_circle = plt.Circle((0, 0), 0.70, fc='white')
    fig.gca().add_artist(center_circle)

    # Styling the chart
    ax.axis('equal')  # Ensures that the pie is drawn as a circle.
    plt.setp(autotexts, size=10, weight="bold")
    plt.setp(texts, size=9)

    # Title in the center of the donut chart
    plt.text(0, 0, f"Total Errors: {sum(sizes)}", horizontalalignment='center', verticalalignment='center', fontsize=12, weight='bold')

    # Display the donut chart in Streamlit
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
        return data.get("tracked_errors", []), data.get("error_frequencies", {})
    except s3.exceptions.NoSuchKey:
        return [], {}  # Default empty data if file doesn't exist


st.title("MentorAI 🤖")

error_description = ""
hint = ""

# Prompt the user for their student code
if 'student_code' not in st.session_state:
    st.session_state.student_code = None

if 'round' not in st.session_state:
    st.session_state.round = 0

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

if not st.session_state.student_code:
    st.session_state.student_code = st.text_input("Enter your student code:", "")
    
    if st.session_state.student_code:
        # Load errors and frequencies for this user
        tracked_errors, error_frequencies = load_user_errors_from_s3(BUCKET_NAME, st.session_state.student_code)
        # tracked_errors, error_frequencies = load_user_errors(st.session_state.student_code)
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

    # Display conversation history
    if st.session_state.conversation_history:
        st.write("### Conversation History")
        for turn in st.session_state.conversation_history:
            st.markdown(f"**You:** {turn['user']}")
            st.markdown(f"**MentorAI:** {turn['assistant']}")
    st.markdown("**Paste your question here:**")
    code_input = st.text_area("", height=200)
    hint_level = st.slider("Choose Hint Level (1: General, 5: Detailed)", 1, 5, 1)

    if st.button("Analyze Code"):
        if code_input.strip():
            with st.spinner("Analyzing your code..."):
                try:
                    hint = get_error_specific_hint(code_input, hint_level)

                    # Update conversation history
                    st.session_state.conversation_history.append({
                        "user": f"Code Input:\n{code_input}\nHint Level: {hint_level}",
                        "assistant": hint,
                        "error_type": error_tracking(code_input)
                    })
                    error_description = error_tracking(code_input)
                    st.write("Your code: ")
                    st.code(code_input)
                    st.markdown("**Hint:** " + hint)

                    # # Display updated conversation history
                    # st.write("### Conversation History")
                    # for turn in st.session_state.conversation_history:
                    #     st.markdown(f"**You:** {turn['user']}")
                    #     st.markdown(f"**MentorAI:** {turn['assistant']}")
                    #     error_description = error_tracking(code_input)
                    
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
                    # st.write("Hint: " + hint)
                    # Notify if this error has been repeated multiple times
                    if st.session_state.error_frequencies[error_description] >= 3:
                        st.warning(f"You've encountered this type of error: {error_description} multiple times ({st.session_state.error_frequencies[error_description]} times). Consider revisiting this topic to strengthen your understanding.")
                        # print("hey")
                        st.session_state.show_practice_popup = True
                        st.session_state.round += 1
                        # Add a button to trigger the pop-up
                        # Check if the pop-up should be displayed

                    # Save updated data to S3
                    update_user_errors_in_s3(
                        BUCKET_NAME,
                        st.session_state.student_code,
                        {
                            "tracked_errors": st.session_state.tracked_errors,
                            "error_frequencies": st.session_state.error_frequencies
                        }
                    )

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

################################################### Yiheng Testing ###################################################
# elif st.session_state.active_feature == 'concept_links':
#     # Display content for Concept Links and Related Resources
#     st.subheader("Concept Links and Related Resources")
#     st.write("""
#     Each hint includes links to external resources that help explain foundational programming concepts.
#     For example, if you're struggling with recursion, you will receive a link to a tutorial on base cases and recursion.
#     """)
#     code_input = st.text_area("Paste your code snippet here:", height=200)

#     if st.button("Get Related Concepts"):
#         related_concept = get_related_concepts(code_input)
#         st.write("Related Concepts: " + related_concept)

elif st.session_state.active_feature == 'concept_links':
    # Display content for Concept Links and Related Resources
    st.subheader("Concept Links and Related Resources")
    st.write("""
    Each hint includes links to external resources that help explain foundational programming concepts.
    For example, if you're struggling with recursion, you will receive a link to a tutorial on base cases and recursion.
    """)

    # Load errors and frequencies
    if st.session_state.tracked_errors and st.session_state.error_frequencies:
        # Combine concepts with their frequencies for display
        concept_options = [
            f"{concept} (Errors: {st.session_state.error_frequencies.get(concept, 0)})"
            for concept in set(st.session_state.tracked_errors)
        ]
        st.write("Tracked Errors (Select a concept to explore):")
        selected_option = st.selectbox("Choose a concept", concept_options)
        
        # Extract the concept name from the selected option
        concept = selected_option.split(" (")[0]
    else:
        st.write("No errors tracked for this user.")

    if "concept" in locals() and st.button("Get Study Links"):
        st.write(f"Fetching study links for concept: **{concept}**")
        links = search_concept_links(concept)
        st.write("### Study Links")
        for link in links:
            st.write(f"- {link}")
################################################### Yiheng Testing ###################################################

elif st.session_state.active_feature == 'error_tracking':
    st.subheader("📊 Error Tracking")
    st.write(f"Student Code: {st.session_state.student_code}")
    st.write("""
    This feature tracks all errors detected during the Error-Specific Guidance sessions.
    Below is a summary of your errors categorized by type.
    """)

    # Load errors and frequencies from S3 to ensure the latest data
    tracked_errors, error_frequencies = load_user_errors_from_s3(BUCKET_NAME, st.session_state.student_code)
    st.session_state.tracked_errors = tracked_errors
    st.session_state.error_frequencies = error_frequencies

    # Display summary of error frequencies
    if st.session_state.error_frequencies:
        st.write("### Error Summary:")
        for idx, (error_type, count) in enumerate(st.session_state.error_frequencies.items(), start=1):
            st.write(f"**{idx}. {error_type}: {count}**")

        # Visualize errors if a visualization function is available
        visualize_error_types_donut(st.session_state.error_frequencies)
    else:
        st.write("No errors tracked yet. Use the **Error-Specific Guidance** feature to analyze code.")

    # Optional: Clear error history for the current user
    if st.button("Clear Error History"):
        # Reset errors in session state
        st.session_state.tracked_errors = []
        st.session_state.error_frequencies = {}

        # Update S3 to clear the file
        update_user_errors_in_s3(
            BUCKET_NAME,
            st.session_state.student_code,
            {"tracked_errors": [], "error_frequencies": {}}
        )
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
