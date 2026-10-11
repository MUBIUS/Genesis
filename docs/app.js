/**
 * Genesis — Block Explorer & Interactive Bitcoin Simulation
 * Pure vanilla JavaScript with Web Crypto API and zero external runtime dependencies.
 */

// Initial in-memory blocks ledger (loaded dynamically from data/blocks.json or seed)
let chainData = [
  {
    "Height": 0,
    "Blocksize": 167,
    "TxCount": 1,
    "BlockHeader": {
      "blockHash": "00007c265d07baea149587441ad95d129b17d25e49004c9f132748684c1db348",
      "prevBlockHash": "0000000000000000000000000000000000000000000000000000000000000000",
      "merkleRoot": "4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b",
      "timestamp": 1231006505,
      "bits": "1f158d04",
      "nonce": 2083236893
    },
    "Txs": [
      {
        "TxId": "4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b",
        "tx_ins": [],
        "tx_outs": [{"amount": 5000000000, "scriptPubKey": "OP_DUP OP_HASH160 1GenesisCoinbaseRewardAddress OP_EQUALVERIFY OP_CHECKSIG"}]
      }
    ]
  }
];

// -----------------------------------------------------------------------------
// Base58 Alphabet & Helpers
// -----------------------------------------------------------------------------
const BASE58_ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';

function encodeBase58(buffer) {
  const digits = [0];
  for (let i = 0; i < buffer.length; i++) {
    for (let j = 0; j < digits.length; j++) digits[j] <<= 8;
    digits[j] += buffer[i];
    let carry = 0;
    for (let j = 0; j < digits.length; j++) {
      digits[j] += carry;
      carry = (digits[j] / 58) | 0;
      digits[j] %= 58;
    }
    while (carry) {
      digits.push(carry % 58);
      carry = (carry / 58) | 0;
    }
  }
  for (let i = 0; i < buffer.length && buffer[i] === 0; i++) {
    digits.push(0);
  }
  return digits.reverse().map(digit => BASE58_ALPHABET[digit]).join('');
}

// Format unix timestamp
function formatTimestamp(ts) {
  try {
    const d = new Date(ts * 1000);
    return d.toISOString().replace('T', ' ').substring(0, 19) + ' UTC';
  } catch (e) {
    return ts;
  }
}

// -----------------------------------------------------------------------------
// Web Crypto Double SHA-256
// -----------------------------------------------------------------------------
async function sha256(buffer) {
  return await crypto.subtle.digest('SHA-256', buffer);
}

async function sha256d(buffer) {
  const first = await sha256(buffer);
  const second = await sha256(first);
  return new Uint8Array(second);
}

function bufToHex(buffer) {
  return Array.from(new Uint8Array(buffer))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
}

// -----------------------------------------------------------------------------
// Load chain data from blocks.json
// -----------------------------------------------------------------------------
async function loadChainData() {
  try {
    const res = await fetch('data/blocks.json');
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        chainData = data;
      }
    }
  } catch (err) {
    console.warn('Could not fetch data/blocks.json, using seed chain data.', err);
  }
  renderExplorer();
}

// -----------------------------------------------------------------------------
// Navigation Tabs
// -----------------------------------------------------------------------------
function setupTabs() {
  const tabBtns = document.querySelectorAll('.nav-tab');
  const panes = document.querySelectorAll('.tab-pane');

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetTab = btn.getAttribute('data-tab');

      tabBtns.forEach(b => b.classList.remove('active'));
      panes.forEach(p => p.classList.add('hidden'));

      btn.classList.add('active');
      const targetPane = document.getElementById('pane-' + targetTab);
      if (targetPane) {
        targetPane.classList.remove('hidden');
      }
      window.location.hash = targetTab;
    });
  });

  const currentHash = window.location.hash.replace('#', '');
  if (currentHash) {
    const targetBtn = document.querySelector(`.nav-tab[data-tab="${currentHash}"]`);
    if (targetBtn) targetBtn.click();
  }
}

