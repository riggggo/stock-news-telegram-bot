import json
import time
import requests
import os
import datetime as dt
import stock_news

MY_BOT_TOKEN = os.environ.get("MY_BOT_TOKEN")
# use 'export MY_BOT_TOKEN=...' to create your token environment variable
request_url = f"https://api.telegram.org/bot{MY_BOT_TOKEN}/getUpdates"
send_url = f"https://api.telegram.org/bot{MY_BOT_TOKEN}/sendMessage"
last_message_id = -1
chat_ids = []
company_names = []
GREETINGS = ["hallo", "hello", "hi", "hey", "moin", "servus"]
COMMAND_LIST = ["/add", "/remove", "/list"]


def set_up():
    global last_message_id
    data = {
        "last_message_id": -1
    }
    try:
        with open("data.json", mode="r") as data_file:
            data = json.load(data_file)
            if "last_message_id" in list(data.keys()):
                last_message_id = data.get("last_message_id")
    except (json.decoder.JSONDecodeError, FileNotFoundError) as e:
        open("data.json", mode="a")
    finally:
        with open(file="data.json", mode="w") as data_file:
            json.dump(data, data_file, indent=4)


def get_data():
    data = requests.get(url=request_url)
    data.raise_for_status()
    return data.json().get("result")


def get_message_id(data, i):
    if len(data) < abs(i):
        return -1
    message = data[i].get("message")
    if message is not None:
        return message.get("message_id")
    else:
        return -1


def get_message(data, i):
    message = data[i].get("message").get("text")
    message_from = data[i].get("message").get("from").get("first_name")
    chat_id = str(data[i].get("message").get("chat").get("id"))
    if chat_id not in chat_ids:
        new_conversation = {
            chat_id: {
                "companies": [],
                "add_mode": False,
                "remove_mode": False
            }
        }
        try:
            with open("data.json", mode="r") as data_file:
                message_data = json.load(data_file)
                if chat_id not in list(message_data.keys()):
                    message_data[chat_id] = new_conversation.get(chat_id)
        except (json.decoder.JSONDecodeError, FileNotFoundError) as e:
            print(e)
            open("data.json", mode="a")
            message_data = new_conversation
        finally:
            with open(file="data.json", mode="w") as data_file:
                json.dump(message_data, data_file, indent=4)
            chat_ids.append(chat_id)
    return message, message_from, chat_id


def add_company_name(company_name, chat_id):
    try:
        with open("data.json", mode="r") as data_file:
            data = json.load(data_file)
            company_name_list = data.get(chat_id).get("companies")
            if company_name not in company_name_list:
                company_name_list.append(company_name)
                data.get(chat_id)["companies"] = company_name_list
            else:
                return f"You already added {company_name}."
        with open("data.json", mode="w") as data_file:
            json.dump(data, data_file, indent=4)
        company_names.append(company_name)
        return f"Congratulations! You will receive every evening news about \"{company_name}\"."
    except (json.decoder.JSONDecodeError, FileNotFoundError) as e:
        return f"Something went wrong :( (\"{print(e)}\"."


def remove_company_name(company_name, chat_id):
    try:
        with open("data.json", mode="r") as data_file:
            data = json.load(data_file)
            company_name_list = data.get(chat_id).get("companies")
        if company_name in company_name_list:
            company_name_list.remove(company_name)
            data.get(chat_id)["companies"] = company_name_list
            with open("data.json", mode="w") as data_file:
                json.dump(data, data_file, indent=4)
            if len(company_name_list) == 0:
                return "You won't receive news messages any more."
            return f"You will not longer receive news about \"{company_name}\"."
        else:
            if len(company_name_list) == 0:
                return f"You never added {company_name}."
            return f"Can´t find \"{company_name}\" in {company_name_list}. Please check if \"{company_name}\" is spelled correctly."

    except (json.decoder.JSONDecodeError, FileNotFoundError) as e:
        return f"Something went wrong :( (\"{print(e)}\")."


def set_mode(mode, value, chat_id):
    try:
        with open("data.json", mode="r") as data_file:
            message_data = json.load(data_file)
            message_data.get(chat_id)[mode] = value
        with open("data.json", mode="w") as data_file:
            json.dump(message_data, data_file, indent=4)
    except (json.decoder.JSONDecodeError, FileNotFoundError) as e:
        sending_messages(message=f"Something went wrong :( (\"{print(e)}\".",
                         chat_id=chat_id)


