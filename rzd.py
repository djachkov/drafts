import logging
import sqlite3

import requests
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    Filters,
)

directions = {
    "Московское": [],
    "Витебское": [],
    "Выборгское": [],
    "Балтийское и Варшавское": [],
    "Волховстроевское": [],
    "Приозерское": [],
    "Ладожское (Ириновское)": [],
}
DIRECTION = ""
STATION_1 = ""
STATION_2 = ""


def start(update, context):
    db = sqlite3.connect("test.db")
    db.execute("""DROP TABLE test""")
    db.execute(
        """CREATE TABLE test
                    (user integer, st1 text, st2 text)"""
    )
    user = (update.effective_user.id,)
    users = []
    for user in db.execute("SELECT * FROM test WHERE user=?", user):
        users.append(user)
    if not users:
        return settings(update, context)


def settings(update, context):
    print("running settings")
    db = sqlite3.connect("test.db")
    user = (update.effective_user.id,)
    api_key = "API_KEY"
    data = requests.get(
        f"https://api.rasp.yandex.net/v3.0/stations_list/?apikey={api_key}&lang=ru_RU&format=json"
    )

    for country in data.json()["countries"]:

        if country["title"] == "Россия":
            for region in country["regions"]:
                if region["title"] == "Санкт-Петербург и Ленинградская область":
                    for city in region["settlements"]:
                        for station in city["stations"]:
                            if station["direction"] in directions:
                                directions[station["direction"]].append(
                                    (station["title"], station["codes"]["yandex_code"])
                                )
    keyboard = [[direction] for direction in directions]
    update.message.reply_text(
        text="Select direction", reply_markup=ReplyKeyboardMarkup(keyboard)
    )
    # uid = (update.from.id,)
    # db.execute("SELECT * FROM test WHERE user=?", uid)
    # print(db.fetchone())
    # print(uid)
    return CHOOSING


def choose_station1(update, context):
    global DIRECTION, STATION_2, STATION_1
    DIRECTION = update.message.text
    keyboard = [[station[0]] for station in directions[DIRECTION]]
    update.message.reply_text(
        "Укажите станцию", reply_markup=ReplyKeyboardMarkup(keyboard)
    )
    return TYPING_CHOICE


def choose_station2(update, context):
    global DIRECTION, STATION_2, STATION_1
    STATION_1 = update.message.text
    keyboard = [[station[0]] for station in directions[DIRECTION]]
    update.message.reply_text(
        "Укажите станцию", reply_markup=ReplyKeyboardMarkup(keyboard)
    )
    return TYPING_REPLY


def save_settings(update, context):
    global DIRECTION, STATION_2, STATION_1
    STATION_2 = update.message.text
    db = sqlite3.connect("test.db")
    user = update.effective_user.id
    db.execute("INSERT INTO test VALUES (?,?,?)", (user, STATION_1, STATION_2))
    for user in db.execute("SELECT * FROM test WHERE user=?", (user,)):
        print(user)
    update.message.reply_text("Настройки сохранены", reply_markup=ReplyKeyboardRemove())


# station_map = {
#     "s9602494": "Московский вокзал",
#     "s9602496": "Витебский вокзал",
#     "s9602497": "Финляндский вокзал",
#     "s9602498": "Балтийский вокзал",
#     "s9602499": "Ладожский вокзал",
# }

#

#

keyboard = [["Настройки"], ["Электричка"]]
rkm = ReplyKeyboardMarkup(keyboard)
CHOOSING, TYPING_REPLY, TYPING_CHOICE = range(3)


def done():
    pass


def main():
    logging.basicConfig(level=logging.DEBUG)
    updater = Updater(token="TOKEN", use_context=True)
    dispatcher = updater.dispatcher
    start_handler = CommandHandler("start", start)
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("settings", settings)],
        states={
            CHOOSING: [
                MessageHandler(
                    Filters.regex(
                        "^Московское|"
                        "Витебское|"
                        "Выборгское|"
                        "Балтийское и Варшавское|"
                        "Воловстроевское|"
                        "Приозерское|"
                        "Ладожское (Ириновское)"
                    ),
                    choose_station1,
                )
            ],
            TYPING_CHOICE: [
                MessageHandler(
                    Filters.regex(
                        "^Шушары|" "Павловск|" "Санкт-Петербург (Витебский вокзал)|"
                    ),
                    choose_station2,
                )
            ],
            TYPING_REPLY: [
                MessageHandler(
                    Filters.regex(
                        "^Шушары|" "Павловск|" "Санкт-Петербург (Витебский вокзал)|"
                    ),
                    save_settings,
                )
            ],
        },
        fallbacks=[MessageHandler(Filters.regex("^Done"), done)],
    )
    # start_handler = CommandHandler("settings", settings)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(conversation_handler)

    updater.start_polling()


if __name__ == "__main__":
    main()
