class Block:

    """
        Block is a container used to Store transactions
    """
    def __init__(self, Height, Blocksize, BlockHeader, TxCount, Txs):

        self.Height = Height
        self.Blocksize = Blocksize
        self.Blockheader = BlockHeader
        self.TxCount = TxCount
        self.Txs = Txs