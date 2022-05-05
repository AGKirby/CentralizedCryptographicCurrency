import datetime

def writeLog(content = "Complete", newLine = False):
    try: 
        f = open("logs.txt", "a")
        start = " "
        if(newLine):
            timestamp = datetime.datetime.now()
            start = "\n" + str(timestamp) + " "
        f.write(start + str(content))
        f.close()
    except Exception as e: 
        f = open("logs.txt", "a")
        f.write(" Error Writing Log: " + str(e))
        f.close()
      