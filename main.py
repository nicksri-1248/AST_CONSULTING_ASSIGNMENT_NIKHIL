import telebot
import requests
import sqlite3
from threading import current_thread

bot = telebot.TeleBot('<bot_api_token>')

API_KEY = '8167f496f528e7285b6fe656df2d1b2f'

subscribed_users = set()
blocked_users = set()

conn = sqlite3.connect('user_data.db')
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS users (
                    chat_id INTEGER PRIMARY KEY,
                    username TEXT,
                    is_subscribed INTEGER,
                    is_blocked INTEGER)''')
conn.commit()

admin_id = <admin_user_id>  # Replace with the actual admin user ID

@bot.message_handler(commands=['start', 'help'])
def start(message):
    user_id = message.chat.id

    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE is_subscribed=1 AND is_blocked=0')
    valid_users = cursor.fetchone()

    #conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE is_blocked=1')
    blocked_users = c.fetchone()

    if user_id == admin_id:
        # Admin user
        bot.reply_to(message, 'Hello, admin! \n'
                              '\n'
                              f"/block <user_name> - to block user \n"
                              f"/unblock <user_name> - to unblock user \n"
                              f"/users - to see subscribed user list \n"
                              f"/blocked - to see blocked user list \n"
                              f"/weather <area_name> - for weather report of the city \n"
                              f"/help \n"
                              )
    elif valid_users is not None and user_id in valid_users:
        # Subscribed user
        bot.reply_to(message, 'Welcome back, subscribed user! \n'
                              '\n'
                              '/unsubscribe - to unsubscribe \n'
                              '/weather <area_name> - for weather report of the city \n'
                              '/help \n')
    elif blocked_users is not None and user_id in blocked_users:
        # Blocked user
        bot.reply_to(message, 'You have been blocked \n'
                              '\n'
                              '/request <your_user_name> - request to admin to unblock you')
    else:
        # Unsubscribed user
        bot.reply_to(message, 'Hello, unsubscribed user! \n'
                              '\n'
                              '/subscribe - please subscribe to use more features')


@bot.message_handler(commands=['request'])
def send_request(message):
    user_id = message.chat.id
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE is_blocked=1')
    blocked_users = c.fetchone()

    if user_id not in blocked_users:
        bot.reply_to(message, "Sorry, you cannot send a request.")
        return

    #admin_chat_id = "admin_id"  # Replace with the actual chat ID of the admin

    try:
        command, username = message.text.split(' ', 1)
        request_message = f"Dear Admin!\nPlease unblock me {username}"
        bot.send_message(admin_id, request_message)
        bot.reply_to(message, "Your request has been sent to the admin.")
    except ValueError:
        bot.reply_to(message, "Invalid request format. Please provide your username after the command.")


@bot.message_handler(commands=['subscribe'])
def subscribe_user(message):
    chat_id = message.chat.id
    username = message.from_user.username
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE chat_id=?', (chat_id,))
    existing_user = cursor.fetchone()

    if existing_user:
        if existing_user[3] == 0:  # Check if user is already subscribed or not
            cursor.execute('UPDATE users SET is_subscribed=1 WHERE chat_id=?', (chat_id,))
            conn.commit()
            bot.reply_to(message, 'You have been subscribed.')
            subscribed_users.add(chat_id)  # Add the user to the set
        else:
            bot.reply_to(message, 'You are already subscribed.')
    else:
        cursor.execute('INSERT INTO users (chat_id, username, is_subscribed) VALUES (?, ?, 1)', (chat_id, username))
        conn.commit()
        bot.reply_to(message, 'You have been subscribed.')
        subscribed_users.add(chat_id)  # Add the user to the set

    cursor.close()
    conn.close()

@bot.message_handler(commands=['unsubscribe'])
def unsubscribe_user(message):
    chat_id = message.chat.id
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE chat_id=? AND is_subscribed=1', (chat_id,))
    existing_user = cursor.fetchone()
    if existing_user:
        cursor.execute('UPDATE users SET is_subscribed=0 WHERE chat_id=?', (chat_id,))
        conn.commit()
        bot.reply_to(message, 'You have been unsubscribed.')
        #subscribed_users.remove(chat_id)  # Remove the user from the set
    else:
        bot.reply_to(message, 'You are not subscribed.')
    cursor.close()
    conn.close()

@bot.message_handler(commands=['users'])
def get_subscribed_users(message):
    if message.chat.id != admin_id:
        unauthorized_message = "Sorry, you are not authorized to view the subscribed users."
        bot.reply_to(message, unauthorized_message)
        return

    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE is_subscribed=1')
    subscribed_users_data = cursor.fetchall()

    if subscribed_users_data:
        user_list = "List of subscribed users:\n"
        for user in subscribed_users_data:
            user_id, username, _, _ = user
            user_list += f"Username: {username}\n"
        bot.reply_to(message, user_list)
    else:
        bot.reply_to(message, "No users are currently subscribed.")

    cursor.close()
    conn.close()

@bot.message_handler(commands=['list'])
def get_all_users(message):
    if message.chat.id != admin_id:
        unauthorized_message = "Sorry, you are not authorized to view the subscribed users."
        bot.reply_to(message, unauthorized_message)
        return

    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    all_users_data = cursor.fetchall()

    if all_users_data:
        user_list = "List of all users:\n"
        for user in all_users_data:
            user_id, username, _, _ = user
            user_list += f"Username: {username}\n"
        bot.reply_to(message, user_list)
    else:
        bot.reply_to(message, "No users are currently.")

    cursor.close()
    conn.close()

# Handle incoming messages
@bot.message_handler(commands=['weather'])
def get_weather(message):
    try:
        command, city_name = message.text.split(' ', 1)

        user_id = message.chat.id
        conn = sqlite3.connect('user_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE chat_id=? AND is_subscribed=1 AND is_blocked=0', (user_id,))
        existing_user = cursor.fetchone()

        # Check if user exists in the user_data table or is an admin
        if existing_user or user_id == admin_id:
            #city_name = message.text

            # Make a request to OpenWeatherMap API
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={API_KEY}&units=metric"
            response = requests.get(url).json()

            if response['cod'] == '404':
                error_message = f"Sorry, I couldn't find any weather information for {city_name}."
                bot.reply_to(message, error_message)
            else:
                weather_data = response['weather'][0]
                temperature = response['main']['temp']
                feels_like = response['main']['feels_like']
                humidity = response['main']['humidity']
                wind_speed = response['wind']['speed']
                description = weather_data['description']

                weather_message = f"The weather in {city_name}:\n\n" \
                                  f"Temperature: {temperature}°C\n" \
                                  f"Feels like: {feels_like}°C\n" \
                                  f"Humidity: {humidity}%\n" \
                                  f"Wind Speed: {wind_speed} m/s\n" \
                                  f"Description: {description}"

                bot.reply_to(message, weather_message)
        else:
            unauthorized_message = "Sorry, you are not an authorized user."
            bot.reply_to(message, unauthorized_message)
    except ValueError:
        bot.reply_to(message, "Invalid request format. Please provide your region after the command.")


@bot.message_handler(commands=['block'])
def block_user(message):
    #admin_id = admin_id # Replace with your admin user ID
    if message.chat.id != admin_id:
        unauthorized_message = "Sorry, you are not authorized to block users."
        bot.reply_to(message, unauthorized_message)
        return

    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE is_blocked=1')
    blocked_users = c.fetchone()

    try:
        command, username = message.text.split(' ', 1)
        user_id = get_user_id_by_username(username)

        if blocked_users is not None and user_id in blocked_users:
            bot.reply_to(message, f"{username} is already blocked")
            return

        if user_id is None:
            bot.reply_to(message, f"User with username '{username}' not found.")
            return

        c.execute('UPDATE users SET is_blocked=1 WHERE chat_id=?', (user_id,))
        conn.commit()
        # blocked_users.add(user_id)  # Add the user to the set
        bot.reply_to(message, f"User '{username}' has been blocked.")
    except ValueError:
        bot.reply_to(message, "Invalid request format. Please provide your username after the command.")


# Handle '/unblock' command and username input
@bot.message_handler(commands=['unblock'])
def unblock_user(message):
    #admin_id = 'YOUR_ADMIN_USER_ID'  # Replace with your admin user ID
    #conn = sqlite3.connect('user_data.db')
    #c = conn.cursor()
    if message.chat.id != admin_id:
        unauthorized_message = "Sorry, you are not authorized to unblock users."
        bot.reply_to(message, unauthorized_message)
        return

    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE is_blocked=0')
    blocked_users = c.fetchone()

    try:
        command, username = message.text.split(' ', 1)
        user_id = get_user_id_by_username(username)

        if blocked_users is not None and user_id in blocked_users:
            bot.reply_to(message, f"{username} is already unblocked")
            return

        if user_id is None:
            bot.reply_to(message, f"User with username '{username}' not found.")
            return

        c.execute('UPDATE users SET is_blocked=0 WHERE chat_id=?', (user_id,))
        conn.commit()
        bot.reply_to(message, f"User '{username}' has been unblocked.")
        # blocked_users.remove(user_id)  # Remove the user from the set
    except ValueError:
        bot.reply_to(message, "Invalid request format. Please provide your username after the command.")

def get_user_id_by_username(username):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute('SELECT chat_id FROM users WHERE username=?', (username,))
    result = c.fetchone()

    if result is not None:
        return result[0]
    else:
        return None

@bot.message_handler(commands=['blocked'])
def get_subscribed_users(message):
    if message.chat.id != admin_id:
        unauthorized_message = "Sorry, you are not authorized to view the subscribed users."
        bot.reply_to(message, unauthorized_message)
        return

    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE is_blocked=1')
    blocked_users_data = cursor.fetchall()

    if blocked_users_data:
        user_list = "List of blocked users:\n"
        for user in blocked_users_data:
            user_id, username, _, _ = user
            user_list += f"Username: {username}\n"
        bot.reply_to(message, user_list)
    else:
        bot.reply_to(message, "No users are currently blocked.")

    cursor.close()
    conn.close()

# Start the bot
bot.polling()