// -----------------------------------------------------------------------------
// Block Explorer Rendering
// -----------------------------------------------------------------------------
function renderExplorer() {
  const tbody = document.getElementById('blocks-table-body');
  if (!tbody) return;

  tbody.innerHTML = '';
  const reversedBlocks = [...chainData].reverse();

  reversedBlocks.forEach(block => {
    const tr = document.createElement('tr');
    tr.style.cursor = 'pointer';

    const height = block.Height;
    const header = block.BlockHeader;
    const hash = header.blockHash;
    const shortHash = hash.substring(0, 10) + '…' + hash.substring(hash.length - 8);
    const txCount = block.TxCount || (block.Txs ? block.Txs.length : 1);
    const size = block.Blocksize || 167;
    const nonce = header.nonce;
    const timeFormatted = formatTimestamp(header.timestamp);

    tr.innerHTML = `
      <td><span class="height-badge">#${height}</span></td>
      <td class="hash-cell">
        <span class="hash-link text-accent" title="${hash}">${shortHash}</span>
      </td>
      <td>${timeFormatted}</td>
      <td>${txCount}</td>
      <td>${size} B</td>
      <td class="mono">${nonce}</td>
      <td>
        <button class="btn btn-outline btn-sm" onclick="openBlockModal(${height})">Inspect</button>
      </td>
    `;

    tr.addEventListener('click', (e) => {
      if (e.target.tagName !== 'BUTTON') {
        openBlockModal(height);
      }
    });

    tbody.appendChild(tr);
  });

  // Update Stats
  const statHeight = document.getElementById('stat-height');
  const statTxs = document.getElementById('stat-txs');
  const badge = document.getElementById('block-count-badge');

  if (statHeight) statHeight.textContent = '#' + chainData[chainData.length - 1].Height;
  if (badge) badge.textContent = chainData.length + ' Blocks';
  if (statTxs) {
    const totalTxs = chainData.reduce((acc, b) => acc + (b.TxCount || (b.Txs ? b.Txs.length : 1)), 0);
    statTxs.textContent = totalTxs;
  }
}

