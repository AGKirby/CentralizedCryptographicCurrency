import mysql.connector
import datetime
from replit import db

mydb = mysql.connector.connect(
  host="remotemysql.com",
  user="",
  password=db["password"],
  database=""
)

print(mydb)


def insertWallet(name, balance, publicKey, discordId):
    mycursor = mydb.cursor()
    timestamp = str(datetime.datetime.now())
    sql = "INSERT INTO Wallet (Name,Balance,PublicKey,DateCreated,Discord) VALUES (%s, %s, %s, %s, %s)"
    val = (name, balance, publicKey, timestamp, discordId)
    mycursor.execute(sql, val)
    mydb.commit()
    if(mycursor.rowcount == 1):
        return True
    return False
  


def getWallets():
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM Wallet") 
    myresult = mycursor.fetchall()
    return myresult
    

def transfer(sender, receiver, amount):
    mycursor = mydb.cursor()
    # add entry to Transaction table
    timestamp = str(datetime.datetime.now())
    sql1 = "INSERT INTO Transaction (SenderID,ReceiverID,Amount,Timestamp) VALUES (%s, %s, %s, %s)"
    val = (sender.id, receiver.id, amount, timestamp)
    mycursor.execute(sql1, val)
    # update sender balance
    if(sender.id != 0):
        sql2 = "UPDATE Wallet SET balance = '" + str(sender.balance) + "' WHERE ID = '" + str(sender.id) + "'"
        mycursor.execute(sql2)
    # update receiver balance
    sql3 = "UPDATE Wallet SET balance = '" + str(receiver.balance) + "' WHERE ID = '" + str(receiver.id) + "'"
    mycursor.execute(sql3)
    mydb.commit()


def getTransactions(id, date = None):
    mycursor = mydb.cursor()
    sql = "SELECT t.Timestamp, w1.Name AS Sender, w2.Name AS Receiver, t.Amount FROM `Wallet` w1, `Wallet` w2, `Transaction` t WHERE w1.id=t.senderID AND w2.id=t.receiverID AND (t.senderID='" + str(id) + "' OR t.receiverID='" + str(id) + "')"
    if(date != None):
        sql += " AND t.Timestamp > '" + date + "'"
    mycursor.execute(sql)
    transactions = mycursor.fetchall()
    return transactions
  


