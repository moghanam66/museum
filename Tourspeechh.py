__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import embedchain
import streamlit as st
import base64
import openai
from PIL import Image
import pandas as pd
from utils import *
from streamlit_chat import message
import os
from deep_translator import GoogleTranslator
from deep_translator import single_detection
from embedchain.config import LlmConfig, ChromaDbConfig
from string import Template
from chromadb.utils import embedding_functions
from embedchain import App
import speech_recognition as sr
from gtts import gTTS
import logging
from elevenlabslib import *




def collect_data():
    os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY
    museumbot = App()
    # museumbot.llm.set_history()
    museumbot.add("art_museum_location.pdf", data_type= "pdf_file")
    # museumbot = App(chromadb_config=ChromaDbConfig(chroma_settings={"allow_reset": True}))
    # museumbot.db.reset()
    print(museumbot.db.count() , "**********************************")
    return museumbot

museumbot = collect_data()
museumbot.online = False


# Create a function to recognize speech
def recognize_speech():
    r = sr.Recognizer()
    with sr.Microphone(device_index=2) as source:
        st.write("Listening...")
        audio = r.listen(source , timeout = 5)
    
    try:
        text = r.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        return "Sorry, I couldn't understand that."
    except sr.RequestError as e:
        return f"Speech recognition request failed: {str(e)}"



def main():
    
    # Congfiger the page attributes
    st.set_page_config(
        page_title='Museum Tour Guide',
        page_icon=":star:",layout="wide")
    # Set the background
    #set_background('background.jpg')
    add_logo("logo4.jpg")
    
    with st.sidebar:
        st.sidebar.image("logo4.jpg", use_column_width=True)      
        st.markdown("<h1 style='color: black;'>💬 AI Museum Tour Guide</h1>", unsafe_allow_html=True)

        # image = Image.open('/home/user/Desktop/SA-hackathon-main/logo4.png')

    # Represent two sentence to represente how the chat works
    if 'history' not in st.session_state:
            st.session_state['history'] = []

    if 'generated' not in st.session_state:
        st.session_state['generated'] = ["Hello! I am a knowledgeable tour guide and archaeologist at the Walters Art Museum. I'm here to provide you with detailed information about the history and location of various pieces and paintings within the museum. How can I assist you today?" +  " 🤗"]

    if 'past' not in st.session_state:
        st.session_state['past'] = ["Hey ! 👋"]
        
        

    #container for the chat history
    response_container = st.container()
    #container for the user's text input
    container = st.container()

    with container:
        with st.form(key='my_form', clear_on_submit=True):
           
            # get the user input
            user_input = st.text_input(" ", placeholder="", key='input')
            
            #buttons
            col1,col2,col3 , col4 = st.columns( [0.5,0.8,.1 , .2])
            with col2:
                submit_button = st.form_submit_button(label='Send')
            with col3:
                record_button = st.form_submit_button(label='Call')
            with col4:
                endCall = st.form_submit_button(label='End Call')
            user_input_trns=user_input
            if not user_input:
                pass
            else:    
                input_language = single_detection(user_input_trns, api_key= "a3c5403a05341fe64784016c17888e01")
                if input_language != "en":
                    user_input_trns = GoogleTranslator(source=input_language, target='en').translate(user_input)
                    user_input_trns=user_input_trns.replace(',','')
                    print('user_input_trns',user_input_trns)
        
               
            # words = user_input_trns.lower().split()
            # print('words',words)
         #submit button 
        if submit_button and user_input:
                # get the output from open ai based on our data stored in the vector store
            output = conversational_chat_guide(user_input_trns,museumbot=museumbot, historyy= chat_history)
            output = GoogleTranslator(source='en' , target=input_language).translate(output)
                
            st.session_state['past'].append(user_input)
            st.session_state['generated'].append(output)
            
            if st.session_state['generated']:
                with response_container:
                    for i in range(len(st.session_state['generated'])):
                        message(st.session_state["past"][i], is_user=True, key=str(i) + '_user', avatar_style="big-smile")
                        message(st.session_state["generated"][i], key=str(i), avatar_style="thumbs")     
            
         #record button  
        if record_button:
            i = 0
            while True:
                user_input = recognize_speech()
                output = conversational_chat_guide(user_input,museumbot=museumbot, historyy= chat_history)
                #output = GoogleTranslator(source='en' , target=input_language).translate(output)
                # st.session_state['past'].append(user_input)
                # st.session_state['generated'].append(output)
                    
                # if st.session_state['generated']:
                #     with response_container:
                #     #for i in range(len(st.session_state['generated'])):
                #         message(st.session_state["past"][i], is_user=True, key=str(i) + '_user', avatar_style="big-smile")
                #         message(st.session_state["generated"][i], key=str(i), avatar_style="thumbs")       
                
                i+=1
                #Elevenlabs Text to Speech
                user = ElevenLabsUser("224fd24073cc2c28159b50472e9e7967") 
                voice = user.get_voices_by_name("Bella")[0]  # This is a list because multiple voices can have the same name
                #voice.generate_play_audio_v2("you")
                st.write(str(output))
                voice.generate_play_audio_v2(str(output), playbackOptions=PlaybackOptions(runInBackground=False))
                # for historyItem in user.get_history_items_paginated():
                #     if historyItem.text == "Test.":
                #         # The first items are the newest, so we can stop as soon as we find one.
                #         historyItem.delete()
                #         break   
                if endCall:
                    break              
                                

