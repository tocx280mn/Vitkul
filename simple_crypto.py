import hashlib
import json
from time import time
from typing import Any, Dict, List, Optional

class Block:
    def __init__(self, index: int, timestamp: float, transactions: List[Dict[str, Any]], previous_hash: str, nonce: int = 0):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.compute_hash()

    def compute_hash(self) -> str:
        block_string = json.dumps(self.__dict__, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

class Blockchain:
    difficulty = 2  # number of leading zeros required in the hash

    def __init__(self):
        self.unconfirmed_transactions: List[Dict[str, Any]] = []
        self.chain: List[Block] = []
        self.create_genesis_block()

    def create_genesis_block(self) -> Block:
        genesis_block = Block(0, time(), [], '0')
        self.chain.append(genesis_block)
        return genesis_block

    def last_block(self) -> Block:
        return self.chain[-1]

    def add_transaction(self, sender: str, receiver: str, amount: float) -> int:
        tx = {'sender': sender, 'receiver': receiver, 'amount': amount}
        self.unconfirmed_transactions.append(tx)
        return self.last_block().index + 1

    def proof_of_work(self, block: Block) -> str:
        block.nonce = 0
        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * Blockchain.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()
        return computed_hash

    def add_block(self, block: Block, proof: str) -> bool:
        previous_hash = self.last_block().hash
        if previous_hash != block.previous_hash:
            return False
        if not proof.startswith('0' * Blockchain.difficulty) or proof != block.compute_hash():
            return False
        block.hash = proof
        self.chain.append(block)
        return True

    def mine(self) -> Optional[Block]:
        if not self.unconfirmed_transactions:
            return None
        new_block = Block(index=self.last_block().index + 1,
                          timestamp=time(),
                          transactions=self.unconfirmed_transactions,
                          previous_hash=self.last_block().hash)
        proof = self.proof_of_work(new_block)
        added = self.add_block(new_block, proof)
        if added:
            self.unconfirmed_transactions = []
            return new_block
        return None

def demo():
    blockchain = Blockchain()
    print('Genesis block created:', blockchain.chain[0].hash)

    blockchain.add_transaction('Alice', 'Bob', 10)
    blockchain.add_transaction('Bob', 'Charlie', 5)
    mined_block = blockchain.mine()
    if mined_block:
        print('Mined block:', mined_block.index, mined_block.hash)
    else:
        print('No transactions to mine.')

    for block in blockchain.chain:
        print(block.index, block.transactions, block.hash)

if __name__ == '__main__':
    demo()