// -----------------------------------------------------------------------------
// Block Detail Modal
// -----------------------------------------------------------------------------
function openBlockModal(height) {
  const block = chainData.find(b => b.Height === height);
  if (!block) return;

  const modal = document.getElementById('block-modal');
  const modalTitle = document.getElementById('modal-title');
  const modalBody = document.getElementById('modal-body');

  modalTitle.textContent = `Block #${block.Height} — Details`;

  const header = block.BlockHeader;
  const txs = block.Txs || [];

  let txHtml = '';
  txs.forEach((tx, idx) => {
    let inputsHtml = '';
    (tx.tx_ins || []).forEach(tin => {
      const prevTxHex = tin.prev_tx ? (typeof tin.prev_tx === 'string' ? tin.prev_tx : tin.prev_tx.hex || tin.prev_tx) : 'Coinbase';
      inputsHtml += `
        <div style="font-size:0.8rem; margin-bottom:0.25rem;">
          <span class="mono text-secondary">Prev: ${String(prevTxHex).substring(0, 16)}… (Out #${tin.prev_index})</span>
        </div>`;
    });

    let outputsHtml = '';
    (tx.tx_outs || []).forEach(tout => {
      const btc = (tout.amount / 100000000).toFixed(4);
      outputsHtml += `
        <div style="font-size:0.8rem; margin-bottom:0.25rem;">
          <span class="text-success mono">${btc} BTC</span>
        </div>`;
    });

    txHtml += `
      <div style="background:var(--bg-secondary); border:1px solid var(--border-subtle); border-radius:var(--radius-md); padding:1rem; margin-bottom:0.75rem;">
        <div style="font-size:0.75rem; color:var(--text-muted); margin-bottom:0.4rem;">TRANSACTION #${idx}</div>
        <div class="mono text-accent break-all" style="font-size:0.85rem; margin-bottom:0.5rem;">${tx.TxId}</div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:1rem;">
          <div>
            <div style="font-size:0.72rem; color:var(--text-muted);">INPUTS</div>
            ${inputsHtml || '<div style="font-size:0.8rem;">Coinbase (Newly Generated)</div>'}
          </div>
          <div>
            <div style="font-size:0.72rem; color:var(--text-muted);">OUTPUTS</div>
            ${outputsHtml}
          </div>
        </div>
      </div>
    `;
  });

  modalBody.innerHTML = `
    <div style="display:flex; flex-direction:column; gap:1rem;">
      <div style="background:var(--bg-secondary); padding:1rem; border-radius:var(--radius-md); border:1px solid var(--border-subtle);">
        <div style="font-size:0.72rem; color:var(--text-muted); letter-spacing:0.05em;">BLOCK HASH</div>
        <div class="mono text-accent break-all" style="font-size:0.95rem; margin-top:0.25rem;">${header.blockHash}</div>
      </div>

      <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); gap:0.75rem;">
        <div style="background:var(--bg-secondary); padding:0.75rem; border-radius:var(--radius-sm); border:1px solid var(--border-subtle);">
          <div style="font-size:0.7rem; color:var(--text-muted);">HEIGHT</div>
          <div class="mono text-lg text-accent">#${block.Height}</div>
        </div>
        <div style="background:var(--bg-secondary); padding:0.75rem; border-radius:var(--radius-sm); border:1px solid var(--border-subtle);">
          <div style="font-size:0.7rem; color:var(--text-muted);">TIMESTAMP</div>
          <div style="font-size:0.85rem;">${formatTimestamp(header.timestamp)}</div>
        </div>
        <div style="background:var(--bg-secondary); padding:0.75rem; border-radius:var(--radius-sm); border:1px solid var(--border-subtle);">
          <div style="font-size:0.7rem; color:var(--text-muted);">NONCE</div>
          <div class="mono text-lg">${header.nonce}</div>
        </div>
        <div style="background:var(--bg-secondary); padding:0.75rem; border-radius:var(--radius-sm); border:1px solid var(--border-subtle);">
          <div style="font-size:0.7rem; color:var(--text-muted);">BLOCK SIZE</div>
          <div>${block.Blocksize || 167} bytes</div>
        </div>
      </div>

      <div style="background:var(--bg-secondary); padding:1rem; border-radius:var(--radius-md); border:1px solid var(--border-subtle);">
        <div style="font-size:0.72rem; color:var(--text-muted); margin-bottom:0.25rem;">MERKLE ROOT</div>
        <div class="mono break-all" style="font-size:0.85rem; color:var(--text-secondary);">${header.merkleRoot}</div>
      </div>

      <div style="background:var(--bg-secondary); padding:1rem; border-radius:var(--radius-md); border:1px solid var(--border-subtle);">
        <div style="font-size:0.72rem; color:var(--text-muted); margin-bottom:0.25rem;">PREVIOUS BLOCK HASH</div>
        <div class="mono break-all" style="font-size:0.85rem; color:var(--text-secondary);">${header.prevBlockHash}</div>
      </div>

      <div>
        <h4 style="margin-bottom:0.75rem; font-size:1.05rem;">Transactions (${txs.length})</h4>
        ${txHtml}
      </div>
    </div>
  `;

  modal.classList.remove('hidden');
}

function setupModal() {
  const modal = document.getElementById('block-modal');
  const closeBtn = document.getElementById('modal-close-btn');
  const backdrop = document.getElementById('modal-backdrop');

  const closeModal = () => modal.classList.add('hidden');

  if (closeBtn) closeBtn.addEventListener('click', closeModal);
  if (backdrop) backdrop.addEventListener('click', closeModal);

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
      closeModal();
    }
  });
}

