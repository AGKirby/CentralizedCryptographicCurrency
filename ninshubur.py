import requests, rsa, datetime, json

#When running on Replit, otherwise change to your needs
from replit import db
# Load Key 
systemPublicKey = None
if("systemPublicKey" in db.keys()):
    systemPublicKey = rsa.PublicKey.load_pkcs1(db["systemPublicKey"])

  
#####################################################
################# Public Functions: #################
### Returns: Tuple(bool, string)                  ###
### Tuple[0] -> True on success, False on failure ###
### Tuple[1] -> String message of success/failure ###
#####################################################

#If running on Replit, call this function once upon creating your application. 
#If not, customize this function to fit your needs and to set the global. 
#Perhaps save systemPublicKey to a text file and then read the file on load and save to the global systemPublicKey variable 
def updateSystemPublicKey():
    response = sendRequest("/getSystemPublicKey", {})
    if(response[0] == True):
        response = response[1]
        response = response["content"]
        if(response != None):
            setSystemPublicKey(response)
            return (True, "Successfully updated system public key")
    return (False, "An error occurred: " + response[1])
  

# On success, returns system public key used to encrypt messages
def getSystemPublicKey():
    response = sendRequest("/getSystemPublicKey", {})
    if(response[0] == True):
        response = response[1]
        return (True, response["content"])
    else: 
        return (False, "An error occurred: " + response[1])


# On success, returns balance associated with senderid
def getBalance(senderid, privateKey):
    content = {
        "senderid": senderid,
        "message": "Get balance"
    }
    response = sendRequest("/getBalance", content, privateKey)
    if(response[0] == True):
        response = response[1]
        return (True, response["message"])
    else: 
        return (False, "An error occurred: " + response[1])


# On success, returns string list of transactions associated with senderid
def getTransactionHistory(senderid, privateKey):
    content = {
        "senderid": senderid,
        "message": "Get transaction history"
    }
    response = sendRequest("/getTransactionHistory", content, privateKey, decrypt=False)
    if(response[0] == True):
        response = response[1]
        return (True, response["message"])
    else: 
        return (False, "An error occurred: " + response[1])


# On success, retursn string csv of wallet id, name, balance, and public keys
def getPublicBoard():
    content = {
        "message": "Get public board"
    }
    response = sendRequest("/getPublicBoard", content)
    if(response[0] == True):
        response = response[1]
        return (True, response["message"])
    else: 
        return (False, "An error occurred: " + response[1])


# On success, transfers $amount from senderid to receiverid and returns success string
def transfer(senderid, receiverid, amount, privateKey):
    content = {
        "senderid": senderid,
        "receiverid": receiverid,
        "amount": amount
    }
    response = sendRequest("/transfer", content, privateKey)
    if(response[0] == True):
        response = response[1]
        return (True, response["message"])
    else: 
        return (False, "An error occurred: " + response[1])


# On success, returns created wallet's id, public_key, and private_key in a dictionary object
def createWallet(name, discord = None):
    content = {
        "name": name,
        "message": "Create wallet for " + name
    }
    if(not discord == None):
        content["discord"] = discord
    response = sendRequest("/createWallet", content)   
    if(response[0] == True):
        response = response[1]
        return (True, response) #has "message", "public_key", and "private_key"
    else: 
        return (False, "An error occurred: " + response[1])



#############################################
###### Cryptographic Helper Functions: ######
#############################################

def setSystemPublicKey(systemPublicKey):
    db["systemPublicKey"] = systemPublicKey.decode()


def generateKeys():
    public, private = rsa.newkeys(1024)
    return (public, private)


def encrypt(key, message):
    if(type(message) is str):
        message = str.encode(message)
    ciphertext = rsa.encrypt(message, key)
    return ciphertext


def decrypt(key, message):
    if(type(message) is str):
        message = str.encode(message)
    plaintext = rsa.decrypt(message, key)
    return plaintext.decode()


def digitalSignature(key, message):
    if(type(message) is str):
        message = message.encode()
    signature = rsa.sign(message, key, 'SHA-1')
    return signature


def verifySignature(message, signature, key):
    if(type(message) is str):
        message = message.encode()
    try:
        hashFunction = rsa.verify(message, signature, key)
        if(hashFunction != "SHA-1"):
            return False
        return True
    except:
        return False


