"""
Encryptum Clone - Configuration Module with Blockchain Support
Enhanced configuration management including blockchain settings
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import json

@dataclass
class EncryptumConfig:
    """Configuration settings for Encryptum clone with blockchain support"""
    
    # IPFS Settings
    ipfs_host: str = '127.0.0.1'
    ipfs_port: int = 5001
    ipfs_gateway_url: str = 'https://ipfs.io/ipfs/'
    
    # Encryption Settings
    pbkdf2_iterations: int = 100000
    
    # MCP Server Settings
    mcp_server_port: int = 8000
    mcp_server_host: str = 'localhost'
    
    # GUI Settings
    window_width: int = 1100
    window_height: int = 750
    theme: str = 'dark'  # 'dark' or 'light'
    
    # Storage Settings
    registry_file: str = 'file_registry.json'
    max_file_size_mb: int = 100
    temp_dir: Optional[str] = None
    
    # Logging Settings
    log_level: str = 'INFO'
    log_file: str = 'encryptum.log'
    log_max_size_mb: int = 10
    log_backup_count: int = 3
    
    # Security Settings
    auto_pin_files: bool = True
    verify_file_integrity: bool = True
    clear_temp_files: bool = True
    
    # Blockchain Settings
    blockchain_enabled: bool = True
    default_network: str = 'sepolia'  # 'ethereum_mainnet', 'polygon', 'arbitrum', 'sepolia'
    blockchain_api_key: Optional[str] = None  # For Alchemy/Infura
    pinning_contract_address: str = ''  # Deployed contract address
    
    # Blockchain Pinning Defaults
    default_pin_duration_days: int = 30
    min_pin_duration_days: int = 30
    max_pin_duration_days: int = 365
    auto_estimate_gas: bool = True
    max_gas_price_gwei: Optional[float] = None  # Max gas price limit
    
    # Gas Configuration (NEW)
    gas_limit_buffer: float = 1.2  # 20% buffer on estimated gas
    gas_price_buffer: float = 1.1  # 10% buffer on gas price
    min_gas_price_gwei: float = 1.0  # Minimum gas price in Gwei
    default_gas_limit: int = 500000  # Default gas limit if estimation fails
    max_gas_limit: int = 2000000  # Maximum allowed gas limit
    gas_estimation_timeout: int = 30  # Timeout for gas estimation in seconds
    
    # Blockchain Network Configs
    custom_networks: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # UI Text and Colors
    app_name: str = "🛡️ ENCRYPTUM"
    app_subtitle: str = "Decentralized • Encrypted • Your Data • Blockchain Pinned"
    
    # Dark theme colors
    bg_color_dark: str = '#1a1a1a'
    panel_color_dark: str = '#2d2d2d'
    accent_color: str = '#00d4aa'
    text_color_dark: str = '#ffffff'
    text_secondary_dark: str = '#888888'
    blockchain_accent: str = '#6366f1'  # Purple for blockchain features
    
    # Light theme colors
    bg_color_light: str = '#ffffff'
    panel_color_light: str = '#f5f5f5'
    text_color_light: str = '#000000'
    text_secondary_light: str = '#666666'
    
    def __post_init__(self):
        """Initialize derived settings"""
        if self.temp_dir is None:
            self.temp_dir = os.path.join(os.getcwd(), 'temp')
        
        # Ensure directories exist
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        os.makedirs('wallets', exist_ok=True)
        
        # Load environment variables for sensitive data
        if not self.blockchain_api_key:
            self.blockchain_api_key = os.getenv('BLOCKCHAIN_API_KEY')
        
        if not self.pinning_contract_address:
            self.pinning_contract_address = os.getenv('PINNING_CONTRACT_ADDRESS', '')
    
    @property
    def ipfs_api_url(self) -> str:
        """Get IPFS API URL"""
        return f'http://{self.ipfs_host}:{self.ipfs_port}'
    
    @property
    def mcp_server_url(self) -> str:
        """Get MCP server URL"""
        return f'http://{self.mcp_server_host}:{self.mcp_server_port}'
    
    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes"""
        return self.max_file_size_mb * 1024 * 1024
    
    @property
    def current_theme_colors(self) -> dict:
        """Get colors for current theme"""
        if self.theme == 'dark':
            return {
                'bg': self.bg_color_dark,
                'panel': self.panel_color_dark,
                'text': self.text_color_dark,
                'text_secondary': self.text_secondary_dark,
                'accent': self.accent_color,
                'blockchain': self.blockchain_accent
            }
        else:
            return {
                'bg': self.bg_color_light,
                'panel': self.panel_color_light,
                'text': self.text_color_light,
                'text_secondary': self.text_secondary_light,
                'accent': self.accent_color,
                'blockchain': self.blockchain_accent
            }
    
    def get_blockchain_config(self) -> Dict[str, Any]:
        """Get blockchain configuration"""
        return {
            'enabled': self.blockchain_enabled,
            'network': self.default_network,
            'api_key': self.blockchain_api_key,
            'contract_address': self.pinning_contract_address,
            'pin_duration': self.default_pin_duration_days,
            'gas_settings': {
                'auto_estimate': self.auto_estimate_gas,
                'max_price_gwei': self.max_gas_price_gwei,
                'gas_limit_buffer': self.gas_limit_buffer,
                'gas_price_buffer': self.gas_price_buffer,
                'min_gas_price_gwei': self.min_gas_price_gwei,
                'default_gas_limit': self.default_gas_limit,
                'max_gas_limit': self.max_gas_limit
            }
        }
    
    @classmethod
    def from_env(cls) -> 'EncryptumConfig':
        """Create config from environment variables"""
        return cls(
            ipfs_host=os.getenv('ENCRYPTUM_IPFS_HOST', '127.0.0.1'),
            ipfs_port=int(os.getenv('ENCRYPTUM_IPFS_PORT', '5001')),
            ipfs_gateway_url=os.getenv('ENCRYPTUM_GATEWAY_URL', 'https://ipfs.io/ipfs/'),
            pbkdf2_iterations=int(os.getenv('ENCRYPTUM_PBKDF2_ITERATIONS', '100000')),
            mcp_server_port=int(os.getenv('ENCRYPTUM_MCP_PORT', '8000')),
            max_file_size_mb=int(os.getenv('ENCRYPTUM_MAX_FILE_SIZE_MB', '100')),
            log_level=os.getenv('ENCRYPTUM_LOG_LEVEL', 'INFO'),
            theme=os.getenv('ENCRYPTUM_THEME', 'dark'),
            registry_file=os.getenv('ENCRYPTUM_REGISTRY_FILE', 'file_registry.json'),
            
            # Blockchain settings from env
            blockchain_enabled=os.getenv('ENCRYPTUM_BLOCKCHAIN_ENABLED', 'true').lower() == 'true',
            default_network=os.getenv('ENCRYPTUM_DEFAULT_NETWORK', 'sepolia'),
            blockchain_api_key=os.getenv('ENCRYPTUM_BLOCKCHAIN_API_KEY'),
            pinning_contract_address=os.getenv('ENCRYPTUM_CONTRACT_ADDRESS', ''),
            default_pin_duration_days=int(os.getenv('ENCRYPTUM_PIN_DURATION', '30')),
            max_gas_price_gwei=float(os.getenv('ENCRYPTUM_MAX_GAS_GWEI', '0')) or None,
            
            # Gas settings from env
            gas_limit_buffer=float(os.getenv('ENCRYPTUM_GAS_LIMIT_BUFFER', '1.2')),
            gas_price_buffer=float(os.getenv('ENCRYPTUM_GAS_PRICE_BUFFER', '1.1')),
            min_gas_price_gwei=float(os.getenv('ENCRYPTUM_MIN_GAS_GWEI', '1.0'))
        )
    
    def save_to_file(self, config_file: str = 'encryptum_config.json'):
        """Save configuration to file"""
        config_dict = {
            'ipfs_host': self.ipfs_host,
            'ipfs_port': self.ipfs_port,
            'ipfs_gateway_url': self.ipfs_gateway_url,
            'pbkdf2_iterations': self.pbkdf2_iterations,
            'mcp_server_port': self.mcp_server_port,
            'window_width': self.window_width,
            'window_height': self.window_height,
            'theme': self.theme,
            'max_file_size_mb': self.max_file_size_mb,
            'log_level': self.log_level,
            'auto_pin_files': self.auto_pin_files,
            'verify_file_integrity': self.verify_file_integrity,
            
            # Blockchain settings
            'blockchain_enabled': self.blockchain_enabled,
            'default_network': self.default_network,
            'pinning_contract_address': self.pinning_contract_address,
            'default_pin_duration_days': self.default_pin_duration_days,
            'max_gas_price_gwei': self.max_gas_price_gwei,
            'custom_networks': self.custom_networks,
            
            # Gas settings
            'gas_limit_buffer': self.gas_limit_buffer,
            'gas_price_buffer': self.gas_price_buffer,
            'min_gas_price_gwei': self.min_gas_price_gwei,
            'default_gas_limit': self.default_gas_limit,
            'max_gas_limit': self.max_gas_limit
        }
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config_dict, f, indent=2)
        except Exception as e:
            print(f"Failed to save config: {e}")
    
    @classmethod
    def load_from_file(cls, config_file: str = 'encryptum_config.json') -> 'EncryptumConfig':
        """Load configuration from file"""
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config_dict = json.load(f)
                
                # Create instance with loaded values
                instance = cls()
                for key, value in config_dict.items():
                    if hasattr(instance, key):
                        setattr(instance, key, value)
                
                return instance
        except Exception as e:
            print(f"Failed to load config file, using defaults: {e}")
        
        return cls()
    
    def add_custom_network(self, name: str, config: Dict[str, Any]):
        """Add a custom blockchain network configuration"""
        self.custom_networks[name] = {
            'rpc_url': config.get('rpc_url', ''),
            'chain_id': config.get('chain_id', 0),
            'name': config.get('name', name),
            'currency': config.get('currency', 'ETH'),
            'explorer': config.get('explorer', '')
        }
        self.save_to_file()

