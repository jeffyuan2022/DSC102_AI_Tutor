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

def get_concept_specific_hint(input_text, hint_level):
    """
    Uses OpenAI API to analyze the user's input and provide hints based on the level.
    Targets DSC102 concepts using the content from 'dsc102.txt'.
    """
    # Load DSC102 course content as the system prompt
    try:
        with open('dsc102.txt', 'r', encoding='utf-8') as file:
            dsc102_system_prompt = file.read()
    except FileNotFoundError:
        raise FileNotFoundError("Error: 'dsc102.txt' not found. Please ensure the file is in the correct directory.")

    # Define hint levels
    hint_descriptions = {
        1: "Provide a very general and high-level hint to guide the user.",
        2: "Provide a slightly specific hint that gives some direction but remains general.",
        3: "Provide a moderately detailed hint, focusing on the concept area.",
        4: "Provide a detailed hint, explaining the concept with examples or applications.",
        5: "Provide an in-depth exploration, including technical details and references to the course content."
    }

    # Construct the user prompt for the OpenAI API
    prompt = f"""
    Analyze the following input and provide a hint related to the DSC102 course based on the user's selected level of guidance. 
    Use the content from the DSC102 course as a reference.
    
    The levels are defined as follows:
    Level 1: {hint_descriptions[1]}
    Level 2: {hint_descriptions[2]}
    Level 3: {hint_descriptions[3]}
    Level 4: {hint_descriptions[4]}
    Level 5: {hint_descriptions[5]}
    
    Hint Level: {hint_level}
    
    Input Text:
    ```
    {input_text}
    ```
    
    Provide a hint at Level {hint_level}.
    """

    # Call the OpenAI API with the system and user prompts
    completion = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": dsc102_system_prompt},
            {"role": "user", "content": prompt}
        ]
    )

    # Extract and return the hint from the completion
    return completion.choices[0].message.content.strip()

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

def track_concepts_from_input(input_text):
    """
    Matches the user's input to DSC102 concepts.
    """
    # Build the conversation history to provide context for MentorAI
    conversation_history = ""
    for turn in st.session_state.conversation_history:
        conversation_history += f"User's Input: {turn['user']}\nConcept Type: {turn['error_type']}\n"

    # Define DSC102-specific concepts
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

    # Create the prompt for concept categorization
    prompt = f"""
    Here is the user's current input: {input_text}
    
    Here are all previous inputs the user has provided and the corresponding concept types:
    {conversation_history}

    If you think the current input's concept type is similar to that of a previous one, 
    please attribute the current input's concept type to that of the previous one.

    Otherwise, please attribute the current input to one of the following DSC102 course topics:
    {', '.join(dsc102_topics)}.

    Output your answer in this format: [[your_answer]]. You MUST output one category from the list.
    """

    # Use OpenAI to determine the concept type
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

def generate_practice_questions_artistic(concept, input_text):
    """
    Generate 2-3 practice questions based on the DSC102 concept.
    """
    try:
        # Define the prompt for generating practice questions
        prompt = f"""
        You are an educational content designer for the DSC102 course.
        The student is studying this topic: {concept}.
        Here is the student's input or area of focus: {input_text}.
        
        Design 2-3 engaging and challenging practice questions to help the student deepen their understanding of this topic.
        Ensure the questions are aligned with the DSC102 course content and emphasize conceptual clarity and application.
        Provide only the questions as output, without any additional text or explanations.
        """
        
        # Use OpenAI's API to generate the practice questions
        completion = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract the response
        response = completion.choices[0].message.content.strip()
        return response
    
    except Exception as e:
        return [f"An error occurred while generating questions: {e}"]

def get_practice_questions_answers(practice_questions):
    try:
        # Define the prompt for generating practice questions
        prompt = f"""
        Please use this context as reference when you are answering these questions: 
        You are an answerer of these questions: {practice_questions}.
        
        Provide only the answers as output, without any additional text or explanations
        Please answer these questions as concise as possible.
        Ensure the questions are aligned with the DSC102 course content.
        """
        
        # Use OpenAI's API to generate the practice questions
        completion = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract the response
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

st.markdown(
    """
    <style>
    .main {
        background-color: #F1F8E9;
    }
    h1, h2 {
        color: #2E7D32;
        font-family: "Arial", sans-serif;
    }
    .stButton>button {
        background-color: #FF8A65;
        color: white;
        border-radius: 8px;
        font-weight: bold;
    }
    </style>

    """,
    unsafe_allow_html=True
)


