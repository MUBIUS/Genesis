import sys
import os

# Dynamically resolve the project root so the app works on any machine
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Flask, render_template, request, redirect, url_for, jsonify
from Blockchain.client.sendBTC import SendBTC
from Blockchain.Backend.core.Tx import Tx
from Blockchain.Backend.core.database.database import BlockchainDB, NodeDB
from Blockchain.Backend.util.util import encode_base58, decode_base58
from Blockchain.Backend.core.network.syncManager import syncManager
from hashlib import sha256
from multiprocessing import Process
from flask_qrcode import QRcode
import time
import datetime

app = Flask(__name__)
qrcode = QRcode(app)
main_prefix = b'\x00'

# Global state defaults (can be updated when running via main() or standalone)
memoryPool = {}
UTXOS = {}
MEMPOOL = {}
localHostPort = 8888


# --------------------------------------------------------------------------
# Helper: convert Unix timestamp to human-readable date
# --------------------------------------------------------------------------
def format_timestamp(ts):
    try:
        dt = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)
        return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    except Exception:
        return str(ts)


# --------------------------------------------------------------------------
# Register Jinja2 filters and globals
# --------------------------------------------------------------------------
app.jinja_env.globals.update(
    format_timestamp=format_timestamp,
    enumerate=enumerate,
)


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------
@app.route('/')
def index():
    try:
        blocks = readDatabase()
        chain_height = blocks[-1]['Height'] if blocks else 0
        total_txs = sum(b.get('TxCount') or b.get('Txcount') or 0 for b in blocks)
        recent_blocks = blocks[::-1][:5]  # 5 most recent
    except Exception:
        chain_height, total_txs, recent_blocks = 0, 0, []
    return render_template(
        'home.html',
        chain_height=chain_height,
        total_txs=total_txs,
        recent_blocks=recent_blocks,
    )


@app.route('/transactions/<txid>')
@app.route('/transactions')
def transactions(txid=None):
    if txid:
        return redirect(url_for('txDetail', txid=txid))
    try:
        allTxs = dict(UTXOS)
    except Exception:
        allTxs = {}
    return render_template('transactions.html', allTransactions=allTxs, refreshtime=10)


@app.route('/tx/<txid>')
def txDetail(txid):
    blocks = readDatabase()
    for block in blocks:
        for tx in block['Txs']:
            if tx['TxId'] == txid:
                return render_template(
                    'txDetail.html', Tx=tx, block=block,
                    encode_base58=encode_base58,
                    bytes=bytes, sha256=sha256,
                    main_prefix=main_prefix,
                    format_timestamp=format_timestamp,
                )
    return render_template('error.html', message=f'Transaction {txid} not found.')


@app.route('/mempool')
def mempool():
    try:
        blocks = readDatabase()
        try:
            mempooltxs = dict(MEMPOOL)
        except Exception:
            mempooltxs = {}

        # Prune stale entries
        for txid in list(memoryPool.keys()):
            if txid not in mempooltxs:
                del memoryPool[txid]

        for Txid in mempooltxs:
            amount = 0
            TxObj = mempooltxs[Txid]
            matchFound = False
            for txin in TxObj.tx_ins:
                for block in blocks:
                    for tx in block['Txs']:
                        if tx['TxId'] == txin.prev_tx.hex():
                            amount += tx['tx_outs'][txin.prev_index]['amount']
                            matchFound = True
                            break
                    if matchFound:
                        matchFound = False
                        break
            memoryPool[TxObj.TxId] = [TxObj.to_dict(), amount / 100_000_000, txin.prev_index]

        return render_template('mempool.html', Txs=memoryPool, refreshtime=2)

    except Exception as e:
        return render_template('mempool.html', Txs=memoryPool, refreshtime=2)


