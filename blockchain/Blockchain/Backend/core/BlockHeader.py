import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from Blockchain.Backend.util.util import hash256, int_to_little_endian, little_endian_to_int


class BlockHeader:
    def __init__(self, version, prevBlockHash, merkleRoot, timestamp, bits, nonce=0):
        self.version = version
        self.prevBlockHash = prevBlockHash
        self.merkleRoot = merkleRoot
        self.timestamp = timestamp
        self.bits = bits
        self.nonce = nonce
        self.blockHash = ''

    # ------------------------------------------------------------------
    # Compute the double-SHA256 block hash from the header fields.
    # Returns the hash as an integer so it can be compared to the target.
    # ------------------------------------------------------------------
    def _compute_hash_int(self):
        return little_endian_to_int(
            hash256(
                int_to_little_endian(self.version, 4)
                + bytes.fromhex(self.prevBlockHash)[::-1]
                + bytes.fromhex(self.merkleRoot)
                + int_to_little_endian(self.timestamp, 4)
                + self.bits
                + int_to_little_endian(self.nonce, 4)
            )
        )

    def generateBlockHash(self):
        """Return the block hash as a little-endian hex string (Bitcoin convention)."""
        raw = int_to_little_endian(self._compute_hash_int(), 32)
        return raw.hex()[::-1]

    def validateBlock(self):
        """Return True if the block hash satisfies proof-of-work (hash < target)."""
        from Blockchain.Backend.util.util import bits_to_target
        target = bits_to_target(self.bits)
        return self._compute_hash_int() < target

    def mine(self, target, newBlockAvailable=None):
        """
        Increment nonce until hash < target.
        Returns True if another miner solved it first (competition over),
        False if this miner won.
        """
        self.blockHash = target + 1  # seed above target to enter loop

        while self.blockHash > target:
            # Check if another process mined a block while we were working
            if newBlockAvailable and len(newBlockAvailable) > 0:
                return True   # competition over

            self.blockHash = self._compute_hash_int()
            self.nonce += 1
            if self.nonce % 5000 == 0:
                print(f"Mining… nonce={self.nonce}", end="\r")

        # Convert winning hash to hex for storage
        raw = int_to_little_endian(self.blockHash, 32)
        self.blockHash = raw.hex()[::-1]
        self.bits = self.bits.hex()
        return False   # this miner won

    def to_hex(self):
        """Serialise binary fields to hex strings for JSON storage."""
        if isinstance(self.prevBlockHash, bytes):
            self.prevBlockHash = self.prevBlockHash.hex()
        if isinstance(self.merkleRoot, bytes):
            self.merkleRoot = self.merkleRoot.hex()
        if isinstance(self.bits, bytes):
            self.bits = self.bits.hex()

    def to_bytes(self):
        """Deserialise hex strings back to bytes (before binary network send)."""
        if isinstance(self.prevBlockHash, str):
            self.prevBlockHash = bytes.fromhex(self.prevBlockHash)
        if isinstance(self.merkleRoot, str):
            self.merkleRoot = bytes.fromhex(self.merkleRoot)
        if isinstance(self.bits, str):
            self.bits = bytes.fromhex(self.bits)

    def to_dict(self):
        return self.__dict__

    @classmethod
    def parse(cls, s):
        """Parse a block header from a byte stream."""
        version = little_endian_to_int(s.read(4))
        prevBlockHash = s.read(32)[::-1]
        merkleRoot = s.read(32)
        timestamp = little_endian_to_int(s.read(4))
        bits = s.read(4)
        nonce = little_endian_to_int(s.read(4))
        return cls(version, prevBlockHash, merkleRoot, timestamp, bits, nonce)

    def serialize(self):
        """Serialize the block header to bytes for network transmission."""
        result = int_to_little_endian(self.version, 4)
        result += bytes.fromhex(self.prevBlockHash)[::-1] if isinstance(self.prevBlockHash, str) else self.prevBlockHash[::-1]
        result += bytes.fromhex(self.merkleRoot) if isinstance(self.merkleRoot, str) else self.merkleRoot
        result += int_to_little_endian(self.timestamp, 4)
        result += bytes.fromhex(self.bits) if isinstance(self.bits, str) else self.bits
        result += int_to_little_endian(self.nonce, 4)
        return result

    def to_bytes(self):
        """Return raw serialized bytes of the block header."""
        return self.serialize()

    def to_hex(self):
        """Return hexadecimal string representation of the serialized header."""
        return self.serialize().hex()

