import unittest
import sys
import os
import json

# Ensure blockchain directory is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOCKCHAIN_DIR = os.path.join(BASE_DIR, "blockchain")
if BLOCKCHAIN_DIR not in sys.path:
    sys.path.insert(0, BLOCKCHAIN_DIR)

from Blockchain.Backend.util.util import hash256, hash160, encode_base58, decode_base58, int_to_little_endian, little_endian_to_int
from Blockchain.Backend.core.EllepticCurve.EllepticCurve import Sha256Point, PrivateKey
from Blockchain.Backend.core.blockHeader import BlockHeader
from Blockchain.Backend.core.Tx import Tx, TxIn, TxOut
from Blockchain.Backend.core.database.database import BlockchainDB
from Blockchain.Frontend.run import app, readDatabase


class TestCryptography(unittest.TestCase):
    """Test cryptographic primitives: SHA256, RIPEMD160, Base58, ECDSA."""

    def test_hash256(self):
        data = b"hello genesis"
        digest = hash256(data)
        self.assertEqual(len(digest), 32)
        self.assertIsInstance(digest, bytes)

    def test_hash160(self):
        data = b"bitcoin address test"
        digest = hash160(data)
        self.assertEqual(len(digest), 20)
        self.assertIsInstance(digest, bytes)

    def test_base58_encoding_decoding(self):
        # Bitcoin Base58Check: prefix (1 byte) + h160 (20 bytes) + checksum (4 bytes)
        prefix = b"\x00"
        h160 = b"\x12" * 20
        payload = prefix + h160
        checksum = hash256(payload)[:4]
        full_payload = payload + checksum
        encoded = encode_base58(full_payload)
        self.assertTrue(isinstance(encoded, str))
        decoded_h160 = decode_base58(encoded)
        self.assertEqual(h160, decoded_h160)

    def test_private_key_and_public_key(self):
        secret = 0x123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef0
        priv = PrivateKey(secret=secret)
        self.assertIsNotNone(priv.point)
        # Check sec serialization (compressed)
        sec_compressed = priv.point.sec(compressed=True)
        self.assertEqual(len(sec_compressed), 33)
        self.assertIn(sec_compressed[0], (2, 3))

    def test_ecdsa_signing_and_verification(self):
        priv = PrivateKey(secret=999999999)
        z = 0xabcdef1234567890abcdef1234567890
        sig = priv.sign(z)
        self.assertIsNotNone(sig.r)
        self.assertIsNotNone(sig.s)
        # Verify with public key point
        valid = priv.point.verify(z, sig)
        self.assertTrue(valid)


class TestBlockHeader(unittest.TestCase):
    """Test BlockHeader creation, serialization, and hashing."""

    def test_block_header_serialization(self):
        version = 1
        prev_block = "00" * 32
        merkle_root = "ff" * 32
        timestamp = 1700000000
        bits = b"\x04\x8d\x15\x1f"
        nonce = 12345

        header = BlockHeader(
            version=version,
            prevBlockHash=prev_block,
            merkleRoot=merkle_root,
            timestamp=timestamp,
            bits=bits,
            nonce=nonce
        )
        raw = header.to_hex()
        self.assertTrue(len(raw) > 0)
        self.assertEqual(header.version, 1)
        self.assertEqual(header.timestamp, 1700000000)

    def test_block_hash_computation(self):
        header = BlockHeader(
            version=1,
            prevBlockHash="0" * 64,
            merkleRoot="a" * 64,
            timestamp=1600000000,
            bits=b"\x04\x8d\x15\x1f",
            nonce=0
        )
        h = header.generateBlockHash()
        self.assertEqual(len(h), 64)
        # Hash should be hexadecimal
        int(h, 16)


class TestDatabase(unittest.TestCase):
    """Test BlockchainDB read operations."""

    def test_read_blockchain(self):
        db = BlockchainDB()
        blocks = db.read()
        self.assertIsInstance(blocks, list)
        self.assertGreater(len(blocks), 0, "Genesis blockchain database should contain mined blocks")
        # Check genesis block structure
        first_block = blocks[0]
        self.assertEqual(first_block["Height"], 0)
        self.assertIn("BlockHeader", first_block)
        self.assertIn("Txs", first_block)


class TestFlaskExplorer(unittest.TestCase):
    """Test the Flask Block Explorer web routes."""

    def setUp(self):
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_home_page(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Genesis", res.data)
        self.assertIn(b"Block Explorer", res.data)

    def test_blocks_list_page(self):
        res = self.client.get("/block")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Latest Blocks", res.data)

    def test_transactions_page(self):
        res = self.client.get("/transactions")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Unspent Transactions", res.data)

    def test_mempool_page(self):
        res = self.client.get("/mempool")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Memory Pool", res.data)

    def test_wallet_page(self):
        res = self.client.get("/wallet")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Send Bitcoin", res.data)

    def test_api_stats(self):
        res = self.client.get("/api/stats")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("chain_height", data)
        self.assertIn("total_blocks", data)
        self.assertGreater(data["total_blocks"], 0)

    def test_api_blocks(self):
        res = self.client.get("/api/blocks")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_block_detail_page(self):
        blocks = readDatabase()
        if blocks:
            b_hash = blocks[0]["BlockHeader"]["blockHash"]
            res = self.client.get(f"/block/{b_hash}")
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Block #0", res.data)

    def test_tx_detail_page(self):
        blocks = readDatabase()
        if blocks and blocks[0].get("Txs"):
            txid = blocks[0]["Txs"][0]["TxId"]
            res = self.client.get(f"/tx/{txid}")
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Transaction Details", res.data)

    def test_search_by_height(self):
        res = self.client.get("/search?q=0", follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Block #0", res.data)

    def test_search_not_found(self):
        res = self.client.get("/search?q=nonexistent12345", follow_redirects=True)
        self.assertEqual(res.status_code, 404)
        self.assertIn(b"Not Found", res.data)


if __name__ == "__main__":
    unittest.main()