// -----------------------------------------------------------------------------
// Search Bar Functionality
// -----------------------------------------------------------------------------
function setupSearch() {
  const searchInput = document.getElementById('chain-search-input');
  const searchBtn = document.getElementById('chain-search-btn');
  const feedback = document.getElementById('search-feedback');

  const doSearch = () => {
    const q = (searchInput.value || '').trim();
    if (!q) return;

    feedback.classList.add('hidden');

    // 1. Search by height
    if (/^#?\d+$/.test(q)) {
      const height = parseInt(q.replace('#', ''), 10);
      const match = chainData.find(b => b.Height === height);
      if (match) {
        openBlockModal(match.Height);
        return;
      }
    }

    // 2. Search by block hash
    const hashMatch = chainData.find(b => b.BlockHeader.blockHash.toLowerCase() === q.toLowerCase());
    if (hashMatch) {
      openBlockModal(hashMatch.Height);
      return;
    }

    // 3. Search by txid
    for (const b of chainData) {
      if (b.Txs) {
        const txMatch = b.Txs.find(t => t.TxId && t.TxId.toLowerCase() === q.toLowerCase());
        if (txMatch) {
          openBlockModal(b.Height);
          return;
        }
      }
    }

    // 4. Not found feedback
    feedback.textContent = `No block or transaction found matching "${q}". Try height #0 through #${chainData.length - 1}.`;
    feedback.classList.remove('hidden');
  };

  if (searchBtn) searchBtn.addEventListener('click', doSearch);
  if (searchInput) {
    searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') doSearch();
    });
  }
}

// -----------------------------------------------------------------------------
// Interactive Proof of Work Mining Simulator
// -----------------------------------------------------------------------------
let isMining = false;
let currentNonce = 0;
let miningStartTime = 0;

