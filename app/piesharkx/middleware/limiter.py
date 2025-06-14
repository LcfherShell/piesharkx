import time
from collections import defaultdict
from threading import Lock
import hashlib
import re
from ..logger import logger
from webob import Request, Response

__all__ = ["RateLimiter"]

class RateLimiter:
    def __init__(self, limit=105, window=60):
        self.limit = limit
        self.window = window
        self.requests = defaultdict(list)
        self.lock = Lock()
        self.last_cleanup = time.time()

    def cleanup(self):
        """Remove old client IDs that have no recent activity"""
        now = time.time()
        if now - self.last_cleanup < self.window:
            return  # Cleanup hanya setiap window detik
        self.last_cleanup = now

        for client_id in list(self.requests.keys()):
            self.requests[client_id] = [t for t in self.requests[client_id] if now - t < self.window]
            if not self.requests[client_id]:
                del self.requests[client_id]  # Hapus client yang tidak aktif

    def get_client_identifier(self, request):
        """
        Get a unique identifier for the client based on a combination of IP address and browser fingerprint.
        """
        # Dapatkan IP address (dengan dukungan proxy/load balancer)
        client_ip = self._get_real_ip(request)
        # Dapatkan browser fingerprint
        user_agent = request.headers.get('User-Agent', '')
        accept_language = request.headers.get('Accept-Language', '')
        accept_encoding = request.headers.get('Accept-Encoding', '')
        
        # Buat fingerprint sederhana dari header browser
        fingerprint_data = f"{user_agent}|{accept_language}|{accept_encoding}"
        fingerprint_hash = hashlib.md5(fingerprint_data.encode()).hexdigest()[:8]
        
        # Kombinasi IP dan fingerprint untuk identifier unik
        client_identifier = f"{client_ip}_{fingerprint_hash}"
        
        return client_identifier

    def _get_real_ip(self, request):
        """
        Get the real IP address, taking into account proxy, load balancer, and CDN
        """
        # Header yang biasa digunakan untuk real IP
        ip_headers = [
            'X-Forwarded-For',
            'X-Real-IP', 
            'X-Client-IP',
            'CF-Connecting-IP',  # Cloudflare
            'True-Client-IP',    # Akamai
            'X-Cluster-Client-IP'
        ]
        # Cek header satu per satu
        for header in ip_headers:
            ip = request.headers.get(header)
            if ip:
                # X-Forwarded-For bisa berisi multiple IP (comma separated)
                # Ambil yang pertama (client asli)
                first_ip = ip.split(',')[0].strip()
                if self._is_valid_ip(first_ip):
                    return first_ip
        
        # Fallback ke remote address
        return request.remote_addr or 'unknown'

    def _is_valid_ip(self, ip):
        """Validate IP address format"""
        if not ip or ip == 'unknown':
            return False
        
        # Regex sederhana untuk IPv4
        ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        # Regex sederhana untuk IPv6
        ipv6_pattern = r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$|^::1$|^::'
        
        if re.match(ipv4_pattern, ip):
            # Validasi range IPv4
            parts = ip.split('.')
            return all(0 <= int(part) <= 255 for part in parts)
        elif re.match(ipv6_pattern, ip):
            return True
        
        return False

    def check_limit(self, request):
        """
        Check if the request from this client is still within the limits
        Args:
            request: Flask/Django/PieShark request object or dict with headers and remote_addr
        """
        with self.lock:
            now = time.time()
            self.cleanup()  # Bersihkan data lama

            # Dapatkan identifier unik untuk client
            client_id = self.get_client_identifier(request)

            # Filter request yang masih dalam window
            self.requests[client_id] = [
                t for t in self.requests[client_id] if now - t < self.window
            ]

            # Cek apakah sudah mencapai limit
            if len(self.requests[client_id]) >= self.limit:
                return False, client_id

            # Tambahkan request baru
            self.requests[client_id].append(now)
            return True, client_id

    def get_remaining_requests(self, request):
        """Get the remaining requests that the client can do"""
        with self.lock:
            client_id = self.get_client_identifier(request)
            now = time.time()
            
            # Filter request yang masih aktif
            active_requests = [
                t for t in self.requests[client_id] if now - t < self.window
            ]
            
            return max(0, self.limit - len(active_requests))

    def get_reset_time(self, request):
        """Get the time when the limit will be reset"""
        with self.lock:
            client_id = self.get_client_identifier(request)
            now = time.time()
            
            if not self.requests[client_id]:
                return 0
            
            # Waktu request tertua + window = waktu reset
            oldest_request = min(self.requests[client_id])
            reset_time = oldest_request + self.window
            
            return max(0, reset_time - now)

    def get_stats(self):
        """Getting rate limiter statistics"""
        with self.lock:
            now = time.time()
            active_clients = 0
            total_requests = 0
            
            for client_id, timestamps in self.requests.items():
                active_requests = [t for t in timestamps if now - t < self.window]
                if active_requests:
                    active_clients += 1
                    total_requests += len(active_requests)
            
            return {
                'active_clients': active_clients,
                'total_active_requests': total_requests,
                'window_seconds': self.window,
                'limit_per_client': self.limit
            }