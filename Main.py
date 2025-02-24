from Frontend. GUI import ( GraphicalUserInterface, SetAssistantStatus,
ShowTextToScreen,
TempDirectoryPath,
SetMicrophoneStatus,
AnswerModifier,
QueryModifier,
GetMicrophoneStatus,
GetAssistantStatus )
from Backend.Model import FirstLayerDMM
from Backend.RealTimeSearchEngine import RealtimeSearchEngine
from Backend.Automation import Automation
from Backend.SpeachToText import SpeechRecognition
from Backend.Chatbot import ChatBot
from Backend.TextToSpeach import TextToSpeech 
from dotenv import dotenv_values
from asyncio import run
from time import sleep 
import subprocess
import threading 
import threading
import time
import json
import os

env_vars= dotenv_values(".env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
DefaultMessage = f'''{Username} : Hello {Assistantname}, How are you?
{Assistantname} : Welcome {Username}. I am doing well. How may i help you?'''
subprocesses = []
Functions = ["open", "close", "play", "system", "content", "google search", "youtube search"]


def ShowDefaultChatIfNoChats():
    with open(r'Data\ChatLog.json', "r", encoding='utf-8') as File:
        if len(File.read()) < 5:
            with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
                file.write("")
            with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as file:
                file.write(DefaultMessage)
            
            
def ReadChatLogJson():
    try:
        with open(r'Data\ChatLog.json', 'r', encoding='utf-8') as file:
            chatlog_data = json.load(file)
        return chatlog_data
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error loading chat log: {e}")
        return []



def ChatLogIntegration():
    json_data = ReadChatLogJson()
    formatted_chatlog = ""
    for entry in json_data:
        if entry["role"] == "user":
            formatted_chatlog += f"User: {entry['content']}\n"
        elif entry["role"] == "assistant":
            formatted_chatlog += f"Assistant: {entry['content']}\n"
    formatted_chatlog = formatted_chatlog.replace("User", Username + " ") 
    formatted_chatlog = formatted_chatlog.replace("Assistant", Assistantname + "")
    
    with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file: 
        file.write(AnswerModifier(formatted_chatlog))
        
        



def ShowChatsOnGUI():
    File = open(TempDirectoryPath('Database.data'),"r", encoding='utf-8') 
    Data = File.read()
    if len(str(Data))>0:
        lines = Data.split('\n')
        result = '\n'.join(lines)
        File.close()
        File = open(TempDirectoryPath('Responses.data'),"w", encoding='utf-8')
        File.write(result)
        File.close()
        

def InitialExecution():
    SetMicrophoneStatus("False")
    ShowTextToScreen("")
    ShowDefaultChatIfNoChats()
    ChatLogIntegration()
    ShowChatsOnGUI()

InitialExecution()
    

def MainExecution():
    TaskExecution = False
    ImageExecution = False
    ImageGenerationQuery = ""
    SetAssistantStatus("Listening...") 
    Query = SpeechRecognition()
    ShowTextToScreen(f"{Username} : {Query}") 
    SetAssistantStatus("Thinking ...") 
    Decision = FirstLayerDMM(Query)
    
    
    print("")
    print(f"Decision: {Decision}")
    print("")
    
    G = any([i for i in Decision if i.startswith("general")])
    R = any([i for i in Decision if i.startswith("realtime")])
    
    print(G, R)
    
    Mearged_query = " and ".join(
        [" ".join(i.split()[1:]) for i in Decision if i.startswith("general") or i.startswith("realtime")]
    )
    
    for queries in Decision:
        if "generate " in queries:
            ImageGenerationQuery = str(queries)
            print(ImageGenerationQuery)
            ImageExecution = True
            
    for queries in Decision:
        if TaskExecution == False:
            if any(queries.startswith(func) for func in Functions):
                run(Automation(list(Decision))) 
                TaskExecution = True
                

    if ImageExecution:
        print("This is true......")
        
        # Fix: Corrected file name
        with open(r"Frontend\Files\ImageGeneration.data", "w") as file: 
            file.write(f"{ImageGenerationQuery}, True")
        
        try:
            print("Calling Model.......")
            p1 = subprocess.Popen(['python', r'Backend\ImageGeneration.py'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                stdin=subprocess.PIPE, shell=True)  # Fix: shell=True for Windows
            
            stdout, stderr = p1.communicate()  # Fix: Capture errors
            
            print("Process:", p1)
            print("STDOUT:", stdout.decode())
            print("STDERR:", stderr.decode())  # Fix: Show errors
            
            if p1.poll() is None:  # Fix: Check if process is running
                subprocesses.append(p1)
            else:
                print("ImageGeneration.py failed to start")

        except Exception as e:
            print(f"Error starting ImageGeneration.py: {e}")

        
    if G and R:
        SetAssistantStatus("Searching...")
        Answer = RealtimeSearchEngine(QueryModifier(Mearged_query)) 
        ShowTextToScreen(f"{Assistantname} : {Answer}")
        SetAssistantStatus("Answering...")
        TextToSpeech(Answer)
        return True
        
    else:
        for Queries in Decision:
            print("I am here.......")
            
            if "general" in Queries:
                SetAssistantStatus("Thinking ... ")
                QueryFinal = Queries.replace("general","") 
                Answer = ChatBot(QueryModifier(QueryFinal)) 
                ShowTextToScreen(f"{Assistantname} : {Answer}") 
                SetAssistantStatus("Answering ... ") 
                TextToSpeech(Answer)
                return True
            
            elif "realtime" in Queries:
                SetAssistantStatus("Searching...")
                QueryFinal = Queries.replace("realtime "," ")
                Answer = RealtimeSearchEngine(QueryModifier(QueryFinal)) 
                ShowTextToScreen(f"{Assistantname} : {Answer}") 
                SetAssistantStatus("Answering ... ")
                TextToSpeech(Answer)
                return True
            
            elif "exit" in Queries:
                QueryFinal = "Okay, Bye!"
                Answer = ChatBot(QueryModifier(QueryFinal)) 
                ShowTextToScreen(f" {Assistantname} : {Answer}")
                SetAssistantStatus("Answering ... .")
                TextToSpeech(Answer)
                SetAssistantStatus("Answering ... ")
                os._exit(1)



def FirstThread():
    while True:
        try:
            CurrentStatus = GetMicrophoneStatus()
            if CurrentStatus == "True":
                MainExecution()
            else:
                AIStatus = GetAssistantStatus()
                if "Available ..." not in AIStatus:
                    SetAssistantStatus("Available ... ")
                time.sleep(0.5)  # Reduce CPU usage when idle
        except Exception as e:
            print(f"Error in FirstThread: {e}")
            time.sleep(1)  # Prevent crash loop

def SecondThread():
    try:
        GraphicalUserInterface()
    except Exception as e:
        print(f"Error in SecondThread: {e}")

if __name__ == "__main__":
    thread1 = threading.Thread(target=FirstThread, daemon=True)
    thread2 = threading.Thread(target=SecondThread, daemon=True)

    thread1.start()
    thread2.start()

    # Keep the main program running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping threads...")