# Global configuration instance
config = EncryptumConfig.from_env()

# Validation functions
def validate_ipfs_connection(host: str, port: int) -> bool:
    """Validate IPFS connection"""
    try:
        import requests
        response = requests.post(f"http://{host}:{port}/api/v0/id", timeout=5)
        return response.status_code == 200
    except:
        return False

def validate_blockchain_connection(network: str, api_key: Optional[str] = None) -> bool:
    """Validate blockchain connection"""
    try:
        from blockchain_handler import EncryptumBlockchain
        blockchain = EncryptumBlockchain(network=network, api_key=api_key)
        return blockchain.w3.is_connected()
    except:
        return False

def validate_file_size(file_path: str, max_size_bytes: int) -> bool:
    """Validate file size"""
    try:
        file_size = os.path.getsize(file_path)
        return file_size <= max_size_bytes
    except:
        return False

def get_supported_file_types() -> list:
    """Get list of supported file types"""
    return [
        # Documents
        '.txt', '.pdf', '.doc', '.docx', '.rtf', '.odt',
        # Images
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp',
        # Audio
        '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a',
        # Video
        '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',
        # Archives
        '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2',
        # Code
        '.py', '.js', '.html', '.css', '.json', '.xml', '.yaml',
        # Spreadsheets
        '.xls', '.xlsx', '.csv', '.ods',
        # Presentations
        '.ppt', '.pptx', '.odp'
    ]

