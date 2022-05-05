from flask import Flask, request, render_template
import json
import ninshubur
import logger

app = Flask("webapp")
print("webapp")

@app.route("/", methods=["GET"])
def index():
    return render_template('home.html')


@app.route("/publicBoard", methods=["GET"])
def publicBoard():
    logger.writeLog("publicBoard GET []", True)
    publicBoard = ninshubur.getPublicBoard()
    logger.writeLog(publicBoard[0])
    if(not publicBoard[0]):
        return "Error"
    publicBoardList = publicBoard[1].split(",")
    print(str(publicBoardList))
    table = "<table>"
    firstRow = True
    rowElementCount = 0
    for element in publicBoardList:
        if(rowElementCount == 4):
            rowElementCount = 0
            firstRow = False
            table += "\n\t</tr>"
        if(rowElementCount == 0):
                table += "\n\t<tr>"
        rowElementCount += 1
        if firstRow:
            table += "\n\t\t<th>"
        else: 
            table += "\n\t\t<td>"
        table += element
        if firstRow:
            table += "</th>"
        else: 
            table += "</td>"
    table += "</table>"
    logger.writeLog()
    return render_template('publicBoard.html', table=table)


@app.route("/createWallet", methods=["GET", "POST"])
def createWallet():
    logger.writeLog("createWallet", True)
    if request.method == "POST":
        logger.writeLog("POST")
        name = request.form.get("name")
        discord = request.form.get("discord")
        logger.writeLog([name, discord])
        if(discord == ""):
            discord = None
        success, response = ninshubur.createWallet(name, discord)
        logger.writeLog(success)
        if success: 
            header = "Your Wallet Has Been Created"
        else: 
            header = "Error Creating Wallet"
        logger.writeLog()
        return displayJson(header, response)
    logger.writeLog("GET [] N/A Complete")
    return render_template('createWallet.html')


@app.route("/code", methods=["GET"])
def code():
    return render_template('code.html')


@app.route("/discordBot", methods=["GET"])
def discordBot():
    return render_template('discordBot.html')


@app.route("/transfer", methods=["GET", "POST"])
def transfer():
    logger.writeLog("transfer", True)
    if request.method == "POST":
        logger.writeLog("POST")
        key = request.form.get("signkey")
        senderid = request.form.get("senderid")
        receiverid = request.form.get("receiverid")
        amount = request.form.get("amount")
        logger.writeLog([senderid, receiverid, amount])
        try: 
            signKey = ninshubur.rsa.PrivateKey.load_pkcs1(key)
        except: 
            return "Invalid format"
        success, response = ninshubur.transfer(senderid, receiverid, amount, signKey)
        logger.writeLog(success)
        if success: 
            header = "Transferred Money"
        else: 
            header = "Error Transfering Money"
        logger.writeLog()
        return render_template('response.html', header=header, label1="Response", response1=response, label2="", response2="")
    logger.writeLog("GET [] N/A Complete")
    return render_template('transfer.html')


@app.route("/getBalance", methods=["GET", "POST"])
def getBalance():
    logger.writeLog("getBalance", True)
    if request.method == "POST":
        logger.writeLog("POST")
        key = request.form.get("signkey")
        senderid = request.form.get("senderid")
        logger.writeLog([senderid])
        # try: 
        signKey = ninshubur.rsa.PrivateKey.load_pkcs1(key)
        print(signKey)
        # except: 
        #     return "Invalid format"
        success, response = ninshubur.getBalance(senderid, signKey)
        logger.writeLog(success)
        if success: 
            header = "Your Wallet's Balance"
        else: 
            header = "Error Getting Balance"
        logger.writeLog()
        return render_template('response.html', header=header, label1="Response", response1=response, label2="", response2="")
    logger.writeLog("GET [] N/A Complete")
    return render_template('getBalance.html')