@app.route('/memTx/<txid>')
def memTxDetails(txid):
    if txid in memoryPool:
        tx = memoryPool.get(txid)[0]
        return render_template(
            'txDetail.html', Tx=tx, refreshtime=2,
            encode_base58=encode_base58, bytes=bytes, sha256=sha256,
            main_prefix=main_prefix, Unconfirmed=True,
            format_timestamp=format_timestamp,
        )
    return redirect(url_for('transactions', txid=txid))


@app.route('/search')
def search():
    identifier = (request.args.get('search') or request.args.get('q') or '').strip()
    if not identifier:
        return redirect(url_for('index'))

    blocks = readDatabase()

    # Search by block height (e.g. "0", "1", "16")
    if identifier.isdigit():
        height = int(identifier)
        for blk in blocks:
            if blk.get('Height') == height:
                return redirect(url_for('showBlock', blockHeader=blk['BlockHeader']['blockHash']))
        return render_template('error.html', message=f'Block at height #{height} not found.'), 404

    # Search by 64-char hash (block hash or txid)
    if len(identifier) == 64:
        # Check blocks first
        for blk in blocks:
            if blk['BlockHeader']['blockHash'].lower() == identifier.lower():
                return redirect(url_for('showBlock', blockHeader=blk['BlockHeader']['blockHash']))
        # Check transactions
        for blk in blocks:
            for tx in blk.get('Txs', []):
                if tx['TxId'].lower() == identifier.lower():
                    return redirect(url_for('txDetail', txid=tx['TxId']))
        return render_template('error.html', message=f'No block or transaction with hash {identifier} was found.'), 404

    # Search by Bitcoin address (starts with 1)
    if identifier.startswith('1') and 25 <= len(identifier) <= 35:
        return redirect(url_for('address', publicAddress=identifier))

    # General fallback
    return render_template('error.html', message=f'No record found for "{identifier}". Please enter a valid block height, 64-char hash, or address.'), 404



# --------------------------------------------------------------------------
# Database helper
# --------------------------------------------------------------------------
def readDatabase():
    ErrorFlag = True
    while ErrorFlag:
        try:
            blockchain = BlockchainDB()
            blocks = blockchain.read()
            ErrorFlag = False
        except Exception:
            ErrorFlag = True
            print('Error reading database, retrying…')
    return blocks or []


# --------------------------------------------------------------------------
# Block routes
# --------------------------------------------------------------------------
@app.route('/block')
def block():
    if request.args.get('blockHeader'):
        return redirect(url_for('showBlock', blockHeader=request.args.get('blockHeader')))
    blocks = readDatabase()
    return render_template('block.html', blocks=blocks, refreshtime=10)


@app.route('/block/<blockHeader>')
def showBlock(blockHeader):
    blocks = readDatabase()
    for blk in blocks:
        if blk['BlockHeader']['blockHash'] == blockHeader:
            return render_template(
                'blockDetails.html', block=blk,
                main_prefix=main_prefix,
                encode_base58=encode_base58,
                bytes=bytes, sha256=sha256,
                format_timestamp=format_timestamp,
            )
    return render_template('error.html', message=f'Block {blockHeader} not found.')


# --------------------------------------------------------------------------
# Address route
# --------------------------------------------------------------------------
@app.route('/address/<publicAddress>')
def address(publicAddress):
    if len(publicAddress) < 35 and publicAddress.startswith('1'):
        try:
            h160 = decode_base58(publicAddress)
        except Exception:
            return render_template('error.html', message='Invalid Bitcoin address.')

        ErrorFlag = True
        while ErrorFlag:
            try:
                AllUtxos = dict(UTXOS)
                ErrorFlag = False
            except Exception:
                ErrorFlag = True

        amount = 0
        AccountUtxos = []
        for TxId in AllUtxos:
            tx_obj = AllUtxos[TxId]
            for tx_out in tx_obj.tx_outs:
                if tx_out.script_pubkey.cmds[2] == h160:
                    amount += tx_out.amount
                    AccountUtxos.append(AllUtxos[TxId])

        return render_template(
            'address.html',
            Txs=AccountUtxos, amount=amount,
            encode_base58=encode_base58,
            bytes=bytes, sha256=sha256,
            main_prefix=main_prefix,
            publicAddress=publicAddress,
            qrcode=qrcode,
        )
    return render_template('error.html', message='Invalid Bitcoin address format.')


