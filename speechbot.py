from flask import Flask, request
import json
import requests
import redis

app = Flask(__name__)

file_name = "speech.ogg"
languages = ["nl", "en-GB", "en-US", "fr", "de", "it", "ru", "cs", "pl", "es", "tr", "pt", "zh", "ar", "sv", "ja"]

token = "token here" #Bot token (Example: 93181085:AAELcePZ1qabYrDiu0t1PVPuw1HI0zXzXmq)
cert = "example.crt" #SSL certificate (Can not be self-signed)
key = "example.key"  #SSL key (Can not be self-signed)

api = "https://api.telegram.org/bot" + token

#Pretend we are human
headers = {"Host": "translate.google.com",
           "Referer": "http://www.gstatic.com/translate/sound_player2.swf",
           "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) "
                         "AppleWebKit/535.19 (KHTML, like Gecko) "
                         "Chrome/18.0.1025.163 Safari/535.19"
}

#Redis database to store language choice
db = redis.StrictRedis(host='localhost', port=6379, db=0)

#How long we should remember language choice (in days)
remember = 5

#Send text to chat
def sendMessage(chat_id, text):
  payload = {'chat_id': chat_id, 'text': text}
  r = requests.post(api + "/sendMessage", params=payload)
  return

#Send voice message to chat
def sendVoice(chat_id, language, text):
  payload = {'tl': language, 'q': text}
  r = requests.get("http://translate.google.com/translate_tts", params=payload, headers=headers)
  
  with open(file_name, 'wb') as file:
    file.write(r.content)
  
  payload = {'chat_id': chat_id}
  file = {'audio': open('speech.ogg', 'rb')}
  
  r = requests.post(api + "/sendAudio", params=payload, files=file)
  return
  
#Where the magic happens
@app.route('/telegram',methods=['POST'])
def main():
  data = json.loads(request.data)
  
  # We are only interested in text messages
  if 'text' in data['message']:
    message = data['message']['text'].encode('utf-8').strip()
    chat_id = data['message']['chat']['id']
    
    # /start
    if message == "/start":
      sendMessage(chat_id, "Use the speech command to let me do something! (Example: /speech I like apples)")
      return "OK"
    
    # /speech
    if message.startswith("/speech "):
    
      submittedText = message.replace("/speech ","",1)
      
      if db.get(chat_id) is not None:
        selectedLanguage = db.get(data['message']['chat']['id'])
        db.expire(data['message']['chat']['id'], remember * 3600)
      else:
        selectedLanguage = 'en-GB' #Default to English if no language has been set
      
      if len(submittedText) <= 99:
        sendVoice(chat_id, selectedLanguage, submittedText)
      else:
        sendMessage(chat_id, "Please use less than 100 characters")
        return "OK"
    elif message == "/speech":
      sendMessage(chat_id, "Use the command like this: /speech Hello, I like apples")
      return "OK"
    
    # /help
    if message == "/help":
      sendMessage(chat_id, """I support the following commands: \n
                           /speech <text> - Translate your text into a voice message
                           /language <language code> - Change the language of the bot
                           /help - Show information about the commands
                           /about - Show information about the bot""")
      return "OK"
    
    # /about  
    if message == "/about":
      sendMessage(chat_id, "Source code: https://github.com/lasermarty/SpeechBot")
      return "OK"
    
    # /language
    if message == "/language":
      sendMessage(chat_id, """Available language codes are: \n
                           nl (Dutch)
                           en-GB (English UK)
                           en-US (English US)
                           fr (French)
                           de (German)
                           it (Italian)
                           ru (Russian)
                           cs (Czech)
                           pl (Polish)
                           es (Spanish)
                           tr (Turkish)
                           pt (Portuguese)
                           zh (Chinese)
                           ar (Arabic)
                           sv (Swedish)
                           ja (Japanese)""")
      return "OK"
    elif message.startswith("/language "):
    
      language = message.replace("/language ","",1)
      
      if language in languages:
        db.set(data['message']['chat']['id'], language)
        db.expire(data['message']['chat']['id'], remember * 3600)
        sendMessage(chat_id, "Successfully set language to " + language)
        return "OK"
      else:
        sendMessage(chat_id, "Please use a correct language code (nl, en-GB, en-US, fr, de, it, ru, cs, pl, es, tr, pt, zh, ar, sv, ja)")
        return "OK"
  return "OK"

if __name__ == '__main__':
   app.run('0.0.0.0', debug=False, port=443, ssl_context=(cert, key), threaded=True) #Port can be 443, 80, 88, 8443
