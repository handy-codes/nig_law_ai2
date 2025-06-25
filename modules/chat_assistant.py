import streamlit as st
import requests
from dotenv import load_dotenv
import os
import time
from datetime import datetime
from utils.db_utils import log_query, log_feedback
from utils.auth import get_current_firebase_user, login_required
from config.database import SessionLocal
import json
import re
from utils.vector_db import search_chunks  # <-- NEW IMPORT

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def extract_document_references(text):
    """Extract document references from the response text."""
    # Pattern to match law references like "Section 1 of the Land Use Act"
    law_pattern = r'(?:Section|Sections?)\s+\d+(?:-\d+)?(?:\s+and\s+\d+)?\s+of\s+the\s+([A-Za-z\s]+(?:Act|Law|Code|Regulation))'
    # Pattern to match case law references
    case_pattern = r'(?:case of|in\s+)?([A-Za-z\s]+v\.\s+[A-Za-z\s]+)'

    laws = re.findall(law_pattern, text)
    cases = re.findall(case_pattern, text)

    return {
        'laws': list(set(laws)),
        'cases': list(set(cases))
    }


def format_response(text):
    """Format the response with better styling and structure."""
    # Split into sections if they exist
    sections = text.split('\n\n')
    formatted_sections = []

    for section in sections:
        if section.strip().startswith('•') or section.strip().startswith('-'):
            # For bullet points, just keep them as markdown lists
            formatted_sections.append(section)
        elif section.strip().endswith(':'):
            # Format headers with markdown bold
            formatted_sections.append(f"**{section}**")
        else:
            formatted_sections.append(section)

    return '\n\n'.join(formatted_sections)


def get_context_from_db(user_query, k=5):
    results = search_chunks(user_query, k=k)
    context = "\n\n".join([r[1] for r in results])  # r[1] is the chunk text
    return context


