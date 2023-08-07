import telebot
import openai
import gdown
import requests
import os
import tiktoken
from telebot import types
import sqlite3 as sl
import json
# from pydub import AudioSegment

openai.api_key = ''
bot = telebot.TeleBot("")
prompt_params = 'Насколько собеседники вежливы друг к другу? Представились ли они? Как им стоит вести себя по отношению друг к другу в будущем? Представился ли кто либо из собеседников ?Использовал ли кто либо из собеседников слова в уменьшительно-ласкательной форме ? Озвучил ли кто нибудь какой либо список услуг?Использовал ли кто либо оскорбления?Делал ли кто либо комплименты?'
conversation_mode = False
num_people = 2
nums = ['Оцени монолог.', 'Оцени разговор двух собеседников.', 'Оцени разговор трех собеседников.', 'Оцени разговор четырех собеседников.', 'Оцени разговор пяти собеседников.']
messages = []
tokenizer = tiktoken.encoding_for_model('gpt-3.5-turbo')
pinned = False
pinned_id = ''
# def long_files(file_path):
#     song = AudioSegment.from_mp3(file_path)
#     song[0:1000]
#     song.export(file_path, format='mp3', bitrate='32k')

def write_db(file_name, obj):
    with open(file_name, 'w') as file:
        json.dump(obj, file, indent=4)

def get_db(file_name):
    with open(file_name, 'r') as file:
        return json.load(file)
        
db = get_db('confs.json')

def allowed_users(user_id):
    with open(os.getcwd() + r'/' + 'admins.txt', 'r') as admins_log:
        admins = ''.join(admins_log.readlines())
    return True if str(user_id) in admins else False


def chat_with_gpt(prompt):

    model = 'gpt-3.5-turbo-16k'
    chat_parameters = {
        'model': model,
        'messages': [{'role': 'system', 'content': 'You are a helpful assistant'},
                     {'role': 'user', 'content': prompt}],
        'temperature': 0.5
    }

    response = openai.ChatCompletion.create(**chat_parameters)
    print(response)
    answer = response['choices'][0]['message']['content']

    return answer

def chat_with_gpt_memory(prompt):
    global messages
    if count_mem() >= 15000:
        messages = []
    save_user_messages(prompt)
    model = 'gpt-3.5-turbo-16k'
    chat_parameters = {
        'model': model,
        'messages': messages,
        'temperature': 0.5
    }

    response = openai.ChatCompletion.create(**chat_parameters)
    print(response)
    answer = response['choices'][0]['message']['content']
    save_asssistant(answer)

    return answer, 

def save_user_messages(prompt):
    global messages
    messages.append({'role':'user', 'content':prompt})

def save_asssistant(answer):
    global messages
    messages.append({'role':'user', 'content': answer})

def count_mem():
    global messages
    global tokenizer
    conversation_text = ''
    for elem in messages:
        conversation_text += ''.join(elem.values())
    return len(tokenizer.encode(conversation_text))



def audio_to_gpt(file_path, file_name):
    audio_file = open(file_path, 'rb')
    params = {
        'file': file_name,
        'model': 'whisper-1',
        'prompt': ''
    }
    transcript = openai.Audio.transcribe("whisper-1", audio_file)
    return transcript


def download_file(url):
    file_id = url.split('/')[-2]
    prefix = 'https://drive.google.com/uc?/export=download&id='
    return gdown.download(prefix + file_id)


def large_message(message, text):
    length = len(text)
    count = 0
    while length > (count + 1) * 4000:
        if (count + 1) * 4000 > length:
            bot.send_message(message.chat.id, text[count * 4000: length])
        else:
            bot.send_message(
                message.chat.id, text[count * 4000: (count + 1) * 4000])
        count += 1

def reply_to_user(message):
    global prompt_params
    prompt_params = message.text

def reply_to_change(message):
    global prompt_params
    bot.send_message(message.chat.id, "текущие параметры оценивания: \n" + prompt_params)

def reply_to_num(message):
    global num_people
    try:
        get_num = int(message.text)
        if(get_num in [1, 2, 3, 4, 5]):
            num_people = get_num
            bot.send_message(message.chat.id, "текущее количество собеседников " + str(num_people))
        else:
            bot.send_message(message.chat.id, "поддерживается количество собеседников до пяти человек\nвведите число от одного до пяти")

    except:
        bot.send_message(message.chat.id, "неверный формат записи количества говорящих")