def is_supported_file_type(file_path: str) -> bool:
    """Check if file type is supported"""
    _, ext = os.path.splitext(file_path.lower())
    return ext in get_supported_file_types()

def estimate_blockchain_costs(file_size_mb: float, duration_days: int, network: str = 'sepolia') -> Dict[str, float]:
    """Estimate blockchain pinning costs"""
    # Rough estimates (should be calculated from contract)
    costs = {
        'ethereum_mainnet': 0.001,  # ETH per GB per day
        'polygon': 0.0001,         # MATIC per GB per day
        'arbitrum': 0.0005,        # ETH per GB per day
        'sepolia': 0.0001,         # ETH per GB per day (testnet)
    }
    
    price_per_gb_per_day = costs.get(network, 0.001)
    size_gb = file_size_mb / 1024
    total_cost = size_gb * duration_days * price_per_gb_per_day
    
    # Add estimated gas costs
    gas_estimates = {
        'ethereum_mainnet': 0.01,   # ETH for gas
        'polygon': 0.001,          # MATIC for gas
        'arbitrum': 0.001,         # ETH for gas
        'sepolia': 0.001,          # ETH for gas (testnet)
    }
    
    gas_cost = gas_estimates.get(network, 0.01)
    
    return {
        'pin_cost': total_cost,
        'gas_cost': gas_cost,
        'total_cost': total_cost + gas_cost
    }

# Contract deployment addresses (example)
DEPLOYED_CONTRACTS = {
    'sepolia': '0x1234567890123456789012345678901234567890',  # Replace with actual
    'polygon_mumbai': '0x0987654321098765432109876543210987654321',  # Replace with actual
    # Add more as contracts are deployed
}

def get_contract_address(network: str) -> Optional[str]:
    """Get deployed contract address for a network"""
    return DEPLOYED_CONTRACTS.get(network)