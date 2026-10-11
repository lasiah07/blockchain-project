import time


class ProofOfWork:

    def __init__(self, difficulty=2):
        self.difficulty = difficulty

    def mine(self, block):

        target = "0" * self.difficulty

        nonce = 0

        start_time = time.time()

        while True:

            block.nonce = nonce
            block.hash = block.calculate_hash()

            if block.hash.startswith(target):
                break

            nonce += 1

        end_time = time.time()

        mining_time = end_time - start_time

        return nonce, block.hash, mining_time