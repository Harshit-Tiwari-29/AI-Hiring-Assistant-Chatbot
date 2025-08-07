import streamlit as st
from datetime import datetime
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import re
import csv

# Page Configuration
st.set_page_config(
    page_title="AI Hiring Assistant",
    layout="wide",
    initial_sidebar_state="expanded",
)
load_dotenv()
os.makedirs("chat_logs", exist_ok=True)


# Caching & Backend
@st.cache_resource
def get_llm_client(api_key):
    """Initializes and returns a cached ChatGroq client."""
    return ChatGroq(groq_api_key=api_key, model_name="Gemma2-9b-It")

def load_user_history(email):
    """Loads chat history for a user from a text file."""
    history_file = f"chat_logs/{email}.txt"
    if os.path.exists(history_file):
        with open(history_file, 'r', encoding='utf-8') as f:
            # Return last 500 characters as a summary
            return f.read()[-500:]
    return "No previous history found."

def save_user_history(email, messages_to_save):
    """Saves new messages to a user's chat history file."""
    if not email: return
    history_file = f"chat_logs/{email}.txt"
    with open(history_file, 'a', encoding='utf-8') as f:
        for role, text in messages_to_save:
            f.write(f"[{role.upper()}]: {text}\n")


# Language & Prompts

TRANSLATIONS = {
    'en': {
        'page_title': "AI Hiring Assistant", 'header': "AI Hiring Assistant", 'controls': "⚙️ Controls", 'api_key_prompt': "### Enter API Key",
        'api_key_input': "Enter your Groq API key", 'submit_key_button': "Submit Key", 'api_key_success': "API key accepted!", 'api_key_warning': "Please enter your API key.",
        'api_key_set': "API key is set.", 'candidate_info_header': "📝 Candidate Information", 'no_info_collected': "No information collected yet.",
        'user_response_placeholder': "Your response...", 'thinking': "Thinking...", 'error_message': "An error occurred: {e}. Please check your API Key or try again.",
        'finalization_error': "An error occurred during finalization: {e}", 'language_selector_label': "Select Language",
        'initial_greeting': "Hi there! 👋 I'm Scout, your friendly AI assistant. To get started, could you please tell me your full name?",
        'final_message_with_questions': "Thank you! Your profile is complete. Here are a few technical questions based on your stack for you to think about:\n\n{questions}\n\nOur recruitment team will review your information and get in touch soon. Have a great day! ✅",
    },
    'es': {
        'page_title': "Asistente de Contratación IA", 'header': "Asistente de Contratación IA", 'controls': "⚙️ Controles", 'api_key_prompt': "### Ingrese la Clave de API",
        'api_key_input': "Ingrese su clave de API de Groq", 'submit_key_button': "Enviar Clave", 'api_key_success': "¡Clave de API aceptada!", 'api_key_warning': "Por favor ingrese su clave de API.",
        'api_key_set': "La clave de API está configurada.", 'candidate_info_header': "📝 Información del Candidato", 'no_info_collected': "Aún no se ha recopilado información.",
        'user_response_placeholder': "Tu respuesta...", 'thinking': "Pensando...", 'error_message': "Ocurrió un error: {e}. Por favor, verifique su clave de API.",
        'finalization_error': "Ocurrió un error durante la finalización: {e}", 'language_selector_label': "Seleccionar Idioma",
        'initial_greeting': "¡Hola! 👋 Soy Scout, tu amigable asistente de IA. Para empezar, ¿podrías decirme tu nombre completo?",
        'final_message_with_questions': "¡Gracias! Tu perfil está completo. Aquí tienes algunas preguntas técnicas basadas en tu stack para que pienses:\n\n{questions}\n\nNuestro equipo de reclutamiento revisará tu información y se pondrá en contacto pronto. ¡Que tengas un buen día! ✅",
    },
    'fr': {
        'page_title': "Assistant de Recrutement IA", 'header': "Assistant de Recrutement IA", 'controls': "⚙️ Contrôles", 'api_key_prompt': "### Entrez la Clé API",
        'api_key_input': "Entrez votre clé API Groq", 'submit_key_button': "Soumettre la Clé", 'api_key_success': "Clé API acceptée !", 'api_key_warning': "Veuillez entrer votre clé API.",
        'api_key_set': "La clé API est configurée.", 'candidate_info_header': "📝 Informations sur le Candidat", 'no_info_collected': "Aucune information collectée.",
        'user_response_placeholder': "Votre réponse...", 'thinking': "Réflexion...", 'error_message': "Une erreur est survenue: {e}. Veuillez vérifier votre clé API.",
        'finalization_error': "Une erreur est survenue lors de la finalisation: {e}", 'language_selector_label': "Sélectionner la Langue",
        'initial_greeting': "Bonjour ! 👋 Je suis Scout, votre assistant IA. Pour commencer, pourriez-vous me donner votre nom complet ?",
        'final_message_with_questions': "Merci ! Votre profil est complet. Voici quelques questions techniques basées sur votre stack pour votre réflexion :\n\n{questions}\n\nNotre équipe de recrutement examinera vos informations et vous contactera bientôt. Bonne journée ! ✅",
    }
}