def get_conf_num(message):
    global prompt_params
    global num_people
    try:
        prompt_params = db[str(message.from_user.id)]['prompts'][int(message.text)]
        num_people = db[str(message.from_user.id)]['nums'][int(message.text)]
    except:
        bot.send_message(message.chat.id, "ошибка")

markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
item1 = types.KeyboardButton("помощь")
item2 = types.KeyboardButton("параметры")
item3 = types.KeyboardButton("настройка промпта")
item4 = types.KeyboardButton("количество говорящих")
item5 = types.KeyboardButton("режим общения")
item6 = types.KeyboardButton("сохранить конфигурацию")
item7 = types.KeyboardButton("выбрать конфигурацию")
markup.add(item1)
markup.add(item2)
markup.add(item3)
markup.add(item4)
markup.add(item5)
markup.add(item6)
markup.add(item7)


@bot.message_handler(commands=["start"])
def start(m, res=False):
    bot.send_message(m.chat.id, "Бот создан для тестирования технологии оценки качества разговора сотрудника колл-центра с помощью gpt. для того чтобы провести оценку качества разговора сотрудника колл-центра с помощью нашего сервиса отправьте файл аудио с записью разговора", reply_markup=markup) if allowed_users(
        m.from_user.id) else bot.send_message(m.chat.id, "вам запрещен доступ")


@bot.message_handler(regexp=r"^(http|https)://\S{1,}")
def reg_answer(message):
    bot.send_message(message.chat.id, 'ссылка обрабатывается. ждите')
    file_name = download_file(message.text)
    # long_files(file_name)
    if file_name != None:
        answer = audio_to_gpt(file_name, file_name)
        os.remove(os.getcwd() + '\\' + file_name)
        if len(answer.text) < 4000:
            bot.send_message(message.chat.id, answer.text)
        else:
            large_message(message, answer.text)
        prompt = 'Раздели следующий диалог на фразы разных собеседников и перепиши :' + answer.text + \
            ".Затем оцени полученный разговор двух собеседников. Насколько они вежливы друг к другу? Представились ли они? Как им стоит вести себя по отношению друг к другу в будущем? Представился ли кто либо из собеседников ?Использовал ли кто либо из собеседников слова в уменьшительно-ласкательной форме ? Озвучил ли кто нибудь какой либо список услуг?Использовал ли кто либо оскорбления?Делал ли кто либо комплименты?"
        result = chat_with_gpt(prompt)
        if len(result) < 4000:
            bot.send_message(message.chat.id, result)
        else:
            large_message(message, result)


@bot.message_handler(content_types=['text'])
def answer(message):
    global prompt_params
    global conversation_mode
    global db
    global pinned
    global pinned_id

    if message.text == 'помощь':
        bot.send_message(message.chat.id, '1.проверьте формат документа(поддерживаются mp3, mp4, wav).2.проверьте размер и длительность отрывка который хотите оценить(размер не более 19 мегабайт, длительность 0-20 минут)', reply_markup=markup) if allowed_users(
            str(message.from_user.id)) else bot.send_message(message.chat.id, "вам запрещен доступ")
    elif 'настройка промпта' == message.text:
        bot.register_next_step_handler(message, reply_to_user)
        bot.register_next_step_handler(message, reply_to_change)
    elif message.text == 'параметры':
        bot.send_message(message.chat.id, prompt_params)
    elif message.text == 'количество говорящих':
        bot.register_next_step_handler(message, reply_to_num)
    elif message.text == "сохранить конфигурацию":
        if str(message.from_user.id) not in db.keys():
            db[str(str(message.from_user.id))] = {'prompts':[prompt_params], 'nums':[num_people]}
        else:
            db[str(message.from_user.id)]['prompts'].append(prompt_params)
            db[str(message.from_user.id)]['nums'].append(num_people)
        write_db('confs.json', db)
    elif message.text == 'выбрать конфигурацию':
        db = get_db('confs.json')
        for i in range(len(db[str(message.from_user.id)]['prompts'])):
            bot.send_message(message.chat.id, "параметры оценивания" + str(db[str(message.from_user.id)]['prompts']) + " .количество человек " + str(db[str(message.from_user.id)]['nums']) + "\nномер конфигурации " + str(i))
        bot.send_message(message.chat.id, "выберите нужную конфигурацию и введите ее номер")
        bot.register_next_step_handler(message, get_conf_num)
    elif message.text == 'режим общения':
        conversation_mode = not conversation_mode
        if conversation_mode and not pinned :
            pinned_id = bot.send_message(message.chat.id, 'режим общения включен').message_id
            bot.pin_chat_message(chat_id = message.chat.id, message_id = pinned_id)
        elif not conversation_mode and not pinned:
            pinned_id = bot.send_message(message.chat.id, 'режим общения выключен').message_id
            bot.pin_chat_message(chat_id = message.chat.id, message_id = pinned_id)
        
    elif conversation_mode:
        answer = chat_with_gpt_memory(message.text)
        bot.send_message(message.chat.id, answer)
        bot.send_message(message.chat.id, str(round(count_mem() / 150, 2)) + '%' + " памяти GPT занято")
    else:
        bot.send_message(message.chat.id, 'для того чтобы провести оценку качества разговора сотрудника колл-центра с помощью нашего сервиса отправьте файл аудио или видео с записью разговора. В случае возникновения проблем или несоответствующего ответа воспользуйтесь кнопкой помощь', reply_markup=markup) if allowed_users(
            str(message.from_user.id)) else bot.send_message(message.chat.id, "вам запрещен доступ")


