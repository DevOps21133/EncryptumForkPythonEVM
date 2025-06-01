"""
Encryptum Clone - GUI Application with Working Blockchain Integration
Uses private key wallet for blockchain pinning (no MetaMask needed)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import threading
import os
import logging
import json
import webbrowser
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
from web3 import Web3
from eth_account import Account
from eth_utils import to_checksum_address
import time
from decimal import Decimal

from encryption import EncryptumCrypto
from ipfs_handler import EncryptumIPFS
from config import config, validate_file_size, is_supported_file_type


# Simplified Contract ABI for pinning
PINNING_CONTRACT_ABI = [
    {
        "inputs": [
            {"name": "fileCID", "type": "string"},
            {"name": "metadataCID", "type": "string"},
            {"name": "fileSize", "type": "uint256"},
            {"name": "duration", "type": "uint256"},
            {"name": "encryptedName", "type": "string"}
        ],
        "name": "pinFile",
        "outputs": [{"name": "pinId", "type": "uint256"}],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "fileSize", "type": "uint256"},
            {"name": "duration", "type": "uint256"}
        ],
        "name": "calculatePinCost",
        "outputs": [{"name": "cost", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "pricePerGBPerDay",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]


class BlockchainPanel(tk.Frame):
    """Blockchain integration panel with private key wallet"""
    
    def __init__(self, parent, file_registry_callback=None):
        super().__init__(parent)
        self.file_registry_callback = file_registry_callback
        self.w3 = None
        self.contract = None
        self.account = None
        self.private_key = None
        self.manual_gas_price = None  # For manual gas price override
        
        self.colors = {
            'bg': '#1a1a1a',
            'panel': '#2d2d2d',
            'accent': '#00d4aa',
            'text': '#ffffff',
            'text_secondary': '#888888',
            'blockchain': '#6366f1',
            'error': '#ff4444',
            'warning': '#ffa500'
        }
        
        self.configure(bg=self.colors['bg'])
        self.setup_ui()
        self.logger = logging.getLogger(__name__)
    
    def setup_ui(self):
        """Setup blockchain panel UI"""
        # Title
        title_frame = tk.Frame(self, bg=self.colors['bg'])
        title_frame.pack(fill='x', pady=20)
        
        title = tk.Label(title_frame, text="⛓️ Blockchain File Pinning", 
                        font=('Arial', 24, 'bold'), 
                        fg=self.colors['blockchain'], bg=self.colors['bg'])
        title.pack()
        
        # Connection Section
        conn_frame = tk.LabelFrame(self, text="Blockchain Connection", 
                                  font=('Arial', 12, 'bold'), 
                                  fg=self.colors['accent'], 
                                  bg=self.colors['panel'], 
                                  relief='groove', bd=2)
        conn_frame.pack(fill='x', padx=20, pady=10)
        
        # Network selection with warning for mainnet
        net_frame = tk.Frame(conn_frame, bg=self.colors['panel'])
        net_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(net_frame, text="Network:", 
                font=('Arial', 11), fg=self.colors['text'], 
                bg=self.colors['panel']).grid(row=0, column=0, sticky='w', padx=(0, 10))
        
        self.network_var = tk.StringVar(value='sepolia')
        network_menu = ttk.Combobox(net_frame, textvariable=self.network_var,
                                   values=['sepolia', 'polygon', 'arbitrum', 'mainnet'],
                                   state='readonly', width=15)
        network_menu.grid(row=0, column=1, sticky='w')
        network_menu.bind('<<ComboboxSelected>>', self.on_network_change)
        
        # Network warning label
        self.network_warning = tk.Label(net_frame, text="", 
                                       font=('Arial', 10, 'bold'), 
                                       fg=self.colors['warning'], 
                                       bg=self.colors['panel'])
        self.network_warning.grid(row=0, column=2, padx=(10, 0))
        
        # RPC URL with dropdown
        tk.Label(net_frame, text="RPC URL:", 
                font=('Arial', 11), fg=self.colors['text'], 
                bg=self.colors['panel']).grid(row=1, column=0, sticky='w', padx=(0, 10), pady=(10, 0))
        
        rpc_frame = tk.Frame(net_frame, bg=self.colors['panel'])
        rpc_frame.grid(row=1, column=1, sticky='w', pady=(10, 0))
        
        self.rpc_entry = tk.Entry(rpc_frame, width=40)
        self.rpc_entry.pack(side='left', padx=(0, 5))
        # Use a reliable public RPC by default
        self.rpc_entry.insert(0, "https://ethereum-sepolia-rpc.publicnode.com")
        
        # RPC dropdown button
        tk.Button(rpc_frame, text="📋 Public RPCs", 
                 command=self.show_rpc_menu,
                 bg='#4a4a4a', fg='white', padx=10).pack(side='left')
        
        tk.Button(rpc_frame, text="🧪 Test", 
                 command=self.test_rpc_connection,
                 bg='#666', fg='white', padx=10).pack(side='left', padx=(5, 0))
        
        # Help text
        help_text = tk.Label(net_frame, 
                           text="Free public RPC included! Click 'Public RPCs' for 20+ options", 
                           font=('Arial', 9), fg=self.colors['text_secondary'], 
                           bg=self.colors['panel'])
        help_text.grid(row=2, column=1, sticky='w', pady=(5, 0))
        
        # Gas settings frame (NEW)
        gas_frame = tk.Frame(net_frame, bg=self.colors['panel'])
        gas_frame.grid(row=3, column=0, columnspan=3, sticky='w', pady=(10, 0))
        
        tk.Label(gas_frame, text="Gas Price (Gwei):", 
                font=('Arial', 11), fg=self.colors['text'], 
                bg=self.colors['panel']).pack(side='left', padx=(0, 10))
        
        self.gas_price_var = tk.StringVar(value="Auto")
        self.gas_price_entry = tk.Entry(gas_frame, textvariable=self.gas_price_var, width=10)
        self.gas_price_entry.pack(side='left', padx=(0, 5))
        
        tk.Label(gas_frame, text="(Enter number or 'Auto' for automatic)", 
                font=('Arial', 9), fg=self.colors['text_secondary'], 
                bg=self.colors['panel']).pack(side='left')
        
        # Connection status
        self.conn_status = tk.Label(conn_frame, 
                                   text="⚪ Not Connected", 
                                   font=('Arial', 12),
                                   fg=self.colors['text_secondary'], 
                                   bg=self.colors['panel'])
        self.conn_status.pack(pady=10)
        
        # Connect button
        self.connect_btn = tk.Button(conn_frame, 
                                    text="🔌 Connect to Blockchain", 
                                    command=self.connect_blockchain,
                                    bg=self.colors['blockchain'], 
                                    fg='white', 
                                    font=('Arial', 12, 'bold'),
                                    padx=30, pady=10)
        self.connect_btn.pack(pady=10)
        
        # Wallet Section
        wallet_frame = tk.LabelFrame(self, text="Wallet", 
                                    font=('Arial', 12, 'bold'), 
                                    fg=self.colors['accent'], 
                                    bg=self.colors['panel'], 
                                    relief='groove', bd=2)
        wallet_frame.pack(fill='x', padx=20, pady=10)
        
        # Wallet status
        self.wallet_status = tk.Label(wallet_frame, 
                                     text="No wallet loaded", 
                                     font=('Arial', 10),
                                     fg=self.colors['text_secondary'], 
                                     bg=self.colors['panel'])
        self.wallet_status.pack(pady=10)
        
        self.account_label = tk.Label(wallet_frame, 
                                     text="Account: Not connected", 
                                     font=('Arial', 10),
                                     fg=self.colors['text_secondary'], 
                                     bg=self.colors['panel'])
        self.account_label.pack()
        
        self.balance_label = tk.Label(wallet_frame, 
                                     text="Balance: --", 
                                     font=('Arial', 10),
                                     fg=self.colors['text_secondary'], 
                                     bg=self.colors['panel'])
        self.balance_label.pack(pady=(0, 10))
        
        # Wallet buttons
        wallet_btn_frame = tk.Frame(wallet_frame, bg=self.colors['panel'])
        wallet_btn_frame.pack(pady=10)
        
        tk.Button(wallet_btn_frame, text="🔑 Import Private Key", 
                 command=self.import_private_key,
                 bg='#4a4a4a', fg='white', padx=20).pack(side='left', padx=5)
        
        tk.Button(wallet_btn_frame, text="💰 Generate New Wallet", 
                 command=self.generate_wallet,
                 bg='#0066cc', fg='white', padx=20).pack(side='left', padx=5)
        
        # Contract Section
        contract_frame = tk.LabelFrame(self, text="Smart Contract", 
                                      font=('Arial', 12, 'bold'), 
                                      fg=self.colors['accent'], 
                                      bg=self.colors['panel'], 
                                      relief='groove', bd=2)
        contract_frame.pack(fill='x', padx=20, pady=10)
        
        # Contract address
        addr_frame = tk.Frame(contract_frame, bg=self.colors['panel'])
        addr_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(addr_frame, text="Contract Address:", 
                font=('Arial', 11), fg=self.colors['text'], 
                bg=self.colors['panel']).pack(side='left', padx=(0, 10))
        
        self.contract_entry = tk.Entry(addr_frame, width=50)
        self.contract_entry.pack(side='left', padx=(0, 10))
        
        tk.Button(addr_frame, text="Load Contract", 
                 command=self.load_contract,
                 bg=self.colors['accent'], fg='black', 
                 padx=20).pack(side='left')
        
        # Contract status
        self.contract_status = tk.Label(contract_frame, 
                                       text="Contract not loaded", 
                                       font=('Arial', 10),
                                       fg=self.colors['text_secondary'], 
                                       bg=self.colors['panel'])
        self.contract_status.pack(pady=(0, 10))
        
        # Pinning Section
        pin_frame = tk.LabelFrame(self, text="File Pinning", 
                                 font=('Arial', 12, 'bold'), 
                                 fg=self.colors['accent'], 
                                 bg=self.colors['panel'], 
                                 relief='groove', bd=2)
        pin_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Duration selection
        dur_frame = tk.Frame(pin_frame, bg=self.colors['panel'])
        dur_frame.pack(pady=10)
        
        tk.Label(dur_frame, text="Pin Duration:", 
                font=('Arial', 11), fg=self.colors['text'], 
                bg=self.colors['panel']).pack(side='left', padx=(0, 20))
        
        self.duration_var = tk.IntVar(value=30)
        for text, days in [('30 days', 30), ('90 days', 90), ('1 year', 365)]:
            tk.Radiobutton(dur_frame, text=text, variable=self.duration_var,
                          value=days, bg=self.colors['panel'], 
                          fg=self.colors['text'],
                          selectcolor=self.colors['panel']).pack(side='left', padx=10)
        
        # Selected files info
        self.selected_label = tk.Label(pin_frame, 
                                      text="No files selected", 
                                      font=('Arial', 10),
                                      fg=self.colors['text_secondary'], 
                                      bg=self.colors['panel'])
        self.selected_label.pack(pady=10)
        
        # Cost estimate
        self.cost_label = tk.Label(pin_frame, 
                                  text="Cost: Select files to estimate", 
                                  font=('Arial', 11, 'bold'),
                                  fg=self.colors['accent'], 
                                  bg=self.colors['panel'])
        self.cost_label.pack(pady=10)
        
        # Gas estimate (NEW)
        self.gas_estimate_label = tk.Label(pin_frame, 
                                         text="", 
                                         font=('Arial', 10),
                                         fg=self.colors['warning'], 
                                         bg=self.colors['panel'])
        self.gas_estimate_label.pack(pady=5)
        
        # Pin button
        self.pin_btn = tk.Button(pin_frame, 
                                text="📌 Pin Selected Files on Blockchain", 
                                command=self.pin_files,
                                bg=self.colors['accent'], 
                                fg='black', 
                                font=('Arial', 12, 'bold'),
                                padx=30, pady=10,
                                state='disabled')
        self.pin_btn.pack(pady=10)
        
        # Transaction log
        log_label = tk.Label(pin_frame, text="Transaction Log:", 
                           font=('Arial', 10), fg=self.colors['text'], 
                           bg=self.colors['panel'])
        log_label.pack(anchor='w', padx=20)
        
        # Log text widget
        log_frame = tk.Frame(pin_frame, bg=self.colors['panel'])
        log_frame.pack(fill='both', expand=True, padx=20, pady=(5, 20))
        
        self.log_text = tk.Text(log_frame, height=6, width=80, 
                               bg='#0a0a0a', fg=self.colors['text'],
                               font=('Consolas', 9))
        self.log_text.pack(side='left', fill='both', expand=True)
        
        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.log_text.config(yscrollcommand=scrollbar.set)
    
    def show_rpc_menu(self):
        """Show menu of public RPC endpoints"""
        # Define public RPCs - updated with all the endpoints
        public_rpcs = {
            'sepolia': [
                ("PublicNode (Recommended)", "https://ethereum-sepolia-rpc.publicnode.com"),
                ("Blast API", "https://eth-sepolia.public.blastapi.io"),
                ("DRPC", "https://sepolia.drpc.org"),
                ("1RPC", "https://1rpc.io/sepolia"),
                ("Alchemy Demo", "https://eth-sepolia.g.alchemy.com/v2/demo"),
                ("Tenderly", "https://gateway.tenderly.co/public/sepolia"),
                ("Ethpandaops", "https://rpc.sepolia.ethpandaops.io"),
                ("ZAN API", "https://api.zan.top/eth-sepolia"),
                ("OmniaNode", "https://endpoints.omniatech.io/v1/eth/sepolia/public"),
                ("Unifra", "https://eth-sepolia-public.unifra.io"),
                ("TheRPC", "https://rpc.therpc.io/ethereum-sepolia"),
                ("Owlracle", "https://rpc.owlracle.info/sepolia/70d38ce1826c4a60bb2a8e05a6c8b20f"),
                ("4everland", "https://eth-testnet.4everland.org/v1/37fa9972c1b1cd5fab542c7bdd4cde2f"),
                ("StackUp", "https://public.stackup.sh/api/v1/node/ethereum-sepolia"),
            ],
            'mainnet': [
                ("PublicNode (Fast)", "https://ethereum-rpc.publicnode.com"),
                ("Cloudflare", "https://cloudflare-eth.com"),
                ("LlamaRPC", "https://eth.llamarpc.com"),
                ("1RPC Privacy", "https://1rpc.io/eth"),
                ("Blast API", "https://eth-mainnet.public.blastapi.io"),
                ("DRPC", "https://eth.drpc.org"),
                ("Tenderly", "https://gateway.tenderly.co/public/mainnet"),
                ("Alchemy Demo", "https://eth-mainnet.g.alchemy.com/v2/demo"),
                ("BlockPi", "https://ethereum.blockpi.network/v1/rpc/public"),
                ("OmniaNode", "https://endpoints.omniatech.io/v1/eth/mainnet/public"),
                ("TheRPC", "https://rpc.therpc.io/ethereum"),
                ("Gashawk", "https://core.gashawk.io/rpc"),
                ("ZAN API", "https://api.zan.top/eth-mainnet"),
                ("Owlracle", "https://rpc.owlracle.info/eth/70d38ce1826c4a60bb2a8e05a6c8b20f"),
                ("0xRPC", "https://0xrpc.io/eth"),
            ],
            'polygon': [
                ("Polygon RPC", "https://polygon-rpc.com"),
                ("Matic Vigil", "https://rpc-mainnet.maticvigil.com"),
                ("1RPC", "https://1rpc.io/matic"),
                ("DRPC", "https://polygon.drpc.org"),
            ],
            'arbitrum': [
                ("Arbitrum Official", "https://arb1.arbitrum.io/rpc"),
                ("1RPC", "https://1rpc.io/arb"),
                ("DRPC", "https://arbitrum.drpc.org"),
            ]
        }
        
        # Create popup menu
        menu = tk.Menu(self, tearoff=0)
        
        # Get current network
        network = self.network_var.get()
        
        if network in public_rpcs:
            # Add header
            menu.add_command(label=f"=== {network.upper()} Public RPCs ===", state='disabled')
            menu.add_separator()
            
            for name, url in public_rpcs[network]:
                menu.add_command(
                    label=name,
                    command=lambda u=url: self.set_rpc_url(u)
                )
        else:
            menu.add_command(label="No public RPCs for this network", state='disabled')
        
        # Add info at bottom
        menu.add_separator()
        menu.add_command(label="💡 Click to select RPC", state='disabled')
        
        # Show menu at button location
        menu.post(self.winfo_pointerx(), self.winfo_pointery())
    
    def set_rpc_url(self, url: str):
        """Set RPC URL from menu selection"""
        self.rpc_entry.delete(0, tk.END)
        self.rpc_entry.insert(0, url)
        self.log(f"RPC URL set to: {url}", 'info')
    
    def log(self, message: str, level: str = 'info'):
        """Add message to transaction log"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Color based on level
        if level == 'error':
            tag = 'error'
        elif level == 'success':
            tag = 'success'
        elif level == 'warning':
            tag = 'warning'
        else:
            tag = 'info'
        
        self.log_text.insert('end', f"[{timestamp}] {message}\n", tag)
        self.log_text.see('end')
        
        # Configure tags
        self.log_text.tag_config('error', foreground='#ff4444')
        self.log_text.tag_config('success', foreground='#00d4aa')
        self.log_text.tag_config('warning', foreground='#ffa500')
        self.log_text.tag_config('info', foreground='#888888')
    
    def on_network_change(self, event=None):
        """Handle network selection change"""
        network = self.network_var.get()
        
        # Update RPC URL to default for the selected network
        default_rpcs = {
            'sepolia': 'https://ethereum-sepolia-rpc.publicnode.com',
            'polygon': 'https://polygon-rpc.com',
            'arbitrum': 'https://arb1.arbitrum.io/rpc',
            'mainnet': 'https://ethereum-rpc.publicnode.com'  # Updated to PublicNode
        }
        
        if network in default_rpcs:
            self.rpc_entry.delete(0, tk.END)
            self.rpc_entry.insert(0, default_rpcs[network])
            self.log(f"Network changed to {network}, RPC updated", 'info')
            
        # Update warning for mainnet
        if network == 'mainnet':
            self.network_warning.config(text="⚠️ REAL ETH!", fg='#ff0000')
            self.log("⚠️ WARNING: Mainnet uses real ETH! Be careful with transactions.", 'warning')
            messagebox.showwarning("Mainnet Warning", 
                                 "⚠️ You're switching to Ethereum Mainnet!\n\n"
                                 "This network uses REAL ETH.\n"
                                 "Transactions cost real money.\n\n"
                                 "For testing, use Sepolia instead.")
        else:
            self.network_warning.config(text="")
            if network == 'sepolia':
                self.log("Using Sepolia testnet - safe for testing", 'info')
    
    def test_rpc_connection(self):
        """Test RPC connection without fully connecting"""
        rpc_url = self.rpc_entry.get().strip()
        if not rpc_url:
            messagebox.showwarning("No URL", "Please enter an RPC URL")
            return
        
        self.log(f"Testing RPC connection to: {rpc_url}", 'info')
        
        try:
            # Quick connection test
            test_w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 5}))
            
            if test_w3.is_connected():
                chain_id = test_w3.eth.chain_id
                block_num = test_w3.eth.block_number
                
                # Get current gas price for info
                gas_price_wei = test_w3.eth.gas_price
                gas_price_gwei = float(test_w3.from_wei(gas_price_wei, 'gwei'))
                
                self.log(f"✅ RPC test successful! Chain ID: {chain_id}, Latest block: {block_num}", 'success')
                self.log(f"Current gas price: {gas_price_gwei:.2f} Gwei", 'info')
                
                messagebox.showinfo("Test Successful", 
                                  f"RPC connection successful!\n\n"
                                  f"Chain ID: {chain_id}\n"
                                  f"Latest block: {block_num}\n"
                                  f"Current gas price: {gas_price_gwei:.2f} Gwei")
            else:
                self.log(f"❌ RPC test failed - not connected", 'error')
                messagebox.showerror("Test Failed", "Could not connect to RPC endpoint")
                
        except Exception as e:
            self.log(f"❌ RPC test failed: {str(e)}", 'error')
            messagebox.showerror("Test Failed", f"RPC connection failed:\n{str(e)}")
    
    def connect_blockchain(self):
        """Connect to blockchain"""
        try:
            self.connect_btn.config(state='disabled', text="Connecting...")
            self.conn_status.config(text="⟳ Connecting...", fg=self.colors['accent'])
            
            # Get RPC URL
            rpc_url = self.rpc_entry.get().strip()
            if not rpc_url:
                raise ValueError("Please enter RPC URL")
            
            # Connect to Web3
            self.w3 = Web3(Web3.HTTPProvider(rpc_url))
            
            if not self.w3.is_connected():
                raise ConnectionError("Failed to connect to blockchain")
            
            # Get chain ID
            chain_id = self.w3.eth.chain_id
            
            # Get current gas price
            gas_price_wei = self.w3.eth.gas_price
            gas_price_gwei = float(self.w3.from_wei(gas_price_wei, 'gwei'))
            
            # Update UI
            self.conn_status.config(text=f"🟢 Connected (Chain ID: {chain_id})", 
                                  fg=self.colors['accent'])
            self.connect_btn.config(text="✓ Connected", bg=self.colors['accent'])
            
            self.log(f"Connected to blockchain (Chain ID: {chain_id})", 'success')
            self.log(f"Current gas price: {gas_price_gwei:.2f} Gwei", 'info')
            
            # Enable features
            self.check_enable_features()
            
        except Exception as e:
            self.conn_status.config(text="🔴 Connection Failed", fg=self.colors['error'])
            self.connect_btn.config(state='normal', text="🔌 Connect to Blockchain")
            self.log(f"Connection failed: {str(e)}", 'error')
            messagebox.showerror("Connection Error", f"Failed to connect:\n{str(e)}")
    
    def import_private_key(self):
        """Import private key"""
        if not self.w3:
            messagebox.showwarning("Not Connected", "Please connect to blockchain first")
            return
        
        # Get private key
        private_key = simpledialog.askstring("Import Private Key", 
                                           "Enter your private key (will be hidden):", 
                                           show='*')
        
        if not private_key:
            return
        
        try:
            # Clean private key - remove 0x prefix if present
            if private_key.startswith('0x'):
                private_key = private_key[2:]
            
            # Ensure private key is properly formatted
            if len(private_key) != 64:
                raise ValueError(f"Invalid private key length: {len(private_key)} (should be 64)")
            
            # Create account from private key
            account = Account.from_key(private_key)
            self.account = account.address
            self.private_key = '0x' + private_key  # Store with 0x prefix
            
            # Get balance
            balance_wei = self.w3.eth.get_balance(self.account)
            balance_eth = self.w3.from_wei(balance_wei, 'ether')
            
            # Update UI
            self.wallet_status.config(text="Wallet loaded", fg=self.colors['accent'])
            self.account_label.config(text=f"Account: {self.account[:6]}...{self.account[-4:]}")
            self.balance_label.config(text=f"Balance: {balance_eth:.4f} ETH")
            
            self.log(f"Wallet imported: {self.account[:6]}...{self.account[-4:]}", 'success')
            
            # Enable features
            self.check_enable_features()
            
        except Exception as e:
            self.log(f"Failed to import wallet: {str(e)}", 'error')
            messagebox.showerror("Import Error", f"Failed to import private key:\n{str(e)}")
    
    def generate_wallet(self):
        """Generate new wallet"""
        try:
            # Generate new account
            account = Account.create()
            
            # Show private key to user
            result = messagebox.askyesno("New Wallet Generated", 
                                       f"New wallet generated!\n\n"
                                       f"Address: {account.address}\n\n"
                                       f"IMPORTANT: Save your private key securely!\n"
                                       f"You will only see it once.\n\n"
                                       f"Click 'Yes' to view private key")
            
            if result:
                # Show private key
                pk_window = tk.Toplevel(self)
                pk_window.title("Private Key")
                pk_window.geometry("600x200")
                pk_window.configure(bg=self.colors['bg'])
                
                tk.Label(pk_window, text="Your Private Key (KEEP IT SECRET!):", 
                        font=('Arial', 12, 'bold'), 
                        fg=self.colors['error'], 
                        bg=self.colors['bg']).pack(pady=20)
                
                pk_text = tk.Text(pk_window, height=2, width=70, 
                                 font=('Consolas', 10))
                pk_text.pack(padx=20)
                pk_text.insert('1.0', account.key.hex())
                pk_text.config(state='disabled')
                
                tk.Button(pk_window, text="Copy & Close", 
                         command=lambda: self.copy_and_close(account.key.hex(), pk_window),
                         bg=self.colors['accent'], fg='black', 
                         padx=20, pady=10).pack(pady=20)
                
                # Use this wallet
                self.account = account.address
                self.private_key = account.key.hex()  # This already includes 0x prefix
                
                # Update UI if connected
                if self.w3:
                    balance_wei = self.w3.eth.get_balance(self.account)
                    balance_eth = self.w3.from_wei(balance_wei, 'ether')
                    
                    self.wallet_status.config(text="New wallet generated", fg=self.colors['accent'])
                    self.account_label.config(text=f"Account: {self.account[:6]}...{self.account[-4:]}")
                    self.balance_label.config(text=f"Balance: {balance_eth:.4f} ETH")
                    
                    self.log(f"New wallet generated: {self.account[:6]}...{self.account[-4:]}", 'success')
                    self.log("⚠️ Make sure to fund this wallet before pinning files", 'warning')
                
                self.check_enable_features()
                
        except Exception as e:
            self.log(f"Failed to generate wallet: {str(e)}", 'error')
            messagebox.showerror("Generation Error", f"Failed to generate wallet:\n{str(e)}")
    
    def copy_and_close(self, text: str, window):
        """Copy text to clipboard and close window"""
        self.clipboard_clear()
        self.clipboard_append(text)
        window.destroy()
        messagebox.showinfo("Copied", "Private key copied to clipboard!\nStore it securely.")
    
    def load_contract(self):
        """Load smart contract"""
        try:
            if not self.w3:
                messagebox.showwarning("Not Connected", "Please connect to blockchain first")
                return
            
            address = self.contract_entry.get().strip()
            if not address:
                raise ValueError("Please enter contract address")
            
            # Validate address
            if not self.w3.is_address(address):
                raise ValueError("Invalid contract address")
            
            # Load contract
            self.contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(address),
                abi=PINNING_CONTRACT_ABI
            )
            
            # Test contract by calling view function
            price_wei = self.contract.functions.pricePerGBPerDay().call()
            price_eth = self.w3.from_wei(price_wei, 'ether')
            
            self.contract_status.config(
                text=f"✓ Contract loaded - Price: {price_eth:.6f} ETH/GB/day",
                fg=self.colors['accent']
            )
            
            self.log(f"Contract loaded at: {address[:10]}...{address[-8:]}", 'success')
            self.log(f"Price per GB per day: {price_eth:.6f} ETH", 'info')
            
            # Save contract address
            config.pinning_contract_address = address
            config.save_to_file()
            
            self.check_enable_features()
            
        except Exception as e:
            self.contract_status.config(
                text=f"Failed: {str(e)[:50]}...",
                fg=self.colors['error']
            )
            self.log(f"Failed to load contract: {str(e)}", 'error')
            messagebox.showerror("Contract Error", f"Failed to load contract:\n{str(e)}")
    
    def check_enable_features(self):
        """Check if features should be enabled"""
        if self.w3 and self.account and self.contract:
            self.pin_btn.config(state='normal')
            self.log("✅ All components ready - you can now pin files", 'success')
        else:
            self.pin_btn.config(state='disabled')
    
    def get_manual_gas_price(self):
        """Get gas price - either manual or automatic"""
        gas_price_str = self.gas_price_var.get().strip()
        
        if gas_price_str.lower() == 'auto' or not gas_price_str:
            # Get automatic gas price
            gas_price_wei = self.w3.eth.gas_price
            # Apply buffer
            gas_price_wei = int(gas_price_wei * config.gas_price_buffer)
            
            # Ensure minimum gas price
            min_gas_wei = self.w3.to_wei(config.min_gas_price_gwei, 'gwei')
            if gas_price_wei < min_gas_wei:
                gas_price_wei = min_gas_wei
                
            return gas_price_wei
        else:
            try:
                # Use manual gas price
                gas_price_gwei = float(gas_price_str)
                if gas_price_gwei < config.min_gas_price_gwei:
                    self.log(f"⚠️ Gas price too low, using minimum: {config.min_gas_price_gwei} Gwei", 'warning')
                    gas_price_gwei = config.min_gas_price_gwei
                
                return self.w3.to_wei(gas_price_gwei, 'gwei')
            except ValueError:
                # Fall back to automatic
                self.log("Invalid gas price, using automatic", 'warning')
                return self.get_manual_gas_price()  # Recursive call with 'auto'
    
    def update_selected_files(self, files: List[Dict[str, Any]]):
        """Update selected files info and estimate cost"""
        self.selected_files = files
        
        if not files:
            self.selected_label.config(text="No files selected")
            self.cost_label.config(text="Cost: Select files to estimate")
            self.gas_estimate_label.config(text="")
            return
        
        total_size = sum(f.get('original_size', 0) for f in files)
        size_mb = total_size / (1024 * 1024)
        
        self.selected_label.config(
            text=f"Selected: {len(files)} files, {size_mb:.2f} MB total"
        )
        
        # Estimate cost if contract loaded
        if self.contract:
            try:
                duration_seconds = self.duration_var.get() * 86400
                cost_wei = self.contract.functions.calculatePinCost(
                    total_size, duration_seconds
                ).call()
                
                # Convert to int to handle Decimal type
                cost_wei = int(cost_wei)
                cost_eth = self.w3.from_wei(cost_wei, 'ether')
                
                # Get current gas price
                gas_price_wei = self.get_manual_gas_price()
                gas_price_gwei = self.w3.from_wei(gas_price_wei, 'gwei')
                
                # Estimate gas for all files
                estimated_gas_per_file = 350000  # Conservative estimate
                total_gas = estimated_gas_per_file * len(files)
                gas_cost_wei = int(total_gas * gas_price_wei)
                gas_cost_eth = self.w3.from_wei(gas_cost_wei, 'ether')
                
                # Convert to float for arithmetic
                total_cost = float(cost_eth) + float(gas_cost_eth)
                
                self.cost_label.config(
                    text=f"Estimated Total Cost: {total_cost:.6f} ETH "
                         f"(Pin: {float(cost_eth):.6f} + Gas: {float(gas_cost_eth):.6f})",
                    fg=self.colors['accent']
                )
                
                self.gas_estimate_label.config(
                    text=f"Gas: ~{total_gas:,} units @ {float(gas_price_gwei):.2f} Gwei",
                    fg=self.colors['warning']
                )
            except Exception as e:
                self.cost_label.config(text="Cost estimation failed", fg=self.colors['error'])
                self.log(f"Cost estimation error: {str(e)}", 'error')
    
    def pin_files(self):
        """Pin selected files on blockchain"""
        if not hasattr(self, 'selected_files') or not self.selected_files:
            messagebox.showwarning("No Files", "Please select files from the Files tab first")
            return
        
        # Check balance
        balance_wei = self.w3.eth.get_balance(self.account)
        balance_eth = float(self.w3.from_wei(balance_wei, 'ether'))
        
        # Estimate total cost
        total_size = sum(f.get('original_size', 0) for f in self.selected_files)
        duration_seconds = self.duration_var.get() * 86400
        
        try:
            cost_wei = self.contract.functions.calculatePinCost(
                total_size, duration_seconds
            ).call()
            
            # Convert to int to handle Decimal type
            cost_wei = int(cost_wei)
            cost_eth = float(self.w3.from_wei(cost_wei, 'ether'))
            
            # Get gas price
            gas_price_wei = self.get_manual_gas_price()
            gas_price_gwei = float(self.w3.from_wei(gas_price_wei, 'gwei'))
            
            # Estimate gas
            estimated_gas_per_file = 350000
            total_gas = estimated_gas_per_file * len(self.selected_files)
            gas_cost_eth = float(self.w3.from_wei(total_gas * gas_price_wei, 'ether'))
            
            total_cost = cost_eth + gas_cost_eth
            
            if balance_eth < total_cost * 1.1:  # 10% safety margin
                messagebox.showerror("Insufficient Balance", 
                                   f"Insufficient balance!\n\n"
                                   f"Required: ~{total_cost * 1.1:.6f} ETH (with safety margin)\n"
                                   f"Balance: {balance_eth:.6f} ETH\n\n"
                                   f"Please fund your wallet.")
                return
            
            # Confirm
            if not messagebox.askyesno("Confirm Pinning", 
                                     f"Pin {len(self.selected_files)} files for {self.duration_var.get()} days?\n\n"
                                     f"Estimated cost: {total_cost:.6f} ETH\n"
                                     f"Gas price: {gas_price_gwei:.2f} Gwei\n"
                                     f"Your balance: {balance_eth:.6f} ETH\n\n"
                                     f"Proceed with transaction?"):
                return
            
            # Execute pinning
            self.execute_pinning()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to estimate cost:\n{str(e)}")
    
    def execute_pinning(self):
        """Execute the pinning transactions"""
        self.pin_btn.config(state='disabled', text="Pinning...")
        
        def pin_thread():
            try:
                successful = 0
                failed = 0
                
                # Import Account at the function level to ensure it's available
                from eth_account import Account as EthAccount
                
                for i, file in enumerate(self.selected_files):
                    try:
                        self.log(f"Pinning file {i+1}/{len(self.selected_files)}: {file['original_name']}", 'info')
                        
                        # Calculate cost for this file
                        duration_seconds = self.duration_var.get() * 86400
                        cost_wei = self.contract.functions.calculatePinCost(
                            file['original_size'], duration_seconds
                        ).call()
                        
                        # Convert to int to handle Decimal type
                        cost_wei = int(cost_wei)
                        
                        # Get current nonce
                        nonce = self.w3.eth.get_transaction_count(self.account)
                        
                        # Get gas price
                        gas_price_wei = self.get_manual_gas_price()
                        gas_price_gwei = float(self.w3.from_wei(gas_price_wei, 'gwei'))
                        
                        self.log(f"Using gas price: {gas_price_gwei:.2f} Gwei", 'info')
                        
                        # First estimate gas for the transaction
                        try:
                            estimated_gas = self.contract.functions.pinFile(
                                file['file_cid'],
                                file['metadata_cid'],
                                file['original_size'],
                                duration_seconds,
                                file.get('original_name', 'File')
                            ).estimate_gas({
                                'from': self.account,
                                'value': cost_wei
                            })
                            
                            # Add buffer to estimated gas
                            gas_limit = int(estimated_gas * config.gas_limit_buffer)
                            
                            # Cap at maximum gas limit
                            if gas_limit > config.max_gas_limit:
                                gas_limit = config.max_gas_limit
                                
                            self.log(f"Estimated gas: {estimated_gas:,}, Using limit: {gas_limit:,}", 'info')
                            
                        except Exception as gas_error:
                            self.log(f"Gas estimation failed: {str(gas_error)}, using default", 'warning')
                            gas_limit = config.default_gas_limit
                        
                        # Build transaction with proper parameters
                        tx_params = {
                            'from': self.account,
                            'value': int(cost_wei),
                            'gas': gas_limit,
                            'gasPrice': int(gas_price_wei),
                            'nonce': nonce,
                            'chainId': self.w3.eth.chain_id
                        }
                        
                        transaction = self.contract.functions.pinFile(
                            file['file_cid'],
                            file['metadata_cid'],
                            file['original_size'],
                            duration_seconds,
                            file.get('original_name', 'File')
                        ).build_transaction(tx_params)
                        
                        # Calculate total transaction cost
                        tx_cost_eth = float(self.w3.from_wei(cost_wei + (gas_limit * gas_price_wei), 'ether'))
                        self.log(f"Transaction cost: {tx_cost_eth:.6f} ETH", 'info')
                        
                        # Sign transaction
                        try:
                            # Ensure private key has 0x prefix
                            pk = self.private_key
                            if not pk.startswith('0x'):
                                pk = '0x' + pk
                            
                            # Sign the transaction
                            signed = EthAccount.sign_transaction(transaction, pk)
                            
                            # Get raw transaction
                            if hasattr(signed, 'rawTransaction'):
                                raw_tx = signed.rawTransaction
                            elif hasattr(signed, 'raw_transaction'):
                                raw_tx = signed.raw_transaction
                            elif hasattr(signed, 'raw'):
                                raw_tx = signed.raw
                            else:
                                raise AttributeError("Cannot find raw transaction in signed object")
                            
                            # Send transaction
                            tx_hash = self.w3.eth.send_raw_transaction(raw_tx)
                            self.log(f"Transaction sent: 0x{tx_hash.hex()}", 'info')
                            
                        except Exception as signing_error:
                            self.log(f"Signing error: {str(signing_error)}", 'error')
                            raise signing_error
                        
                        # Wait for receipt
                        self.log(f"Waiting for transaction confirmation...", 'info')
                        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                        
                        if receipt['status'] == 1:
                            actual_gas_used = receipt['gasUsed']
                            actual_gas_cost = float(self.w3.from_wei(actual_gas_used * gas_price_wei, 'ether'))
                            
                            self.log(f"✓ File pinned successfully! Gas used: {actual_gas_used:,} ({actual_gas_cost:.6f} ETH)", 'success')
                            successful += 1
                            
                            # Update file registry
                            if self.file_registry_callback:
                                self.file_registry_callback(file['file_id'], {
                                    'blockchain_pinned': True,
                                    'pin_tx': tx_hash.hex(),
                                    'pin_date': datetime.now().isoformat(),
                                    'pin_duration_days': self.duration_var.get(),
                                    'pin_network': self.network_var.get(),
                                    'pin_gas_used': actual_gas_used,
                                    'pin_gas_price_gwei': float(gas_price_gwei)
                                })
                        else:
                            self.log(f"✗ Transaction failed for {file['original_name']}", 'error')
                            failed += 1
                            
                    except Exception as e:
                        error_msg = str(e)
                        self.log(f"✗ Failed to pin {file['original_name']}: {error_msg}", 'error')
                        
                        # Provide helpful error messages
                        if "insufficient funds" in error_msg.lower():
                            self.log("⚠️ Insufficient funds - check wallet balance", 'warning')
                        elif "gas required exceeds" in error_msg.lower():
                            self.log("⚠️ Gas limit too low - increase gas limit", 'warning')
                        elif "replacement transaction underpriced" in error_msg.lower():
                            self.log("⚠️ Gas price too low - increase gas price", 'warning')
                        elif "nonce too low" in error_msg.lower():
                            self.log("⚠️ Nonce issue - previous transaction may be pending", 'warning')
                        
                        failed += 1
                        continue
                
                # Summary
                self.log(f"\nPinning complete: {successful} successful, {failed} failed", 
                        'success' if failed == 0 else 'warning')
                
                # Update UI
                self.master.after(0, lambda: self.on_pinning_complete(successful, failed))
                
            except Exception as e:
                import traceback
                self.log(f"Pinning process error: {str(e)}", 'error')
                self.log(f"Debug trace: {traceback.format_exc()[-200:]}", 'error')
                self.master.after(0, lambda: self.on_pinning_error(str(e)))
        
        threading.Thread(target=pin_thread, daemon=True).start()
    
    def on_pinning_complete(self, successful: int, failed: int):
        """Handle pinning completion"""
        self.pin_btn.config(state='normal', text="📌 Pin Selected Files on Blockchain")
        
        if failed == 0:
            messagebox.showinfo("Success", 
                              f"All {successful} files pinned successfully!\n\n"
                              "Your files are now permanently stored on IPFS\n"
                              "with blockchain-guaranteed availability.")
        else:
            messagebox.showwarning("Partial Success", 
                                 f"Pinning completed with issues:\n\n"
                                 f"Successful: {successful} files\n"
                                 f"Failed: {failed} files\n\n"
                                 f"Check the transaction log for details.")
    
    def on_pinning_error(self, error: str):
        """Handle pinning error"""
        self.pin_btn.config(state='normal', text="📌 Pin Selected Files on Blockchain")
        messagebox.showerror("Pinning Error", f"Failed to complete pinning:\n{error}")


