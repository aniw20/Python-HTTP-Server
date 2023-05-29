import socket
import json
from urllib.parse import unquote, quote
import threading
import colorama

colorama.init(convert=True)

def decodeUri(expression: str):
    return unquote(expression)

def getUrl(text):
    try:
        text = text.split("\n")
        return text[0].split(" ")[1].split("?")[0]
    except:
        return "/"

def getArgs(text):
    try:
        gtargs = {}
        text = text.split("\n")[0]
        text = text.split(" ")[1].split("?")[1]
        args = text.split("&")
        for arg in args:
            t = arg.split("=")
            gtargs[decodeUri(t[0].replace("+", " "))] = decodeUri(t[1].replace("+", " "))
        return gtargs
    except:
        return {}

def getMethod(req):
    try:
        method = req.split("\n")[0].split(" ")[0]
    except:
        method = "NONE"
    return method

def postArgs(text):
    try:
        gtargs = {}
        if text.split("\n")[0].split(" ")[0] == "POST":
            t = text.split("\n")
            text = t[len(t) - 1]
            args = text.split("&")
            for arg in args:
                t = arg.split("=")
                gtargs[decodeUri(t[0].replace("+", " "))] = decodeUri(t[1].replace("+", " "))
            return gtargs
        else:
            return {}
    except:
        return {}

def getElement(text, keyword):
    try:
        found = False
        text = text.split("\n")
        for line in text:
            if keyword in line:
                text = line
                text = text.replace(keyword, "")
                found = True
        if not found:
            text = ""
    except:
        text = ""
    return text

def getWebSocket(req):
    getElement(req, "Upgrade: ").replace(" ", "")

def getCookies(req):
    data = getElement(req, "Cookie: ")
    try:
        cookies = {}
        data = data.split(";")
        for d in data:
            i = d.split("=")
            name = i[0].replace(" ", "").replace("+", " ")
            value = i[1].replace(" ", "").replace("+", " ")
            name = unquote(name)
            value = unquote(value).split("\r")[0]
            cookies[name] = value
        return cookies
    except:
        return {}

def handleClient(self, conn, addr):
    text = conn.recv(1024).decode()
    if self.showRequests:
        print("-----------------------------------------------")
        print("Request: ", text)
        print("-----------------------------------------------")
    route = getUrl(text)
    get = getArgs(text)
    post = postArgs(text)
    method = getMethod(text)
    platform = getElement(text, "sec-ch-ua-platform: ")
    userAgent = getElement(text, "User-Agent: ")
    cookies = getCookies(text)

    request = self.convertArgsToDict(get = get, post = post, addr = addr, 
    method = method, platform=platform, userAgent = userAgent, cookies = cookies)

    if route in self.routes:
        if len(self.routes[route]) == 2:
            try:
                content = self.routes[route][0](self.routes[route][1], request=request)
                self.okHeader += "Connection: close\r\n\n"
                if self.showRequests == True:
                    print("Response: ", self.okHeader+content)
                conn.send(f'{self.okHeader}{content}'.encode("utf-8"))
            except:
                content = self.routes[route][0](self.routes[route][1])
                self.okHeader += "Connection: close\r\n\n"
                if self.showRequests == True:
                    print("Response: ", self.okHeader+content)
                conn.send(f'{self.okHeader}{content}'.encode())
        else:
            try:
                content = self.routes[route][0](request=request)
                self.okHeader += "Connection: close\r\n\n"
                if self.showRequests == True:
                    print("Response: ", self.okHeader+content)
                conn.send(f'{self.okHeader}{content}'.encode()) 
            except:
                content = self.routes[route][0]()
                self.okHeader += "Connection: close\r\n\n"
                if self.showRequests == True:
                    print("Response: ", self.okHeader+content)
                conn.send(f'{self.okHeader}{content}'.encode())
    else:
        conn.send(self.notFountHeader.encode("utf-8"))
    self.okHeader = "HTTP/1.1 200 OK \r\n"
    conn.close()

class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.stop = False
        self.okHeader = "HTTP/1.1 200 OK \r\n"
        self.notFountHeader = "HTTP/1.1 404 NOT_FOUND \r\n"
        self.routes = {}
        self.args = {}
        self.showRequests = False
    def run(self):
        self.server.bind((self.host, self.port))
        self.server.listen(5)
        print(colorama.Fore.GREEN + "[+] Server is running!" + colorama.Fore.RESET)
        self.loop()
    def sendCookies(self, cookies: dict):
        content = ""
        for cookie in cookies:
            content += "Set-Cookie: " + quote(cookie) + "=" + quote(cookies[cookie]) + "\r\n"
        self.okHeader += content
        return ""
    def sendJsonFile(self, filename):
        self.okHeader += "Content-Type: application/json\r\n"
        return open(filename, "r").read()
    def sendHtmlFile(self, filename, **kwargs):
        content = open(filename, "r").read()
        for i in kwargs:
            content = content.replace("{{"+i+"}}", str(kwargs[i]))
        self.okHeader += "Content-Type: text/html\r\n"
        return content
    def sendStyleFile(self, filename, **kwargs):
        content = open(filename, "r").read()
        for i in kwargs:
            content = content.replace("{{"+i+"}}", str(kwargs[i]))
        return content
    def sendJson(self, content: dict | str):
        if type(content == dict):
            content = json.dumps(content)
        self.okHeader = "Content-Type: application/json\r\n"
        return content
    def sendHtml(self, content: str):
        self.okHeader += "Content-Type: text/html\r\n"
        return content
    def convertArgsToDict(self, **args):
        return args
    def route(self, route, f, *args):
        self.routes[route] = (f, *args)
    def redirect(self, path):
        self.okHeader = self.okHeader.replace("HTTP/1.1 200 OK \r\n", "HTTP/1.1 302 OTHER \r\n")
        self.okHeader += "Location: "+path+"\r\n"
        return ""
    def loop(self):
        while True:
            self.args = {}
            conn, addr = self.server.accept()
            thread = threading.Thread(target=handleClient, args=(self, conn, addr))
            thread.start()
            #handleClient(self, conn, addr)