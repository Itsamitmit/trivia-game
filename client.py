import socket
from sre_constants import SUCCESS
import chatlib  # To use chatlib functions or consts, use chatlib.****

SERVER_IP = "127.0.0.1"  # Our server will run on same computer as client
SERVER_PORT = 5678

# HELPER SOCKET METHODS

def build_and_send_message(conn, code, msg):
	"""
	Builds a new message using chatlib, wanted code and message. 
	Prints debug info, then sends it to the given socket.
	Paramaters: conn (socket object), code (str), msg (str)
	Returns: Nothing
	"""
	
	full_msg = chatlib.build_message(code, msg)
	conn.send(full_msg.encode())
	print("Message Sent: ", full_msg)


def recv_message_and_parse(conn):
	"""
	Recieves a new message from given socket.
	Prints debug info, then parses the message using chatlib.
	Paramaters: conn (socket object)
	Returns: cmd (str) and data (str) of the received message. 
	If error occured, will return None, None
	"""

	data = conn.recv(4096).decode()

	cmd, msg = chatlib.parse_message(data)
	print("Recieved: ", cmd, msg)
	return cmd, msg


def build_send_recv_parse(conn, code, data):
	build_and_send_message(conn, code, data)
	cmd, msg = recv_message_and_parse(conn)
	return cmd, msg


def connect():
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((SERVER_IP,SERVER_PORT))
    return conn


def error_and_exit(msg):
	print("Error: ", msg)
	exit()


def login(conn):
	logged_in = False

	while not logged_in:
		username = input("Please enter username: \n")
		password = input("Please enter password: \n")

		build_and_send_message(conn, chatlib.PROTOCOL_CLIENT["login_msg"],username+"#"+password)
		cmd, msg = recv_message_and_parse(conn)
		logged_in = cmd.startswith("LOGIN_OK")
		
	
def logout(conn):
    build_and_send_message(conn, chatlib.PROTOCOL_CLIENT["logout_msg"],"")


def get_score(conn):
	cmd, msg = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["getscore_msg"], "")
	if cmd == chatlib.PROTOCOL_SERVER["yourscore_msg"]:
		print(msg)
	else:
		error_and_exit(msg)


def play_question(conn):
	cmd, msg = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["getquestion_msg"], "")
	if cmd == chatlib.PROTOCOL_SERVER["noquestions_msg"]:
		print("No questions left")
		return
	parts = msg.split("#")
	question_id = parts[0]
	question = parts[1]
	answer1, answer2, answer3, answer4 = parts[2], parts[3], parts[4], parts[5]

	print(f"Question: {question}")
	print(f"Answers: \n1: {answer1}\n2: {answer2}\n3: {answer3}\n4: {answer4}")
	answer = input("What is the answer: (1-4)\n")

	cmd, msg = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["sendanswer_msg"], f"{question_id}#{answer}")
	if cmd == chatlib.PROTOCOL_SERVER["correct_msg"]:
		print("Correct answer")
	elif cmd == chatlib.PROTOCOL_SERVER["wrong_msg"]:
		print(f"Wrong answer, the correct answer was {msg}")
	else:
		error_and_exit(msg)


def get_highscore(conn):
	cmd, msg = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["gethighscore_msg"], "")
	if cmd == chatlib.PROTOCOL_SERVER["highscore_msg"]:
		print(msg)
	else:
		error_and_exit(msg)

def get_logged_users(conn):
	cmd, msg = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["getlogged_msg"], "")
	if cmd == chatlib.PROTOCOL_SERVER["logged_msg"]:
		print(msg)
	else:
		error_and_exit(msg)


def main():
	LOGOUT = False

	conn = connect()
	login(conn)

	while not LOGOUT:
		action = input("LOGOUT / SCORE / HIGHSCORE / LOGGED / PLAY\n").upper()

		if action == "SCORE":
			get_score(conn)
		elif action == "HIGHSCORE":
			get_highscore(conn)
		elif action == "LOGGED":
			get_logged_users(conn)
		elif action == "PLAY":
			play_question(conn)
		elif action == "LOGOUT":
			LOGOUT = True
		else:
			print("Unkown Action")
	logout(conn)
	conn.close()


if __name__ == '__main__':
    main()