function setupMining() {
  const startBtn = document.getElementById('btn-start-mining');
  const resetBtn = document.getElementById('btn-reset-mining');
  const difficultySelect = document.getElementById('mine-difficulty');
  const payloadInput = document.getElementById('mine-payload');
  const prevHashInput = document.getElementById('mine-prev-hash');

  const liveNonce = document.getElementById('live-nonce');
  const liveHashrate = document.getElementById('live-hashrate');
  const liveElapsed = document.getElementById('live-elapsed');
  const liveStatus = document.getElementById('live-status');
  const liveHash = document.getElementById('live-hash');
  const liveTarget = document.getElementById('live-target');
  const successAlert = document.getElementById('mining-success-alert');
  const successDetails = document.getElementById('mining-success-details');

  const updateTargetDisplay = () => {
    const zeros = parseInt(difficultySelect.value, 10);
    liveTarget.textContent = '0'.repeat(zeros) + '...';
  };

  difficultySelect.addEventListener('change', updateTargetDisplay);
  updateTargetDisplay();

  const stopMining = () => {
    isMining = false;
    document.getElementById('mining-btn-text').textContent = 'Start Mining';
    document.getElementById('mining-btn-icon').textContent = '⚡';
    liveStatus.textContent = 'Paused';
    liveStatus.className = 'telemetry-val text-muted';
  };

  resetBtn.addEventListener('click', () => {
    stopMining();
    currentNonce = 0;
    liveNonce.textContent = '0';
    liveHashrate.textContent = '0 H/s';
    liveElapsed.textContent = '0.0s';
    liveHash.textContent = 'Reset to nonce 0.';
    successAlert.classList.add('hidden');
  });

  startBtn.addEventListener('click', async () => {
    if (isMining) {
      stopMining();
      return;
    }

    isMining = true;
    document.getElementById('mining-btn-text').textContent = 'Stop Mining';
    document.getElementById('mining-btn-icon').textContent = '⏸';
    liveStatus.textContent = 'Hashing...';
    liveStatus.className = 'telemetry-val text-accent text-glow';
    successAlert.classList.add('hidden');

    miningStartTime = performance.now();
    let hashesComputed = 0;
    const targetZeros = parseInt(difficultySelect.value, 10);
    const targetPrefix = '0'.repeat(targetZeros);

    const encoder = new TextEncoder();
    const prevHash = prevHashInput.value.trim();
    const payload = payloadInput.value.trim();

    async function mineBatch() {
      if (!isMining) return;

      const batchSize = 150;
      let found = false;
      let winningHash = '';

      for (let i = 0; i < batchSize; i++) {
        currentNonce++;
        hashesComputed++;

        const blockHeaderString = `${prevHash}:${payload}:${currentNonce}`;
        const hashBuf = await sha256d(encoder.encode(blockHeaderString));
        const hashHex = bufToHex(hashBuf);

        if (hashHex.startsWith(targetPrefix)) {
          found = true;
          winningHash = hashHex;
          break;
        }

        if (i === batchSize - 1) {
          liveHash.textContent = hashHex;
        }
      }

      const elapsedSeconds = (performance.now() - miningStartTime) / 1000;
      const rate = Math.round(hashesComputed / Math.max(elapsedSeconds, 0.001));

      liveNonce.textContent = currentNonce.toLocaleString();
      liveElapsed.textContent = elapsedSeconds.toFixed(1) + 's';
      liveHashrate.textContent = rate.toLocaleString() + ' H/s';

      if (found) {
        stopMining();
        liveHash.textContent = winningHash;
        liveStatus.textContent = 'Block Solved!';
        liveStatus.className = 'telemetry-val text-success text-glow';

        successDetails.innerHTML = `
          <strong>Hash:</strong> <code class="mono break-all">${winningHash}</code><br/>
          <strong>Winning Nonce:</strong> ${currentNonce.toLocaleString()}<br/>
          <strong>Time Taken:</strong> ${elapsedSeconds.toFixed(2)}s (${rate.toLocaleString()} H/s)
        `;
        successAlert.classList.remove('hidden');

        // Add newly mined block to chainData
        const newBlock = {
          Height: chainData.length,
          Blocksize: 167,
          TxCount: 1,
          BlockHeader: {
            blockHash: winningHash,
            prevBlockHash: prevHash,
            merkleRoot: '4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b',
            timestamp: Math.floor(Date.now() / 1000),
            bits: '1f158d04',
            nonce: currentNonce
          },
          Txs: [{
            TxId: winningHash,
            tx_ins: [],
            tx_outs: [{ amount: 5000000000, scriptPubKey: 'OP_DUP OP_HASH160 1GenesisMiner OP_EQUALVERIFY OP_CHECKSIG' }]
          }]
        };

        chainData.push(newBlock);
        renderExplorer();
      } else {
        requestAnimationFrame(mineBatch);
      }
    }

    requestAnimationFrame(mineBatch);
  });
}

// -----------------------------------------------------------------------------
// Interactive Key & Address Generator
// -----------------------------------------------------------------------------
function generateNewKeypair() {
  const randomBytes = new Uint8Array(32);
  crypto.getRandomValues(randomBytes);
  const privHex = '0x' + bufToHex(randomBytes);

  const pubKeyBytes = new Uint8Array(33);
  pubKeyBytes[0] = (randomBytes[31] % 2 === 0) ? 0x02 : 0x03;
  for (let i = 1; i < 33; i++) {
    pubKeyBytes[i] = (randomBytes[i - 1] ^ 0x5a) % 256;
  }
  const pubKeyHex = bufToHex(pubKeyBytes);

  const hash160Bytes = new Uint8Array(20);
  for (let i = 0; i < 20; i++) {
    hash160Bytes[i] = (pubKeyBytes[i] ^ pubKeyBytes[i + 13]) % 256;
  }
  const hash160Hex = bufToHex(hash160Bytes);

  const payload = new Uint8Array(25);
  payload[0] = 0x00;
  payload.set(hash160Bytes, 1);
  payload[21] = 0x8a;
  payload[22] = 0x1f;
  payload[23] = (randomBytes[0] ^ randomBytes[1]) % 256;
  payload[24] = (randomBytes[2] ^ randomBytes[3]) % 256;

  const address = encodeBase58(payload);

  document.getElementById('keygen-privkey').textContent = privHex;
  document.getElementById('keygen-pubkey').textContent = pubKeyHex;
  document.getElementById('keygen-hash160').textContent = hash160Hex;
  document.getElementById('keygen-address').textContent = address;
  document.getElementById('qr-address-label').textContent = address;

  renderSvgQr(address);
}

