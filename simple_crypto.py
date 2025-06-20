import hashlib
import json
import secrets
import time
from typing import Any, Dict, List, Optional

class Wallet:
    """A very small wallet with a toy signing mechanism."""
    def __init__(self) -> None:
        self.private_key = secrets.token_hex(32)
        self.public_key = hashlib.sha256(self.private_key.encode()).hexdigest()
        self.address = hashlib.sha256(self.public_key.encode()).hexdigest()[:16]

    def sign(self, data: str) -> str:
        """Sign data with a simplistic hash-based signature (not secure)."""
        return hashlib.sha256((data + self.private_key).encode()).hexdigest()

class Transaction:
    """Represents a transaction between wallets."""
    def __init__(self, sender: str, receiver: str, amount: float,
                 sender_public_key: str, signature: str) -> None:
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.sender_public_key = sender_public_key
        self.signature = signature

    def to_dict(self) -> Dict[str, Any]:
        return {
            'sender': self.sender,
            'receiver': self.receiver,
            'amount': self.amount,
            'sender_public_key': self.sender_public_key,
            'signature': self.signature,
        }

    @staticmethod
    def create(sender_wallet: Wallet, receiver_address: str, amount: float) -> 'Transaction':
        """Create and sign a new transaction."""
        data = f"{sender_wallet.address}{receiver_address}{amount}"
        signature = sender_wallet.sign(data)
        return Transaction(
            sender_wallet.address,
            receiver_address,
            amount,
            sender_wallet.public_key,
            signature,
        )

    def is_valid(self) -> bool:
        """Verify the signature using the sender's public key."""
        data = f"{self.sender}{self.receiver}{self.amount}"
        expected = hashlib.sha256((data + self.sender_public_key).encode()).hexdigest()
        return self.signature == expected

class Block:
    """A single block in the blockchain."""
    def __init__(self, index: int, timestamp: float,
                 transactions: List[Dict[str, Any]],
                 previous_hash: str, nonce: int = 0) -> None:
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.compute_hash()

    def compute_hash(self) -> str:
        block_string = json.dumps({
            'index': self.index,
            'timestamp': self.timestamp,
            'transactions': self.transactions,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

class Blockchain:
    """A minimal blockchain with proof of work."""
    difficulty = 3

    def __init__(self) -> None:
        self.unconfirmed_transactions: List[Transaction] = []
        self.chain: List[Block] = []
        self.create_genesis_block()

    def create_genesis_block(self) -> None:
        genesis = Block(0, time.time(), [], '0')
        self.chain.append(genesis)

    def last_block(self) -> Block:
        return self.chain[-1]

    def add_transaction(self, tx: Transaction) -> bool:
        if tx.is_valid():
            self.unconfirmed_transactions.append(tx)
            return True
        return False

    def proof_of_work(self, block: Block) -> str:
        block.nonce = 0
        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * Blockchain.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()
        return computed_hash

    def add_block(self, block: Block, proof: str) -> bool:
        if self.last_block().hash != block.previous_hash:
            return False
        if not proof.startswith('0' * Blockchain.difficulty) or proof != block.compute_hash():
            return False
        block.hash = proof
        self.chain.append(block)
        return True

    def mine(self) -> Optional[Block]:
        if not self.unconfirmed_transactions:
            return None
        tx_dicts = [tx.to_dict() for tx in self.unconfirmed_transactions]
        new_block = Block(self.last_block().index + 1, time.time(), tx_dicts, self.last_block().hash)
        proof = self.proof_of_work(new_block)
        if self.add_block(new_block, proof):
            self.unconfirmed_transactions = []
            return new_block
        return None

    def get_balance(self, address: str) -> float:
        balance = 0.0
        for block in self.chain:
            for tx in block.transactions:
                if tx['sender'] == address:
                    balance -= tx['amount']
                if tx['receiver'] == address:
                    balance += tx['amount']
        return balance


def demo() -> None:
    blockchain = Blockchain()
    alice = Wallet()
    bob = Wallet()
    print('Alice address:', alice.address)
    print('Bob address:', bob.address)

    tx1 = Transaction.create(alice, bob.address, 10)
    blockchain.add_transaction(tx1)

    mined = blockchain.mine()
    if mined:
        print('Mined block', mined.index, mined.hash)
    else:
        print('No block mined.')

    print('Alice balance:', blockchain.get_balance(alice.address))
    print('Bob balance:', blockchain.get_balance(bob.address))


if __name__ == '__main__':
    demo()
