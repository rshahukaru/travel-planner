import sys
import streamlit as st
from openai import OpenAI

# SQLite workaround
__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import chromadb
from chromadb.config import Settings

# Initialize OpenAI client
if 'openai_client' not in st.session_state:
    st.session_state.openai_client = OpenAI(api_key=st.secrets["openai_api_key"])

# Initialize chat history and memory
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'conversation_memory' not in st.session_state:
    st.session_state.conversation_memory = []

TRAVEL_DOCS = {
    "destinations.txt": "Popular destinations guide, visa requirements, best times to visit",
    "local_customs.txt": "Cultural norms, etiquette, dress codes, tipping practices",
    "safety.txt": "Travel safety tips, emergency contacts, common scams to avoid"
}

def get_chat_response(query, context):
    conversation_history = "\n".join([
        f"Human: {exchange['question']}\nAssistant: {exchange['answer']}"
        for exchange in st.session_state.conversation_memory[-3:]
    ])
    
    system_message = f"""You are a travel advisor helping users plan trips and solve travel problems. 
    Previous conversation:\n{conversation_history}\n
    Context:\n{context}
    
    After each response, ask if they need more specific information."""
    
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": query}
    ]
    
    response = st.session_state.openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.75
    )
    return response.choices[0].message.content

st.title("🌍 Travel Buddy")

# Display chat history
for message in st.session_state.chat_history[-5:]:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
query = st.chat_input("Ask about your travel plans...")

if query:
    # Display user message
    with st.chat_message("user"):
        st.write(query)
    
    # Get chatbot response
    response = get_chat_response(query, str(TRAVEL_DOCS))
    
    # Display assistant message
    with st.chat_message("assistant"):
        st.write(response)
    
    # Update history and memory
    st.session_state.chat_history.extend([
        {"role": "user", "content": query},
        {"role": "assistant", "content": response}
    ])
    
    st.session_state.conversation_memory.append({
        "question": query,
        "answer": response
    })
    
    st.rerun()