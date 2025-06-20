import base64
import hashlib
import json
import secrets
import time
from typing import Any, Dict, List, Optional

# Name of this toy cryptocurrency
COIN_NAME = "Scryptify"

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
        # Use scrypt to generate a digest and then encode it with base64
        digest = hashlib.scrypt(
            block_string,
            salt=b'blockchain',
            n=2 ** 12,
            r=8,
            p=1,
            dklen=32,
        )
        return base64.b64encode(digest).decode()

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
        """Simple proof of work using the base64+scrypt hash."""
        block.nonce = 0
        computed_hash = block.compute_hash()
        target = '0' * Blockchain.difficulty
        while not computed_hash.startswith(target):
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


class Node:
    """A minimal peer that holds a wallet and a blockchain."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.wallet = Wallet()
        self.blockchain = Blockchain()
        self.peers: List['Node'] = []

    def register_peer(self, peer: 'Node') -> None:
        if peer is not self and peer not in self.peers:
            self.peers.append(peer)

    def broadcast_transaction(self, tx: Transaction) -> None:
        for peer in self.peers:
            peer.receive_transaction(tx)

    def receive_transaction(self, tx: Transaction) -> None:
        self.blockchain.add_transaction(tx)

    def submit_transaction(self, receiver: str, amount: float) -> Transaction:
        """Create a transaction from this node and broadcast it."""
        tx = Transaction.create(self.wallet, receiver, amount)
        self.blockchain.add_transaction(tx)
        self.broadcast_transaction(tx)
        return tx

    def broadcast_block(self, block: Block) -> None:
        for peer in self.peers:
            peer.receive_block(block)

    def receive_block(self, block: Block) -> None:
        if block.previous_hash == self.blockchain.last_block().hash:
            self.blockchain.add_block(block, block.hash)

    def mine(self) -> Optional[Block]:
        new_block = self.blockchain.mine()
        if new_block:
            self.broadcast_block(new_block)
        return new_block

    def sync(self) -> None:
        """Synchronize the blockchain with peers (longest chain wins)."""
        longest = self.blockchain.chain
        for peer in self.peers:
            if len(peer.blockchain.chain) > len(longest):
                longest = peer.blockchain.chain
        if longest is not self.blockchain.chain:
            self.blockchain.chain = [
                Block(
                    b.index,
                    b.timestamp,
                    b.transactions,
                    b.previous_hash,
                    b.nonce,
                )
                for b in longest
            ]


def demo() -> None:
    print(f"--- {COIN_NAME} Demo ---")
    alice = Node('Alice')
    bob = Node('Bob')
    carol = Node('Carol')

    # register peers
    alice.register_peer(bob)
    alice.register_peer(carol)
    bob.register_peer(alice)
    bob.register_peer(carol)
    carol.register_peer(alice)
    carol.register_peer(bob)

    print('Alice address:', alice.wallet.address)
    print('Bob address:', bob.wallet.address)
    print('Carol address:', carol.wallet.address)

    # Alice sends coins to Bob and broadcasts the transaction
    alice.submit_transaction(bob.wallet.address, 5)

    # Alice mines the transaction and broadcasts the block
    mined = alice.mine()
    if mined:
        print('Alice mined block', mined.index, mined.hash)

    # Peers synchronize their chains
    bob.sync()
    carol.sync()

    print('Alice balance:', alice.blockchain.get_balance(alice.wallet.address))
    print('Bob balance:', bob.blockchain.get_balance(bob.wallet.address))
    print('Carol balance:', carol.blockchain.get_balance(carol.wallet.address))


if __name__ == '__main__':
    demo()