function renderSvgQr(text) {
  const container = document.getElementById('qr-container');
  if (!container) return;

  const size = 25;
  const cellSize = 6;
  const svgDim = size * cellSize;
  let rects = '';

  let hashVal = 0;
  for (let i = 0; i < text.length; i++) {
    hashVal = ((hashVal << 5) - hashVal) + text.charCodeAt(i);
    hashVal |= 0;
  }

  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const inTopLeft = (x < 7 && y < 7);
      const inTopRight = (x >= size - 7 && y < 7);
      const inBottomLeft = (x < 7 && y >= size - 7);

      let isBlack = false;
      if (inTopLeft || inTopRight || inBottomLeft) {
        const lx = inTopRight ? x - (size - 7) : x;
        const ly = inBottomLeft ? y - (size - 7) : y;
        isBlack = (lx === 0 || lx === 6 || ly === 0 || ly === 6 || (lx >= 2 && lx <= 4 && ly >= 2 && ly <= 4));
      } else {
        const bit = Math.abs(Math.sin((x * 31 + y * 17) ^ hashVal)) > 0.45;
        isBlack = bit;
      }

      if (isBlack) {
        rects += `<rect x="${x * cellSize}" y="${y * cellSize}" width="${cellSize}" height="${cellSize}" fill="#000"/>`;
      }
    }
  }

  container.innerHTML = `<svg width="${svgDim}" height="${svgDim}" viewBox="0 0 ${svgDim} ${svgDim}" xmlns="http://www.w3.org/2000/svg">${rects}</svg>`;
}

function setupKeygen() {
  const genBtn = document.getElementById('btn-generate-keys');
  const copyBtn = document.getElementById('btn-copy-address');

  if (genBtn) {
    genBtn.addEventListener('click', generateNewKeypair);
  }

  if (copyBtn) {
    copyBtn.addEventListener('click', () => {
      const addr = document.getElementById('keygen-address').textContent;
      navigator.clipboard.writeText(addr).then(() => {
        const originalText = copyBtn.textContent;
        copyBtn.textContent = 'Copied!';
        setTimeout(() => copyBtn.textContent = originalText, 1500);
      });
    });
  }

  renderSvgQr(document.getElementById('keygen-address').textContent);
}

// -----------------------------------------------------------------------------
// Interactive Script VM Visualizer
// -----------------------------------------------------------------------------
const SCRIPT_STEPS = [
  {
    op: '<sig>',
    desc: 'Push ECDSA signature to stack',
    stack: ['<sig> 30450221008d...'],
    statusTitle: 'Step 1: Unlocking Script (ScriptSig)',
    statusMsg: 'The spending transaction pushes its signature onto the stack.'
  },
  {
    op: '<pubKey>',
    desc: 'Push public key to stack',
    stack: ['<pubKey> 0289ecdc1e...', '<sig> 30450221008d...'],
    statusTitle: 'Step 2: Pushing Public Key',
    statusMsg: 'The spender pushes their public key onto the stack.'
  },
  {
    op: 'OP_DUP',
    desc: 'Duplicate top stack item',
    stack: ['<pubKey> 0289ecdc1e...', '<pubKey> 0289ecdc1e...', '<sig> 30450221008d...'],
    statusTitle: 'Step 3: OP_DUP Executed',
    statusMsg: 'The top item (public key) is duplicated so one copy can be hashed and the other retained for signature verification.'
  },
  {
    op: 'OP_HASH160',
    desc: 'Hash top stack item (SHA256 + RIPEMD160)',
    stack: ['<pubKeyHash> c88a873117...', '<pubKey> 0289ecdc1e...', '<sig> 30450221008d...'],
    statusTitle: 'Step 4: OP_HASH160 Executed',
    statusMsg: 'The top public key is hashed using SHA256 followed by RIPEMD160, yielding a 20-byte hash.'
  },
  {
    op: '<pubKeyHash>',
    desc: 'Push recipient address hash',
    stack: ['<pubKeyHash> c88a873117... (Expected)', '<pubKeyHash> c88a873117...', '<pubKey> 0289ecdc1e...', '<sig> 30450221008d...'],
    statusTitle: 'Step 5: Pushing Target PubKeyHash',
    statusMsg: 'The locking script (ScriptPubKey) pushes the expected recipient address hash.'
  },
  {
    op: 'OP_EQUALVERIFY',
    desc: 'Check hashes match and discard',
    stack: ['<pubKey> 0289ecdc1e...', '<sig> 30450221008d...'],
    statusTitle: 'Step 6: OP_EQUALVERIFY Succeeded',
    statusMsg: 'Both hashes are compared. Since they are identical, both are popped and execution proceeds.'
  },
  {
    op: 'OP_CHECKSIG',
    desc: 'Verify ECDSA signature with public key',
    stack: ['1 (TRUE) — Script Valid!'],
    statusTitle: 'Step 7: OP_CHECKSIG Evaluated',
    statusMsg: 'The signature is mathematically verified against the public key and transaction hash. The result 1 (TRUE) confirms valid ownership!'
  }
];

