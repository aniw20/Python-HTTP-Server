import webServer
import sqlite3

server = webServer.Server('0.0.0.0', 80)

server.showRequests = True

def home():
    return server.sendHtmlFile("index.html")

server.route("/", home)

def mainStyle():
    return server.sendStyleFile("style.css")
server.route("/style.css", mainStyle)

server.run()