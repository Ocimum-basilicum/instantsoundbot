import redis
import telepot
import base64
from random import shuffle
from os import listdir, path, environ

REDIS_PW = environ['REDISPW']
r = redis.StrictRedis(host='172.30.28.75', port=6379, db=0, password=REDIS_PW)

# absolute dir the script is in
script_dir = path.dirname(__file__)
#file_list from directory sounds/
sounds_dir = path.join(script_dir, "sounds")
file_list = listdir(sounds_dir)

#flushed DB, cleanup before renewing, only needed in special cases
#def flushDB():
#    r.flushdb()
#    print "--- DB FLUSHED ----"

#this function can be called at "/updateFilelist"
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


#this function can be called at "/updateFilelist"
#creates a set with filenames for all files who start with X
def createFile_Setx():
    for i in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
              'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']:
        files_with_x = [f for f in listdir(sounds_dir) if f[0] == i]
        for j in files_with_x:
            r.sadd("sounds:"+i, j)

        print r.smembers("sounds:"+i)



#this function can be called at "/updateFilelist", it generates a datastore mapping "filename"-->"file_id"
#it sends all new sounds to my ID (10760033), out of the response it gets the file_id
def createFileID_store():
    TOKEN = environ['TOKEN']
    bot = telepot.Bot(TOKEN)

    file_list_new = r.smembers("file_list_new")

    #loops over all new files and sends each file to my ID
    for i in file_list_new:

        #builds path to file
        file_path = path.join(script_dir, "sounds/"+i)
        #opens file
        music_file = open(file_path, 'rb')

        response = bot.sendVoice(10760033, music_file)
        r.set(i, response["voice"]["file_id"])
        print "New - filename: %s file_id: %s" % (i, r.get(i))



#creates a entry (key: inline_results) in datastore with 50  sounds in the 'list[{dict}]' inline results format
def create_default_inline_results():

    #shuffles the results so they are not always the same
    shuffle(file_list)

    count = 0
    default_sounds_list = []
    for i in file_list:
        if count == 49:
            break
        sound = {
            'type': 'voice',
            'id': str(count),
            'title': i[:-4],
            'voice_file_id': r.get(i)
        }
        count += 1
        default_sounds_list.append(sound)

    #stores the list at key 'inline_results'
    r.set("inline_results", default_sounds_list)


def create_x_inline_results():
    #inline results for starting character "inline_results:a", "inline_results:b" etc.
    for i in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
              'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']:
        inline_results_with_x = r.smembers("sounds:"+i)
        count = 0
        x_sounds_list = []
        for j in inline_results_with_x:
            if count == 49:
                break
            sound = {
                'type': 'voice',
                'id': str(count),
                'title': j[:-4],
                'voice_file_id': r.get(j)
            }
            count += 1
            x_sounds_list.append(sound)

        r.set("inline_results:"+i, x_sounds_list)
        print "Key: "+i, r.get("inline_results:"+i)
