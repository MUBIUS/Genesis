import sys
sys.path.append('/Users/my/Desktop/blockchain')

from Blockchain.Backend.core.block import Block
from Blockchain.Backend.core.blockHeader import BlockHeader
from Blockchain.Backend.util.util import hash256
from Blockchain.Backend.core.database.database import BlockchainDB
from Blockchain.Backend.core.Tx import CoinbaseTx
import time

ZERO_HASH = '0' * 64
VERSION = 1

class Blockchain:
    def __init__(self):
        pass

    def write_on_disk(self, block):
        blockchainDB = BlockchainDB()
        blockchainDB.write(block)

    def fetch_last_block(self):
        blockchainDB = BlockchainDB()
        return blockchainDB.lastBlock()

    def GenesisBlock(self):
        BlockHeight = 0
        prevBlockHash = ZERO_HASH
        self.addBlock(BlockHeight, prevBlockHash)

    def addBlock(self, BlockHeight, prevBlockHash):
        timestamp = int(time.time())
        coinbaseInstance = CoinbaseTx(BlockHeight)
        coinbaseTx = coinbaseInstance.CoinbaseTransaction()

        merkleRoot = coinbaseTx.TxId  # Placeholder value, you need to compute the actual merkle root
        bits = 'ffff001f'  # Placeholder value, you need to compute the actual bits
        blockHeader = BlockHeader(VERSION, prevBlockHash, merkleRoot, timestamp, bits)
        blockHeader.mine()  # Attempt to mine the block header
        
        print(f'Block {BlockHeight} Mined successfully with Nonce value {blockHeader.nonce}')
        self.write_on_disk([Block(BlockHeight, 1, blockHeader.__dict__, 1, coinbaseTx.to_dict()).__dict__])

        

    def main(self):
        lastBlock =self.fetch_last_block()
        if lastBlock is None:
            self.GenesisBlock()

        while True:
            lastBlock = self.fetch_last_block()
            BlockHeight = lastBlock["Height"] + 1
            prevBlockHash = lastBlock['Blockheader']['blockHash']
            self.addBlock(BlockHeight, prevBlockHash)


if __name__ == "__main__":
    blockchain = Blockchain()
    blockchain.main()