@app.route("/getTransactionHistory", methods=["GET", "POST"])
def getTransactionHistory():
    logger.writeLog("getTransactionHistory", True)
    if request.method == "POST":
        key = request.form.get("signkey")
        senderid = request.form.get("senderid")
        logger.writeLog([senderid])
        try: 
            signKey = ninshubur.rsa.PrivateKey.load_pkcs1(key)
        except: 
            return "Invalid format"
        success, response = ninshubur.getTransactionHistory(senderid, signKey)
        logger.writeLog(success)
        if not success:
            header = "Error Getting Your Transaction History"
            return render_template('response.html', header=header, label1="Response", response1=response, label2="", response2="")
        transactionHistory = response.split(",")
        table = "<table>"
        firstRow = True
        rowElementCount = 0
        for element in transactionHistory:
            if(rowElementCount == 4):
                rowElementCount = 0
                firstRow = False
                table += "\n\t</tr>"
            if(rowElementCount == 0):
                    table += "\n\t<tr>"
            rowElementCount += 1
            if firstRow:
                table += "\n\t\t<th>"
            else: 
                table += "\n\t\t<td>"
            table += element
            if firstRow:
                table += "</th>"
            else: 
                table += "</td>"
        table += "</table>"
        logger.writeLog()
        return render_template('transactionHistoryTable.html', table=table)
    logger.writeLog("GET [] N/A Complete")
    return render_template('getTransactionHistory.html')


@app.route("/encryptMessage", methods=["GET", "POST"])
def encryptMessage():
    logger.writeLog("encryptMessage", True)
    if request.method == "POST":
        logger.writeLog("POST []")
        key1 = request.form.get("encryptkey")
        key2 = request.form.get("signkey")
        plaintext = request.form.get("plaintext")
        try: 
            jsonMessage = json.loads(plaintext)
            encryptKey = ninshubur.rsa.PublicKey.load_pkcs1(key1)
            signKey = ninshubur.rsa.PrivateKey.load_pkcs1(key2)
        except: 
            return "Invalid format"
        response, signature = ninshubur.encryptMessage(encryptKey, jsonMessage, signKey)
        header = "Your Encrypted Message and Digital Signature"
        logger.writeLog()
        return render_template('response.html', header=header, label1="Encrypted Message", response1=response.hex(), label2="Digital Signature", response2=signature.hex())
    defaulttext = "{\n\t\"senderid\": _,\n\t\"message\": \"_\"\n}"
    logger.writeLog("GET [] N/A Complete")
    return render_template('encryptMessage.html', defaulttext=defaulttext)


@app.route("/decryptMessage", methods=["GET", "POST"])
def decryptMessage():
    logger.writeLog("decryptMessage", True)
    if request.method == "POST":
        logger.writeLog("POST []")
        key1 = request.form.get("verifykey")
        key2 = request.form.get("decryptkey")
        ciphertextHex = request.form.get("ciphertext")
        signatureHex = request.form.get("signature")
        try: 
            ciphertext = bytes.fromhex(ciphertextHex)
            print(str(ciphertext))
            signature = bytes.fromhex(signatureHex)
            print(str(ciphertext))
            verifyKey = ninshubur.rsa.PublicKey.load_pkcs1(key1)
            print(str(verifyKey))
            decryptKey = ninshubur.rsa.PrivateKey.load_pkcs1(key2)
            print(str(decryptKey))
        except: 
            return "Invalid format"
        response = ninshubur.decryptMessage(ciphertext, decryptKey, signature, verifyKey)
        header = "Your Decrypted Message"
        logger.writeLog()
        return render_template('response.html', header=header, label1="Decrypted Message", response1=response)
    logger.writeLog("GET [] N/A Complete")
    return render_template('decryptMessage.html')


def displayJson(header, jsonStr):
    jsonDict = json.loads(jsonStr)
    htmlStr = ""
    for key in jsonDict.keys():
        keyStr = "\n<h3>" + str(key) + "</h3>"
        htmlStr += keyStr
        itemStr = "\n<p style=\"word-wrap: break-word;\">" + str(jsonDict[key]) + "</p>\n<br>"
        htmlStr += itemStr
    return render_template('jsonResponse.html', header=header, items=htmlStr)


app.run(host="0.0.0.0", port=8000)