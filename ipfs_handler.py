"""
Encryptum Clone - IPFS Integration Module (HTTP Gateway Method)
Bypasses version compatibility issues by using HTTP API directly
"""

import requests
import json
import tempfile
import os
from typing import Dict, Any
import logging
from datetime import datetime

class EncryptumIPFS:
    """IPFS handler using HTTP API directly"""
    
    def __init__(self, ipfs_host='127.0.0.1', ipfs_port=5001, gateway_url='https://ipfs.io/ipfs/'):
        self.host = ipfs_host
        self.port = ipfs_port
        self.gateway_url = gateway_url
        self.base_url = f"http://{ipfs_host}:{ipfs_port}/api/v0"
        self.logger = logging.getLogger(__name__)
        
        # Test connection
        try:
            self.test_connection()
            print("✅ Connected to IPFS node via HTTP API")
        except Exception as e:
            self.logger.error(f"Failed to connect to IPFS: {str(e)}")
            raise Exception(f"Failed to connect to IPFS: {str(e)}")
    
    def test_connection(self):
        """Test IPFS connection using HTTP API"""
        try:
            response = requests.post(f"{self.base_url}/id", timeout=10)
            if response.status_code == 200:
                node_info = response.json()
                node_id = node_info.get('ID', 'Unknown')[:20]
                self.logger.info(f"Connected to IPFS node: {node_id}...")
                
                # Try to get version
                try:
                    version_response = requests.post(f"{self.base_url}/version", timeout=5)
                    if version_response.status_code == 200:
                        version_info = version_response.json()
                        print(f"   IPFS Version: {version_info.get('Version', 'Unknown')}")
                except:
                    print(f"   IPFS Version: Unable to determine")
                    
                return True
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Cannot connect to IPFS HTTP API: {e}")
    
    def store_encrypted_file(self, encrypted_data: bytes, metadata: dict) -> dict:
        """
        Store encrypted file on IPFS using HTTP API
        
        Args:
            encrypted_data: Encrypted file bytes
            metadata: File metadata
            
        Returns:
            dict: Storage result with CIDs
        """
        try:
            # Store main file
            files = {'file': ('encrypted_file', encrypted_data, 'application/octet-stream')}
            
            response = requests.post(
                f"{self.base_url}/add",
                files=files,
                params={'only-hash': 'false', 'pin': 'true'},
                timeout=60
            )
            
            if response.status_code != 200:
                raise Exception(f"IPFS add failed: HTTP {response.status_code}: {response.text}")
            
            # Parse response - IPFS returns newline-separated JSON
            lines = response.text.strip().split('\n')
            result = json.loads(lines[-1])  # Last line contains the final result
            cid = result.get('Hash')
            
            if not cid:
                raise Exception("No CID returned from IPFS")
            
            # Enhance metadata
            enhanced_metadata = {
                **metadata,
                'upload_timestamp': datetime.now().isoformat(),
                'file_cid': cid
            }
            
            # Store metadata
            metadata_json = json.dumps(enhanced_metadata, indent=2).encode()
            metadata_files = {'file': ('metadata.json', metadata_json, 'application/json')}
            
            metadata_response = requests.post(
                f"{self.base_url}/add",
                files=metadata_files,
                params={'only-hash': 'false', 'pin': 'true'},
                timeout=30
            )
            
            if metadata_response.status_code != 200:
                raise Exception(f"Metadata storage failed: HTTP {metadata_response.status_code}")
            
            metadata_lines = metadata_response.text.strip().split('\n')
            metadata_result = json.loads(metadata_lines[-1])
            metadata_cid = metadata_result.get('Hash')
            
            if not metadata_cid:
                raise Exception("No metadata CID returned from IPFS")
            
            result_data = {
                'file_cid': cid,
                'metadata_cid': metadata_cid,
                'gateway_url': f"{self.gateway_url}{cid}",
                'metadata_gateway_url': f"{self.gateway_url}{metadata_cid}",
                'ipfs_urls': {
                    'file': f"ipfs://{cid}",
                    'metadata': f"ipfs://{metadata_cid}"
                }
            }
            
            self.logger.info(f"File stored on IPFS: {cid}")
            return result_data
            
        except Exception as e:
            self.logger.error(f"IPFS storage failed: {str(e)}")
            raise Exception(f"IPFS storage failed: {str(e)}")
    
    def retrieve_file(self, cid: str) -> bytes:
        """
        Retrieve file from IPFS using HTTP API
        
        Args:
            cid: Content identifier
            
        Returns:
            bytes: File data
        """
        try:
            self.logger.info(f"Retrieving file from IPFS: {cid}")
            
            response = requests.post(
                f"{self.base_url}/cat",
                params={'arg': cid},
                timeout=60
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to retrieve file: HTTP {response.status_code}: {response.text}")
            
            return response.content
            
        except Exception as e:
            self.logger.error(f"IPFS retrieval failed: {str(e)}")
            raise Exception(f"IPFS retrieval failed: {str(e)}")
    
    def retrieve_metadata(self, metadata_cid: str) -> dict:
        """
        Retrieve metadata from IPFS using HTTP API
        
        Args:
            metadata_cid: Metadata content identifier
            
        Returns:
            dict: Metadata
        """
        try:
            self.logger.info(f"Retrieving metadata from IPFS: {metadata_cid}")
            
            response = requests.post(
                f"{self.base_url}/cat",
                params={'arg': metadata_cid},
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to retrieve metadata: HTTP {response.status_code}")
            
            return json.loads(response.content.decode())
            
        except Exception as e:
            self.logger.error(f"Metadata retrieval failed: {str(e)}")
            raise Exception(f"Metadata retrieval failed: {str(e)}")
    
    def pin_file(self, cid: str):
        """
        Pin file using HTTP API
        
        Args:
            cid: Content identifier to pin
        """
        try:
            response = requests.post(
                f"{self.base_url}/pin/add",
                params={'arg': cid},
                timeout=30
            )
            
            if response.status_code == 200:
                self.logger.info(f"Pinned file: {cid}")
                print(f"📌 Pinned file: {cid}")
            else:
                self.logger.warning(f"Could not pin file {cid}: HTTP {response.status_code}")
                
        except Exception as e:
            self.logger.warning(f"Could not pin file {cid}: {str(e)}")
    
    def unpin_file(self, cid: str):
        """
        Unpin file using HTTP API
        
        Args:
            cid: Content identifier to unpin
        """
        try:
            response = requests.post(
                f"{self.base_url}/pin/rm",
                params={'arg': cid},
                timeout=30
            )
            
            if response.status_code == 200:
                self.logger.info(f"Unpinned file: {cid}")
            else:
                self.logger.warning(f"Could not unpin file {cid}: HTTP {response.status_code}")
                
        except Exception as e:
            self.logger.warning(f"Could not unpin file {cid}: {str(e)}")
    
    def get_file_stats(self, cid: str) -> dict:
        """
        Get file statistics using HTTP API
        
        Args:
            cid: Content identifier
            
        Returns:
            dict: File statistics
        """
        try:
            response = requests.post(
                f"{self.base_url}/object/stat",
                params={'arg': cid},
                timeout=30
            )
            
            if response.status_code == 200:
                stats = response.json()
                return {
                    'cid': cid,
                    'size': stats.get('CumulativeSize', 0),
                    'num_links': stats.get('NumLinks', 0),
                    'block_size': stats.get('BlockSize', 0)
                }
            else:
                return {'cid': cid, 'size': 0, 'num_links': 0, 'block_size': 0}
                
        except Exception as e:
            self.logger.error(f"Failed to get stats for {cid}: {str(e)}")
            return {'cid': cid, 'size': 0, 'num_links': 0, 'block_size': 0}
    
    def list_pinned_files(self) -> list:
        """
        List pinned files using HTTP API
        
        Returns:
            list: List of pinned CIDs
        """
        try:
            response = requests.post(
                f"{self.base_url}/pin/ls",
                params={'type': 'recursive'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'Keys' in result:
                    return list(result['Keys'].keys())
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to list pinned files: {str(e)}")
            return []
    
    def get_node_info(self) -> dict:
        """
        Get IPFS node information using HTTP API
        
        Returns:
            dict: Node information
        """
        try:
            # Get node ID
            id_response = requests.post(f"{self.base_url}/id", timeout=10)
            node_info = {}
            
            if id_response.status_code == 200:
                node_data = id_response.json()
                node_info.update({
                    'peer_id': node_data.get('ID', 'Unknown'),
                    'public_key': node_data.get('PublicKey', 'Unknown'),
                    'addresses': node_data.get('Addresses', []),
                    'agent_version': node_data.get('AgentVersion', 'Unknown'),
                    'protocol_version': node_data.get('ProtocolVersion', 'Unknown')
                })
            
            # Get version
            try:
                version_response = requests.post(f"{self.base_url}/version", timeout=10)
                if version_response.status_code == 200:
                    version_data = version_response.json()
                    node_info.update({
                        'ipfs_version': version_data.get('Version', 'Unknown'),
                        'commit': version_data.get('Commit', 'Unknown')
                    })
            except:
                node_info.update({
                    'ipfs_version': 'Unknown',
                    'commit': 'Unknown'
                })
            
            return node_info
            
        except Exception as e:
            self.logger.error(f"Failed to get node info: {str(e)}")
            return {
                'peer_id': 'Unknown',
                'ipfs_version': 'Unknown',
                'error': str(e)
            }
    
    def check_connection(self) -> bool:
        """
        Check if IPFS connection is healthy
        
        Returns:
            bool: True if connected
        """
        try:
            response = requests.post(f"{self.base_url}/id", timeout=5)
            return response.status_code == 200
        except:
            return False