error_description = ""
hint = ""

# Prompt the user for their Student ID
if 'student_code' not in st.session_state:
    st.session_state.student_code = None

if 'round' not in st.session_state:
    st.session_state.round = 0

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

if not st.session_state.student_code:
    st.session_state.student_code = st.text_input("Enter your student ID:", "")
    
    if st.session_state.student_code:
        # Load errors and frequencies for this user
        tracked_errors, error_frequencies = load_user_errors_from_s3(BUCKET_NAME, st.session_state.student_code)
        # tracked_errors, error_frequencies = load_user_errors(st.session_state.student_code)
        st.session_state.tracked_errors = tracked_errors
        st.session_state.error_frequencies = error_frequencies
        st.success(f"Welcome, student {st.session_state.student_code}! Your error history is loaded.")
    else:
        st.stop()  # Stop the app until a valid Student ID is entered



if 'active_feature' not in st.session_state:
    st.session_state.active_feature = None

if 'show_practice_popup' not in st.session_state:
    st.session_state.show_practice_popup = True

if 'practice_questions_indicator' not in st.session_state:
    st.session_state.practice_questions_indicator = False

if 'show_answer_indicator' not in st.session_state:
    st.session_state.show_answer_indicator = False

if 'practice_questions' not in st.session_state:
    st.session_state.practice_questions = ''

if 'show_answer' not in st.session_state:
    st.session_state.show_answer = ''

if 'tracked_concepts' not in st.session_state:
    st.session_state.tracked_concepts = ''

if 'concept_frequency' not in st.session_state:
    st.session_state.concept_frequencies = 0

# Create three columns for the buttons
col1, col2, col3 = st.columns(3)

# Place buttons in separate columns to arrange them horizontally
with col1:
    if st.button("🛠️Concept Guidance"):
        st.session_state.active_feature = 'concept_guidance'
with col2:
    if st.button("🔗Concept Self-Study Links"):
        st.session_state.active_feature = 'concept_links'
with col3:  # Add this under the existing buttons
    if st.button("📊Concept Tracking"):
        st.session_state.active_feature = 'concept_tracking'

if st.session_state.active_feature == 'concept_guidance':
    # Display content for Concept-Specific Guidance and Hints
    st.subheader("Concept-Specific Guidance and Hints")
    st.write("""
    This feature allows students to input questions or topics related to the DSC102 course and receive guidance based on the specific concepts involved.
    The hints start with general information and become more detailed as needed, helping students deepen their understanding of the concepts.
    """)

    # Display conversation history
    if st.session_state.conversation_history:
        st.write("### Conversation History")
        for turn in st.session_state.conversation_history:
            st.markdown(f"**You:** {turn['user']}")
            st.markdown(f"**MentorAI:** {turn['assistant']}")
    st.markdown("**Paste your question here:**")
    code_input = st.text_area("Input your question or topic:", height=200, label_visibility="collapsed")
    hint_level = st.slider("Choose Hint Level (1: General, 5: Detailed)", 1, 5, 1)


    if st.session_state.practice_questions_indicator and st.session_state.show_answer_indicator:
        st.markdown("***Here are your practice questions:***")
        st.write(st.session_state.practice_questions)
        st.markdown("***Here are answers of your practice questions***")
        st.write(st.session_state.show_answer)
        st.session_state.practice_questions_indicator = False
        st.session_state.show_answer_indicator = False

        if st.button("Exit Practice Questions"):
            print("AAA")



    if st.button("Analyze Code"):
        if code_input.strip():
            with st.spinner("Analyzing your code..."):
                
                hint = get_concept_specific_hint(code_input, hint_level)

                # Update conversation history
                st.session_state.conversation_history.append({
                    "user": f"Input Text:\n{code_input}\nHint Level: {hint_level}",
                    "assistant": hint,
                    "error_type": track_concepts_from_input(code_input)
                })
                error_description = track_concepts_from_input(code_input)
                st.write("Your input: ")
                st.text(code_input)
                st.markdown("**Hint:** " + hint)

                    # # Display updated conversation history
                    # st.write("### Conversation History")
                    # for turn in st.session_state.conversation_history:
                    #     st.markdown(f"**You:** {turn['user']}")
                    #     st.markdown(f"**MentorAI:** {turn['assistant']}")
                    #     error_description = track_concepts_from_input(code_input)
                    
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
                    st.warning(f"You've engaged with this concept: {error_description} multiple times ({st.session_state.error_frequencies[error_description]} times). Consider reviewing additional resources to strengthen your understanding.")
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
                st.session_state.round += 1
                if st.session_state.get("show_practice_popup", True) and st.session_state.round > 0 and st.session_state.error_frequencies[error_description] >= 3:
                    st.title("Practice Questions")
                    st.markdown("### Practice Questions")
                    st.write("Here are some practice questions based on your repeated concepts:")

                    # Generate practice questions
                    with st.spinner("Creating practice questions..."):
                        practice_questions = generate_practice_questions_artistic(error_description, code_input)
                        st.write(practice_questions)
                        answers = get_practice_questions_answers(practice_questions)
                        st.session_state.show_answer_indicator = True
                        st.session_state.practice_questions_indicator = True
                        st.session_state.show_answer = answers
                        st.session_state.practice_questions = practice_questions


                    
                    show_answers = st.selectbox(
                            "Would you like to view the answers?",
                            ["No", "Yes"],
                            index=0
                        )


                    # Add a button to close the pop-up
                    if st.button("Close"):
                        st.session_state.show_practice_popup = False  # Reset the flag
                    st.stop()  # Prevent further execution
    
                    # Add a select box to control the display of answers
                    
