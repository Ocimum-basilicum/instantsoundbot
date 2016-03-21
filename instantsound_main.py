from flask import Flask, request
import telepot
import base64
import random
import redis
from update_filelist import createFile_Set, createFile_Setx
from os import listdir, path
from Queue import Queue
app = Flask(__name__)

r = redis.StrictRedis(host='127.2.73.2', port=16379, db=0, password="ZTNiMGM0NDI5OGZjMWMxNDlhZmJmNGM4OTk2ZmI5")



def on_chat_message(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    msg_text = msg['text']
    print 'Chat Message:', msg

    # absolute dir the script is in
    script_dir = path.dirname(__file__)
    #directory /sounds
    sounds_dir = path.join(script_dir, "sounds")


    #gets the file_list from redis set
    file_set = r.smembers("file_list")


    if content_type != "text":
        pass

    ### /get command ###
    #sends file with given filename
    elif msg_text.startswith("/get"):
        #gets the filename
        file_name = msg_text[5:]+".mp4"

        #checks if file is the directory/exists
        if file_name in file_set:
            #builds path to file
            rel_path = "sounds/"+file_name
            abs_file_path = path.join(script_dir, rel_path)

            #opens file
            music_file = open(abs_file_path, 'rb')

            #gets message_id for the reply title
            msg_id = msg['message_id']

            #sends it as voice message with reply (used as "title")
            bot.sendChatAction(chat_id, "upload_audio")
            bot.sendVoice(chat_id, music_file, reply_to_message_id=msg_id)

        else:
            bot.sendChatAction(chat_id, "typing")
            bot.sendMessage(chat_id, "404, file _"+file_name[:-4]+"_ not found.\nDid you mean xy.mp4? WIP", parse_mode="Markdown")


    ### /random command ###
    #sends random soundfile from /sounds
    elif msg_text.startswith("/random"):

        #gets random number out length from file_list
        rnd_num_filelist = random.randrange(0,len(file_set))
        rnd_file= file_set[rnd_num_filelist]

        #builds path to file
        abs_file_path = path.join(script_dir, "sounds/"+rnd_file)

        #opens file
        music_file = open(abs_file_path, 'rb')

        #gets message_id
        msg_id = msg['message_id']

        #sends it as voice message
        bot.sendChatAction(chat_id, "typing")
        bot.sendMessage(chat_id,  rnd_file[:-4])
        bot.sendChatAction(chat_id, "upload_audio")
        bot.sendVoice(chat_id, music_file)


    ### /help command ###
    #sends /help and /Start message
    elif (msg_text[:5] == "/help") or (msg_text[:6] == "/start"):

        bot.sendMessage(chat_id,
                        "*--- Instant Sound Bot ---*\n"
                        "*Use the following commands:*\n"
                        "\n"
                        "`/get [file_name]`\n"
                        "--> eg. '`/get badumtss`'\n"
                        "\n"
                        "`/search [keyword]` \n"
                        "--> search for a sound\n"
                        "\n"
                        "`/random`\n"
                        "--> sends random sound\n "
                        "\n"
                        "`/list A` \n"
                        "--> lists all sounds who start with a",
                        parse_mode="Markdown")


    ### /list command ###
    #lists all sounds who start with [x]
    elif (msg_text[:5] == "/list"):
        #gets the key letter "/list [key]"
        key_letter = msg_text[6:8].lower()

        #pics all sounds who start with [x]
        #file_list = [f for f in file_set if f[0] == key_letter]
        file_set = r.smembers("sounds:"+key_letter)

        #checks if keyletter is specified
        if key_letter:

            #formats the file list
            string_x = ""
            for i in file_set:
                string_x = string_x + i[:-4] + "\n"

            #if no file is found
            if not string_x:
                string_x = "No files with _"+key_letter+"_ found"

            #sends out the string "sound1.mp4 \n sound2.mp4 \n....."
            bot.sendChatAction(chat_id, "typing")
            bot.sendMessage(chat_id, string_x, parse_mode="Markdown")

        #sends message for input without character
        else:
            bot.sendChatAction(chat_id, "typing")
            bot.sendMessage(chat_id, "You need to specify a character\ne.g. `'/list a'`", parse_mode="Markdown")





# def on_inline_query(msg):
#     query_id, from_id, query_string = telepot.glance(msg, flavor='inline_query')
#     print 'Inline Query:', msg
#
#
#     # Compose your own answers
#     articles = [{'type': 'article',
#                     'id': '1', 'title': 'Badumtss', 'message_text': '/get@instantsoundbot badumtss'}]
#
#     bot.answerInlineQuery(query_id, articles)
#
#
#
# def on_chosen_inline_result(msg):
#     result_id, from_id, query_string = telepot.glance(msg, flavor='chosen_inline_result')
#     print 'Chosen Inline Result:', result_id, from_id, query_string





TOKEN = base64.b64decode("MjA5Mjk0MDAyOkFBRjA4bUV4YWwxRVpfMHBUdXFSWFpVWnk0dmhTQWJTTUhZ")

#Flask routing and passing the POST to the queue test
app = Flask(__name__)
bot = telepot.Bot(TOKEN)
update_queue = Queue()  # channel between `app` and `bot`

bot.notifyOnMessage({'normal': on_chat_message}, source=update_queue) # take updates from queue



@app.route('/'+TOKEN, methods=['GET', 'POST'])
def pass_update():
    update_queue.put(request.data)  # pass update to bot
    return 'OK'

@app.route('/updateFilelist', methods=['GET'])
def start_filelist_update():
    createFile_Set() #creates the file_set --> see update_filelist.py
    createFile_Setx() #creates sets for all starting letters --> see update_filelist.py
    return 'OK'



if __name__ == '__main__':
    app.run()