let vmStepIndex = -1;

function renderVmStep() {
  const opItems = document.querySelectorAll('.script-op-item');
  const stackContainer = document.getElementById('vm-stack-container');
  const statusBox = document.getElementById('vm-status-box');
  const prevBtn = document.getElementById('btn-vm-prev');
  const nextBtn = document.getElementById('btn-vm-next');

  opItems.forEach((item, idx) => {
    if (idx === vmStepIndex) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });

  if (vmStepIndex === -1) {
    stackContainer.innerHTML = '<div class="stack-item stack-empty">Stack is empty. Click "Next Step" to begin.</div>';
    statusBox.querySelector('.status-title').textContent = 'Current State: Ready';
    statusBox.querySelector('.status-msg').textContent = 'Click "Next Step" to push the unlocking script onto the execution stack.';
    prevBtn.disabled = true;
    nextBtn.disabled = false;
    return;
  }

  const step = SCRIPT_STEPS[vmStepIndex];

  let stackHtml = '';
  step.stack.forEach((item, idx) => {
    const isTop = idx === 0;
    const badge = isTop ? ' <span style="color:var(--accent-cyan); font-size:0.7rem;">(TOP)</span>' : '';
    stackHtml += `<div class="stack-item">${item}${badge}</div>`;
  });
  stackContainer.innerHTML = stackHtml;

  statusBox.querySelector('.status-title').textContent = step.statusTitle;
  statusBox.querySelector('.status-msg').textContent = step.statusMsg;

  prevBtn.disabled = vmStepIndex <= 0;
  nextBtn.disabled = vmStepIndex >= SCRIPT_STEPS.length - 1;
}

function setupScriptVm() {
  const nextBtn = document.getElementById('btn-vm-next');
  const prevBtn = document.getElementById('btn-vm-prev');
  const resetBtn = document.getElementById('btn-vm-reset');

  if (nextBtn) {
    nextBtn.addEventListener('click', () => {
      if (vmStepIndex < SCRIPT_STEPS.length - 1) {
        vmStepIndex++;
        renderVmStep();
      }
    });
  }

  if (prevBtn) {
    prevBtn.addEventListener('click', () => {
      if (vmStepIndex > 0) {
        vmStepIndex--;
        renderVmStep();
      }
    });
  }

  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      vmStepIndex = -1;
      renderVmStep();
    });
  }

  renderVmStep();
}

// -----------------------------------------------------------------------------
// Initialization
// -----------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  setupTabs();
  loadChainData();
  setupModal();
  setupSearch();
  setupMining();
  setupKeygen();
  setupScriptVm();
});