elif st.session_state.active_feature == 'concept_links':
    # Display content for Concept Links and Related Resources
    st.subheader("Concept Links and Related Resources")
    st.write("""
    Explore topics from the DSC102 course and find related resources to deepen your understanding.
    Each topic includes links to external tutorials or resources, and you can track which concepts you want to revisit.
    """)

    tracked_concepts, concept_frequencies = load_user_errors_from_s3(BUCKET_NAME, st.session_state.student_code)
    st.session_state.tracked_concepts = tracked_concepts
    st.session_state.concept_frequencies = concept_frequencies

    # Load tracked concepts and their frequencies
    if st.session_state.tracked_concepts and st.session_state.concept_frequencies:
        # Combine concepts with their frequencies for display
        concept_options = [
            f"{concept} (Occurrences: {st.session_state.concept_frequencies.get(concept, 0)})"
            for concept in set(st.session_state.tracked_concepts)
        ]
        st.write("Tracked Concepts (Select a topic to explore):")
        selected_option = st.selectbox("Choose a concept", concept_options)
        
        # Extract the concept name from the selected option
        concept = selected_option.split(" (")[0]
    else:
        st.write("No concepts tracked yet. Start exploring topics to build your understanding.")

    # Provide study links for the selected concept
    if "concept" in locals() and st.button("Get Study Links"):
        st.write(f"Fetching study links for concept: **{concept}**")
        links = search_concept_links(concept)
        st.write("### Study Resources")
        if links:
            for link in links:
                st.write(f"- {link}")
        else:
            st.write("No resources found for this concept. Try a different topic or check back later.")

elif st.session_state.active_feature == 'concept_tracking':
    st.subheader("📊 DSC102 Course Concept Tracking")
    st.write(f"Student ID: {st.session_state.student_code}")
    st.write("""
    This feature tracks all concepts explored during your learning sessions.
    Below is a summary of the concepts you've engaged with, categorized by DSC102 topics.
    """)

    # Load concepts and frequencies from S3 to ensure the latest data
    tracked_concepts, concept_frequencies = load_user_errors_from_s3(BUCKET_NAME, st.session_state.student_code)
    st.session_state.tracked_concepts = tracked_concepts
    st.session_state.concept_frequencies = concept_frequencies

    # Display summary of concept frequencies
    if st.session_state.concept_frequencies:
        st.write("### Concept Engagement Summary:")
        for idx, (concept, count) in enumerate(st.session_state.concept_frequencies.items(), start=1):
            st.write(f"**{idx}. {concept}: {count} occurrences**")

        # Visualize concept engagement if a visualization function is available
        visualize_error_types_donut(st.session_state.concept_frequencies)
    else:
        st.write("No concepts tracked yet. Use the **Concept Exploration** feature to start learning.")

    # Optional: Clear concept history for the current user
    if st.button("Clear Concept History"):
        # Reset concepts in session state
        st.session_state.tracked_concepts = []
        st.session_state.concept_frequencies = {}

        # Update S3 to clear the file
        update_user_errors_in_s3(
            BUCKET_NAME,
            st.session_state.student_code,
            {"tracked_concepts": [], "concept_frequencies": {}}
        )
        st.success("Concept history cleared.")

else:
    # Default content when no button is clicked
    st.write("""
    Welcome to MentorAI! Click any of the buttons above to learn more about the features of this application.
    """)
