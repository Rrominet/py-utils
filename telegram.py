import socket
import requests
import time

class Bot : 
    def __init__(self, token) : 
        self.token = token.split("\n")[0]

    def route(self) : 
        return "https://api.telegram.org/bot" + self.token + "/"

    #data is in dictionnary format here - json like
    def request(self, function, data): 
        url = self.route() + function
        r = requests.post(url, json = data)
        return r.json()

    def sendMessage(self, chatId, content) : 
        data = {
            "chat_id" : chatId,
            "text" : content
        }
        return self.request("sendMessage", data)

    def getUpdates(self): 
        return self.request("getUpdates", {})

    def infos(self) : 
        infos = "Bot " + self.token + "\n"
        infos += "API URL : " + self.route() + "\n"
        return infos

