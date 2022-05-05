import database, rsa
import datetime

wallets = {}
names = []
MAXWALLETS = 20

class Wallet:
    def __init__(self, id, name, balance, publicKey, dateCreated, discord):
        self.id = int(id)
        self.name = name
        self.balance = float(balance)
        self.publicKey = publicKey
        self.dateCreated = dateCreated
        self.discord = discord
    
    def deposit(self, amount):
        self.balance += amount

    def withdrawl(self, amount):
        self.balance -= amount

    def getBalance(self):
        return self.balance

    def getPublicKey(self):
        return self.publicKey

    def getDiscord(self):
        return self.discord

    def __str__(self) -> str:
        return str(self.id)+","+self.name+","+str(self.balance)+","+str(self.active)+","+str(self.created)



def transaction(sender, receiver, amount):
    if(not(type(sender) is Wallet and type(receiver) is Wallet and (type(amount) is float or type(amount) is int))):
        return "Error: Invalid arguments"
    elif(sender.balance < amount):
        return "Error: Insufficient funds"
    elif(amount <= 0):
        return "Error: Non-positive amount"
    elif(sender.id == receiver.id):
        return "Error: Cannot transfer money to yourself"
    else:
        sender.withdrawl(amount)
        receiver.deposit(amount)
        try:
            database.transfer(sender, receiver, amount)
            return "Successfully transferred funds"
        except: #Error - Rollback
            sender.deposit(amount)
            receiver.withdrawal(amount)
            return "Failed to transfer funds: Database error"
        


def createWallet(name, publicKey, discordId = "", balance = 0.0):
    global MAXWALLETS
    if(len(wallets) >= MAXWALLETS):
        return (False, "Too many wallets created. Contact Adam.")
    if(not(type(name) is str and type(publicKey) is str and type(discordId) is str and (type(balance) is float or type(balance) is int))):
        return (False, "Invalid arguments for creating wallet")
    if(name in names):
        return (False, "Name must be unique")
    try: 
        success = database.insertWallet(name, balance, publicKey, discordId)
    except: 
        return (False, "Crashed trying to update database")
    if(not success):
        return (False, "Failed to update database")
    getWalletList()
    return (True, "Success")
    

def getTransactions(id, date = None):
    if(not(type(id) is int and (type(date) is datetime.datetime) or date==None)):
        return None
    result = database.getTransactions(id, date)
    response = "From,To,Amount,Timestamp\n"
    for row in result:
        string = "," + row[1] + "," + row[2] + "," + str(row[3]) + "," + row[0] + "\n"
        response += string
    return response


def getWalletList():
    global wallets
    wallets = {}
    walletsList = database.getWallets()
    for x in walletsList:
        try: 
            wallet = Wallet(x[0], x[1], x[2], rsa.PublicKey.load_pkcs1(x[3]), x[4], x[5])
            wallets[x[0]] = wallet
        except: 
            wallet = Wallet(x[0], x[1], x[2], x[3], x[4], x[5])
            wallets[x[0]] = wallet
        names.append(x[1])


def getPublicBoard():
    board = ""
    for wallet in wallets.values():
        id = str(wallet.id)
        if(id == 0):
            continue
        name = wallet.name
        balance = str(wallet.getBalance())
        try: 
            publicKey = (wallet.getPublicKey()).save_pkcs1().decode()
        except: 
            publicKey = wallet.getPublicKey()
        row = "," + id + "," + name + "," + balance + "," + publicKey
        board += row
    return board


getWalletList()