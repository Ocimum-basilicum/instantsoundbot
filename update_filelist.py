import redis
import telepot
import base64
from os import listdir, path

r = redis.StrictRedis(host='127.2.73.2', port=16379, db=0, password="ZTNiMGM0NDI5OGZjMWMxNDlhZmJmNGM4OTk2ZmI5")

# absolute dir the script is in
script_dir = path.dirname(__file__)
#file_list from directory sounds/
sounds_dir = path.join(script_dir, "sounds")
file_list = listdir(sounds_dir)

#flushed DB, cleanup before renewing, only needed in special cases
# def flushDB():
#      r.flushdb()
#      print "--- DB FLUSHED ----"


#creates a set with all filenames
def createFile_Set():
    #gets the file_list from redis set
    file_set = r.smembers("file_list")

    #removes the "old sound"
    file_set_new = r.smembers("file_list_new")
    for i in file_set_new:
        r.srem("file_list_new", i)

    #creates a set "file_list_new" with all newly added sounds
    for i in file_list:
        if i not in file_set:
            r.sadd("file_list_new", i)
    print r.smembers("file_list_new")


    #adds all files from folder /sounds
    for i in file_list:
        r.sadd("file_list", i)
    print r.smembers("file_list")


#creates a set with filenames for all files who start with X
def createFile_Setx():
    for i in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
              'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']:
        files_with_x = [f for f in listdir(sounds_dir) if f[0] == i]
        for j in files_with_x:
            r.sadd("sounds:"+i, j)

        print r.smembers("sounds:"+i)


#this function can be called at "/fileIDList", it generates a datastore mapping "filename"-->"file_id"
#it sends all sounds to my ID (10760033), out of the response it gets the file_id
def createFileID_store():
    TOKEN = base64.b64decode("MjA5Mjk0MDAyOkFBRjA4bUV4YWwxRVpfMHBUdXFSWFpVWnk0dmhTQWJTTUhZ")
    bot = telepot.Bot(TOKEN)

    for i in file_list:
        #builds path to file
        file_path = path.join(script_dir, "sounds/"+i)
        #opens file
        music_file = open(file_path, 'rb')

        response = bot.sendVoice(10760033, music_file)
        r.set(i, response["voice"]["file_id"])
        print r.get(i)