@bot.message_handler(content_types=['video'])
def answer_video(message):
    global prompt_params
    bot.send_message(message.chat.id, 'видео транскрибируется',
                     reply_markup=markup)
    if (message.video.file_size >= 19000000):
        bot.send_message(
            message.chat.id, "файл слишком большой. скиньте ссылку на гугл диск")
        return None

    file_info = bot.get_file(message.video.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    src = os.getcwd() + '\\' + message.video.file_name
    print(src)
    with open(src, 'wb') as new_file:
        new_file.write(downloaded_file)
    print(file_info)

    bot.send_message(message.chat.id, "видео транскрибируется, ожидайте...")
    answer = audio_to_gpt(src, message.video.file_name)
    os.remove(src)
    bot.send_message(message.chat.id, "транскрибированный текст:")
    if len(answer.text) < 4000:
        bot.send_message(message.chat.id, answer.text)
    else:
        large_message(message, answer.text)
    bot.send_message(
        message.chat.id, "текст обрабатывает chatGPT, ожидайте...")
    prompt = 'Раздели следующий диалог на фразы разных собеседников и перепиши ' + answer.text
    result = chat_with_gpt(prompt)
    if len(result) < 4000:
        bot.send_message(message.chat.id, result)
    else:
        large_message(message, result)
    bot.send_message(message.chat.id, 'разговор оценивается chatGPT')
    # prompt_params для установки пользовательских параметров оценивания
    prompt = nums[num_people] + prompt_params + result
    result = chat_with_gpt(prompt)
    if len(result) < 4000:
        bot.send_message(message.chat.id, result)
    else:
        large_message(message, result)


@bot.message_handler(content_types=['audio'])
def answer_audio(message):
    global prompt_params
    print("something requested")
    if (message.audio.file_size >= 19000000):
        bot.send_message(
            message.chat.id, "файл слишком большой. скиньте ссылку на гугл диск")
        return None

    file_info = bot.get_file(message.audio.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    src = os.getcwd() + '\\' + message.audio.file_name
    print(src)
    with open(src, 'wb') as new_file:
        new_file.write(downloaded_file)
    print(file_info)
    # long_files(src)
    bot.send_message(
        message.chat.id, "аудио транскрибируется, ожидайте...", reply_markup=markup)
    answer = audio_to_gpt(src, message.audio.file_name)
    os.remove(src)
    # diarization = chat_with_gpt(
    #     'Раздели следующий диалог на фразы разных собеседников и перепиши :' + answer.text)
    # bot.send_message(message.chat.id, diarization)
    bot.send_message(message.chat.id, "транскрибированный текст:")
    if len(answer.text) < 4000:
        bot.send_message(message.chat.id, answer.text)
    else:
        large_message(message, answer.text)
    bot.send_message(
        message.chat.id, "текст обрабатывает chatGPT, ожидайте...")
    prompt = 'Раздели следующий диалог на фразы разных собеседников и перепиши ' + answer.text
    result = chat_with_gpt(prompt)
    # bot.send_message(message.chat.id, result)
    if len(result) < 4000:
        bot.send_message(message.chat.id, result)
    else:
        large_message(message, result)
    bot.send_message(message.chat.id, 'разговор оценивается chatGPT')
    # prompt_params для установки пользовательских параметров оценивания
    prompt = nums[num_people - 1] + prompt_params + result
    result = chat_with_gpt(prompt)
    if len(result) < 4000:
        bot.send_message(message.chat.id, result)
    else:
        large_message(message, result)


bot.polling(none_stop=True, interval=0)