class EncryptumGUI:
    """Main GUI application with blockchain integration"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🛡️ Encryptum - Decentralized Encrypted Storage")
        self.root.geometry("1200x800")
        
        # Set theme colors
        self.colors = config.current_theme_colors
        self.root.configure(bg=self.colors['bg'])
        
        # Initialize handlers
        self.crypto = None
        self.ipfs = None
        self.blockchain_panel = None
        self.file_registry = {}
        
        self.logger = logging.getLogger(__name__)
        
        # Setup UI
        self.setup_ui()
        
        # Initialize components
        self.initialize_components()
        
        # Load registry
        self.load_registry()
    
    def setup_ui(self):
        """Setup the main user interface"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Style the notebook
        style = ttk.Style()
        style.configure('TNotebook', background=self.colors['bg'])
        style.configure('TNotebook.Tab', padding=[20, 10])
        
        # Files tab
        self.files_tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(self.files_tab, text="📁 Files")
        
        # Blockchain tab
        self.blockchain_tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(self.blockchain_tab, text="⛓️ Blockchain")
        
        # Setup tabs
        self.setup_files_tab()
        self.setup_blockchain_tab()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Initializing...")
        status_bar = tk.Label(self.root, textvariable=self.status_var, 
                            relief='sunken', anchor='w', 
                            bg='#333', fg='#888')
        status_bar.pack(side='bottom', fill='x')
    
    def setup_files_tab(self):
        """Setup the files tab"""
        # Header
        header = tk.Frame(self.files_tab, bg=self.colors['panel'], height=100)
        header.pack(fill='x', padx=10, pady=10)
        header.pack_propagate(False)
        
        title = tk.Label(header, text=config.app_name, 
                        font=('Arial', 28, 'bold'), 
                        fg=self.colors['accent'], bg=self.colors['panel'])
        title.pack(pady=20)
        
        subtitle = tk.Label(header, text=config.app_subtitle, 
                           font=('Arial', 12), fg=self.colors['text_secondary'], 
                           bg=self.colors['panel'])
        subtitle.pack()
        
        # Main content
        content_frame = tk.Frame(self.files_tab, bg=self.colors['bg'])
        content_frame.pack(fill='both', expand=True, padx=10)
        
        # Upload section
        upload_frame = tk.LabelFrame(content_frame, text="Upload & Encrypt", 
                                   font=('Arial', 12, 'bold'), 
                                   fg=self.colors['accent'], 
                                   bg=self.colors['panel'], 
                                   relief='groove', bd=2)
        upload_frame.pack(fill='x', pady=(0, 10))
        
        tk.Button(upload_frame, text="📁 Select File to Encrypt & Store", 
                 command=self.select_and_upload_file, 
                 font=('Arial', 12),
                 bg=self.colors['accent'], fg='black', 
                 padx=20, pady=10).pack(pady=15)
        
        # File list section
        list_frame = tk.LabelFrame(content_frame, text="Stored Files", 
                                 font=('Arial', 12, 'bold'), 
                                 fg=self.colors['accent'], 
                                 bg=self.colors['panel'], 
                                 relief='groove', bd=2)
        list_frame.pack(fill='both', expand=True)
        
        # Treeview
        columns = ('File ID', 'Name', 'Size', 'CID', 'Pinned', 'Date')
        self.file_tree = ttk.Treeview(list_frame, columns=columns, 
                                     show='headings', height=12,
                                     selectmode='extended')  # Allow multiple selection
        
        # Configure columns
        self.file_tree.heading('File ID', text='File ID')
        self.file_tree.heading('Name', text='Name')
        self.file_tree.heading('Size', text='Size')
        self.file_tree.heading('CID', text='CID')
        self.file_tree.heading('Pinned', text='Pinned')
        self.file_tree.heading('Date', text='Upload Date')
        
        self.file_tree.column('File ID', width=120)
        self.file_tree.column('Name', width=200)
        self.file_tree.column('Size', width=80)
        self.file_tree.column('CID', width=150)
        self.file_tree.column('Pinned', width=80)
        self.file_tree.column('Date', width=150)
        
        # Bind selection event
        self.file_tree.bind('<<TreeviewSelect>>', self.on_file_selection_changed)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', 
                                 command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=scrollbar.set)
        
        self.file_tree.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        scrollbar.pack(side='right', fill='y', pady=10)
        
        # File operations buttons
        button_frame = tk.Frame(list_frame, bg=self.colors['panel'])
        button_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Button(button_frame, text="🔄 Refresh", 
                 command=self.refresh_file_list,
                 bg='#4a4a4a', fg='white', padx=15).pack(side='left', padx=5)
        
        tk.Button(button_frame, text="📥 Download & Decrypt", 
                 command=self.download_file,
                 bg='#0066cc', fg='white', padx=15).pack(side='left', padx=5)
        
        tk.Button(button_frame, text="🗑️ Delete", 
                 command=self.delete_file,
                 bg='#cc0000', fg='white', padx=15).pack(side='left', padx=5)
        
        # Help text
        help_text = ("Select files with Ctrl+Click for blockchain pinning. "
                    "Go to Blockchain tab to pin selected files.")
        tk.Label(button_frame, text=help_text, 
                font=('Arial', 9), fg=self.colors['text_secondary'], 
                bg=self.colors['panel']).pack(side='right', padx=10)
    
    def setup_blockchain_tab(self):
        """Setup the blockchain tab"""
        self.blockchain_panel = BlockchainPanel(self.blockchain_tab, self.update_file_pinning_status)
        self.blockchain_panel.pack(fill='both', expand=True)
    
    def on_file_selection_changed(self, event):
        """Handle file selection change"""
        selection = self.file_tree.selection()
        selected_files = []
        
        for item in selection:
            values = self.file_tree.item(item)['values']
            file_id = values[0]
            
            if file_id in self.file_registry:
                file_info = self.file_registry[file_id]
                # Skip already pinned files
                if not file_info.get('blockchain_pinned', False):
                    selected_files.append({
                        'file_id': file_id,
                        'file_cid': file_info['file_cid'],
                        'metadata_cid': file_info['metadata_cid'],
                        'original_size': file_info.get('original_size', 0),
                        'original_name': file_info.get('original_name', 'Unknown')
                    })
        
        # Update blockchain panel
        if self.blockchain_panel:
            self.blockchain_panel.update_selected_files(selected_files)
    
    def update_file_pinning_status(self, file_id: str, pin_info: dict):
        """Update file pinning status from blockchain panel"""
        if file_id in self.file_registry:
            self.file_registry[file_id].update(pin_info)
            self.save_registry()
            self.refresh_file_list()
            self.status_var.set(f"✅ File pinned on blockchain")
    
    def initialize_components(self):
        """Initialize core components"""
        try:
            # Initialize encryption
            self.crypto = EncryptumCrypto(iterations=config.pbkdf2_iterations)
            self.logger.info("Encryption module initialized")
            
            # Initialize IPFS
            self.ipfs = EncryptumIPFS(
                ipfs_host=config.ipfs_host,
                ipfs_port=config.ipfs_port,
                gateway_url=config.ipfs_gateway_url
            )
            self.logger.info("IPFS connection established")
            
            self.status_var.set("Ready • IPFS Connected")
            
        except Exception as e:
            self.logger.error(f"Initialization error: {e}")
            self.status_var.set(f"Error: {str(e)}")
            
            messagebox.showerror("Initialization Error", 
                               f"Failed to initialize:\n\n{e}\n\n"
                               "Please ensure IPFS is running.")
    
    def load_registry(self):
        """Load file registry from disk"""
        try:
            registry_path = Path(config.registry_file)
            if registry_path.exists():
                with open(registry_path, 'r') as f:
                    self.file_registry = json.load(f)
                self.refresh_file_list()
                self.logger.info(f"Loaded {len(self.file_registry)} files from registry")
        except Exception as e:
            self.logger.error(f"Failed to load registry: {e}")
    
    def save_registry(self):
        """Save file registry to disk"""
        try:
            with open(config.registry_file, 'w') as f:
                json.dump(self.file_registry, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save registry: {e}")
    
    def select_and_upload_file(self):
        """Select and upload a file"""
        file_path = filedialog.askopenfilename(
            title="Select file to encrypt and store",
            filetypes=[("All files", "*.*")]
        )
        
        if file_path:
            # Check file size
            if not validate_file_size(file_path, config.max_file_size_bytes):
                messagebox.showerror("File Too Large", 
                                   f"File size exceeds {config.max_file_size_mb}MB limit")
                return
            
            # Check file type
            if not is_supported_file_type(file_path):
                if not messagebox.askyesno("Unsupported File Type", 
                                         "This file type is not officially supported.\n"
                                         "Do you want to continue anyway?"):
                    return
            
            # Get password
            password = simpledialog.askstring("Encryption Password", 
                                            "Enter encryption password:", 
                                            show='*')
            if password:
                # Upload in thread
                threading.Thread(target=self.upload_file_thread, 
                               args=(file_path, password), 
                               daemon=True).start()
    
    def upload_file_thread(self, file_path: str, password: str):
        """Upload file in background thread"""
        try:
            self.status_var.set("Encrypting file...")
            self.root.update()
            
            # Encrypt file
            encrypted_result = self.crypto.encrypt_file(file_path, password)
            
            self.status_var.set("Storing on IPFS...")
            self.root.update()
            
            # Store on IPFS
            ipfs_result = self.ipfs.store_encrypted_file(
                encrypted_result['encrypted_data'],
                {
                    'salt': encrypted_result['salt'].hex(),
                    'original_hash': encrypted_result['original_hash'],
                    'original_name': encrypted_result['original_name'],
                    'original_size': encrypted_result['original_size'],
                    'encrypted_size': encrypted_result['encrypted_size']
                }
            )
            
            # Create file entry
            file_id = encrypted_result['original_hash'][:16]
            self.file_registry[file_id] = {
                **ipfs_result,
                'original_name': encrypted_result['original_name'],
                'original_size': encrypted_result['original_size'],
                'upload_date': datetime.now().isoformat(),
                'file_hash': encrypted_result['original_hash'],
                'blockchain_pinned': False
            }
            
            # Save registry
            self.save_registry()
            
            # Update UI
            self.root.after(0, lambda: self.on_upload_success(file_id, ipfs_result))
            
        except Exception as e:
            self.root.after(0, lambda: self.on_upload_error(str(e)))
    
    def on_upload_success(self, file_id: str, ipfs_result: dict):
        """Handle successful upload"""
        self.status_var.set(f"✅ File uploaded: {ipfs_result['file_cid'][:20]}...")
        self.refresh_file_list()
        
        messagebox.showinfo("Upload Successful", 
                          f"File encrypted and stored!\n\n"
                          f"File ID: {file_id}\n"
                          f"CID: {ipfs_result['file_cid']}\n\n"
                          "Select file and go to Blockchain tab to pin permanently")
    
    def on_upload_error(self, error: str):
        """Handle upload error"""
        self.status_var.set("❌ Upload failed")
        messagebox.showerror("Upload Error", f"Failed to upload:\n{error}")
    
    def refresh_file_list(self):
        """Refresh the file list display"""
        # Clear existing
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        # Add files
        for file_id, info in self.file_registry.items():
            size_mb = info.get('original_size', 0) / (1024 * 1024)
            upload_date = info.get('upload_date', 'Unknown')
            
            if isinstance(upload_date, str) and 'T' in upload_date:
                try:
                    dt = datetime.fromisoformat(upload_date)
                    upload_date = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            
            pinned = "Yes ✓" if info.get('blockchain_pinned', False) else "No"
            
            self.file_tree.insert('', 'end', values=(
                file_id,
                info.get('original_name', 'Unknown'),
                f"{size_mb:.2f} MB",
                info['file_cid'][:12] + '...',
                pinned,
                upload_date
            ))
    
    def download_file(self):
        """Download and decrypt selected file"""
        selection = self.file_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a file")
            return
        
        # Only download first selected file
        item = self.file_tree.item(selection[0])
        file_id = item['values'][0]
        
        if file_id not in self.file_registry:
            messagebox.showerror("Error", "File not found in registry")
            return
        
        # Get password
        password = simpledialog.askstring("Decryption Password", 
                                        "Enter decryption password:", 
                                        show='*')
        if not password:
            return
        
        # Get save location
        original_name = self.file_registry[file_id].get('original_name', 'file')
        save_path = filedialog.asksaveasfilename(
            title="Save decrypted file as",
            initialfile=original_name
        )
        
        if save_path:
            threading.Thread(target=self.download_file_thread, 
                           args=(file_id, password, save_path), 
                           daemon=True).start()
    
    def download_file_thread(self, file_id: str, password: str, save_path: str):
        """Download file in background thread"""
        try:
            self.status_var.set("Retrieving from IPFS...")
            self.root.update()
            
            # Get file info
            file_info = self.file_registry[file_id]
            
            # Retrieve from IPFS
            encrypted_data = self.ipfs.retrieve_file(file_info['file_cid'])
            metadata = self.ipfs.retrieve_metadata(file_info['metadata_cid'])
            
            self.status_var.set("Decrypting file...")
            self.root.update()
            
            # Decrypt
            salt = bytes.fromhex(metadata['salt'])
            decrypted_data = self.crypto.decrypt_file(encrypted_data, password, salt)
            
            # Verify integrity
            if self.crypto.verify_file_integrity(decrypted_data, metadata['original_hash']):
                # Save file
                with open(save_path, 'wb') as f:
                    f.write(decrypted_data)
                
                self.root.after(0, lambda: self.on_download_success(save_path))
            else:
                raise Exception("File integrity check failed")
            
        except Exception as e:
            self.root.after(0, lambda: self.on_download_error(str(e)))
    
    def on_download_success(self, save_path: str):
        """Handle successful download"""
        self.status_var.set("✅ File downloaded successfully")
        messagebox.showinfo("Download Complete", 
                          f"File decrypted and saved to:\n{save_path}")
    
    def on_download_error(self, error: str):
        """Handle download error"""
        self.status_var.set("❌ Download failed")
        messagebox.showerror("Download Error", f"Failed to download:\n{error}")
    
    def delete_file(self):
        """Delete selected file from registry"""
        selection = self.file_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select files to delete")
            return
        
        # Delete all selected files
        deleted = 0
        for item in selection:
            values = self.file_tree.item(item)['values']
            file_id = values[0]
            file_name = values[1]
            
            if file_id in self.file_registry:
                # Check if pinned
                if self.file_registry[file_id].get('blockchain_pinned', False):
                    if not messagebox.askyesno("File Pinned", 
                                             f"'{file_name}' is pinned on blockchain.\n"
                                             "It will remain available on IPFS.\n\n"
                                             "Remove from local registry anyway?"):
                        continue
                
                del self.file_registry[file_id]
                deleted += 1
        
        if deleted > 0:
            self.save_registry()
            self.refresh_file_list()
            self.status_var.set(f"Deleted {deleted} file(s) from registry")
    
    def run(self):
        """Run the application"""
        self.root.mainloop()


def main():
    """Main entry point"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n🛡️ Encryptum with Blockchain Integration")
    print("=" * 50)
    print("\nStarting application...")
    print("\nFor blockchain pinning:")
    print("1. Go to the Blockchain tab")
    print("2. Connect to blockchain with your RPC URL")
    print("3. Import your private key or generate new wallet")
    print("4. Load your smart contract from Remix")
    print("5. Select files and pin them on blockchain\n")
    
    # Create and run GUI
    app = EncryptumGUI()
    app.run()


if __name__ == "__main__":
    main()