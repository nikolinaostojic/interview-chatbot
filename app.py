import streamlit as st
from openai import OpenAI
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title = "Streamlit Chat", page_icon = "💭")

st.header("Interview Chatbot")

if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0
if "feedback_shown" not in st.session_state:
    st.session_state.feedback_shown = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_complete" not in st.session_state:
    st.session_state.chat_complete = False

def complete_setup(): # pravimo ovu funkciju koja ce setup postaviti kao complete kad zavrsimo unos podataka
    st.session_state.setup_complete = True

def show_feedback(): 
    st.session_state.feedback_shown = True

if not st.session_state.setup_complete:
    st.subheader("Personal information", divider = 'rainbow')

    if "name" not in st.session_state:
        st.session_state.name = ""
    if "experience" not in st.session_state:
            st.session_state.experience = ""
    if "skills" not in st.session_state:
            st.session_state.skills = ""

    st.session_state.name = st.text_input(label = 'Name', max_chars = 40, value = st.session_state.name, placeholder = "Enter your name")
    # for experience and skills, we will use text area instead of text input since those parameters require more space
    st.session_state.experience = st.text_area(label = 'Experience', value = st.session_state.experience, height = None, max_chars = 200, placeholder = "Describe your experience")
    st.session_state.skills = st.text_area(label = 'Skills', value = st.session_state.skills, height = None, max_chars = 200, placeholder = "List your skills")

    st.subheader("Company and Position", divider = 'rainbow')

    if "level" not in st.session_state:
            st.session_state.level = "Junior" # start point for each dropdown menu 
    if "position" not in st.session_state:
            st.session_state.position = "Data Scientist"
    if "company" not in st.session_state:
            st.session_state.company = "Amazon"

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.level = st.radio('Choose level', key = 'visibility', options = ['Junior', 'Mid-level', 'Senior']) # radio buttons/checkers

    with col2:
        st.session_state.position = st.selectbox('Choose a position', ('Data Scientist', 'Data Engineer', 'Data Analyst'))


    st.session_state.company = st.selectbox('Choose a company', ('Amazon', 'Meta', 'Udemy', '365 Company', 'LinkedIn', 'Nestle', 'Spotify'))

    st.write(f"**You're applying for**: {st.session_state.level} {st.session_state.position} at {st.session_state.company}")

    if st.button("Start Interview", on_click = complete_setup): # complete setup je funkcija koja se izvrsava pri kliku
         st.write("Setup complete. Starting interview...")


if st.session_state.setup_complete and not st.session_state.feedback_shown and not st.session_state.chat_complete:

    st.info("""
            Start by introducing yourself.
            """,
            icon = "👋")
     
    client = OpenAI(api_key = st.secrets["OPENAI_API_KEY"])

    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-5.6-luna"

    if not st.session_state.messages: # ako je lista jos uvek prazna
        st.session_state.messages = [{"role": "system",
                                    "content": f'''You are an HR  executive that interviews an interviewee called {st.session_state.name} 
                                    with {st.session_state.experience} experience and the following skills: {st.session_state.skills}. 
                                    You should interview them for the position {st.session_state.level} {st.session_state.position} 
                                    at the company {st.session_state.company}.'''}] 
        # mozemo da inicijalizujemo kao praznu listu ili da dodamo system poruku

    # prikazujemo sve poruke do trenutka prompt-a
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if st.session_state.user_message_count < 5:
        if prompt := st.chat_input("Your question: ", max_chars = 1000): # dajemo vrednost prompt promneljivoj i ujedno proveravamo da li prompt postoji, tj nije False
            st.session_state.messages.append({"role": "user",
                                            "content": prompt}) # dodaj prompt u poruke 

            with st.chat_message("user"):
                st.markdown(prompt)

            if st.session_state.user_message_count < 4: # max 5 user-assistant interactions
                 
                with st.chat_message("assistant"):
                    stream = client.chat.completions.create(
                        model = st.session_state["openai_model"],
                        messages = [{"role": m["role"], "content": m["content"]}
                                    for m in st.session_state.messages], # chat history, dajemo kao kontekst pri generisanju odgovora
                        stream = True)
                    response = st.write_stream(stream)
                st.session_state.messages.append({"role": "assistant",
                                                "content": response})

            st.session_state.user_message_count += 1

    if st.session_state.user_message_count >= 5:
         st.session_state.chat_complete = True

if st.session_state.chat_complete and not st.session_state.feedback_shown:
     if st.button("Get Feedback", on_click = show_feedback):
          st.write("Fetching feedback...")


# Show feedback screen
if st.session_state.feedback_shown:
    st.subheader("Feedback")

    conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])

    # Initialize new OpenAI client instance for feedback
    feedback_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    # Generate feedback using the stored messages and write a system prompt for the feedback
    feedback_completion = feedback_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": """You are a helpful tool that provides feedback on an interviewee performance.
             Before the Feedback give a score of 1 to 10.
             Follow this format:
             Overal Score: //Your score
             Feedback: //Here you put your feedback
             Give only the feedback do not ask any additional questins.
              """},
            {"role": "user", "content": f"This is the interview you need to evaluate. Keep in mind that you are only a tool. And you shouldn't engage in any converstation: {conversation_history}"}
        ]
    )

    st.write(feedback_completion.choices[0].message.content) # we're extracting first message from the list which is a feedback
          
    if st.button("Restart Interview", type = "primary"):
        streamlit_js_eval(js_experssions = "parent.window.location.reload()")

