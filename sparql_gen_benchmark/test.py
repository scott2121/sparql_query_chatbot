import os
from datetime import datetime

import const
import pandas as pd
import requests
import streamlit as st
from functions.prompt_maker import make_one_prompt
from functions.SPARQL_executer import execute_one_query
from functions.SPARQL_generator import generate_one_sparql
from openai import OpenAI

# Streamlit layout settings
st.set_page_config(layout="wide")
st.markdown(const.HIDE_ST_STYLE, unsafe_allow_html=True)

# API endpoint
API_BASE_URL = "http://chatbot-backend:8000"

# Initialize session state
if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "query_code" not in st.session_state:
    st.session_state["query_code"] = ""

if "query_result" not in st.session_state:
    st.session_state["query_result"] = None

if "selected_db" not in st.session_state:
    st.session_state["selected_db"] = "uniprot"  # Default to "uniprot"

if "previous_query" not in st.session_state:
    st.session_state["previous_query"] = ""

if "previous_user_input" not in st.session_state:
    st.session_state["previous_user_input"] = ""

if "conversation_id" not in st.session_state:
    st.session_state["conversation_id"] = None

# Add new session state variables for query history
if "query_history" not in st.session_state:
    st.session_state["query_history"] = []
    
if "query_history_position" not in st.session_state:
    st.session_state["query_history_position"] = -1

def create_new_conversation(title=None):
    """Create a new conversation with given title or default timestamp title"""
    if title is None:
        title = f"New Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/conversations/",
            json={"title": title}
        )
        response.raise_for_status()
        data = response.json()
        
        # Reset all relevant session state
        st.session_state["conversation_id"] = data.get("id")
        st.session_state["messages"] = []
        st.session_state["previous_query"] = ""
        st.session_state["previous_user_input"] = ""
        st.session_state["query_code"] = ""
        st.session_state["query_result"] = None
        st.session_state["query_history"] = []
        st.session_state["query_history_position"] = -1
        
        return data.get("id")
    except requests.RequestException as e:
        st.error(f"Failed to create a new conversation: {e}")
        return None

def load_conversation(conversation_id):
    """Load a conversation by ID"""
    try:
        response = requests.get(f"{API_BASE_URL}/conversations/{conversation_id}/messages")
        response.raise_for_status()
        conversation_data = response.json()
        
        # Reset messages and state
        st.session_state["messages"] = []
        st.session_state["query_code"] = ""
        st.session_state["previous_query"] = ""
        st.session_state["previous_user_input"] = ""
        st.session_state["query_history"] = []
        st.session_state["query_history_position"] = -1
        
        # Convert and load messages
        last_user_question = None
        last_query = None
        
        for msg in conversation_data.get("messages", []):
            if msg.get("user_question"):
                st.session_state["messages"].append({
                    "user": "user",
                    "message": msg["user_question"]
                })
                last_user_question = msg["user_question"]
                
            
            if msg.get("assistant_answer"):
                st.session_state["messages"].append({
                    "user": "assistant",
                    "message": msg["assistant_answer"]
                })
            
            if msg.get("sparql_query"):
                last_query = msg["sparql_query"]
                st.session_state["query_code"] = last_query
                # Add query to history
                st.session_state["query_history"].append(last_query)
                st.session_state["query_history_position"] = len(st.session_state["query_history"]) - 1
        
        # Set the last question and query as previous
        if last_user_question and last_query:
            st.session_state["previous_user_input"] = last_user_question
            st.session_state["previous_query"] = last_query
        
        st.session_state["conversation_id"] = conversation_id
        return True
    except requests.RequestException as e:
        st.error(f"Failed to load conversation: {e}")
        return False

def save_message(user_question, assistant_answer, sparql_query):
    """Save a message to the current conversation"""
    payload = {
        "user_question": user_question,
        "assistant_answer": assistant_answer,
        "sparql_query": sparql_query,
    }
    try:
        response = requests.post(
            f"{API_BASE_URL}/conversations/{st.session_state['conversation_id']}/messages/",
            json=payload
        )
        response.raise_for_status()
    except requests.RequestException as e:
        st.error(f"Failed to save message: {e}")


def normalize_user_input(user_input: str) -> str:
    """Normalize user input"""
    payload = {
        "user_input": user_input
    }
    try:
        response = requests.post(
            f"{API_BASE_URL}/huflair2/",
            json=payload
        )
        response.raise_for_status()
    except requests.RequestException as e:
        st.error(f"Failed to save message: {e}")
    return response.json()


