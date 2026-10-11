from block import Block


class Blockchain:

    def __init__(self):
        self.chain = [self.create_genesis_block()]

    def create_genesis_block(self):

        return Block(
            index=0,
            data={
                "keterangan": "Genesis Block"
            },
            previous_hash="0"
        )

    def add_block(self, data):

        previous_block = self.chain[-1]

        new_block = Block(
            index=len(self.chain),
            data=data,
            previous_hash=previous_block.hash,
            nonce=0
        )

        self.chain.append(new_block)

    def is_valid(self):

        for i in range(1, len(self.chain)):

            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            # Memeriksa hash block
            if current_block.hash != current_block.calculate_hash():
                return False

            # Memeriksa hubungan dengan block sebelumnya
            if current_block.previous_hash != previous_block.hash:
                return False

        return True