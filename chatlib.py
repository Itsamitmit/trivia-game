# Protocol Constants

CMD_FIELD_LENGTH = 16	# Exact length of cmd field (in bytes)
LENGTH_FIELD_LENGTH = 4   # Exact length of length field (in bytes)
MAX_DATA_LENGTH = 10**LENGTH_FIELD_LENGTH-1  # Max size of data field according to protocol
MSG_HEADER_LENGTH = CMD_FIELD_LENGTH + 1 + LENGTH_FIELD_LENGTH + 1  # Exact size of header (CMD+LENGTH fields)
MAX_MSG_LENGTH = MSG_HEADER_LENGTH + MAX_DATA_LENGTH  # Max size of total message
DELIMITER = "|"  # Delimiter character in protocol

# Protocol Messages 
# In this dictionary we will have all the client and server command names

PROTOCOL_CLIENT = {
	'login_msg':'LOGIN', 
	'logout_msg':'LOGOUT', 
	'getscore_msg':'MY_SCORE', 
	'getlogged_msg':'LOGGED', 
	'gethighscore_msg':'HIGHSCORE', 
	'getquestion_msg':'GET_QUESTION', 
	'sendanswer_msg':'SEND_ANSWER'
}

PROTOCOL_SERVER = {
	'login_ok_msg':'LOGIN_OK', 
	'login_failed_msg':'ERROR', 
	'yourscore_msg':'YOUR_SCORE', 
	'highscore_msg':'ALL_SCORE', 
	'logged_msg':'LOGGED_ANSWER', 
	'correct_msg':'CORRECT_ANSWER', 
	'wrong_msg':'WRONG_ANSWER', 
	'question_msg':'YOUR_QUESTION', 
	'error_msg':'ERROR', 
	'noquestions_msg':'NO_QUESTIONS'
}


# Other constants

ERROR_RETURN = None  # What is returned in case of an error


def build_message(cmd, data):
	"""
	Gets command name and data field and creates a valid protocol message
	Returns: str, or None if error occured
	"""

	try:
		if len(cmd) > 16 or len(data) > 9999:
			return None
		cmd = cmd.ljust(16)
		message_len = (str(len(data))).rjust(4, "0")
		full_msg = cmd + "|" + message_len + "|" + data

		return full_msg
	except:
		return None

def parse_message(data):
	"""
	Parses protocol message and returns command name and data field
	Returns: cmd (str), data (str). If some error occured, returns None, None
	"""
	
	parts = data.split(DELIMITER, 2)
	try:
		msg_len = int(parts[1])
		if msg_len > 9999 or len(parts[0]) != 16 or len(parts[2]) != msg_len:
			return None, None
		cmd = parts[0].split()[0]
		msg = parts[2][:msg_len]
		return cmd, msg
	except:
		return None, None
    

	
def split_msg(msg, expected_fields):
	"""
	Helper method. gets a string and number of expected fields in it. Splits the string 
	using protocol's delimiter (|) and validates that there are correct number of fields.
	Returns: list of fields if all ok. If some error occured, returns None
	"""
	try:
		fields = msg.split(DELIMITER)
		if len(fields) == expected_fields:
			return fields
	except:
		return None


def join_msg(msg_fields):
	"""
	Helper method. Gets a list, joins all of it's fields to one string divided by the delimiter. 
	Returns: string that looks like cell1|cell2|cell3
	"""
	for field in msg_fields:
		field = str(field)
		
	return DELIMITER.join(msg_fields)