def should_modify_existing_query(previous_input, previous_query, current_input):
    """Determine if existing query can be modified"""
        
    prompt = f"""
You are an interactive SPARQL query generation assistant.
Previous user question: "{previous_input}"
Previous SPARQL query: "{previous_query}"
Current user question: "{current_input}"
Can this question be answered if I modify it using the same graph structure within the query? Please answer Yes or No.
"""
    client = OpenAI()
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a capable assistant."},
            {"role": "user", "content": prompt},
        ],
    )
    answer = completion.choices[0].message.content.strip()
    
    return "Yes" in answer

def modify_existing_query(previous_query, user_input):
    """Modify existing SPARQL query"""
    prompt = f"""
Previous SPARQL query:
{previous_query}

User's new question: "{user_input}"

Please modify the previous query to answer the new question.
Output only the modified SPARQL query.
"""
    client = OpenAI()
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a SPARQL expert."},
            {"role": "user", "content": prompt},
        ],
    )
    try:
        sparql_query = completion.choices[0].message.content.strip().split("```sparql")[1].split("```")[0]
    except Exception:
        sparql_query = completion.choices[0].message.content.strip()
    return sparql_query

def generate_answer(question, query_code, query_results):
    """Generate answer using GPT-4"""
    prompt = f"""
User question: "{question}"
SPARQL query: "{query_code}"
Query results: {query_results.head(5)}
Using the query results, please answer the user's question.
"""
    client = OpenAI()
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a capable assistant."},
            {"role": "user", "content": prompt},
        ],
    )
    return completion.choices[0].message.content.strip()

# Sidebar for conversation history
with st.sidebar:
    st.title("Conversation History")
    
    # New conversation button
    if st.button("New Conversation"):
        st.session_state["conversation_id"] = None
        st.session_state["messages"] = []
        st.session_state["previous_query"] = ""
        st.session_state["previous_user_input"] = ""
        st.session_state["query_code"] = ""
        st.session_state["query_result"] = None
        st.session_state["query_history"] = []
        st.session_state["query_history_position"] = -1
        st.rerun()
        
    # Load conversation history
    try:
        response = requests.get(f"{API_BASE_URL}/conversations")
        response.raise_for_status()
        conversations = response.json()
        
        if conversations:
            st.write("Click on a conversation to load:")
            
            # Display conversations as a list
            for conv in conversations:
                # Create a unique key for each button
                button_key = f"conv_{conv['conversation_id']}"
                
                # Add visual indicator for current conversation
                is_current = str(conv['conversation_id']) == str(st.session_state.get("conversation_id"))
                button_label = f"{'→ ' if is_current else ''}{conv['title']}"
                
                # Create a button for each conversation
                if st.button(button_label, key=button_key):
                    if load_conversation(conv['conversation_id']):
                        st.success(f"Loaded: {conv['title']}")
                        st.rerun()
        else:
            st.info("No conversations found")
            
    except requests.RequestException as e:
        st.error(f"Failed to fetch conversations: {e}")

# Main layout
col1, col2 = st.columns([1, 1])

# Database selection
with col1:
    database_list = ["uniprot", "rhea", "bgee"]
    selected_db = st.selectbox(
        "Select Database:",
        database_list,
        index=database_list.index(st.session_state["selected_db"])
    )

# Reset session state if database changed
if selected_db != st.session_state["selected_db"]:
    st.session_state["selected_db"] = selected_db
    st.session_state["query_code"] = ""
    st.session_state["query_result"] = None
    st.session_state["previous_query"] = ""
    st.session_state["previous_user_input"] = ""
    st.session_state["query_history"] = []
    st.session_state["query_history_position"] = -1

# Display conversation
with col1:
    st.subheader("Conversation")
    for message in st.session_state["messages"]:
        with st.chat_message(message["user"]):
            st.write(message["message"])