SYSTEM_PROMPT = """
You are Scout, an intelligent, friendly, and multilingual AI Hiring Assistant.

**Conversation History Summary:**
{history}

**Your Core Rules:**
1.  **Language**: You MUST conduct the entire conversation in **{language}**.
2.  **Personalization**: Once you collect the user's email, check the Conversation History. If it's not empty, you can acknowledge them as a returning user in your next message.
3.  **Strict Sequence**: Ask for information in this exact order: Full Name, Email Address, Phone Number, Years of Experience, Desired Position(s), Current Location, Tech Stack.
4.  **One Question at a Time**: Ask only ONE question per turn.
5.  **Input Validation**: Validate every user input. If invalid, politely ask for a correction in {language} and DO NOT proceed.
6.  **Data Tagging**: After receiving a VALID response, embed a tag: `[COLLECTED: key=value]`. This is critical.
7.  **Tone**: Maintain a friendly, professional, and encouraging tone in {language}.
"""

TECH_QUESTION_PROMPT = """
Based on the candidate's specified tech stack, generate a set of 3-5 relevant technical questions to assess their proficiency.
**Tech Stack:** {tech_stack}
The questions should be clear, concise, and tailored to the technologies listed. All questions MUST be in this language: **{language}**. Return *only* the questions in a numbered list.
"""

# --- CSS & UI Functions ---
st.markdown("""<style> @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
:root { --primary-color: #0B3379; --secondary-color: #F0F4FA; --accent-color: #2FDEB4; --text-light: #FFFFFF; --text-dark: #313131; --user-bubble-bg: #D4EDFF; --ai-bubble-bg: #FFFFFF; }
html, body, [class*="st-"] { font-family: 'Space Grotesk', sans-serif; }
.stApp { background-color: var(--secondary-color); } .header { background-color: var(--primary-color); color: var(--text-light); padding: 1rem; border-radius: 12px; margin-bottom: 1rem; }
.header h1 { margin: 0; font-size: 2.2rem; font-weight: 600; text-align: center; } .chat-row { display: flex; align-items: flex-start; gap: 10px; margin: 10px 0; }
.chat-row.user { justify-content: flex-end; } .chat-row.ai { justify-content: flex-start; }
.chat-avatar { width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 20px; flex-shrink: 0; }
.user-avatar { background-color: var(--primary-color); color: var(--text-light); } .ai-avatar { background-color: var(--accent-color); color: var(--primary-color); }
.chat-bubble { padding: 12px 18px; border-radius: 18px; max-width: 70%; font-size: 16px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); word-wrap: break-word; }
.user-bubble { background-color: var(--user-bubble-bg); color: var(--text-dark); border-bottom-right-radius: 2px; }
.ai-bubble { background-color: var(--ai-bubble-bg); color: var(--text-dark); border-bottom-left-radius: 2px; }
.chat-timestamp { font-size: 10px; color: #888; text-align: right; margin-top: 5px; } </style>""", unsafe_allow_html=True)

def show_message(message, role, timestamp):
    avatar_html = f'<div class="chat-avatar {role}-avatar">{"👤" if role == "user" else "🤖"}</div>'
    bubble_html = f"""<div class="chat-row {role}">{avatar_html if role == "ai" else ""}<div class="chat-bubble {role}-bubble"><div>{message}</div>
        <div class="chat-timestamp">{timestamp.strftime("%H:%M")}</div></div>{avatar_html if role == "user" else ""}</div>"""
    st.markdown(bubble_html, unsafe_allow_html=True)

# Initialize Session State
if 'groq_api_key' not in st.session_state: st.session_state.groq_api_key = os.getenv("GROQ_API_KEY")
if 'language' not in st.session_state: st.session_state.language = 'en'
if 'conversation_stage' not in st.session_state: st.session_state.conversation_stage = 'greeting'
if 'messages' not in st.session_state: st.session_state.messages = []
if 'candidate_info' not in st.session_state: st.session_state.candidate_info = {}
if 'user_email' not in st.session_state: st.session_state.user_email = None
if 'history_summary' not in st.session_state: st.session_state.history_summary = "No previous history found."

