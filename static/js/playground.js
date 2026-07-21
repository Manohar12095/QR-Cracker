'use strict';

const Playground = (() => {
  // Elements
  const inputEl = document.getElementById('cipher-input');
  const outputEl = document.getElementById('cipher-output');
  const selectEl = document.getElementById('cipher-select');
  const detectorEl = document.getElementById('detector-result');
  const actionBtns = document.querySelectorAll('.toggle-btn[data-action]');
  const clearBtn = document.getElementById('clear-input-btn');
  
  // Keys
  const keyContainers = document.querySelectorAll('.cipher-key-container');
  const caesarKey = document.getElementById('caesar-key');
  const vigenereKey = document.getElementById('vigenere-key');

  let currentAction = 'encode'; // default
  let currentCipher = 'base64';

  function init() {
    if (!inputEl) return;
    
    // Bind Action Buttons (Encode/Decode)
    actionBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        actionBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentAction = btn.dataset.action;
        processInput();
      });
    });

    // Bind Cipher Select
    selectEl.addEventListener('change', (e) => {
      currentCipher = e.target.value;
      updateKeyUI();
      processInput();
    });

    // Bind Inputs
    inputEl.addEventListener('input', processInput);
    caesarKey.addEventListener('input', processInput);
    vigenereKey.addEventListener('input', processInput);
    
    // Clear
    clearBtn.addEventListener('click', () => {
      inputEl.value = '';
      processInput();
    });
    
    // Save Custom Cipher
    const saveCipherBtn = document.getElementById('save-custom-cipher-btn');
    if (saveCipherBtn) {
      saveCipherBtn.addEventListener('click', async () => {
        const nameInput = document.getElementById('custom-cipher-name');
        const mappingInput = document.getElementById('custom-cipher-mapping');
        const name = nameInput.value.trim();
        const mappingStr = mappingInput.value.trim().toUpperCase();
        
        if (!name || mappingStr.length !== 26 || new Set(mappingStr.split('')).size !== 26) {
          alert("Please provide a name and exactly 26 unique letters for the mapping.");
          return;
        }

        const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
        const mappingObj = {};
        for (let i = 0; i < 26; i++) {
          mappingObj[alphabet[i]] = mappingStr[i];
        }

        try {
          const res = await fetch('/api/cipher/custom', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name, mapping: mappingObj })
          });
          const data = await res.json();
          if (data.success) {
            window.location.reload(); // Quick way to update the dropdown list
          } else {
            alert(data.error || "Failed to save cipher.");
          }
        } catch (e) {
          alert("Network Error");
        }
      });
    }

    updateKeyUI();
  }

  function updateKeyUI() {
    keyContainers.forEach(el => el.style.display = 'none');
    if (currentCipher === 'caesar') {
      document.getElementById('key-container-caesar').style.display = 'block';
    } else if (currentCipher === 'vigenere') {
      document.getElementById('key-container-vigenere').style.display = 'block';
    }
  }

  function getKey() {
    if (currentCipher === 'caesar') return caesarKey.value;
    if (currentCipher === 'vigenere') return vigenereKey.value;
    return null;
  }

  async function processInput() {
    const text = inputEl.value;
    if (!text) {
      outputEl.innerHTML = '<span style="color: var(--text-muted);">Result will appear here as you type...</span>';
      detectorEl.innerHTML = 'Waiting for input...';
      return;
    }

    // Prepare payload
    const payload = {
      text: text,
      cipher: currentCipher,
      key: getKey()
    };

    // Make request for encoding/decoding
    try {
      const endpoint = currentAction === 'encode' ? '/api/cipher/encode' : '/api/cipher/decode';
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      
      if (res.ok) {
        // Subtle fade effect
        outputEl.style.opacity = '0.5';
        setTimeout(() => {
          outputEl.textContent = data.result;
          outputEl.style.opacity = '1';
        }, 50);
      } else {
        outputEl.innerHTML = `<span style="color: var(--danger);">${data.error || 'Error'}</span>`;
      }
    } catch (e) {
      outputEl.innerHTML = `<span style="color: var(--danger);">Network Error</span>`;
    }

    // Make request for detector (only if we are typing something that could be decoded)
    // Actually, pattern detector makes sense to run on the *input* text to guess what it is.
    detectPattern(text);
  }

  async function detectPattern(text) {
    if (!text || text.length < 3) {
      detectorEl.textContent = 'Need more text to detect pattern...';
      return;
    }
    try {
      const res = await fetch('/api/cipher/detect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text })
      });
      if (res.ok) {
        const data = await res.json();
        if (data.detected && data.detected !== "Unknown") {
          detectorEl.innerHTML = `Identified Pattern: <strong>${data.detected}</strong> <br><span style="font-size:0.8rem;color:var(--text-muted);">${data.confidence}</span>`;
        } else {
          detectorEl.innerHTML = 'No clear pattern detected. Natural text or custom cipher?';
        }
      }
    } catch (e) {
      // fail silently for detector
    }
  }

  return { init };
})();

document.addEventListener('DOMContentLoaded', Playground.init);
