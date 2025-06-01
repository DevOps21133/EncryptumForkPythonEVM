# Building Encryptum Clone with Python for Windows 11

## Overview

This guide shows how to build a decentralized, encrypted file storage system similar to Encryptum using Python on Windows 11. The system combines:

- **IPFS** for decentralized storage
- **AES encryption** for file security
- **Model Context Protocol (MCP)** for AI agent integration
- **GUI interface** for easy file management
- **Content addressing** with unique CIDs

## Prerequisites

### 1. Install IPFS Desktop
```bash
# Download from: https://docs.ipfs.tech/install/ipfs-desktop/
# Install IPFS Desktop for Windows (.exe installer)
# Start IPFS daemon after installation
```

### 2. Python Environment Setup
```bash
# Create virtual environment
python -m venv encryptum_env
encryptum_env\Scripts\activate

# Install required packages
pip install cryptography ipfshttpclient mcp tkinter-tooltip requests python-dotenv
```

## Core System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GUI Interface │────│  Encryption     │────│  IPFS Storage   │
│   (tkinter)     │    │  (AES-256)      │    │  (Content IDs)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   MCP Server    │
                    │  (AI Integration)│
                    └─────────────────┘
```

## Implementation

### 1. Core Encryption Module (`encryption.py`)

```python
import os
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class EncryptumCrypto:
    def __init__(self):
        pass
    
    def generate_key_from_password(self, password: str, salt: bytes = None) -> tuple:
        """Generate encryption key from password using PBKDF2"""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt
    
    def encrypt_file(self, file_path: str, password: str) -> tuple:
        """Encrypt file and return encrypted data + metadata"""
        try:
            # Generate key and salt
            key, salt = self.generate_key_from_password(password)
            fernet = Fernet(key)
            
            # Read and encrypt file
            with open(file_path, 'rb') as file:
                file_data = file.read()
            
            encrypted_data = fernet.encrypt(file_data)
            
            # Calculate hash for verification
            file_hash = hashlib.sha256(file_data).hexdigest()
            
            return {
                'encrypted_data': encrypted_data,
                'salt': salt,
                'original_hash': file_hash,
                'original_name': os.path.basename(file_path)
            }
        except Exception as e:
            raise Exception(f"Encryption failed: {str(e)}")
    
    def decrypt_file(self, encrypted_data: bytes, password: str, salt: bytes) -> bytes:
        """Decrypt file data"""
        try:
            key, _ = self.generate_key_from_password(password, salt)
            fernet = Fernet(key)
            return fernet.decrypt(encrypted_data)
        except Exception as e:
            raise Exception(f"Decryption failed: {str(e)}")
```

### 2. IPFS Integration Module (`ipfs_handler.py`)

```python
import ipfshttpclient
import json
import tempfile
import os
from typing import Dict, Any

class EncryptumIPFS:
    def __init__(self, ipfs_host='127.0.0.1', ipfs_port=5001):
        try:
            self.client = ipfshttpclient.connect(f'/ip4/{ipfs_host}/tcp/{ipfs_port}')
            # Test connection
            self.client.version()
            print("✅ Connected to IPFS node")
        except Exception as e:
            raise Exception(f"Failed to connect to IPFS: {str(e)}")
    
    def store_encrypted_file(self, encrypted_data: bytes, metadata: dict) -> str:
        """Store encrypted file on IPFS and return CID"""
        try:
            # Create temporary file with encrypted data
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(encrypted_data)
                temp_file_path = temp_file.name
            
            # Add to IPFS
            result = self.client.add(temp_file_path)
            cid = result['Hash']
            
            # Store metadata separately
            metadata_json = json.dumps(metadata).encode()
            with tempfile.NamedTemporaryFile(delete=False) as meta_file:
                meta_file.write(metadata_json)
                meta_file_path = meta_file.name
            
            meta_result = self.client.add(meta_file_path)
            metadata_cid = meta_result['Hash']
            
            # Clean up temp files
            os.unlink(temp_file_path)
            os.unlink(meta_file_path)
            
            return {
                'file_cid': cid,
                'metadata_cid': metadata_cid,
                'gateway_url': f"https://ipfs.io/ipfs/{cid}"
            }
            
        except Exception as e:
            raise Exception(f"IPFS storage failed: {str(e)}")
    
    def retrieve_file(self, cid: str) -> bytes:
        """Retrieve file from IPFS using CID"""
        try:
            return self.client.cat(cid)
        except Exception as e:
            raise Exception(f"IPFS retrieval failed: {str(e)}")
    
    def retrieve_metadata(self, metadata_cid: str) -> dict:
        """Retrieve metadata from IPFS"""
        try:
            metadata_bytes = self.client.cat(metadata_cid)
            return json.loads(metadata_bytes.decode())
        except Exception as e:
            raise Exception(f"Metadata retrieval failed: {str(e)}")
    
    def pin_file(self, cid: str):
        """Pin file to ensure persistence"""
        try:
            self.client.pin.add(cid)
            print(f"📌 Pinned file: {cid}")
        except Exception as e:
            print(f"Warning: Could not pin file: {str(e)}")
