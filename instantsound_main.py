from flask import Flask, request, render_template
import telepot
import base64
import redis
import os
from ast import literal_eval
from update_filelist import *
from statistics import get_stats, write_user_stats, write_sound_stats
from Queue import Queue

app = Flask(__name__)


REDIS_PW = os.environ['REDISPW']
r = redis.StrictRedis(host='172.30.28.75', port=6379, db=0, password=REDIS_PW)

##
### normal bot-chat handling ###
##
def on_chat_message(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)

    #only process if the message is a text message
    if content_type == "text":

        #gets the file_list from redis set
        file_set = r.smembers("file_list")

        msg_text = msg['text']

        ### /get command ###
        #sends file with given filename
        if (msg_text.startswith("/get")):
            #gets the filename
            file_name = msg_text[5:]+".ogg"

            #checks if file is in the file_set/exists
            if file_name in file_set:

                #gets message_id for the reply title
                msg_id = msg['message_id']

                #sends it as voice message with reply (used as "title")
                bot.sendChatAction(chat_id, "upload_audio")
                #send the file by using its file_id
                bot.sendVoice(chat_id, r.get(file_name), reply_to_message_id=msg_id)
                write_sound_stats(file_name)

            #if file doesn't exist this will send a message and suggestions if the string is <=3
            else:
                #checks if input is more than >= 3
                if len(file_name[:-4]) >= 3:
                    #filters the file_set for matching strings
                    result = filter(lambda x: file_name[:-4] in x, file_set)

                    #if results are found, format them
                    if result:
                        suggestions = ""
                        #formats the found results
                        for i in result:
                            suggestions = suggestions + i[:-4] + "\n"
                        suggestions = "\nDid you mean: \n" + suggestions
                    #no results = sorry message
                    else:
                        suggestions = "\nSorry no suggestions available"

                    bot.sendChatAction(chat_id, "typing")
                    bot.sendMessage(chat_id, "`404`\nSound *"+file_name[:-4]+"* not found."+suggestions,
                                    parse_mode="Markdown")

                #sends 404 and search / list help
                else:
                    bot.sendChatAction(chat_id, "typing")
                    bot.sendMessage(chat_id, "`404`\nSound *"+file_name[:-4]+"* not found.\n Try `/search [xx...]` or `/list [x]`" ,
                                    parse_mode="Markdown")


        ### /search command ###
        #searchs for string in all filenames
        elif (msg_text.startswith("/search")):

            key_word = msg_text[8:].lower()

            #checks if input is more than >= 2
            if len(key_word) >= 2 and key_word.isalpha():
                #filters the file_set for matching strings
                result = filter(lambda x: key_word in x, file_set)

                #if results are found, format them
                if result:
                    suggestions = ""
                    #formats the found results
                    for i in result:
                        suggestions = suggestions + i[:-4] + "\n"

                #no results =  No results found add 3 random suggestions
                else:
                    #todo dont show duplicate results
                    suggestions = "No search results found! \n*Recommendations:*\n"\
                                  + r.srandmember("sounds:"+key_word[0])[:-4]+"\n" \
                                  + r.srandmember("sounds:"+key_word[0])[:-4]+"\n" \
                                  + r.srandmember("sounds:"+key_word[1])[:-4]
                bot.sendChatAction(chat_id, "typing")
                bot.sendMessage(chat_id, "*Results:*\n"+suggestions,
                                    parse_mode="Markdown")

            #sends
            else:
                bot.sendChatAction(chat_id, "typing")
                bot.sendMessage(chat_id, "Please type 2 or more characters\nOr try `/list [x]`",
                                    parse_mode="Markdown")

        ### /random command ###
        #sends random soundfile from /sounds
        #also shuffles the default inline results
        elif msg_text.startswith("/random"):

            #gets random number out length from file_list
            rnd_file = r.srandmember("file_list")

            #sends it as voice message
            bot.sendChatAction(chat_id, "typing")
            bot.sendMessage(chat_id,  rnd_file[:-4])
            bot.sendChatAction(chat_id, "upload_audio")
            bot.sendVoice(chat_id, r.get(rnd_file))
            write_sound_stats(rnd_file)


            #shuffles the default_inline_results
            create_default_inline_results()


        ### /help + /start command ###
        #sends /help and /start message
        elif (msg_text.startswith("/help")) or (msg_text.startswith("/start")):

            #inline help triggered by clicking on the "no sound found! click here for help" button
            if msg_text == "/start inline_help":
                bot.sendMessage(chat_id,
                            "*--- Inline help ---*\n"
                            "You can use two methods inline:\n"
                            "\n"
                            "*Single character:*\n"
                            "  `x` --> shows you all sounds starting with this character\n"
                            "\n"
                            "*Search (2 or more characters):*\n"
                            "  `cat` --> searches for 'cat'\n"
                            "\n"
                            "[Please rate this bot! Click here](telegram.me/storebot?start=instantsoundbot)\n"
                            "\n"
                            "[For support or sound requests! Click here](https://telegram.me/instantsoundbot_support)",
                            disable_web_page_preview=True,
                            parse_mode="Markdown")

            #normal /help and /start message
            else:
                bot.sendMessage(chat_id,
                                "*--- Instant Sound Bot ---*\n"
                                "*Use the following commands:*\n"
                                "\n"
                                "`/get [file_name]`\n"
                                "--> eg. '`/get badumtss`'\n"
                                "\n"
                                "`/search [keyword]` \n"
                                "--> search for a sound\n"
                                "--> requires at least 2 characters\n"
                                "\n"
                                "`/random`\n"
                                "--> sends random sound\n "
                                "\n"
                                "`/list [x]` \n"
                                "--> eg. '`/list a`'\n"
                                "--> lists all sounds who start with a\n"
                                "\n"
                                "`/new` \n"
                                "--> shows all new sounds"
                                "\n"
                                "[Please rate this bot! Click here](telegram.me/storebot?start=instantsoundbot)\n"
                                "\n"
                                "[For support or sound requests! Click here](https://telegram.me/instantsoundbot_support)",
                                disable_web_page_preview=True,
                                parse_mode="Markdown")

        ### /list command ###
        #lists all sounds who start with [x]
        elif (msg_text.startswith("/list")):
            #gets the key letter "/list [key]"
            key_letter = msg_text[6:7].lower()

            #pics all sounds who start with [x]
            file_set = r.smembers("sounds:"+key_letter)

            #checks if keyletter is specified
            if key_letter and key_letter.isalpha():

                #formats the file list
                string_x = ""
                for i in file_set:
                    string_x = string_x + i[:-4] + "\n"

                #if no file is found
                if not string_x:
                    string_x = "No files with *"+key_letter+"* found"

                #sends out the string "sound1.ogg \n sound2.ogg \n....."
                bot.sendChatAction(chat_id, "typing")
                bot.sendMessage(chat_id, string_x, parse_mode="Markdown")

            #sends message for input without character
            else:
                bot.sendChatAction(chat_id, "typing")
                bot.sendMessage(chat_id, "You need to specify a character\ne.g. `'/list a'`", parse_mode="Markdown")


        ### /new command ###
        #lists all new sounds
        elif (msg_text.startswith("/new")):
            #gets the new sounds out of datastore
            file_set_new = r.smembers("file_list_new")

            #only if file_set_new has content
            if file_set_new:
                #formats the file list
                new_sounds = ""
                for i in file_set_new:
                    new_sounds = new_sounds + i[:-4] + "\n"

                #sends out the string "sound1.ogg \n sound2.ogg \n....."
                bot.sendChatAction(chat_id, "typing")
                bot.sendMessage(chat_id, new_sounds, parse_mode="Markdown")
            else:
                #sends nothing new
                bot.sendChatAction(chat_id, "typing")
                bot.sendMessage(chat_id, "Nothing new!")


        #prints chat message for debuging
        print 'Chat Message:', msg
        #writes user stats
        write_user_stats(chat_id)

    else:
        pass


