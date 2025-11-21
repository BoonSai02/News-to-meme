import sys

def error_message_detail(error, exc_tb):
    """Extract detailed error information"""
    if exc_tb is None:
        return str(error)
    try:
        file_name = exc_tb.tb_frame.f_code.co_filename
        error_message = "Error occurred in python script name [{0}] line number [{1}] error message[{2}]".format(
            file_name, exc_tb.tb_lineno, str(error))
        return error_message
    except AttributeError:
        return str(error)  # Fallback if tb_frame is unavailable

class CustomException(Exception):
    """Custom exception class for the news meme pipeline"""
    def __init__(self, error_message, exc_tb=None):
        super().__init__(error_message)
        self.error_message = error_message_detail(error_message, exc_tb)
    
    def __str__(self):
        return self.error_message