##############################################################################
# server.py
##############################################################################

from distutils.command.build import build
import socket
import select
import random
import html
import requests
from tkinter.messagebox import NO

import chatlib

# GLOBALS
users = {}
questions = {}
logged_users = {} # a dictionary of client hostnames to usernames - will be used later
messages_to_send = []

ERROR_MSG = "Error! "
SERVER_PORT = 5678
SERVER_IP = "127.0.0.1"


# HELPER SOCKET METHODS

def build_and_send_message(conn, code, msg):
    """
    Builds a new message using chatlib, wanted code and message. 
    Prints debug info, then sends it to the given socket.
    Paramaters: conn (socket object), code (str), msg (str)
    Returns: Nothing
    """
	
    full_msg = chatlib.build_message(code, msg)

    messages_to_send.append((conn, full_msg))

	# conn.send(full_msg.encode())
	
    print("[SERVER] ",full_msg)	  # Debug print

def recv_message_and_parse(conn):
    """
    Recieves a new message from given socket.
    Prints debug info, then parses the message using chatlib.
    Paramaters: conn (socket object)
    Returns: cmd (str) and data (str) of the received message. 
    If error occured, will return None, None
    """
    try:
        data = conn.recv(4096).decode()
        if data:
            cmd, msg = chatlib.parse_message(data)
            full_msg = chatlib.build_message(cmd, msg)
            print("[CLIENT] ", full_msg)	  # Debug print

            return cmd, msg
        return "", ""
    except:
        return "", ""
	
def print_client_sockets():
    """
    Prints all the connected client sockets
    """
    for user in logged_users:
        print(user)

# Data Loaders #


def load_questions_from_web():
    """
    Loads 50 random multiple choice questions from the Open Trivia Database
    Recieves: -
    Returns: questions dictionary
    """
    r = requests.get('https://opentdb.com/api.php?amount=50&type=multiple')
    question_data = r.json()["results"]

    for i, question in enumerate(question_data):
        q = html.unescape(question["question"])
        answers = [question["correct_answer"]] + question["incorrect_answers"]
        random.shuffle(answers)
        correct = answers.index(question["correct_answer"]) + 1
        questions[i+1] = {"question": q, "answers": answers, "correct": correct}
	
    return questions


def load_questions(filename):
    """
    Loads questions bank from file	## FILE SUPPORT TO BE ADDED LATER
    Recieves: filename
    Returns: questions dictionary
    """
    questions = {}

    with open(filename, 'r') as f:
        question_data = f.readlines()
    for i, question in enumerate(question_data):
        question = question.strip()
        data = question.split(chatlib.DELIMITER)
        question = data[0]
        answers = [data[1], data[2], data[3], data[4]]
        correct = data[5]
        questions[i] = {"question": question, "answers": answers, "correct": correct}
	
    return questions


def load_user_database(filename):
    """
    Loads users list from file	## FILE SUPPORT TO BE ADDED LATER
    Recieves: filename
    Returns: user dictionary
    """ 

    users = {}

    with open(filename, 'r') as f:
        user_data = f.readlines()
    for user in user_data:
        user = user.strip()
        data = user.split(chatlib.DELIMITER)
        username = data[0]
        password = data[1]
        score = int(data[2])
        if list(questions).count(chatlib.DELIMITER) > 3:
            questions_asked = data[3].split(',')
        else:
            questions_asked = []
        for i, q in enumerate(questions_asked):
            questions_asked[i] = int(q)
        users[username] = {"password": password, "score": score, "questions_asked": questions_asked}
    return users

	
# SOCKET CREATOR

def setup_socket():
    """
    Creates new listening socket and returns it
    Recieves: -
    Returns: the socket object
    """
	
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((SERVER_IP,SERVER_PORT))
    sock.listen()

    return sock
	


		
def send_error(conn, error_msg):
	"""
	Send error message with given message
	Recieves: socket, message error string from called function
	Returns: None
	"""
	build_and_send_message(conn, chatlib.PROTOCOL_SERVER["error_msg"], error_msg)
	

##### TRIVIA LOGIC

def create_random_quetsion(username):
    """
    Chooses a random new question for the user
    Recieves: username
    Returns: question
    """
    global questions
    options = list(questions.keys())

    while len(options) > 0:
        question_id = random.choice(options)
        if question_id in users[username]["questions_asked"]:
            options.remove(question_id)
        else:
            break
    if len(options) == 0 and question_id in users[username]["questions_asked"]:
        return None
    question = f"{question_id}#{questions[question_id]['question']}#{'#'.join(questions[question_id]['answers'])}"
    users[username]["questions_asked"].append(question_id)
    return question


##### MESSAGE HANDLING

def handle_question_message(conn, username):
    """
    Sends a question to the user asking for it
    Recieves: client socket, username
    Returns: -
    """
    try:
        question = create_random_quetsion(username)
        if question:
            build_and_send_message(conn, chatlib.PROTOCOL_SERVER["question_msg"], question)
        else:
            build_and_send_message(conn, chatlib.PROTOCOL_SERVER["noquestions_msg"], "")
    except:
        send_error("Couldnt get a question")