# --------------------------------------------------------------------------
# Wallet route
# --------------------------------------------------------------------------
@app.route('/wallet', methods=['GET', 'POST'])
def wallet():
    message = ''
    message_type = ''

    if request.method == 'POST':
        FromAddress = request.form.get('fromAddress', '').strip()
        ToAddress = request.form.get('toAddress', '').strip()
        Amount = request.form.get('Amount', type=int)

        if not FromAddress or not ToAddress or not Amount:
            message = 'All fields are required.'
            message_type = 'error'
        else:
            try:
                sendCoin = SendBTC(FromAddress, ToAddress, Amount, UTXOS)
                TxObj = sendCoin.prepareTransaction()
                scriptPubKey = sendCoin.scriptPubKey(FromAddress)
                verified = True

                if not TxObj:
                    message = 'Invalid transaction: insufficient funds or unknown address.'
                    message_type = 'error'
                elif isinstance(TxObj, Tx):
                    for index, tx in enumerate(TxObj.tx_ins):
                        if not TxObj.verify_input(index, scriptPubKey):
                            verified = False

                    if verified:
                        MEMPOOL[TxObj.TxId] = TxObj
                        relayTxs = Process(target=broadcastTx, args=(TxObj, localHostPort))
                        relayTxs.start()
                        message = f'Transaction {TxObj.TxId[:16]}… submitted to mempool.'
                        message_type = 'success'
                    else:
                        message = 'Transaction signature verification failed.'
                        message_type = 'error'
            except Exception as e:
                message = f'Transaction error: {str(e)}'
                message_type = 'error'

    return render_template('wallet.html', message=message, message_type=message_type)


# --------------------------------------------------------------------------
# JSON API endpoints (bonus — useful for demos)
# --------------------------------------------------------------------------
@app.route('/api/stats')
def api_stats():
    try:
        blocks = readDatabase()
        chain_height = blocks[-1]['Height'] if blocks else 0
        total_txs = sum(b.get('TxCount') or b.get('Txcount') or 0 for b in blocks)
        return jsonify({
            'chain_height': chain_height,
            'total_blocks': len(blocks),
            'total_transactions': total_txs,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/blocks')
def api_blocks():
    try:
        blocks = readDatabase()
        result = []
        for b in blocks[::-1][:20]:  # last 20 blocks
            result.append({
                'height': b['Height'],
                'hash': b['BlockHeader']['blockHash'],
                'timestamp': b['BlockHeader']['timestamp'],
                'tx_count': b.get('TxCount') or b.get('Txcount') or 0,
                'size': b.get('Blocksize', 0),
                'nonce': b['BlockHeader']['nonce'],
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# --------------------------------------------------------------------------
# Broadcast helper
# --------------------------------------------------------------------------
def broadcastTx(TxObj, localHostPort=None):
    try:
        node = NodeDB()
        portList = node.read()
        for port in portList:
            if localHostPort != port:
                sync = syncManager('127.0.0.1', port)
                try:
                    sync.connectToHost(localHostPort - 1, port)
                    sync.publishTx(TxObj)
                except Exception:
                    pass
    except Exception:
        pass


# --------------------------------------------------------------------------
# App entry point (called from blockchain.py via multiprocessing)
# --------------------------------------------------------------------------
def main(utxos, MemPool, port, localPort):
    global UTXOS, MEMPOOL, localHostPort
    UTXOS = utxos
    MEMPOOL = MemPool
    localHostPort = localPort
    app.run(port=port, debug=False, use_reloader=False)
