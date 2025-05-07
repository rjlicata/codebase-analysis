import streamlit as st

from codebase_analysis import Orchestrator
from codebase_analysis.file_utils import download_repo


def main():
    """main function for the streamlit app"""
    # define title and initial instructions
    st.title("GitHub Repository Chatbot")
    subheader = st.empty()
    subheader.subheader("The chat session begins once select a GitHub URL.")
    # define sidebar options
    st.sidebar.title("Enter a GitHub URL")
    st.session_state.repo_name = st.sidebar.text_input("GitHub URL:")

    if "check" not in st.session_state:
        st.session_state.check = False

    if st.sidebar.button("Begin Chat"):
        st.session_state.check = True

    # once file is uploaded, doownload the repo and process it
    if st.session_state.check:
        # update instructions
        subheader.subheader("Processing the repository. This may take a few minutes.")
        # load data and create agent
        if "repo_path" not in st.session_state:
            # download the repo
            st.session_state.repo_path = download_repo(st.session_state.repo_name)
        if "orch" not in st.session_state and st.session_state.check:
            subheader.subheader("Processing the repository. This may take a few minutes.")
            st.session_state.orch = Orchestrator(
                config_path="/workspace/data/base_config.yml",
                repo_path=st.session_state.repo_path,
                init=True,
            )
            description, codebase = st.session_state.orch.get_stats()
            st.sidebar.text(description)
            st.session_state.orch.add_data(codebase)
            st.session_state.repo_loaded = True

        if st.session_state.get("repo_loaded", False):
            subheader.subheader("The repository has been processed. Ask me anything!")

            if "messages" not in st.session_state:
                st.session_state.messages = []

            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            user_input = st.chat_input("Input your query here")
            if user_input:
                st.session_state.messages.append({"role": "user", "content": user_input})
                with st.chat_message("user"):
                    st.markdown(user_input)
                bot_response = st.session_state.orch.query(user_input)
                st.session_state.messages.append({"role": "assistant", "content": bot_response})
                with st.chat_message("assistant"):
                    st.markdown(bot_response)


# run the Streamlit app
if __name__ == "__main__":
    main()