#############################################
######### Web API Helper Functions: #########
#############################################
      
# Message format: 
#  content = { 
#     senderid: int
#     request: hex
#     timestamp: timestamp
#  }
#  signature = hex
def sendMessage(senderPrivateKey, content):
    content["timestamp"] = str(datetime.datetime.now())
    jsonContent = json.dumps(content)
    encryptedContent = encrypt(systemPublicKey, jsonContent)
    signature = digitalSignature(senderPrivateKey, jsonContent)
    return (encryptedContent, signature)


def receiveMessage(signature, content, senderPrivateKey):
    jsonMessage = decrypt(senderPrivateKey, content)
    jsonContent = json.loads(jsonMessage)
    # validate message, get sender 
    if(not verifySignature(jsonMessage, signature, systemPublicKey)):
        return (None, "Invalid Signature")
    # prevent replay attack
    timestamp = datetime.datetime.strptime(jsonContent["timestamp"], "%Y-%m-%d %H:%M:%S.%f")
    difference = datetime.datetime.now() - timestamp
    if(difference.total_seconds() > 20):
        return (None, "Message expired")
    # perform message request
    return jsonContent



def sendRequestWithEncryptedContent(url, encryptedContent, digitalSignature):
    api_url = "https://JudicialPrudentSoftwareagent.granetoa.repl.co" + url
    encryptedContent = encryptedContent.hex()
    digitalSignature = digitalSignature.hex()
    #prepare and send message
    payload = {
      "content": encryptedContent,
      "signature": digitalSignature
    }
    response = requests.post(api_url, payload)
    if(response.ok): 
        message = response.json()
        response.close()
        content = message["content"]
        signature = message["signature"]
        return (content, signature)
    else: #if error occurred
        error = response.json()
        response.close()
        error["error"] = "Error " + str(response.status_code) + ": " + str(response.reason)
        return (False, error)


def decryptContent(contentHex, signatureHex, privateKey):
    content = bytes.fromhex(contentHex)
    signature = bytes.fromhex(signatureHex)
    message = receiveMessage(signature, content, privateKey)
    return message
  

def sendRequest(url, content, privateKey = None, publicKey = None, decrypt = True):
    api_url = "https://JudicialPrudentSoftwareagent.granetoa.repl.co" + url
    signature = None
    if(privateKey != None): #if need to encrypt
        content, signature = sendMessage(privateKey, content)
        content = content.hex()
        signature = signature.hex()
        #prepare and send message
        payload = {
          "content": content,
          "signature": signature
        }
    else: 
        payload = content
    response = requests.post(api_url, payload)
    # response received
    if(response.ok): 
        message = response.json()
        if not decrypt:
            return (True, message)
        response.close()
        if(privateKey != None): #if need to decrypt
            content = bytes.fromhex(message["content"])
            signature = bytes.fromhex(message["signature"])
            message = receiveMessage(signature, content, privateKey)
        return (True, message)
    else: #if error occurred
        error = response.text
        print("Error " + str(response.status_code) + ": " + str(response.reason))
        response.close()
        return (False, error)




def encryptMessage(encryptionPublicKey, content, signingPrivateKey):
    content["timestamp"] = str(datetime.datetime.now())
    jsonContent = json.dumps(content)
    encryptedContent = encrypt(encryptionPublicKey, jsonContent)
    signature = digitalSignature(signingPrivateKey, jsonContent)
    return (encryptedContent, signature)


def decryptMessage(content, decryptionPrivateKey, signature, verifyingPublicKey):
    jsonMessage = decrypt(decryptionPrivateKey, content)
    jsonContent = json.loads(jsonMessage)
    # validate message, get sender 
    if(not verifySignature(jsonMessage, signature, verifyingPublicKey)):
        return (None, "Invalid Signature")
    # prevent replay attack
    # timestamp = datetime.datetime.strptime(jsonContent["timestamp"], "%Y-%m-%d %H:%M:%S.%f")
    # difference = datetime.datetime.now() - timestamp
    # if(difference.total_seconds() > 20):
    #     return (None, "Message expired")
    # perform message request
    return jsonContent