def handle_answer_message(conn, username, answer):
    """
    Responds to the client if they were right or not in their answer
    Recieves: client socket, username, client answer
    Returns: -
    """
    global questions
    global users

    question_id = int(answer.split("#")[0])
    choice = answer.split("#")[1]
    correct = questions[question_id]["correct"]

    if str(choice) == str(correct):
        build_and_send_message(conn, chatlib.PROTOCOL_SERVER["correct_msg"], "")
        users[username]["score"] += 1
    else:
        build_and_send_message(conn, chatlib.PROTOCOL_SERVER["wrong_msg"], str(correct))


def handle_getscore_message(conn, username):
    """
    Sends a user's score to them
    Recieves: client socket, username
    Returns: -
    """
    global users
	
    try:
        build_and_send_message(conn, chatlib.PROTOCOL_SERVER["yourscore_msg"], str(users[username]["score"]))
    except:
        send_error(conn, "Couldn't get score")
	

def handle_gethighscore_message(conn):
    """
    Sends the trivia highscores to the user
    Recieves: client socket
    Returns: -
    """
    global users

    scores = []
    for user in users:
        scores.append((user, users[user]["score"]))
    scores = sorted(scores, key = lambda x: x[1], reverse = True)
    highscore = ""
    for score in scores[:5]:
        highscore += f"{score[0]}: {score[1]}\n"

    try:
        build_and_send_message(conn, chatlib.PROTOCOL_SERVER["highscore_msg"], highscore)
    except:
        send_error(conn, "Couldn't get highscores")


def handle_getlogged_message(conn):
    """
    Sends a list of all logged users to the client
    Recieves: client socket
    Returns: -
    """
    global users
    logged = ",".join(list(users.keys()))

    try:
        build_and_send_message(conn, chatlib.PROTOCOL_SERVER["logged_msg"], logged)
    except:
        send_error(conn, "Couldnt get logged users")


def handle_logout_message(conn):
	"""
	Closes the given socket (in laster chapters, also remove user from logged_users dictioary)
	Recieves: socket
	Returns: None
	"""
	global logged_users
	logged_users.pop(conn.getpeername())

	conn.close()


def handle_login_message(conn, data):
    """
    Gets socket and message data of login message. Checks  user and pass exists and match.
    If not - sends error and finished. If all ok, sends OK message and adds user and address to logged_users
    Recieves: socket, message code and data
    Returns: None (sends answer to client)
    """
    global users  # This is needed to access the same users dictionary from all functions
    global logged_users	 # To be used later

    parts = data.split("#")
    username = parts[0]
    password = parts[1]

    if username in users:
        if username in list(logged_users.values()):
            send_error(conn, "User already logged in")
        else:
            if users[username]["password"] == password:
                build_and_send_message(conn, chatlib.PROTOCOL_SERVER["login_ok_msg"], "")
                logged_users[conn.getpeername()] = username
            else:
                send_error(conn, "Wrong password")
    else:
        send_error(conn, "Username doesnt exist")


def handle_client_message(conn, cmd, data):
    """
    Gets message code and data and calls the right function to handle command
    Recieves: socket, message code and data
    Returns: None
    """
    global logged_users	 # To be used later
    

    if cmd == chatlib.PROTOCOL_CLIENT["login_msg"]:
        handle_login_message(conn, data)
    elif conn.getpeername() in logged_users:
        username = logged_users[conn.getpeername()]
        if cmd == chatlib.PROTOCOL_CLIENT["getscore_msg"]:
            handle_getscore_message(conn, username)
        elif cmd == chatlib.PROTOCOL_CLIENT["logout_msg"] or cmd == "":
            handle_logout_message(conn)
        elif cmd == chatlib.PROTOCOL_CLIENT["getquestion_msg"]:
            handle_question_message(conn, username)
        elif cmd == chatlib.PROTOCOL_CLIENT["sendanswer_msg"]:
            handle_answer_message(conn, username, data)
        elif cmd == chatlib.PROTOCOL_CLIENT["gethighscore_msg"]:
            handle_gethighscore_message(conn)
        elif cmd == chatlib.PROTOCOL_CLIENT["getlogged_msg"]:
            handle_getlogged_message(conn)
        else:
            send_error(conn, "Invalid command")
    else:
        send_error(conn, "User must be logged in")


def main():

    global users
    global questions
    global messages_to_send

    # questions = load_questions("questions.txt")
    questions = load_questions_from_web()
    users = load_user_database("users.txt")
    server = setup_socket()

    print("Welcome to Trivia Server!")

    clients = []
	
    while True:
        rlist, wlist, xlist = select.select([server]+clients, [], [])
        for conn in rlist:
            if conn is server:
                client, address = conn.accept()
                clients.append(client)
                print("New client joined")
            else:
                cmd, data = recv_message_and_parse(conn)
                handle_client_message(conn, cmd, data)
                if cmd == chatlib.PROTOCOL_CLIENT["logout_msg"] or cmd == "":
                    clients.remove(conn)
                    conn.close()
                    print("Client disconnected")
        for message in messages_to_send:
            try:
                conn = message[0]
                data = message[1]
                conn.send(data.encode())
                messages_to_send.remove(message)
            except:
                pass
    


if __name__ == '__main__':
	main()

	