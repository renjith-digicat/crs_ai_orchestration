"""Minimal Streamlit UI for chatbot app to interact with the agents."""

import streamlit as st
import asyncio
from agents_runner import process_query

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Settings [Not functional now]")
    model_name = st.selectbox(
        "Model",
        options=[
            "ollama:qwen3:4b",
            "openai:gpt-4o",
            "groq:moonshotai/kimi-k2-instruct",
        ],
        index=0,
    )
    temperature = st.slider("Temperature", 0.0, 1.5, 0.2, 0.05)
    st.caption("Tip: keep this close to zero for reducing hallucination.")
    # show_thinking = st.checkbox("Show thinking log", value=False)

    st.divider()
    if st.button("🧹 Clear chat history"):
        st.session_state.pop("messages", None)
        st.rerun()

    st.divider()
    with st.expander("ℹ️ About this app", expanded=False):
        st.markdown(
            """
            This chat UI calls an agentic pipeline for CRS orchestration.
            - Left sidebar holds runtime settings
            - Use **Clear chat history** to reset the session
            """
        )

st.title("AI Assistant for CRS Orchestration")


# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []  # list of {"role": ..., "content": ...}

# Display existing conversation from history on each run
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input widget (pinned to bottom of page)
if user_query := st.chat_input("How can I help you?..."):
    # 1. Display the user message immediately
    with st.chat_message("user"):
        st.markdown(user_query)
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": user_query})

    # 2. Process the query through the agent pipeline - with history included
    # (Calling the async function via asyncio.run, since Streamlit expects sync code)
    thinking_log, results = asyncio.run(
        process_query(user_query, history=st.session_state.messages)
    )

    # 3. Format the assistant's response with separate Thinking and Result sections
    # `thinking_log` is a large string of all prints
    # For clarity, split the log into reasoning vs final outputs:
    log_text = str(thinking_log)
    result_section = ""
    if results:
        if len(results) == 0:
            result_lines = "No result found."
        else:
            result_lines = results[0]
        result_section = f"**Response:**\n\n{result_lines}"

    # Everything before "Search Summary:" treat it as thinking process
    # TODO: This logic needs to be improved
    if "-THINKING ENDS-" in log_text:
        reasoning_part = log_text.split("-THINKING ENDS-")[0]
    else:
        reasoning_part = log_text
    thinking_section = (
        "*Thinking Process...*\n```text\n" + reasoning_part.strip() + "\n```"
    )

    full_response_md = thinking_section + "\n\n" + result_section

    # 4. Display the assistant message (reasoning + result)
    with st.chat_message("assistant"):
        st.markdown(full_response_md)
    # Add assistant response to history - excluding the thinking process
    st.session_state.messages.append({"role": "assistant", "content": result_section})
