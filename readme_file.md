# 🛡️ Encryptum Clone

A **decentralized encrypted file storage system** built with Python for Windows 11. This project replicates the core functionality of Encryptum, combining AES-256 encryption, IPFS decentralized storage, and Model Context Protocol (MCP) integration for AI agents.

## ✨ Features

- **🔒 Military-Grade Encryption**: AES-256 encryption with PBKDF2 key derivation
- **🌐 Decentralized Storage**: IPFS network for resilient, distributed file storage
- **🤖 AI Agent Integration**: Model Context Protocol (MCP) server for AI interactions
- **📱 Modern GUI**: Clean, intuitive interface built with tkinter
- **🔗 Content Addressing**: Unique Content IDs (CIDs) for file verification
- **⚡ High Performance**: Optimized for large files and batch operations
- **🛡️ Zero-Knowledge**: Passwords never stored or transmitted
- **📊 File Management**: Complete file lifecycle management

## 🏗️ Architecture

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

## 🚀 Quick Start

### Prerequisites

1. **Python 3.7+** - Download from [python.org](https://www.python.org/downloads/)
2. **IPFS Desktop** - Download from [IPFS Docs](https://docs.ipfs.tech/install/ipfs-desktop/)

### Installation

1. **Clone or download the project files**
   ```bash
   # Create project directory
   mkdir encryptum_clone
   cd encryptum_clone
   
   # Copy all .py files to this directory
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # macOS/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start IPFS Desktop**
   - Install and launch IPFS Desktop
   - Ensure it's running (check system tray)

5. **Run the application**
   ```bash
   python main.py
   ```

## 💻 Usage

### GUI Mode (Default)

```bash
python main.py
```

**File Upload Process:**
1. Click "🔒 Select File to Encrypt & Store"
2. Choose your file (up to 100MB by default)
3. Enter a strong encryption password
4. File is encrypted and stored on IPFS
5. Receive unique File ID and CID

**File Download Process:**
1. Select file from the stored files list
2. Click "📥 Download & Decrypt"
3. Enter the decryption password
4. Choose save location
5. File is retrieved and decrypted

### Server Mode (No GUI)

```bash
python main.py --no-gui
```

Runs only the MCP server for AI agent integration.

### Command Line Options

```bash
python main.py --help                    # Show all options
python main.py --ipfs-host 192.168.1.100 # Use remote IPFS node
python main.py --theme light             # Use light theme
python main.py --log-level DEBUG         # Enable debug logging
```

## 🤖 AI Integration (MCP)

The application includes a Model Context Protocol server that allows AI agents to interact with the storage system.

### Available MCP Tools

- `upload_encrypted_file(file_path, password)` - Upload and encrypt files
- `retrieve_encrypted_file(file_id, password, output_path)` - Download and decrypt files
- `list_stored_files()` - List all stored files
- `get_file_info(file_id)` - Get detailed file information
- `delete_file(file_id)` - Delete files from storage
- `get_system_status()` - Check system health

### Using with Claude Desktop

1. Add to your Claude Desktop MCP configuration:
   ```json
   {
     "mcpServers": {
       "encryptum": {
         "command": "python",
         "args": ["path/to/encryptum_clone/main.py", "--no-gui"]
       }
     }
   }
   ```

2. Restart Claude Desktop to load the MCP server

## ⚙️ Configuration

### Environment Variables

```bash
# IPFS Settings
ENCRYPTUM_IPFS_HOST=127.0.0.1
ENCRYPTUM_IPFS_PORT=5001
ENCRYPTUM_GATEWAY_URL=https://ipfs.io/ipfs/

# Security Settings
ENCRYPTUM_PBKDF2_ITERATIONS=100000
ENCRYPTUM_MAX_FILE_SIZE_MB=100

# UI Settings
ENCRYPTUM_THEME=dark
ENCRYPTUM_LOG_LEVEL=INFO
```

### Configuration File

Create `encryptum_config.json`:
```json
{
  "ipfs_host": "127.0.0.1",
  "ipfs_port": 5001,
  "theme": "dark",
  "max_file_size_mb": 100,
  "pbkdf2_iterations": 100000,
  "auto_pin_files": true
}
```

## 📁 Project Structure

```
encryptum_clone/
├── main.py              # Main application entry point
├── encryption.py        # AES-256 encryption module
├── ipfs_handler.py      # IPFS integration module
├── mcp_server.py        # Model Context Protocol server
├── gui_app.py           # GUI application module
├── config.py            # Configuration management
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── logs/               # Application logs
├── temp/               # Temporary files
└── file_registry.json  # File storage registry
```

## 🔐 Security Features

- **AES-256 Encryption**: Industry-standard symmetric encryption
- **PBKDF2 Key Derivation**: 100,000+ iterations with random salt
- **Content Addressing**: Files verified by cryptographic hashes
- **Zero-Knowledge Architecture**: Passwords never stored
- **Integrity Verification**: Automatic file corruption detection
- **Secure Deletion**: Proper cleanup of temporary files

## 🌐 IPFS Integration

- **Decentralized Storage**: Files distributed across IPFS network
- **Content IDs (CIDs)**: Unique identifiers for each file
- **Gateway Access**: Files accessible via public IPFS gateways
- **Pinning Service**: Files pinned for persistence
- **Metadata Storage**: Encrypted metadata stored separately

## 🔧 Advanced Usage

### Custom IPFS Node

```python
# Connect to remote IPFS node
python main.py --ipfs-host your-node-ip --ipfs-port 5001
```

### Batch Operations

```python
# Example: Upload multiple files via MCP
import json
from mcp_client import MCPClient

client = MCPClient()
for file_path in file_list:
    result = await client.upload_encrypted_file(file_path, password)
    print(f"Uploaded: {json.loads(result)['cid']}")
```

### File Sharing

```python
# Share file via CID
cid = "QmYourFileHashHere"
gateway_url = f"https://ipfs.io/ipfs/{cid}"
# Share this URL with others
```

## 🐛 Troubleshooting

### IPFS Connection Issues

```bash
# Check IPFS status
ipfs version
ipfs id

# Restart IPFS daemon
ipfs daemon
```

### Python Dependencies

```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Check Python version
python --version  # Should be 3.7+
```

### Common Errors

**"Failed to connect to IPFS"**
- Ensure IPFS Desktop is running
- Check if port 5001 is available
- Try restarting IPFS daemon

**"Encryption failed"**
- Check file permissions
- Ensure file is not empty
- Verify file size is under limit

**"Import Error"**
- Activate virtual environment
- Install missing dependencies
- Check Python path

## 📊 Performance

- **File Size Limit**: 100MB (configurable)
- **Encryption Speed**: ~50MB/s on modern hardware
- **Upload Speed**: Depends on IPFS network connectivity
- **Memory Usage**: ~50MB base + file size during operations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest black flake8

# Run tests
pytest

# Format code
black .

# Lint code
flake8 .
```

## 📜 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- **IPFS** - InterPlanetary File System
- **Cryptography Library** - Python cryptographic recipes
- **Model Context Protocol** - Anthropic's MCP standard
- **Encryptum** - Original inspiration

## 📞 Support

For support and questions:

1. Check the troubleshooting section
2. Review the logs in `logs/encryptum.log`
3. Open an issue on the project repository
4. Check IPFS documentation for network issues

## 🚀 Roadmap

- [ ] Web interface for browser access
- [ ] Mobile app support
- [ ] Enhanced file sharing features
- [ ] Cloud pinning service integration
- [ ] Multi-user support with access control
- [ ] File versioning and history
- [ ] Backup and restore functionality
- [ ] Performance optimizations
- [ ] Enhanced security auditing

---

**Built with ❤️ for the decentralized web**