# Main Application
txt = TRANSLATIONS[st.session_state.language]
st.markdown(f'<div class="header"><h1>{txt["header"]}</h1></div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.selectbox(label=txt['language_selector_label'], options=['en', 'es', 'fr'], format_func=lambda x: "English" if x == 'en' else "Español" if x == 'es' else "Français", key='language')
    st.markdown("---")
    st.markdown(f"## {txt['controls']}")
    if not st.session_state.groq_api_key:
        with st.container(border=True):
            st.markdown(f"{txt['api_key_prompt']}")
            key = st.text_input(txt['api_key_input'], type="password", label_visibility="collapsed")
            if st.button(txt['submit_key_button']):
                if key: st.session_state.groq_api_key = key; st.success(txt['api_key_success']); st.rerun()
                else: st.warning(txt['api_key_warning'])
    else: st.success(txt['api_key_set'])
    st.markdown("---")
    st.markdown(f"## {txt['candidate_info_header']}")
    if st.session_state.candidate_info:
        for key, value in st.session_state.candidate_info.items():
            st.info(f"**{key.replace('_', ' ').title()}:** {value}")
    else: st.info(txt['no_info_collected'])

# Chat Stages

# Initial Greeting
if st.session_state.conversation_stage == 'greeting':
    if not st.session_state.messages: 
        if not st.session_state.groq_api_key:
            st.warning("Please set your Groq API key in the sidebar to begin.")
        else:
            st.session_state.messages.append(("ai", txt['initial_greeting'], datetime.now()))
    st.session_state.conversation_stage = 'gathering'

# Display chat history for all subsequent stages
chat_container = st.container()
with chat_container:
    for role, text, ts in st.session_state.messages:
        show_message(text, role, ts)


# Main gathering and finalization logic
if st.session_state.conversation_stage == 'gathering':
    user_input = st.chat_input(txt['user_response_placeholder'])
    if user_input:
        info_collected_before = set(st.session_state.candidate_info.keys())
        st.session_state.messages.append(("user", user_input, datetime.now()))

        with st.spinner(txt['thinking']):
            try:
                llm = get_llm_client(st.session_state.groq_api_key)
                lang_map = {'en': "English", 'es': "Spanish", 'fr': "French"}
                formatted_system_prompt = SYSTEM_PROMPT.format(history=st.session_state.history_summary, language=lang_map[st.session_state.language])

                prompt_messages = [SystemMessage(content=formatted_system_prompt)]
                for role, text, ts in st.session_state.messages:
                    prompt_messages.append(HumanMessage(content=text) if role == 'user' else AIMessage(content=text))

                response = llm.invoke(prompt_messages)
                ai_response_text = response.content

                matches = re.findall(r'\[COLLECTED: (.*?)=(.*?)\]', ai_response_text)
                for key, value in matches:
                    key_cleaned = key.strip().lower().replace(' ', '_')
                    st.session_state.candidate_info[key_cleaned] = value.strip()

                display_text = re.sub(r'\[COLLECTED:.*?\]', '', ai_response_text).strip()
                st.session_state.messages.append(("ai", display_text, datetime.now()))

                info_collected_after = set(st.session_state.candidate_info.keys())
                newly_collected_info = info_collected_after - info_collected_before

                # Personalization
                if 'email_address' in newly_collected_info:
                    email = st.session_state.candidate_info['email_address']
                    st.session_state.user_email = email.lower().strip()
                    st.session_state.history_summary = load_user_history(st.session_state.user_email)

                # Save history after user is identified
                save_user_history(st.session_state.user_email, [("user", user_input), ("ai", display_text)])

                # Finalization Trigger
                if 'tech_stack' in newly_collected_info:
                    st.session_state.conversation_stage = 'finalizing'
                
                st.rerun()

            except Exception as e:
                st.error(txt['error_message'].format(e=e))

elif st.session_state.conversation_stage == 'finalizing':
    with st.status("Finalizing your profile...", expanded=True) as status:
        try:
            # 1. Save Candidate Data to CSV
            status.update(label="Updating candidate records...", state="running")
            st.session_state.candidate_info['submission_time'] = datetime.now().isoformat()
            fieldnames = list(st.session_state.candidate_info.keys())
            file_exists = os.path.isfile("candidate_data.csv")
            with open("candidate_data.csv", mode='a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                if not file_exists: writer.writeheader()
                writer.writerow(st.session_state.candidate_info)

            # 2. Generate Technical Questions
            status.update(label="Generating personalized technical questions...", state="running")
            llm = get_llm_client(st.session_state.groq_api_key)
            lang_map = {'en': "English", 'es': "Spanish", 'fr': "French"}
            tech_stack = st.session_state.candidate_info.get('tech_stack', 'Not provided')
            formatted_tech_prompt = TECH_QUESTION_PROMPT.format(tech_stack=tech_stack, language=lang_map[st.session_state.language])
            question_response = llm.invoke(formatted_tech_prompt)
            questions = question_response.content

            # 3. Finalize
            status.update(label="Profile complete!", state="complete", expanded=False)
            final_message = txt['final_message_with_questions'].format(questions=questions)
            st.session_state.messages.append(("ai", final_message, datetime.now()))
            save_user_history(st.session_state.user_email, [("ai", final_message)])
            st.session_state.conversation_stage = 'done'
            st.rerun()

        except Exception as e:
            status.update(label="Error during finalization.", state="error")
            st.error(txt['finalization_error'].format(e=e))

elif st.session_state.conversation_stage == 'done':
    st.success("The screening process is complete. You may close this window.")

