"""
Advanced Network Scanner and HTTP Response Analyzer
Provides comprehensive network analysis including HTTP header inspection, 
SSL certificate validation, and port scanning capabilities.
"""
import socket
import ssl
import threading
import socketserver
import requests
import json
import time
import logging
from urllib import request as urllib_request
from urllib.parse import urlparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import sys
from ..logger import logger

__all__ = ["NetworkScanner", "NetworkServer"]

@dataclass
class ScanResult:
    """Data class for storing scan results"""
    host: str
    port: int
    status: str
    response_time: float
    headers: Dict[str, str]
    ssl_info: Optional[Dict[str, Union[str, bool]]] = None
    error_message: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    """Enhanced TCP request handler with logging and error handling"""
    
    def handle(self):
        try:
            client_address = self.client_address
            logger.info(f"Connection from {client_address}")
            
            # Receive data with timeout
            self.request.settimeout(10.0)
            data = self.request.recv(4096).decode('ascii', errors='ignore')
            
            if not data:
                logger.warning(f"No data received from {client_address}")
                return
                
            cur_thread = threading.current_thread()
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            response_data = {
                'thread': cur_thread.name,
                'client': str(client_address),
                'timestamp': timestamp,
                'received_data': data.strip(),
                'data_length': len(data)
            }
            
            response = json.dumps(response_data, indent=2).encode('ascii')
            self.request.sendall(response)
            
            logger.info(f"Response sent to {client_address}")
            
        except socket.timeout:
            logger.error(f"Timeout handling request from {self.client_address}")
        except Exception as e:
            logger.error(f"Error handling request from {self.client_address}: {e}")

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Enhanced threaded TCP server with proper cleanup"""
    allow_reuse_address = True
    daemon_threads = True

class NetworkScanner:
    """Advanced network scanner with multiple scanning methods"""
    
    def __init__(self, timeout: int = 10, max_workers: int = 50):
        self.timeout = timeout
        self.max_workers = max_workers
        self.results: List[ScanResult] = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NetworkScanner/1.0 (Advanced Network Analysis Tool)'
        })
        
    def scan_port(self, host: str, port: int) -> bool:
        """Check if a specific port is open"""
        try:
            with socket.create_connection((host, port), timeout=self.timeout):
                return True
        except (socket.timeout, socket.error, ConnectionRefusedError):
            return False
    
    def get_ssl_info(self, host: str, port: int = 443) -> Optional[Dict[str, Union[str, bool]]]:
        """Extract SSL certificate information"""
        try:
            context = ssl.create_default_context()
            with socket.create_connection((host, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert()
                    
                    ssl_info = {
                        'version': ssock.version(),
                        'cipher': ssock.cipher(),
                        'subject': dict(x[0] for x in cert.get('subject', [])),
                        'issuer': dict(x[0] for x in cert.get('issuer', [])),
                        'not_before': cert.get('notBefore'),
                        'not_after': cert.get('notAfter'),
                        'serial_number': str(cert.get('serialNumber', '')),
                        'is_expired': self._is_cert_expired(cert)
                    }
                    return ssl_info
        except Exception as e:
            logger.debug(f"SSL info extraction failed for {host}:{port} - {e}")
            return None
    
    def _is_cert_expired(self, cert: Dict) -> bool:
        """Check if SSL certificate is expired"""
        try:
            not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
            return datetime.now() > not_after
        except:
            return False
    
    def analyze_http_response(self, host: str, port: int = 80, use_https: bool = False) -> ScanResult:
        """Comprehensive HTTP response analysis"""
        protocol = 'https' if use_https else 'http'
        url = f"{protocol}://{host}" + (f":{port}" if port not in [80, 443] else "")
        
        start_time = time.time()
        
        try:
            # Try with requests first
            response = self.session.get(
                url, 
                timeout=self.timeout, 
                verify=False, 
                allow_redirects=True
            )
            
            response_time = time.time() - start_time
            
            headers = dict(response.headers)
            ssl_info = None
            
            if use_https:
                ssl_info = self.get_ssl_info(host, port)
            
            return ScanResult(
                host=host,
                port=port,
                status=f"HTTP {response.status_code}",
                response_time=response_time,
                headers=headers,
                ssl_info=ssl_info
            )
            
        except requests.exceptions.RequestException as e:
            # Fallback to urllib
            try:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                
                with urllib_request.urlopen(url, context=ctx, timeout=self.timeout) as response:
                    response_time = time.time() - start_time
                    headers = dict(response.headers)
                    
                    return ScanResult(
                        host=host,
                        port=port,
                        status="HTTP 200 (urllib)",
                        response_time=response_time,
                        headers=headers
                    )
                    
            except Exception as urllib_error:
                # Final fallback - raw socket
                return self._raw_socket_check(host, port, start_time)
    
    def _raw_socket_check(self, host: str, port: int, start_time: float) -> ScanResult:
        """Raw socket HTTP check as final fallback"""
        try:
            with socket.create_connection((host, port), timeout=self.timeout) as sock:
                request = f"GET / HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
                sock.send(request.encode('utf-8'))
                
                response_data = b""
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    response_data += chunk
                    if len(response_data) > 8192:  # Limit response size
                        break
                
                response_time = time.time() - start_time
                response_str = response_data.decode('utf-8', errors='ignore')
                
                # Parse status
                status_line = response_str.split('\r\n')[0] if response_str else "Unknown"
                
                return ScanResult(
                    host=host,
                    port=port,
                    status=status_line,
                    response_time=response_time,
                    headers={'raw_response': response_str[:500]}
                )
                
        except Exception as e:
            response_time = time.time() - start_time
            return ScanResult(
                host=host,
                port=port,
                status="Connection Failed",
                response_time=response_time,
                headers={},
                error_message=str(e)
            )
    
    def scan_multiple_hosts(self, targets: List[Tuple[str, int, bool]]) -> List[ScanResult]:
        """Scan multiple hosts concurrently"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_target = {
                executor.submit(self.analyze_http_response, host, port, use_https): (host, port, use_https)
                for host, port, use_https in targets
            }
            
            for future in as_completed(future_to_target):
                target = future_to_target[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.info(f"Completed scan for {target[0]}:{target[1]}")
                except Exception as e:
                    logger.error(f"Scan failed for {target[0]}:{target[1]} - {e}")
                    
        return results
    
    def port_scan_range(self, host: str, start_port: int, end_port: int) -> List[int]:
        """Scan a range of ports and return open ports"""
        open_ports = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_port = {
                executor.submit(self.scan_port, host, port): port
                for port in range(start_port, end_port + 1)
            }
            
            for future in as_completed(future_to_port):
                port = future_to_port[future]
                try:
                    if future.result():
                        open_ports.append(port)
                        logger.info(f"Port {port} is open on {host}")
                except Exception as e:
                    logger.debug(f"Error scanning port {port} on {host}: {e}")
                    
        return sorted(open_ports)
    
    def generate_report(self, results: List[ScanResult], filename: str = None) -> str:
        """Generate detailed scan report"""
        if filename is None:
            filename = f"scan_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
        report_data = {
            'scan_info': {
                'timestamp': datetime.now().isoformat(),
                'total_targets': len(results),
                'timeout': self.timeout,
                'max_workers': self.max_workers
            },
            'results': [asdict(result) for result in results]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)
            
        logger.info(f"Report saved to {filename}")
        return filename

class NetworkServer:
    """Enhanced network server for testing purposes"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8080):
        self.host = host
        self.port = port
        self.server = None
        self.server_thread = None
        
    def start_server(self):
        """Start the threaded TCP server"""
        try:
            self.server = ThreadedTCPServer((self.host, self.port), ThreadedTCPRequestHandler)
            
            # Get actual address (useful when port=0 for auto-assignment)
            actual_host, actual_port = self.server.server_address
            logger.info(f"Server starting on {actual_host}:{actual_port}")
            
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            logger.info(f"Server running in thread: {self.server_thread.name}")
            return actual_host, actual_port
            
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            raise
    
    def stop_server(self):
        """Stop the server gracefully"""
        if self.server:
            logger.info("Shutting down server...")
            self.server.shutdown()
            self.server.server_close()
            if self.server_thread:
                self.server_thread.join(timeout=5)
            logger.info("Server stopped")
    
    def send_test_message(self, message: str) -> str:
        """Send test message to server"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(10)
                sock.connect((self.host, self.port))
                sock.sendall(message.encode('ascii'))
                response = sock.recv(4096).decode('ascii')
                return response
        except Exception as e:
            logger.error(f"Failed to send test message: {e}")
            return f"Error: {e}"


def client(ip, port, message):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((ip, port))
        sock.sendall(bytes(message, 'ascii'))
        response = str(sock.recv(1024), 'ascii')
        print("Received: {}".format(response))

HOST, PORT = "127.0.0.1", 80

"""if __name__ == "__main__":
    # Port 0 means to select an arbitrary unused port
    

    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    with server:
        ip, port = server.server_address
        print(ip, port)
        # Start a thread with the server -- that thread will then start one
        # more thread for each request
        server_thread = threading.Thread(target=server.serve_forever)
        # Exit the server thread when the main thread terminates
        server_thread.daemon = True
        server_thread.start()
        print("Server loop running in thread:", server_thread.name)

        client(ip, port, "Hello World 1")
        client(ip, port, "Hello World 2")
        client(ip, port, "Hello World 3")
        server.serve_forever()

"""
"""import ssl

hostname = 'www.google.com'
context = ssl.create_default_context()

with socket.create_connection((hostname, 80)) as sock:
    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
        print(ssock.version())"""

"""with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(b"Hello, world")
    data = s.recv(1024)
print(data)
"""
class Shake:
    def __init__(self):
        super(Shake, self).__init__()
        self.response_outputs = ''

    def response(self, host:str,port:int=80):
            response_output = 'Private APP'
            if port != 80:
                urls = 'http://{host}:{port}'.format(host=host, port=port)
            else:
                urls = 'http://{host}'.format(host=host)

            try:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                with requests.get(urls, cert=ctx) as f:
                    response_output = f.headers
            except:
                try:
                    with requests.get(urls) as res:
                        response_output = res.headers
                except:
                    response_output = 'ERROR URL'
                    """try:
                                                                                    s = socket.create_connection((host, port))
                                                                                    s.send("GET / HTTP/1.1\r\n\r\n".encode('utf-8'))
                                                                                    x = s.recv(800)
                                                                                    response_output =  x.decode('utf-8')
                                                                                    if '404' in response_output:
                                                                                        response_output = 'Private APP'
                                                                                except:
                                                                                    """

            finally:
                self.saving = str(response_output)

    @property
    def saving(self):
        return self.response_outputs

    @saving.setter
    def saving(self, response_output:str):
        self.response_outputs = response_output