def bot_answer(message_list):
    message = message_list[0].title()
    command_string = "\n".join(COMMAND_LIST)
    chat_id = message_list[2]
    if message.lower() in GREETINGS or message.lower() == "/start":
        sending_messages(message=f"Moin {message_list[1].title()}", chat_id=chat_id)
        sending_messages(
            message=f"Use the following commands to setup your stock news notifications:\n{command_string}",
            chat_id=chat_id)
    elif message.lower() == COMMAND_LIST[0]:  # add
        sending_messages(message=f"Please enter a company name to receive daily news: (e.g. \"Apple or \"Tesla\")",
                         chat_id=chat_id)
        set_mode("add_mode", True, chat_id)
        set_mode("remove_mode", False, chat_id)
    elif message.lower() == COMMAND_LIST[1]:  # remove
        sending_messages(message=f"Please enter a company name to stop getting news about it: ", chat_id=chat_id)
        set_mode("add_mode", False, chat_id)
        set_mode("remove_mode", True, chat_id)
    elif message.lower() == COMMAND_LIST[2]:    # list
        try:
            with open("data.json", mode="r") as data_file:
                message_data = json.load(data_file)
                companies = message_data.get(chat_id).get("companies")
        except (json.decoder.JSONDecodeError, FileNotFoundError) as e:
            sending_messages(message=f"Something went wrong :( (\"{print(e)}\".",
                             chat_id=chat_id)
        else:
            sending_messages(message=f"You will receive news about the following companies: {companies}",
                             chat_id=chat_id)
    else:
        message = message.title()
        try:
            with open("data.json", mode="r") as data_file:
                message_data = json.load(data_file)
                add_mode = message_data.get(chat_id).get("add_mode")
                remove_mode = message_data.get(chat_id).get("remove_mode")
        except (json.decoder.JSONDecodeError, FileNotFoundError) as e:
            sending_messages(message=f"Something went wrong :( (\"{print(e)}\".",
                             chat_id=chat_id)
        if add_mode:
            answer = add_company_name(message, chat_id)
            sending_messages(message=answer, chat_id=chat_id)
            set_mode("add_mode", False, chat_id)
        elif remove_mode:
            answer = remove_company_name(message, chat_id)
            sending_messages(message=answer, chat_id=chat_id)
            set_mode("remove_mode", False, chat_id)
        else:
            sending_messages(
                message=f"Use the following commands to setup your stock news notifications:\n{command_string}",
                chat_id=message_list[2])


def sending_messages(chat_id, message):
    parameter = {
        "chat_id": chat_id,
        "text": message
    }
    requests.post(url=send_url, params=parameter)


def send_news():
    try:
        with open("data.json", mode="r") as data_file:
            data = json.load(data_file)
            all_chats = list(data.keys())
            all_chats.remove("last_message_id")
            for chat_id in all_chats:
                company_list = data.get(chat_id).get("companies")
                message_list = []
                for company in company_list:
                    message_list.append(stock_news.get_all_data(company))
                message = "\n\n".join(message_list)
                print(message)
                sending_messages(
                    message=message,
                    chat_id=chat_id)
    except (json.decoder.JSONDecodeError, FileNotFoundError) as e:
        print(f"Something went wrong :( (\"{print(e)}\").")


def answer_all_new_messages():
    global last_message_id
    current_message_id = get_message_id(received_data, -1)
    if last_message_id == current_message_id or current_message_id == -1:
        pass
    else:
        message_info_list_to_answer = []
        index = -1
        current_message_id = get_message_id(received_data, index)
        tmp = current_message_id
        try:
            with open("data.json", mode="r") as all_data:
                stored_data = json.load(all_data)
                stored_data["last_message_id"] = current_message_id
        except (json.decoder.JSONDecodeError, FileNotFoundError) as e:
            print(e)
        finally:
            with open(file="data.json", mode="w") as all_data:
                json.dump(stored_data, all_data, indent=4)
        while True:
            message_info = get_message(received_data, index)
            message_info_list_to_answer.append(message_info)
            index -= 1
            current_message_id = get_message_id(received_data, index)
            if current_message_id == -1 or current_message_id == last_message_id:
                last_message_id = tmp
                break
        message_info_list_to_answer = message_info_list_to_answer[::-1]
        for message_info in message_info_list_to_answer:
            bot_answer(message_info)


daily_news_sent = False
set_up()
while True:
    current_time = dt.datetime.now().hour
    if not daily_news_sent:
        if current_time == 17:
            send_news()
            daily_news_sent = True
    if current_time == 0:
        daily_news_sent = False
    received_data = get_data()
    answer_all_new_messages()
    time.sleep(1)
