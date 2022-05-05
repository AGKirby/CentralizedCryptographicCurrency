# import database, wallet
import crypto, wallet
from flask import Flask, request, send_file
from werkzeug.exceptions import HTTPException
import logger  

app = Flask("app")


@app.route("/", methods=["GET", "POST"])
def index():
    return "Hello World"


@app.route("/getSystemPublicKey", methods=["GET", "POST"])
def getSystemPublicKey():
    logger.writeLog("getSystemPublicKey", True)
    response = {
        "content": crypto.systemPublicKey.save_pkcs1().decode()
    }
    logger.writeLog()
    return response


@app.route("/cookies", methods=["GET", "POST"])
def cookies():
    return "\"Cookies are gay.\" - Someone famous\n We don't use cookies here."


@app.route("/ninshubur", methods=["GET", "POST"])
def ninshubur():
    return send_file("ninshubur.jpg")


@app.errorhandler(Exception)
def error(e):
    code = 500
    if isinstance(e, HTTPException):
        code = e.code
    logger.writeLog("ERROR " + str(code))
    return "ERROR " + str(code), code


#  content = { 
#     senderid: 
#     timestamp:
#  }
#  signature = ...
@app.route("/getBalance", methods=["POST"])
def getBalance():
    logger.writeLog("getBalance", True)
    senderID, content = getRequestContent(request.form)
    logger.writeLog([senderID, content])
    if senderID is None:
        return sendError(content)
    sender = wallet.wallets[senderID]
    response = {
      "message": "Your account balance is " + str(sender.getBalance())
    }
    return sendResponse(sender.getPublicKey(), response)


@app.route("/getTransactionHistory", methods=["POST"])
def getTransactionHistory():
    logger.writeLog("getTransactionHistory", True)
    senderID, content = getRequestContent(request.form)
    logger.writeLog([senderID, content])
    if senderID is None:
        return sendError(content)
    sender = wallet.wallets[senderID]
    afterDate = None
    if("after_date" in content.keys()):
        afterDate = content["after_date"]
    result = str(wallet.getTransactions(senderID, afterDate))
    response = {
      "message": result
    }
    # return sendResponse(sender.getPublicKey(), response)
    return response


@app.route("/getPublicBoard", methods=["GET", "POST"])
def getPublicBoard():
    logger.writeLog("getPublicBoard", True)
    response = {
      "message": "ID,Name,Balance,PublicKey\n" + str(wallet.getPublicBoard())
    }
    logger.writeLog()
    return response


@app.route("/transfer", methods=["POST"])
def transfer():
    logger.writeLog("transfer", True)
    senderID, content = getRequestContent(request.form)
    logger.writeLog([senderID, content])
    if senderID is None:
        return sendError(content)
    sender = wallet.wallets[senderID]
    receiverid = int(content["receiverid"])
    if receiverid is None:
        return sendError("You may not just remove currency from circulation")
    receiver = wallet.wallets[receiverid]
    if receiver is None:
        return sendError("You may not just remove currency from circulation")
    amount = float(content["amount"])
    if amount is None:
        return sendError("You must enter an amount to transfer")
    result = wallet.transaction(sender, receiver, amount)
    response = {
      "message": result
    }
    return sendResponse(sender.getPublicKey(), response)


# message received and sent in the clear
@app.route("/createWallet", methods=["POST"])
def createWallet():
    logger.writeLog("createWallet", True)
    # get and verify content
    content = request.form.to_dict(flat=True)
    logger.writeLog([content])
    # get name
    if(not ("name" in content.keys())):
        return sendError("Name required")
    name = content["name"]
    if name is None:
        return sendError("Name Required")
    # get discord
    discord = ""
    if("discord" in content.keys() and content["discord"] != None and content["discord"] != "None"):
        discord = content["discord"] #can be None
    # generate keys and create wallet
    keys = crypto.generateKeys()
    result = wallet.createWallet(name, keys[0].save_pkcs1().decode(), discord, 0.0)
    if not result[0]: #if unsuccessful
        return sendError(result[1]) #return error message
    # return JSON output
    newWalletId = list(wallet.wallets)[-1] 
    response = {
        "message": "Successfully created your wallet " + name + ". Attached is your wallet's id and its public and private keys. Please store them in a safe place where they will be secret and you will not lose them. NOTE: Adam can NOT recover your private key!",
        "wallet_id": newWalletId,
        "public_key": keys[0].save_pkcs1().decode(),
        "private_key": keys[1].save_pkcs1().decode()
    }
    return response
    
  

def getRequestContent(requestData):
    encryptedContent = bytes.fromhex(requestData["content"])
    digitalSignature = bytes.fromhex(requestData["signature"])
    if encryptedContent is None or digitalSignature is None:
        return (None, "Must send content and signature data")
    try: 
      senderID, content = crypto.receiveMessage(digitalSignature, encryptedContent)
    except: 
        return (None, "Failed to decrypt message")
    if senderID is None:
        return (None, content)
    return (senderID, content)


def sendResponse(senderPublicKey, message):
    encryptedContent, signature = crypto.sendMessage(senderPublicKey, message)
    response = {
        "content": encryptedContent.hex(),
        "signature": signature.hex()
    }
    logger.writeLog()
    return response


def sendError(message):
    errorcode = 400
    response = {
        "message": message
    }
    return response, errorcode



app.run(host="0.0.0.0", port=8000)
