open IPFS desktop app and run it before you do anything.
to use the program just run  {python gui_app_blockchain.py}
Upload a file go to the blockchain section and connect to an RPC provider
generate new wallet and save your private key
paste in your contract address from the deployed smart contract what I did provide you here in the files
then hit pin selected files on blockchain your files will be stored as you wish for one day until 100 days

# Encryptum Clone - Essential Requirements 
# Python 3.7+ required

# Core Dependencies
cryptography>=41.0.0
requests>=2.31.0
python-dotenv>=1.0.0

# Blockchain
web3>=6.0.0
eth-account>=0.10.0
eth-utils>=2.3.0

# GUI (tkinter comes with Python)
# tkinter is included in Python standard library

# Optional but recommended
colorlog>=6.7.0


# System Requirements

## Prerequisites

### 1. Python 3.7+
- Download from: https://www.python.org/downloads/
- Verify: `python --version`

### 2. IPFS Desktop
- **REQUIRED**: Download from https://docs.ipfs.tech/install/ipfs-desktop/
- Install and ensure IPFS daemon is running
- Default API port: 5001

### 3. Git (optional)
- For cloning the repository
- Download from: https://git-scm.com/

## Quick Install

```bash
# 1. Install IPFS Desktop (see link above)
# 2. Start IPFS daemon
# 3. Install Python packages:
pip install -r requirements.txt
