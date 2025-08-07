
#  The AI Hiring Assistant

**AI Hirirng Assistant** is a sophisticated, multilingual chatbot designed to streamline the initial candidate screening process. Built with **Streamlit** and powered by the **Groq API** for high-speed language model inference, this AI assistant engages potential hires in natural conversations to collect essential information. It concludes by generating relevant technical questions based on their stated technology stack.

The entire application is contained within a single Python script: `app.py`.

---

## 🌟 Key Features

- **Multilingual Conversations**: Engages candidates in English, Spanish, or French, with all user-facing text managed through a `TRANSLATIONS` dictionary.
- **Structured Information Gathering**: Collects key details in strict sequence:
  - Full Name
  - Email
  - Phone Number
  - Years of Experience
  - Desired Positions
  - Current Location
  - Tech Stack
- **Dynamic Technical Questions**: Generates 3-5 custom technical questions tailored to the candidate’s skills using a dedicated prompt.
- **Persistent Chat History**: Remembers returning candidates using a summary stored in `chat_logs/{email}.txt`.
- **Data Persistence**: Stores candidate details with timestamp in `candidate_data.csv` and logs complete conversation history.
- **User-Friendly Interface**: Clean UI with chat bubbles and a custom theme using Streamlit and CSS.

---

## 🛠️ Installation & Setup

### 1. Prerequisites

- Python 3.8+
- Git

### 2. Clone the Repository

```bash
git clone <your-repository-url>
cd <repository-directory>
```

### 3. Set Up a Virtual Environment

```bash
# For macOS/Linux
python3 -m venv venv
source venv/bin/activate

# For Windows
python -m venv venv
.env\Scriptsctivate
```

### 4. Install Dependencies

Create a `requirements.txt` file with the following content:

```plaintext
streamlit
python-dotenv
langchain-groq
langchain-core
```

Then install the dependencies:

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

1. Sign up at [Groq](https://groq.com) to get your API key.
2. Create a `.env` file in your project root and add:

```dotenv
GROQ_API_KEY="your_groq_api_key"
```

---

## 🚀 Usage Guide

To launch the app:

```bash
streamlit run app.py
```

- A browser tab will open with the chatbot interface.
- If the `GROQ_API_KEY` is missing, you’ll be prompted in the sidebar to input it manually.
- Select your preferred language (English, Spanish, French).
- Proceed with the conversation in the chat input box.
- As responses are gathered, they’ll appear in the sidebar.
- When complete, you'll see a “process is complete” message.

---

## ⚙️ Technical Details

### Core Libraries

- **Streamlit**: UI rendering, session state, and interaction handling.
- **LangChain**: Prompt management and LLM message flow (`ChatPromptTemplate`, `HumanMessage`, `AIMessage`).
- **ChatGroq**: LangChain integration with Groq API for fast inference.
- **python-dotenv**: Loads the Groq API key from `.env`.

### Language Model

- **Model**: `Gemma2-9b-It` via Groq’s LPU™ Inference Engine.
- **Purpose**: Fast and coherent conversations tailored to screening needs.

### Application Architecture

- **State Management**: Controlled via `st.session_state.conversation_stage` (e.g., greeting → gathering → finalizing → done).
- **Data Extraction**: Uses `[COLLECTED: key=value]` tags in model output, parsed via regex to ensure accurate data capture.
- **Chat Logs**: Stored per user by email in `chat_logs/{email}.txt`.
- **Candidate Info**: Stored in `candidate_data.csv` with a timestamp.
- **Custom UI**: Styled via injected CSS using `st.markdown(..., unsafe_allow_html=True)`.

---

## 💡 Prompt Design

### SYSTEM_PROMPT - The Core Rule Engine

Defines the chatbot’s persona and rules:

- **Persona**: "You are Scout, an intelligent, friendly, and multilingual AI Hiring Assistant."
- **Rules**:
  1. Language enforcement (`{language}`)
  2. Strict sequencing (only one question per turn)
  3. Input validation with polite correction requests
  4. Data tagging after valid input: `[COLLECTED: key=value]`

### TECH_QUESTION_PROMPT - Dynamic Question Generation

- Takes `{tech_stack}` and `{language}` as input.
- Instructs the model to return **only** a numbered list of 3–5 relevant technical questions.

---

## 🧠 Challenges & Solutions

### Challenge 1: Crafting Effective Prompts

**Problem**: LLMs often deviate from instructions.

**Solution**: Explicitly engineered prompts using numbered rules and the `[COLLECTED: ...]` tagging format for consistent structure.

---

### Challenge 2: Designing an Effective User Interface (UI)

**Problem**: Streamlit has limited out-of-the-box styling.

**Solution**: Injected custom CSS for fonts, colors, bubble style, and layout for a polished look.

---

### Challenge 3: Reliably Extracting Structured Data

**Problem**: Extracting fields like email or phone from natural language is error-prone.

**Solution**: Forced tagging (`[COLLECTED: key=value]`) allows reliable regex-based extraction.

---

### Challenge 4: Managing Conversational State

**Problem**: Streamlit reruns scripts on every interaction.

**Solution**: `st.session_state` tracks conversation stage, candidate info, and message history, ensuring smooth multi-turn dialogue flow.

---

## 📂 File Structure Overview

```
project-root/
│
├── final.py                  # Main application script
├── candidate_data.csv        # Stores all collected candidate details
├── chat_logs/
│   └── {email}.txt           # Chat summaries per user
├── .env                      # API key configuration
└── requirements.txt          # Dependency list
```

---

## 📄 License

MIT License – feel free to use and modify this project for personal or professional use.

---

## 🙌 Acknowledgments

- [Groq](https://groq.com) for blazing-fast model inference.
- [LangChain](https://www.langchain.com) for managing LLM workflows.
- [Streamlit](https://streamlit.io) for the intuitive interface engine.
