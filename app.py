import streamlit as st
import openai

# Set up OpenAI API key
openai.api_key = "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"

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

st.title("MentorAI")

if 'active_feature' not in st.session_state:
    st.session_state.active_feature = None

# Create three columns for the buttons
col1, col2, col3 = st.columns(3)

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
        st.write("Analyzing your code... (hint generation would be here)")
        hint = get_error_specific_hint(code_input)
        st.write("Hint: " + hint)

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

else:
    # Default content when no button is clicked
    st.write("""
    Welcome to MentorAI! Click any of the buttons above to learn more about the features of this application.
    """)

# else:
#     # Default content when no button is clicked
#     st.write("""
#     Welcome to the Interactive Coding Helper! Click any of the buttons above to learn more about the features of this application.
#     """)

# # Sidebar for input and concept options
# st.sidebar.header("Input Code Here")
# code_input = st.sidebar.text_area("Paste your code snippet:", height=200)

# # Button to analyze code
# if st.sidebar.button("Analyze Code"):
#     st.write("Analyzing your code and generating hints...")
#     # Call function to get hints from OpenAI API (to be implemented)

# # Area to display hints
# st.header("Hints and Resources")
# hint_area = st.empty()  # Placeholder for hints
# concept_area = st.empty()  # Placeholder for related concepts
# pseudocode_area = st.empty()  # Placeholder for pseudocode

# # Display additional resources
# st.header("Additional Resources")
# st.write("Links to further study and practice will appear here.")

# if code_input:
#     # Fetch and display hint
#     hint = get_error_specific_hint(code_input)
#     hint_area.write("Hint: " + hint)

#     # Fetch and display related concepts
#     related_concepts = get_related_concepts(code_input)
#     concept_area.write("Related Concepts: " + related_concepts)

#     # Fetch and display pseudocode outline
#     pseudocode_outline = generate_pseudocode_outline(code_input)
#     pseudocode_area.write("Pseudocode Outline:\n" + pseudocode_outline)