##
### inline query handling ###
##
def on_inline_query(msg):
    query_id, from_id, query_string = telepot.glance(msg, flavor='inline_query')

    query_string = query_string.lower()

    #if query_string is empty
    if query_string == "":
        #gets the 50 random results from datastore and evals it to list[dict]
        default_sounds_list = literal_eval(r.get('inline_results'))
        bot.answerInlineQuery(query_id, default_sounds_list)

    #if only one character is given, send all sounds starting with this character
    elif len(query_string) == 1 and query_string.isalpha():
        #gets all starting with x from datastore and evals it to list[dict]
        x_sounds_list = literal_eval(r.get("inline_results:"+query_string))

        bot.answerInlineQuery(query_id, x_sounds_list)

    #checks if input is more than >= 2
    elif len(query_string) >= 2:
        #gets the file_list from redis set
        file_set = r.smembers("file_list")

        #deletes the sounds_list for results
        sounds_list = []
        #filters the file_set for matching strings
        result = filter(lambda x: query_string in x, file_set)

        if result:
            count = 0
            for i in result:
                if count == 49:
                    break
                sound = {
                    'type': 'voice',
                    'id': str(count),
                    'title': i[:-4],
                    'voice_file_id': r.get(i)
                }
                count += 1
                sounds_list.append(sound)

            bot.answerInlineQuery(query_id, sounds_list)

        else:
            bot.answerInlineQuery(query_id, '[]',
                                  switch_pm_text="No sound found! Click/tap here for help",
                                  switch_pm_parameter="inline_help")

    #else for untypical inputs (special character $?/"%& etc.)
    else:
        bot.answerInlineQuery(query_id, '[]',
                                  switch_pm_text="No sound found! Click/tap here for help",
                                  switch_pm_parameter="inline_help")


    ## format needed
    # sounds_list = [{'type': 'voice', 'id': '1', 'title': 'murloc', 'voice_file_id': 'AwADBAADhAoAArKSeQygPJb0M8dBLAI'},
    #           {'type': 'voice', 'id': '2', 'title': 'fuckyou', 'voice_file_id': 'AwADBAADhQoAArKSeQz7Px6ofuqq6gI'}]



