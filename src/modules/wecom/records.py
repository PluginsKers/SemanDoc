import time
from collections import deque
from typing import List


class HistoryRecords:
    def __init__(self, max_length=1):
        self.history = deque(maxlen=max_length)
        # Set the initial time as the current time
        self.time = time.time()

    def add_record(self, msg: str, answer: str):
        # Check if more than 3 hours have passed
        if time.time() - self.time > 10800:  # 3 hours in seconds
            self.clear_history()  # Clear history if more than 3 hours
        if not isinstance(msg, str) or not isinstance(answer, str):
            raise ValueError("Both question and answer must be strings.")
        self.history.append({"role": "user", "content": msg})
        self.history.append(
            {"role": "assistant", "metadata": "", "content": answer})
        # Update the time using time.time()
        self.time = time.time()

    def get_history(self) -> List[dict]:
        # Check if more than 3 hours have passed
        if time.time() - self.time > 10800:
            return []  # Return an empty list if more than 3 hours
        return list(self.history)

    def get_raw_history(self) -> str:
        raw = ""
        for record in self.history:
            raw += f"{record['role']}: {record['content']}\n"
        return raw

    def clear_history(self):
        # Clear the history
        self.history.clear()
