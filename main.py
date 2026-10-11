#!/usr/bin/env python3
"""
Genesis — Bitcoin Blockchain Built From Scratch in Python
Entry-point CLI for launching the explorer, running tests, or inspecting the chain.
"""

import sys
import os
import argparse

# Ensure the blockchain package is on the Python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BLOCKCHAIN_DIR = os.path.join(ROOT_DIR, "blockchain")
if BLOCKCHAIN_DIR not in sys.path:
    sys.path.insert(0, BLOCKCHAIN_DIR)


def run_explorer(port=5900, host="127.0.0.1", debug=False):
    """Launch the Flask Block Explorer web server."""
    print("=" * 60)
    print("  GENESIS — BITCOIN BLOCK EXPLORER")
    print("=" * 60)
    print(f"  Web Explorer running at: http://{host}:{port}/")
    print("  Press Ctrl+C to stop.")
    print("=" * 60)
    from Blockchain.Frontend.run import app
    app.run(host=host, port=port, debug=debug, use_reloader=False)


def run_tests():
    """Execute the full automated test suite."""
    print("=" * 60)
    print("  GENESIS — RUNNING TEST SUITE")
    print("=" * 60)
    import unittest
    loader = unittest.TestLoader()
    suite = loader.discover(os.path.join(ROOT_DIR, "tests"), pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)


def generate_account():
    """Generate a new cryptographic keypair and Bitcoin address."""
    print("=" * 60)
    print("  GENESIS — NEW BITCOIN ADDRESS GENERATOR")
    print("=" * 60)
    from Blockchain.client.account import account
    acct = account()
    acct.createKeys()
    print(f"  Private Key (Hex): {hex(acct.privateKey)}")
    print(f"  Public Address:    {acct.PublicAddress}")
    print("=" * 60)


def show_info():
    """Display chain summary statistics."""
    from Blockchain.Backend.core.database.database import BlockchainDB
    db = BlockchainDB()
    blocks = db.read() or []
    print("=" * 60)
    print("  GENESIS — BLOCKCHAIN SUMMARY")
    print("=" * 60)
    print(f"  Total Blocks on Chain: {len(blocks)}")
    if blocks:
        latest = blocks[-1]
        print(f"  Current Block Height:  #{latest.get('Height')}")
        print(f"  Latest Block Hash:     {latest.get('BlockHeader', {}).get('blockHash')}")
        total_txs = sum(b.get('TxCount') or b.get('Txcount') or 0 for b in blocks)
        print(f"  Total Transactions:    {total_txs}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Genesis: Bitcoin blockchain built from scratch in Python."
    )
    parser.add_argument(
        "--explorer",
        action="store_true",
        help="Run the Block Explorer web application (default mode)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5900,
        help="Port for the Block Explorer (default: 5900)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host for the Block Explorer (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run the automated test suite",
    )
    parser.add_argument(
        "--account",
        action="store_true",
        help="Generate a new cryptographic keypair and Bitcoin address",
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show blockchain status and summary metrics",
    )

    args = parser.parse_args()

    if args.test:
        run_tests()
    elif args.account:
        generate_account()
    elif args.info:
        show_info()
    else:
        # Default behavior: run the explorer
        run_explorer(port=args.port, host=args.host)


if __name__ == "__main__":
    main()