# User input handling
user_input = st.chat_input("Please enter your question")
if user_input:
    # Normalize user input
    # user_input_normalized = normalize_user_input(user_input)

    # Create new conversation if none exists
    if not st.session_state["conversation_id"]:
        conversation_id = create_new_conversation(user_input)
        if not conversation_id:
            st.error("Failed to create new conversation")
            st.stop()
    
    # Add user message
    st.session_state["messages"].append({"user": "user", "message": user_input})
    with col1:
        with st.chat_message("user"):
            st.write(user_input)
    
    # Assistant response
    with col1:
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.write("Generating...")

    try:
        # Debug information
        st.session_state["debug_info"] = {
            "previous_query": st.session_state["previous_query"],
            "previous_input": st.session_state["previous_user_input"],
            "current_input": user_input
        }
        
        # Generate or modify SPARQL query
        if st.session_state["previous_query"] and should_modify_existing_query(
            st.session_state["previous_user_input"],
            st.session_state["previous_query"],
            user_input
        ):
            sparql_query = modify_existing_query(st.session_state["previous_query"], user_input)
        else:
            user_prompt = make_one_prompt(selected_db, user_input)
            sparql_query = generate_one_sparql(selected_db, user_prompt, False)
        
        st.session_state["query_code"] = sparql_query
        
        # Execute query
        result = execute_one_query(sparql_query, os.environ[f"ENDPOINT_{selected_db.upper()}"])
        df_result = pd.DataFrame(result)
        df_result = df_result if df_result.empty else df_result.applymap(lambda x: x["value"] if isinstance(x, dict) and "value" in x else x)
        st.session_state["query_result"] = df_result
        
        # Add query to history
        if not st.session_state["query_history"] or sparql_query != st.session_state["query_history"][-1]:
            # Remove any forward history if we're not at the end
            st.session_state["query_history"] = st.session_state["query_history"][:st.session_state["query_history_position"] + 1]
            st.session_state["query_history"].append(sparql_query)
            st.session_state["query_history_position"] = len(st.session_state["query_history"]) - 1
        
        # Generate and display answer
        answer = generate_answer(user_input, st.session_state["query_code"], df_result)
        message_placeholder.markdown(answer)
        
        # Update session state
        st.session_state["messages"].append({"user": "assistant", "message": answer})
        st.session_state["previous_query"] = sparql_query
        st.session_state["previous_user_input"] = user_input
        
        # Save message
        save_message(user_input, answer, sparql_query)

    except Exception as e:
        error_message = f"An error occurred: {e}"
        message_placeholder.error(error_message)
        st.session_state["messages"].append({"user": "assistant", "message": error_message})

# Right column: Query and results
with col2:
    st.subheader("SPARQL Query and Results")
    
    # Add navigation buttons in a row
    nav_col1, nav_col2, nav_col3 = st.columns([1, 8, 1])
    
    with nav_col1:
        back_button = st.button("←", disabled=st.session_state["query_history_position"] <= 0)
    with nav_col3:
        forward_button = st.button("→", disabled=st.session_state["query_history_position"] >= len(st.session_state["query_history"]) - 1)
    
    # Handle navigation button clicks
    if back_button and st.session_state["query_history_position"] > 0:
        st.session_state["query_history_position"] -= 1
        st.session_state["query_code"] = st.session_state["query_history"][st.session_state["query_history_position"]]
        st.rerun()
        
    if forward_button and st.session_state["query_history_position"] < len(st.session_state["query_history"]) - 1:
        st.session_state["query_history_position"] += 1
        st.session_state["query_code"] = st.session_state["query_history"][st.session_state["query_history_position"]]
        st.rerun()

    edited_query = st.text_area(
        "You can edit the query here:",
        value=st.session_state["query_code"],
        height=300
    )

    if st.button("Execute Query"):
        try:
            # Execute modified query
            result = execute_one_query(
                edited_query,
                os.environ[f"ENDPOINT_{selected_db.upper()}"]
            )
            df_result = pd.DataFrame(result)
            df_result = df_result if df_result.empty else df_result.applymap(lambda x: x["value"] if isinstance(x, dict) and "value" in x else x)
            st.session_state["query_result"] = df_result
            st.session_state["query_code"] = edited_query
            
            # Add new query to history
            if not st.session_state["query_history"] or edited_query != st.session_state["query_history"][-1]:
                # Remove any forward history if we're not at the end
                st.session_state["query_history"] = st.session_state["query_history"][:st.session_state["query_history_position"] + 1]
                st.session_state["query_history"].append(edited_query)
                st.session_state["query_history_position"] = len(st.session_state["query_history"]) - 1
            
            st.success("Query executed successfully")

            # Generate new answer if there are messages
            if st.session_state["messages"]:
                answer = generate_answer(None, st.session_state['query_code'], df_result)
                st.session_state["messages"].append({"user": "assistant", "message": answer})
                
                with col1:
                    with st.chat_message("assistant"):
                        st.write(answer)
                
                # Save message
                save_message(None, answer, edited_query)

        except Exception as e:
            st.error(f"An error occurred: {e}")

    # Display query results
    if st.session_state["query_result"] is not None:
        st.dataframe(st.session_state["query_result"])
    else:
        st.write("No query results.")