@login_required
def chat_interface():
    st.header("💬 Nigerian Legal AI Assistant")

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {
                "role": "system",
                "content": """You are a legal assistant specialized in Nigerian laws. 
                Follow these guidelines:
                1. Always cite relevant laws and sections
                2. Provide context and explanations
                3. Mention if laws have been updated or amended
                4. Include relevant case law when applicable
                5. Be clear about jurisdiction (Federal, State, or both)
                6. If unsure, acknowledge limitations
                7. Format responses with clear sections and bullet points using Markdown only. DO NOT use any HTML tags (e.g., <div>, <span>).
                8. Always start with a brief summary
                9. End with practical implications or next steps"""
            }
        ]

    # Text input
    user_input = st.text_input(
        "Ask a legal question (e.g., What are the rights of tenants under the Land Use Act?)")

    if st.button("Ask") and user_input:
        start_time = time.time()

        # Add user message to chat history
        st.session_state.chat_history.append(
            {"role": "user", "content": user_input})

        with st.spinner("Thinking like a lawyer..."):
            try:
                # --- RAG: Retrieve context from vector DB ---
                context = get_context_from_db(user_input, k=5)

                # --- Compose prompt with context ---
                prompt = f"""
                You are a Nigerian legal expert AI. Use the following context from Nigerian law to answer the user's question. Cite the source if possible.

                Context:
                {context}

                Question:
                {user_input}
                """

                # --- Call Groq API with RAG prompt ---
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {GROQ_API_KEY}"
                }
                payload = {
                    "model": "llama3-8b-8192",
                    "messages": [
                        {"role": "system", "content": prompt}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 1000,
                    "stream": False
                }

                response = requests.post(url, headers=headers, json=payload)
                if response.status_code != 200:
                    st.error(
                        f"API error: {response.status_code} - {response.text}")
                    return

                data = response.json()
                answer = data['choices'][0]['message']['content']

                # Extract document references
                references = extract_document_references(answer)

                # Format the response
                formatted_answer = format_response(answer)

                st.session_state.chat_history.append(
                    {"role": "assistant", "content": formatted_answer})

                # Calculate response time
                response_time = time.time() - start_time

                # Log the query and response
                with SessionLocal() as db:
                    user = get_current_firebase_user()
                    query = log_query(
                        db=db,
                        user_id=user['id'],
                        question=user_input,
                        response=answer,
                        documents_used=references,
                        response_time=response_time
                    )

                    # Store query ID for feedback
                    st.session_state.last_query_id = query.id

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                return

    # Display conversation
    for idx, msg in enumerate(st.session_state.chat_history[1:]):
        role = "You" if msg["role"] == "user" else "JuristAI"

        # Create a container for each message
        with st.container():
            st.markdown(f"**{role}:**")

            # Add styling based on role
            if msg["role"] == "assistant":
                # Extract and display references
                references = extract_document_references(msg['content'])

                st.markdown(f"""
                <div style="
                    background-color: #333333; /* Dark background color */
                    padding: 15px;
                    border-radius: 10px;
                    margin: 10px 0;
                    color: #FFFFFF; /* White text color */
                ">
                    {msg['content']}
                </div>
                """, unsafe_allow_html=True)

                # Display references if any
                if references['laws'] or references['cases']:
                    st.markdown("**References:**")
                    if references['laws']:
                        st.markdown("**Laws:**")
                        for law in references['laws']:
                            st.markdown(f"- {law}")
                    if references['cases']:
                        st.markdown("**Cases:**")
                        for case in references['cases']:
                            st.markdown(f"- {case}")
            else:
                st.markdown(msg['content'])

        # Show feedback only for the latest assistant message
        if msg["role"] == "assistant" and idx == len(st.session_state.chat_history[1:]) - 1:
            st.markdown("---")
            st.markdown("**Was this answer helpful?**")

            col1, col2, col3 = st.columns([1, 1, 2])

            with col1:
                if st.button("👍 Yes", key="helpful_yes"):
                    with SessionLocal() as db:
                        log_feedback(
                            db=db,
                            user_id=get_current_firebase_user()['id'],
                            query_id=st.session_state.last_query_id,
                            rating=5,
                            is_helpful=True
                        )
                    st.success("Feedback submitted! Thank you!")

            with col2:
                if st.button("👎 No", key="helpful_no"):
                    with SessionLocal() as db:
                        log_feedback(
                            db=db,
                            user_id=get_current_firebase_user()['id'],
                            query_id=st.session_state.last_query_id,
                            rating=1,
                            is_helpful=False
                        )
                    st.info("Feedback submitted. We will use this to improve.")

            with col3:
                feedback_text = st.text_input(
                    "Optional: Please tell us more about your feedback", key="feedback_text")
                if st.button("Submit Additional Feedback", key="submit_additional_feedback"):
                    if feedback_text:
                        with SessionLocal() as db:
                            log_feedback(
                                db=db,
                                user_id=get_current_firebase_user()['id'],
                                query_id=st.session_state.last_query_id,
                                rating=0,
                                is_helpful=False,
                                feedback_text=feedback_text
                            )
                            st.success(
                                "Additional feedback submitted! Thank you!")
                    else:
                        st.warning(
                            "Please enter some text for additional feedback.")

    # Add a clear chat button in the sidebar
    if st.sidebar.button("Clear Chat History"):
        st.session_state.chat_history = [
            {
                "role": "system",
                "content": """You are a legal assistant specialized in Nigerian laws. 
                Follow these guidelines:
                1. Always cite relevant laws and sections
                2. Provide context and explanations
                3. Mention if laws have been updated or amended
                4. Include relevant case law when applicable
                5. Be clear about jurisdiction (Federal, State, or both)
                6. If unsure, acknowledge limitations
                7. Format responses with clear sections and bullet points using Markdown only. DO NOT use any HTML tags (e.g., <div>, <span>).
                8. Always start with a brief summary
                9. End with practical implications or next steps"""
            }
        ]
        st.experimental_rerun()