#todo sound stats? Filename needed!...
def on_chosen_inline_result(msg):
    result_id, from_id, query_string = telepot.glance(msg, flavor='chosen_inline_result')
    write_user_stats(from_id)
    #Workaround...
    write_sound_stats("inline_sound.ogg")

    print 'Inline Feedback:', msg


TOKEN = os.environ['TOKEN']

#Flask routing and passing the POST to the queue test
app = Flask(__name__)
bot = telepot.Bot(TOKEN)
update_queue = Queue()  # channel between `app` and `bot`

bot.message_loop({'chat': on_chat_message,
                  'inline_query': on_inline_query,
                  'chosen_inline_result': on_chosen_inline_result}, source=update_queue) # take updates from queue



@app.route('/'+TOKEN, methods=['GET', 'POST'])
def pass_update():
    update_queue.put(request.data)  # pass update to bot
    return 'OK'

@app.route('/updateFilelist', methods=['GET'])
def start_filelist_update():
    createFile_Set() #creates the file_set --> see update_filelist.py
    createFile_Setx() #creates sets for all starting letters --> see update_filelist.py
    createFileID_store() #creates data store with filenames and file_id
    create_default_inline_results() #create 50 default inline results
    create_x_inline_results() #creates <=50 inline results starting with char x
    return 'OK'

@app.route('/stats', methods=['GET'])
def show_stats():
    stats, date_list, daily_requests, sound_stats = get_stats() #gets the values from statistics.py
    return render_template('stats.html', **locals())


if __name__ == '__main__':
    app.run()