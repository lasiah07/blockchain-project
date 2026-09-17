import hashlib
import json
from datetime import datetime


class Block:

    def __init__(self, index, data, previous_hash, nonce=0):
        self.index = index
        self.timestamp = datetime.now()
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()

    def calculate_hash(self):

        block_data = (
            str(self.index)
            + str(self.timestamp)
            + json.dumps(self.data, sort_keys=True)
            + str(self.previous_hash)
            + str(self.nonce)
        )

        return hashlib.sha256(block_data.encode()).hexdigest()