```

### 3. MCP Server Integration (`mcp_server.py`)

```python
from mcp.server.fastmcp import FastMCP, Context
from typing import Dict, Any
import json

# Initialize MCP server
mcp = FastMCP("Encryptum Storage Server")

class EncryptumMCPServer:
    def __init__(self, crypto_handler, ipfs_handler):
        self.crypto = crypto_handler
        self.ipfs = ipfs_handler
        self.file_registry = {}  # Store file mappings
    
    def setup_mcp_tools(self):
        """Setup MCP tools for AI agents"""
        
        @mcp.tool()
        async def upload_encrypted_file(file_path: str, password: str, ctx: Context) -> str:
            """Upload and encrypt a file to decentralized storage"""
            try:
                ctx.info(f"Encrypting file: {file_path}")
                
                # Encrypt file
                encrypted_result = self.crypto.encrypt_file(file_path, password)
                
                ctx.info("Storing on IPFS...")
                
                # Store on IPFS
                ipfs_result = self.ipfs.store_encrypted_file(
                    encrypted_result['encrypted_data'],
                    {
                        'salt': encrypted_result['salt'].hex(),
                        'original_hash': encrypted_result['original_hash'],
                        'original_name': encrypted_result['original_name']
                    }
                )
                
                # Store in registry
                file_id = encrypted_result['original_hash'][:16]
                self.file_registry[file_id] = ipfs_result
                
                return json.dumps({
                    'success': True,
                    'file_id': file_id,
                    'cid': ipfs_result['file_cid'],
                    'gateway_url': ipfs_result['gateway_url'],
                    'message': f'File successfully encrypted and stored on IPFS'
                })
                
            except Exception as e:
                return json.dumps({
                    'success': False,
                    'error': str(e)
                })
        
        @mcp.tool()
        async def retrieve_encrypted_file(file_id: str, password: str, output_path: str, ctx: Context) -> str:
            """Retrieve and decrypt a file from decentralized storage"""
            try:
                if file_id not in self.file_registry:
                    return json.dumps({
                        'success': False,
                        'error': 'File not found in registry'
                    })
                
                ctx.info(f"Retrieving file: {file_id}")
                
                # Get file info
                file_info = self.file_registry[file_id]
                
                # Retrieve encrypted data
                encrypted_data = self.ipfs.retrieve_file(file_info['file_cid'])
                metadata = self.ipfs.retrieve_metadata(file_info['metadata_cid'])
                
                ctx.info("Decrypting file...")
                
                # Decrypt
                salt = bytes.fromhex(metadata['salt'])
                decrypted_data = self.crypto.decrypt_file(encrypted_data, password, salt)
                
                # Save to output path
                with open(output_path, 'wb') as f:
                    f.write(decrypted_data)
                
                return json.dumps({
                    'success': True,
                    'output_path': output_path,
                    'original_name': metadata['original_name'],
                    'message': 'File successfully retrieved and decrypted'
                })
                
            except Exception as e:
                return json.dumps({
                    'success': False,
                    'error': str(e)
                })
        
        @mcp.tool()
        async def list_stored_files(ctx: Context) -> str:
            """List all files stored in the system"""
            return json.dumps({
                'files': [
                    {
                        'file_id': fid,
                        'cid': info['file_cid'],
                        'gateway_url': info['gateway_url']
                    }
                    for fid, info in self.file_registry.items()
                ]
            })

# Start MCP server
def start_mcp_server(crypto_handler, ipfs_handler, port=8000):
    server = EncryptumMCPServer(crypto_handler, ipfs_handler)
    server.setup_mcp_tools()
    return mcp
```

### 4. GUI Application (`gui_app.py`)

```python
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import threading
from encryption import EncryptumCrypto
from ipfs_handler import EncryptumIPFS
import os

class EncryptumGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Encryptum - Decentralized Encrypted Storage")
        self.root.geometry("800x600")
        self.root.configure(bg='#1a1a1a')
        
        # Initialize handlers
        try:
            self.crypto = EncryptumCrypto()
            self.ipfs = EncryptumIPFS()
            self.file_registry = {}
        except Exception as e:
            messagebox.showerror("Error", f"Failed to initialize: {str(e)}")
            return
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Header
        header = tk.Frame(self.root, bg='#2d2d2d', height=80)
        header.pack(fill='x', padx=10, pady=10)
        header.pack_propagate(False)
        
        title = tk.Label(header, text="🛡️ ENCRYPTUM", font=('Arial', 24, 'bold'), 
                        fg='#00d4aa', bg='#2d2d2d')
        title.pack(pady=15)
        
        subtitle = tk.Label(header, text="Decentralized • Encrypted • Your Data", 
                           font=('Arial', 12), fg='#888', bg='#2d2d2d')
        subtitle.pack()
        
        # Main content area
        main_frame = tk.Frame(self.root, bg='#1a1a1a')
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Upload section
        upload_frame = tk.LabelFrame(main_frame, text="Upload & Encrypt", 
                                   font=('Arial', 14, 'bold'), fg='#00d4aa', 
                                   bg='#2d2d2d', relief='groove', bd=2)
        upload_frame.pack(fill='x', pady=(0, 20))
        
        tk.Button(upload_frame, text="📁 Select File to Encrypt", 
                 command=self.select_and_upload_file, font=('Arial', 12),
                 bg='#00d4aa', fg='white', padx=20, pady=10).pack(pady=15)
        
        # File list section
        list_frame = tk.LabelFrame(main_frame, text="Stored Files", 
                                 font=('Arial', 14, 'bold'), fg='#00d4aa', 
                                 bg='#2d2d2d', relief='groove', bd=2)
        list_frame.pack(fill='both', expand=True, pady=(0, 20))
        
        # Treeview for file list
        columns = ('File ID', 'Original Name', 'CID', 'Status')
        self.file_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.file_tree.heading(col, text=col)
            self.file_tree.column(col, width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=scrollbar.set)
        
        self.file_tree.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        scrollbar.pack(side='right', fill='y', pady=10)
        
        # Buttons for file operations
        button_frame = tk.Frame(list_frame, bg='#2d2d2d')
        button_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Button(button_frame, text="🔄 Refresh List", command=self.refresh_file_list,
                 bg='#4a4a4a', fg='white', padx=10).pack(side='left', padx=5)
        
        tk.Button(button_frame, text="📥 Download & Decrypt", command=self.download_file,
                 bg='#0066cc', fg='white', padx=10).pack(side='left', padx=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready • IPFS Connected")
        status_bar = tk.Label(self.root, textvariable=self.status_var, 
                            relief='sunken', anchor='w', bg='#333', fg='#888')
        status_bar.pack(side='bottom', fill='x')
    
    def select_and_upload_file(self):
        """Select and upload a file"""
        file_path = filedialog.askopenfilename(
            title="Select file to encrypt and store",
            filetypes=[("All files", "*.*")]
        )
        
        if file_path:
            # Get password
            password = simpledialog.askstring("Password", "Enter encryption password:", show='*')
            if password:
                # Run upload in separate thread
                threading.Thread(target=self.upload_file_thread, 
                               args=(file_path, password), daemon=True).start()
    
    def upload_file_thread(self, file_path, password):
        """Upload file in separate thread"""
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
                    'original_name': encrypted_result['original_name']
                }
            )
            
            # Store in registry
            file_id = encrypted_result['original_hash'][:16]
            self.file_registry[file_id] = {
                **ipfs_result,
                'original_name': encrypted_result['original_name'],
                'upload_date': str(os.path.getctime(file_path))
            }
            
            # Update UI
            self.root.after(0, lambda: self.on_upload_success(file_id, ipfs_result))
            
        except Exception as e:
            self.root.after(0, lambda: self.on_upload_error(str(e)))
    
    def on_upload_success(self, file_id, ipfs_result):
        """Handle successful upload"""
        self.status_var.set(f"✅ File uploaded successfully! CID: {ipfs_result['file_cid'][:20]}...")
        self.refresh_file_list()
        messagebox.showinfo("Success", 
                           f"File encrypted and stored!\n\n"
                           f"File ID: {file_id}\n"
                           f"CID: {ipfs_result['file_cid']}\n"
                           f"Gateway: {ipfs_result['gateway_url']}")
    
    def on_upload_error(self, error_msg):
        """Handle upload error"""
        self.status_var.set("❌ Upload failed")
        messagebox.showerror("Upload Error", f"Failed to upload file:\n{error_msg}")
    
    def refresh_file_list(self):
        """Refresh the file list"""
        # Clear existing items
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        # Add files from registry
        for file_id, info in self.file_registry.items():
            self.file_tree.insert('', 'end', values=(
                file_id,
                info.get('original_name', 'Unknown'),
                info['file_cid'][:20] + '...',
                '✅ Stored'
            ))
    
    def download_file(self):
        """Download and decrypt selected file"""
        selection = self.file_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a file to download")
            return
        
        item = self.file_tree.item(selection[0])
        file_id = item['values'][0]
        
        # Get password
        password = simpledialog.askstring("Password", "Enter decryption password:", show='*')
        if not password:
            return
        
        # Get save location
        save_path = filedialog.asksaveasfilename(
            title="Save decrypted file as",
            initialname=self.file_registry[file_id].get('original_name', 'decrypted_file')
        )
        
        if save_path:
            threading.Thread(target=self.download_file_thread, 
                           args=(file_id, password, save_path), daemon=True).start()
    
    def download_file_thread(self, file_id, password, save_path):
        """Download file in separate thread"""
        try:
            self.status_var.set("Retrieving from IPFS...")
            self.root.update()
            
            # Get file info
            file_info = self.file_registry[file_id]
            
            # Retrieve encrypted data
            encrypted_data = self.ipfs.retrieve_file(file_info['file_cid'])
            metadata = self.ipfs.retrieve_metadata(file_info['metadata_cid'])
            
            self.status_var.set("Decrypting file...")
            self.root.update()
            
            # Decrypt
            salt = bytes.fromhex(metadata['salt'])
            decrypted_data = self.crypto.decrypt_file(encrypted_data, password, salt)
            
            # Save file
            with open(save_path, 'wb') as f:
                f.write(decrypted_data)
            
            self.root.after(0, lambda: self.on_download_success(save_path))
            
        except Exception as e:
            self.root.after(0, lambda: self.on_download_error(str(e)))
    
    def on_download_success(self, save_path):
        """Handle successful download"""
        self.status_var.set("✅ File downloaded and decrypted successfully!")
        messagebox.showinfo("Success", f"File decrypted and saved to:\n{save_path}")
    
    def on_download_error(self, error_msg):
        """Handle download error"""
        self.status_var.set("❌ Download failed")
        messagebox.showerror("Download Error", f"Failed to download file:\n{error_msg}")
    
    def run(self):
        """Start the GUI application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = EncryptumGUI()
    app.run()
```

### 5. Main Application Entry Point (`main.py`)

```python
#!/usr/bin/env python3
"""
Encryptum Clone - Decentralized Encrypted File Storage
Built with Python for Windows 11
"""

import sys
import os
import threading
from gui_app import EncryptumGUI
from mcp_server import start_mcp_server
from encryption import EncryptumCrypto
from ipfs_handler import EncryptumIPFS

def check_dependencies():
    """Check if all required dependencies are available"""
    try:
        import ipfshttpclient
        import cryptography
        import tkinter
        print("✅ All dependencies available")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install cryptography ipfshttpclient")
        return False

def main():
    """Main application entry point"""
    print("🛡️ Starting Encryptum Clone...")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    try:
        # Initialize core components
        crypto = EncryptumCrypto()
        ipfs = EncryptumIPFS()
        
        # Start MCP server in background (optional)
        mcp_server = start_mcp_server(crypto, ipfs)
        print("🔌 MCP server initialized for AI agent integration")
        
        # Start GUI
        print("🖥️ Starting GUI application...")
        app = EncryptumGUI()
        app.run()
        
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## Usage Instructions

### 1. Setup and Installation

```bash
# 1. Install IPFS Desktop from https://docs.ipfs.tech/install/ipfs-desktop/
# 2. Start IPFS daemon
# 3. Clone/create project directory
mkdir encryptum_clone
cd encryptum_clone

# 4. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 5. Install dependencies
pip install cryptography ipfshttpclient mcp tkinter-tooltip requests
```

### 2. Running the Application

```bash
# Make sure IPFS daemon is running
# Then start the application
python main.py
```

### 3. Core Features

**File Upload & Encryption:**
- Select any file through the GUI
- Enter a secure password
- File is encrypted with AES-256
- Stored on IPFS with unique CID
- Metadata stored separately

**File Retrieval & Decryption:**
- Browse stored files in the GUI
- Select file and enter password
- File is retrieved from IPFS
- Decrypted and saved locally

**MCP Integration:**
- AI agents can interact with the storage system
- Upload/download files programmatically
- List stored files
- Integrate with Claude Desktop or other MCP clients

## Security Features

- **AES-256 Encryption**: Military-grade encryption for all files
- **Password-Based Key Derivation**: PBKDF2 with 100,000 iterations
- **Content Addressing**: Files verified by cryptographic hashes
- **Decentralized Storage**: No single point of failure
- **Zero-Knowledge**: Passwords never stored or transmitted

## Advanced Configuration

### Custom IPFS Node
```python
# In ipfs_handler.py, modify connection
ipfs = EncryptumIPFS(ipfs_host='your-node-ip', ipfs_port=5001)
```

### Enhanced Security
```python
# Increase PBKDF2 iterations for stronger security
iterations=500000  # In encryption.py
```

### MCP Server Deployment
```bash
# Run MCP server standalone for AI integration
python -c "from mcp_server import start_mcp_server; start_mcp_server()"
```

This implementation provides a fully functional decentralized encrypted file storage system similar to Encryptum, built specifically for Windows 11 using Python. The system combines the security of AES encryption, the resilience of IPFS storage, and the interoperability of the Model Context Protocol.