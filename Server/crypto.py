import rsa
from Crypto.Hash import SHA256
import datetime, json
import wallet

timestamps = []

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


def hash(message):
    if(type(message) is str):
        message = str.encode(message)
    hash_object = SHA256.new(data = message)
    return hash_object.hexdigest()


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

      
#  content = { 
#     senderid: 
#     request: 
#     timestamp:
#  }
#  signature = ...
def sendMessage(senderPublicKey, content):
    content["timestamp"] = str(datetime.datetime.now())
    jsonContent = json.dumps(content)
    encryptedContent = encrypt(senderPublicKey, jsonContent)
    signature = digitalSignature(systemPrivateKey, jsonContent)
    return (encryptedContent, signature)


def receiveMessage(signature, content, senderPublicKey = None):
    jsonMessage = decrypt(systemPrivateKey, content)
    jsonContent = json.loads(jsonMessage)
    # validate message, get sender 
    senderID = jsonContent["senderid"]
    try: 
        sender = wallet.wallets[int(senderID)]
    except: 
        return (None, "No wallet with ID")
    senderPublicKey = sender.getPublicKey()
    if(not verifySignature(jsonMessage, signature, senderPublicKey)):
        return (None, "Invalid Signature")
    # prevent replay attack
    timestamp = datetime.datetime.strptime(jsonContent["timestamp"], "%Y-%m-%d %H:%M:%S.%f")
    difference = datetime.datetime.now() - timestamp
    if(difference.total_seconds() > 60):
        return (None, "Message expired: " + str(timestamp))
    if(difference.total_seconds() < -60):
        return (None, "Message premature. Resend at: " + str(timestamp))
    if((senderID,timestamp) in timestamps):
        return (None, "Cannot send duplicate requests")
    timestamps.append((senderID,timestamp))
    # perform message request
    return (int(senderID), jsonContent)


  
from replit import db
# Reset Keys
# systemKeys = generateKeys()
# db["systemPublicKey"] = systemKeys[0].save_pkcs1().decode()
# db["systemPrivateKey"] = systemKeys[1].save_pkcs1().decode()
# Load Keys
systemPublicKey = rsa.PublicKey.load_pkcs1(db["systemPublicKey"])
systemPrivateKey = rsa.PrivateKey.load_pkcs1(db["systemPrivateKey"])