# def conversational_chat(query,travelbot):
#         # config the chain with the llm and the vector store
#         # chain = ConversationalRetrievalChain.from_llm(
#         #     llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY,temperature=0.0,model_name='gpt-3.5-turbo'),
#         #     retriever=_vectorstore.as_retriever())
        
#         # result = chain({"question": query, 
#         # "chat_history": st.session_state['history']})
#         result = travelbot.query(query)
#         st.session_state['history'].append((query, result))
        
#         return result


chat_history = ['User: Hi', 'Bot: How can I help you!']
def conversational_chat_guide(query, museumbot, historyy):
    
    # museumbot.llm.set_history(chat_history)
    historyy  = chat_history
        
    chat_template = Template(""" 
            your answer should be briefly in 20 words maximum.                
            I want you to act as a knowledgeable tour guide and archaeologist at the Walters Art Museum and understand all languages. \
            I will provide you with the name or category of a specific piece or painting in the museum, and you will tell me about its history and location within the museum. \
            For example, I might say 'Tell me about the Scarab Amulet' or 'Where can I find the Relief Fragment Showing a Priest with an Incense Burner?' \
            Additionally, you have a deep understanding of the history and categories of each piece and painting in the museum. You also know the precise location of each item. \
                
            But First know the user interests start with suggestions of some locations from the data and say: Before we begin, let me suggest some locations in the museum based on your interests: 
            1. Egyptian Artifacts \
            2. Jewelry \
            3. Sculptures \
            4. Animal Representations \
            5. Functional Objects
            Feel free to let me know which category or section intrigues you the most, or if there's a specific piece you'd like to learn more about. \
            I'm here to provide you with detailed information about its history and guide you to its location within the museum. Let's get started! \
               
            And if the question is not related to the Walters Art museum or the history of artifacts, say you don't know or you have no information about it.\
            You are respond in a polite way and friendly.
            
        Here is a question:
        {input}
        
        Your answer must be short, maximum 20 words only.
        Use the following information about objects in the Walters Art Museum to respond to
        the human's query acting as tour guide.
        Your answer must be short, maximum 20 words only.
        Context: $context
        History: $history
        If you don't know the answer, just say that you don't know, don't try to make up an answer.
        Your answer must be short, maximum 20 words only.
        Human: $query
        Tour guide:""")
    
    llm_config = LlmConfig(template=chat_template, system_prompt="You are a knowledgeable tour guide and archaeologist at the Walters Art Museum")

    result = museumbot.query(query, config=llm_config)

    
    # query_config = QueryConfig(template=chat_template)
    # result = museumbot.query(query,config=query_config)
    
    User_question = f"User: {query}"
    Bot_answer = f"Bot: {result}"
    chat_history.append(User_question )
    chat_history.append(Bot_answer)
    # st.session_state['history'].append((query, result))
            
    return result    

       

if __name__ == "__main__":
    main()
