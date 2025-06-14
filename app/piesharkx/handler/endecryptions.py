import requests, base64, hashlib, re, string, secrets, sys, math, time, random, os, json, threading, uuid
#from requests.packages.urllib3.exceptions import InsecureRequestWarning
from datetime import datetime, timezone
from Crypto import Random
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Cipher import AES
from bs4 import BeautifulSoup
from chardet import detect
import statistics

__all__ = ["AdvancedCryptoSystem", "Base64_Token_128", "Ciphertext_128", 
            "Magic_Data", "AESCipher", "AUTH_TOKEN", "AESCipher_2", "AES", "base64", "hashlib"]
#PY3 = sys.version_info[0] == 3

token_api = ''

cache_base128 = []

class AdvancedCryptoSystem:
    """Enhanced encryption/decryption system with multiple layers of security and modern UUID management"""
    
    def __init__(self, app_config=None):
        self.app_config = app_config or {}
        self.session_cache = {}
        self.key_cache = {}
        self.encryption_history = []
        self.uuid_registry = {}
        self.lock = threading.Lock()
        self.system_uuid = self.generate_system_uuid()
        
    def generate_system_uuid(self):
        """Generate unique system UUID with metadata"""
        system_id = uuid.uuid4()
        mac_uuid = uuid.uuid1()  # MAC address based
        namespace_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, 'crypto.system.local')
        
        system_info = {
            'system_id': str(system_id),
            'mac_uuid': str(mac_uuid),
            'namespace_uuid': str(namespace_uuid),
            'created_at': datetime.now(timezone.utc).isoformat(),
            'node_id': hex(uuid.getnode()),
            'version': '2.0.0'
        }
        
        return system_info
    
    def generate_uuid_variants(self, namespace=None, name=None):
        """Generate various UUID types for different use cases"""
        uuids = {}
        
        # UUID1 - MAC address and timestamp based
        uuids['uuid1'] = str(uuid.uuid1())
        
        # UUID4 - Random UUID (most secure)
        uuids['uuid4'] = str(uuid.uuid4())
        
        # UUID3 - MD5 namespace based
        if namespace and name:
            if isinstance(namespace, str):
                # Convert string to valid namespace UUID
                namespace = uuid.uuid5(uuid.NAMESPACE_DNS, namespace)
            uuids['uuid3'] = str(uuid.uuid3(namespace, name))
        
        # UUID5 - SHA1 namespace based (recommended over UUID3)
        if namespace and name:
            if isinstance(namespace, str):
                namespace = uuid.uuid5(uuid.NAMESPACE_DNS, namespace)
            uuids['uuid5'] = str(uuid.uuid5(namespace, name))
        
        # Custom UUID variants
        uuids['short_uuid'] = self.generate_short_uuid()
        uuids['secure_uuid'] = self.generate_secure_uuid()
        uuids['timestamped_uuid'] = self.generate_timestamped_uuid()
        
        return uuids
    
    def generate_short_uuid(self, length=8):
        """Generate shorter UUID for performance-critical applications"""
        full_uuid = str(uuid.uuid4()).replace('-', '')
        return full_uuid[:length]
    
    def generate_secure_uuid(self):
        """Generate cryptographically secure UUID with additional entropy"""
        # Combine multiple entropy sources
        entropy_sources = [
            secrets.token_bytes(16),
            os.urandom(16),
            str(time.time_ns()).encode(),
            str(uuid.uuid4()).encode()
        ]
        
        combined_entropy = b''.join(entropy_sources)
        secure_hash = hashlib.sha256(combined_entropy).digest()
        
        # Create UUID from hash
        secure_uuid = uuid.UUID(bytes=secure_hash[:16])
        return str(secure_uuid)
    
    def generate_timestamped_uuid(self):
        """Generate UUID with embedded timestamp"""
        timestamp = int(time.time() * 1000000)  # microseconds
        random_part = secrets.randbits(64)
        
        # Combine timestamp and random data
        combined = (timestamp << 64) | random_part
        uuid_bytes = combined.to_bytes(16, byteorder='big')
        
        timestamped_uuid = uuid.UUID(bytes=uuid_bytes)
        return str(timestamped_uuid)
    
    def decode_timestamped_uuid(self, timestamped_uuid):
        """Extract timestamp from timestamped UUID"""
        try:
            uuid_obj = uuid.UUID(timestamped_uuid)
            uuid_int = int(uuid_obj.hex, 16)
            timestamp = (uuid_int >> 64) / 1000000  # convert back to seconds
            return datetime.fromtimestamp(timestamp, timezone.utc)
        except:
            return None
    
    def generate_hierarchical_uuid(self, parent_uuid=None, level=0):
        """Generate hierarchical UUID structure"""
        if parent_uuid is None:
            parent_uuid = str(uuid.uuid4())
        
        hierarchy_data = {
            'parent': parent_uuid,
            'level': level,
            'timestamp': time.time(),
            'random': secrets.randbits(32)
        }
        
        hierarchy_string = json.dumps(hierarchy_data, sort_keys=True)
        child_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, hierarchy_string))
        
        return {
            'uuid': child_uuid,
            'parent': parent_uuid,
            'level': level,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
    
    def register_uuid(self, uuid_str, metadata=None):
        """Register UUID with metadata in registry"""
        with self.lock:
            if uuid_str not in self.uuid_registry:
                self.uuid_registry[uuid_str] = {
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'access_count': 0,
                    'last_accessed': None,
                    'metadata': metadata or {},
                    'status': 'active'
                }
            
            self.uuid_registry[uuid_str]['access_count'] += 1
            self.uuid_registry[uuid_str]['last_accessed'] = datetime.now(timezone.utc).isoformat()
    
    def validate_uuid(self, uuid_str, version=None):
        """Validate UUID format and version"""
        try:
            uuid_obj = uuid.UUID(uuid_str)
            if version and uuid_obj.version != version:
                return False
            return True
        except ValueError:
            return False
    
    def uuid_analytics(self):
        """Get analytics about UUID usage"""
        with self.lock:
            total_uuids = len(self.uuid_registry)
            active_uuids = sum(1 for info in self.uuid_registry.values() 
                             if info['status'] == 'active')
            
            access_counts = [info['access_count'] for info in self.uuid_registry.values()]
            avg_access = statistics.mean(access_counts) if access_counts else 0
            
            return {
                'total_registered': total_uuids,
                'active_uuids': active_uuids,
                'average_access_count': avg_access,
                'system_uuid': self.system_uuid['system_id'],
                'registry_size_kb': len(str(self.uuid_registry)) / 1024
            }
        """Generate cryptographically secure random key"""
        return secrets.token_bytes(length)
    
    def derive_key_from_password(self, password, salt=None, iterations=100000):
        """Derive encryption key from password using PBKDF2"""
        if salt is None:
            salt = get_random_bytes(16)
        
        key = PBKDF2(password, salt, dkLen=32, count=iterations)
        return key, salt
    
    def generate_dynamic_key(self, seed_data=None):
        """Generate dynamic key based on statistical operations"""
        if seed_data is None:
            seed_data = [random.randint(1, 100) for _ in range(20)]
        
        # Statistical operations for key generation
        mean_val = statistics.mean(seed_data)
        median_val = statistics.median(seed_data)
        mode_val = statistics.mode(seed_data) if len(set(seed_data)) < len(seed_data) else mean_val
        
        # Create key material from statistics
        key_material = f"{mean_val}{median_val}{mode_val}{sum(seed_data)}"
        
        # Hash the key material
        key_hash = hashlib.sha256(key_material.encode()).digest()
        return key_hash

    def aes_encrypt(self, plaintext, key=None, password=None, use_uuid=True):
        """AES encryption with CBC mode and optional UUID tracking"""
        operation_uuid = str(uuid.uuid4()) if use_uuid else None
        
        if key is None and password is not None:
            key, salt = self.derive_key_from_password(password)
        elif key is None:
            key = self.generate_secure_key()
            salt = None
        else:
            salt = None
        
        # Generate random IV
        iv = get_random_bytes(16)
        
        # Pad plaintext to multiple of 16 bytes
        padding_length = 16 - (len(plaintext) % 16)
        padded_plaintext = plaintext + bytes([padding_length] * padding_length)
        
        # Encrypt
        cipher = AES.new(key, AES.MODE_CBC, iv)
        ciphertext = cipher.encrypt(padded_plaintext)
        
        # Combine IV and ciphertext
        encrypted_data = iv + ciphertext
        
        result = {
            'encrypted_data': base64.b64encode(encrypted_data).decode('utf-8'),
            'key': base64.b64encode(key).decode('utf-8'),
            'salt': base64.b64encode(salt).decode('utf-8') if salt else None,
            'timestamp': time.time(),
            'operation_uuid': operation_uuid,
            'algorithm': 'AES-256-CBC'
        }
        
        if use_uuid and operation_uuid:
            self.register_uuid(operation_uuid, {
                'operation': 'aes_encrypt',
                'algorithm': 'AES-256-CBC',
                'data_size': len(plaintext)
            })
        
        return result

    def aes_decrypt(self, encrypted_data, key, salt=None):
        """AES decryption with CBC mode"""
        try:
            # Decode base64
            encrypted_bytes = base64.b64decode(encrypted_data)
            key_bytes = base64.b64decode(key)
            
            # Extract IV and ciphertext
            iv = encrypted_bytes[:16]
            ciphertext = encrypted_bytes[16:]
            
            # Decrypt
            cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
            padded_plaintext = cipher.decrypt(ciphertext)
            
            # Remove padding
            padding_length = padded_plaintext[-1]
            plaintext = padded_plaintext[:-padding_length]
            
            return plaintext
            
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")

    def custom_base64_encrypt(self, message, custom_key=None):
        """Enhanced custom base64 encryption"""
        if custom_key is None:
            custom_key = self.generate_custom_key()
        
        # Convert message to bytes if string
        if isinstance(message, str):
            message = message.encode('utf-8')
        
        # XOR encryption with custom key
        encrypted_bytes = []
        for i, byte in enumerate(message):
            key_byte = custom_key[i % len(custom_key)]
            encrypted_bytes.append(byte ^ key_byte)
        
        # Base64 encode
        encrypted_b64 = base64.b64encode(bytes(encrypted_bytes)).decode('utf-8')
        
        # Additional obfuscation
        obfuscated = self.obfuscate_string(encrypted_b64)
        
        return {
            'encrypted': obfuscated,
            'key': base64.b64encode(custom_key).decode('utf-8'),
            'checksum': hashlib.md5(message).hexdigest()
        }

    def custom_base64_decrypt(self, encrypted_data, key, expected_checksum=None):
        """Enhanced custom base64 decryption"""
        try:
            # Deobfuscate
            deobfuscated = self.deobfuscate_string(encrypted_data)
            
            # Decode base64
            encrypted_bytes = base64.b64decode(deobfuscated)
            key_bytes = base64.b64decode(key)
            
            # XOR decryption
            decrypted_bytes = []
            for i, byte in enumerate(encrypted_bytes):
                key_byte = key_bytes[i % len(key_bytes)]
                decrypted_bytes.append(byte ^ key_byte)
            
            decrypted_message = bytes(decrypted_bytes)
            
            # Verify checksum if provided
            if expected_checksum:
                actual_checksum = hashlib.md5(decrypted_message).hexdigest()
                if actual_checksum != expected_checksum:
                    raise ValueError("Checksum verification failed")
            
            return decrypted_message
            
        except Exception as e:
            raise ValueError(f"Custom decryption failed: {str(e)}")
    
    def generate_secure_key(self, length=32):
        """Generate cryptographically secure random key"""
        return secrets.token_bytes(length)
    
    def generate_custom_key(self, length=32):
        """Generate custom key with statistical properties"""
        # Generate random seed data
        seed_data = [random.randint(1, 255) for _ in range(50)]
        
        # Calculate statistical values
        mean_val = int(statistics.mean(seed_data))
        median_val = int(statistics.median(seed_data))
        
        # Create key pattern
        key_pattern = []
        for i in range(length):
            if i % 3 == 0:
                key_pattern.append(mean_val % 256)
            elif i % 3 == 1:
                key_pattern.append(median_val % 256)
            else:
                key_pattern.append(secrets.randbelow(256))
        
        return bytes(key_pattern)

    def obfuscate_string(self, text):
        """Simple string obfuscation"""
        obfuscated = ""
        shift = 3
        for char in text:
            if char.isalnum():
                if char.isdigit():
                    obfuscated += str((int(char) + shift) % 10)
                elif char.isupper():
                    obfuscated += chr((ord(char) - ord('A') + shift) % 26 + ord('A'))
                else:
                    obfuscated += chr((ord(char) - ord('a') + shift) % 26 + ord('a'))
            else:
                obfuscated += char
        return obfuscated

    def deobfuscate_string(self, text):
        """Reverse string obfuscation"""
        deobfuscated = ""
        shift = 3
        for char in text:
            if char.isalnum():
                if char.isdigit():
                    deobfuscated += str((int(char) - shift) % 10)
                elif char.isupper():
                    deobfuscated += chr((ord(char) - ord('A') - shift) % 26 + ord('A'))
                else:
                    deobfuscated += chr((ord(char) - ord('a') - shift) % 26 + ord('a'))
            else:
                deobfuscated += char
        return deobfuscated

    def hybrid_encrypt(self, message, password=None):
        """Hybrid encryption combining AES and custom methods"""
        # First layer: AES encryption
        aes_result = self.aes_encrypt(message.encode('utf-8'), password=password)
        
        # Second layer: Custom base64 encryption on the AES result
        custom_result = self.custom_base64_encrypt(aes_result['encrypted_data'])
        
        return {
            'hybrid_encrypted': custom_result['encrypted'],
            'aes_key': aes_result['key'],
            'aes_salt': aes_result['salt'],
            'custom_key': custom_result['key'],
            'checksum': custom_result['checksum'],
            'timestamp': aes_result['timestamp']
        }

    def hybrid_decrypt(self, hybrid_data):
        """Hybrid decryption for layered encryption"""
        try:
            # First layer: Custom base64 decryption
            custom_decrypted = self.custom_base64_decrypt(
                hybrid_data['hybrid_encrypted'],
                hybrid_data['custom_key'],
                hybrid_data['checksum']
            )
            
            # Second layer: AES decryption
            aes_decrypted = self.aes_decrypt(
                custom_decrypted.decode('utf-8'),
                hybrid_data['aes_key'],
                hybrid_data['aes_salt']
            )
            
            return aes_decrypted.decode('utf-8')
            
        except Exception as e:
            raise ValueError(f"Hybrid decryption failed: {str(e)}")

    def secure_session_encrypt(self, data, session_id=None, use_custom_uuid=False):
        """Session-based encryption with key rotation and modern UUID"""
        if session_id is None:
            if use_custom_uuid:
                session_id = self.generate_secure_uuid()
            else:
                session_id = str(uuid.uuid4())
        
        # Generate session key
        session_key = self.generate_secure_key()
        session_uuid = str(uuid.uuid4())
        
        # Store in session cache
        self.session_cache[session_id] = {
            'key': session_key,
            'session_uuid': session_uuid,
            'created': time.time(),
            'access_count': 0,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'last_activity': datetime.now(timezone.utc).isoformat()
        }
        
        # Register UUIDs
        self.register_uuid(session_id, {
            'type': 'session_id',
            'status': 'active'
        })
        self.register_uuid(session_uuid, {
            'type': 'session_internal',
            'linked_session': session_id
        })
        
        # Encrypt data
        result = self.aes_encrypt(data.encode('utf-8'), key=session_key)
        result['session_id'] = session_id
        result['session_uuid'] = session_uuid
        
        return result

    def secure_session_decrypt(self, encrypted_data, session_id):
        """Session-based decryption with UUID tracking"""
        if session_id not in self.session_cache:
            raise ValueError("Invalid session ID")
        
        session_info = self.session_cache[session_id]
        session_info['access_count'] += 1
        session_info['last_activity'] = datetime.now(timezone.utc).isoformat()
        
        # Update UUID registry
        if session_id in self.uuid_registry:
            self.uuid_registry[session_id]['access_count'] += 1
            self.uuid_registry[session_id]['last_accessed'] = datetime.now(timezone.utc).isoformat()
        
        # Check session expiry (24 hours)
        if time.time() - session_info['created'] > 86400:
            self.cleanup_session(session_id)
            raise ValueError("Session expired")
        
        decrypted = self.aes_decrypt(encrypted_data, base64.b64encode(session_info['key']).decode('utf-8'))
        return decrypted.decode('utf-8')
    
    def cleanup_session(self, session_id):
        """Clean up specific session and its UUIDs"""
        if session_id in self.session_cache:
            session_info = self.session_cache[session_id]
            
            # Mark UUIDs as inactive
            if session_id in self.uuid_registry:
                self.uuid_registry[session_id]['status'] = 'expired'
            
            if 'session_uuid' in session_info and session_info['session_uuid'] in self.uuid_registry:
                self.uuid_registry[session_info['session_uuid']]['status'] = 'expired'
            
            del self.session_cache[session_id]

    def cleanup_sessions(self):
        """Clean up expired sessions and UUIDs"""
        current_time = time.time()
        expired_sessions = []
        
        for sid, info in list(self.session_cache.items()):
            if current_time - info['created'] > 86400:
                expired_sessions.append(sid)
                self.cleanup_session(sid)
        
        return len(expired_sessions)
    
    def create_uuid_namespace(self, name):
        """Create custom namespace for UUID generation"""
        namespace_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f"crypto.{name}.local")
        
        self.register_uuid(str(namespace_uuid), {
            'type': 'namespace',
            'name': name,
            'purpose': 'uuid_generation'
        })
        
        return namespace_uuid
    
    def generate_batch_uuids(self, count=10, uuid_type='uuid4'):
        """Generate batch of UUIDs for bulk operations"""
        batch_id = str(uuid.uuid4())
        batch_uuids = []
        
        for i in range(count):
            if uuid_type == 'uuid1':
                new_uuid = str(uuid.uuid1())
            elif uuid_type == 'uuid4':
                new_uuid = str(uuid.uuid4())
            elif uuid_type == 'secure':
                new_uuid = self.generate_secure_uuid()
            elif uuid_type == 'short':
                new_uuid = self.generate_short_uuid()
            elif uuid_type == 'timestamped':
                new_uuid = self.generate_timestamped_uuid()
            else:
                new_uuid = str(uuid.uuid4())
            
            batch_uuids.append(new_uuid)
            
            # Register each UUID
            self.register_uuid(new_uuid, {
                'batch_id': batch_id,
                'batch_index': i,
                'type': uuid_type
            })
        
        return {
            'batch_id': batch_id,
            'uuids': batch_uuids,
            'count': count,
            'type': uuid_type,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
    
class Base64_Token_128:
    """docstring for Base64_Token_128"""
    def __init__(self, app):
        super(Base64_Token_128, self).__init__()
        self.app = app
        try:
            if len(self.app.config['URI_TOKEN'])>5:
                self.remove_function = True
            else:
                self.remove_function = False
        except:
            self.remove_function = False
        self.cache = None
        self.cookies = None

    @property
    def Make_Key(self):
        key_mapp__ = [ random.randint(3, 9) for _ in range(0, 12)]
        self.cache = ''
        for _ in range(0, random.choice([statistics.mode(key_mapp__), round(statistics.median(key_mapp__))])):
            self.cache += "-".join([str(random.getrandbits(x)) for x in key_mapp__])
        def u_id(self, token):
            cache, token =  [self.cache, token]
            return sum( [ int(int_) for int_ in self.cache.split('-')] )/int(token)
        #u_id(self, token=12)
        self.cirt = u_id(self, token=self.mode( [ int(_output) for _output in self.cache.split('-')], 'nm' ) )
        self.cache = str(round(self.cirt)).encode('utf-8')

    @staticmethod
    def key_mapp__(self):
        key_mapp__ = {
        "data2": "as15",
        "data2_0": "as15",
        "data2_5": "as180",
        "data3":"abc152",
        "data3_0":"abc152",
        "data3_5":"acb180",
        "data4":"cbn992",
        "data4_0":"cbn992",
        "data4_5":"vbs999",
        "data5":"xvas1823",
        "data5_0":"xvas1823",
        "data5_5":"xvbs1938",
        "data6": "aks127cc",
        "data6_0": "aks127cc",
        "data6_5": "aks688cd",
        "data7":"zer0b726",
        "data7_0":"zer0b726",
        "data7_5":"zer0b99d",
        "data8":"n0xc627zo",
        "data8_0":"n0xc627zo",
        "data8_5":"n0xc6987v",
        "data9":"death9999xxx",
        "data9_0":"death9999xxx"
        }

        median = self.mode( [ _x_int_ for _x_int_ in range(2, 9) if int(self.cache.decode('utf-8'))%_x_int_] , 'mo')
        median_split = str(median).split(".")
        keyword = "data"+str([median if median_split[1:len(median_split)] != '0' else int(median)][0]).replace(".", "_")
        return key_mapp__[keyword] or key_mapp__.get(keyword)

    def mode(self, arr, funct):
        if funct == "mo":
            return statistics.median(arr)
        elif funct == "nm":
            return statistics.mode(arr)
        else:
            raise TypeError("------------")

    def decode_base64(self, key, message):
        dec = []
        if id(key) != id(self.key_mapp__(self)):
            raise TypeError("Failed Key") 

        padding = 4 - (len(message) % 4)
        message = message + ("=" * padding)
        message = base64.urlsafe_b64decode(message).decode('utf-8')
        message = message.split('-')
        for v in range(len(message)):
            key_c = key[v % len(key)]
            dec_c = chr((ord(message[v]) - ord(key_c)))
            dec.append(dec_c)
        if self.cookies:
            raise MemoryError("Please, delete existing cookies")
        else:
            self.cookies = "".join([str(random.getrandbits(ord(x))) for x in dec.copy()])
        return "".join(dec)

    def encode_base64(self, key, message):
        enc = []
        if id(key) != id(self.key_mapp__(self)):
            raise TypeError("Failed Key") 
        for n in range(len(message)):
            key_c = key[n % len(key)]
            en = chr(ord(message[n])+ord(key_c))
            enc.append(en)
        if self.cookies:
            raise MemoryError("Please, delete existing cookies")
        else:
            self.cookies = "".join([str(random.getrandbits(ord(x))) for x in enc.copy()])
        return base64.urlsafe_b64encode(str("-".join(enc)).encode('utf-8')).decode('utf-8').rstrip("=")

    @property
    def remove(self):
        print(cache_base128)

    @remove.setter
    def remove(self):
        raise TypeError("remove coordinate is read and delete")
        
    @remove.deleter
    def remove(self):
        global cache_base128
        def rm(self):
            if self.cookies and self.cache:
                self.cache = None
                self.cookies = None
            else:
                pass
        if self.remove_function:
            cache = self.cache
            rm(self)
            self.cache = cache
        else:
            rm(self)
        try:
            self.caches1 = bytes(self.cache.decode('utf-8'), 'utf-8')
            self.caches2 = bytes(self.cache.decode('utf-8'), 'ascii')
        except:
            self.caches1 = self.cache.decode('utf-8').encode('utf-8')
            self.caches2 = self.cache.decode('utf-8').encode('ascii')

        array_bytes1, array_bytes2 =[[], []]

        for byte in self.caches1:
            array_bytes1.append(byte)

        for byte in self.caches2:
            array_bytes2.append(byte)

        assert array_bytes1 == array_bytes2
        cache = list(set(array_bytes1))
        if len(cache_base128) == 0:
            cache_base128 = cache
        else:
            cache_base128.clear()

    



class Ciphertext_128:
            def __init__(self):
                self.get = {
                'upper': string.ascii_uppercase,
                'lower': string.ascii_lowercase ,
                'letther': string.ascii_letters ,
                'digits': string.digits,
                'speciall': string.punctuation
                }
                self.data = ''
                self.hex_logic = 0xaa, None
            def Generate_String(self, size):
                chars = self.get['letther']+str(self.get['digits'])+self.get['speciall']
                return ''.join(random.choice(chars) for _ in range(size))

            def ciphertext(self, options='encrypt', text="test"):
                mapkey = {'A': '9', 'B': 'O', 'C': '3', 'D': 'R', 'E': 'v', 'F': "'", 'G': ';', 'H': '(', 'I': '2', 'J': ',', 'K': 'm', 'L': 'w', 'M': 'g', 'N': '[', 'O': '"', 'P': '}', 'Q': 'q', 'R': '7', 'S': 'T', 'T': '1', 'U': 'K', 'V': ']', 'W': 'Y', 'X': 'b', 'Y': 'e', 'Z': 'l', 'a': 'u', 'b': 'H', 'c': 'V', 'd': '6', 'e': ':', 'f': '5', 'g': 'B', 'h': 'y', 'i': ' ', 'j': 'z', 'k': 'N', 'l': '<', 'm': 'F', 'n': '!', 'o': '0', 'p': '^', 'q': 'p', 'r': 'I', 's': '\\', 't': 'j', 'u': 'd', 'v': 'c', 'w': 'W', 'x': '>', 'y': 'Q', 'z': '/', '0': '~', '1': 'C', '2': '&', '3': '.', '4': '`', '5': '@', '6': 'D', '7': '$', '8': '=', '9': 'o', ':': 'E', '.': 'L', ';': '{', ',': '#', '?': 'S', '!': 's', '@': 't', '#': 'J', '$': '_', '%': '+', '&': 'k', '(': 'i', ')': '?', '+': 'a', '=': 'U', '-': '*', '*': '-', '/': 'M', '_': '%', '<': 'X', '>': 'A', ' ': 'G', '[': 'n', ']': 'f', '{': 'h', '}': 'x', '`': 'r', '~': 'Z', '^': 'P', '"': '8', "'": '4', '\\': ')'} , self.hex_logic
                self.chars = self.get['letther']+str(self.get['digits'])+self.get['speciall']
                public_key = ''
                private_key = ''
                def generate_key(self):
                   """Generate an key for our cipher"""
                   global mapkey
                   shuffled = sorted(self.chars, key=lambda k: random.random())
                   mapkey = dict(zip(self.chars, shuffled)), self.hex_logic
                   return mapkey
                def login_(self, mapx=2):
                    exract_key= int(mapkey[1:][0][:1][0])
                    if exract_key%mapx == 0:
                        private_key = exract_key is self.hex_logic[0]
                        public_key = mapkey[:1][0]
                        return private_key, public_key
                    return False, None
                    ########Encrypt text using chipherset 128bit
                def encrypt(key, plaintext):
                    """Encrypt the string and return the ciphertext"""
                    return ''.join(key[l] for l in plaintext)
                def decrypt(key, ciphertext):
                    """Decrypt the string and return the plaintext"""
                    flipped = {v: k for k, v in key.items()}
                    return ''.join(flipped[l] for l in ciphertext) 

                log = login_(self)
                pent0 = []
                pent1 = []
                if log[0] == True:
                    for data in log[1]:
                                pent0.append(data)
                                pent1.append(log[1][data])
                    key = dict(zip(pent0, pent1))

                if options == 'encrypt':
                    try:
                        return encrypt(key, text)
                    except:
                        return None
                elif options == 'decrypt':
                    try:
                        return decrypt(key, text)
                    except:
                        return None
                elif options == 'generate-key':
                    mapkey = generate_key(self)
                    return mapkey
                elif options == 'show-key':
                    try:
                        return key
                    except:
                        return None
                else:
                    return None

            def HexaDecimall(self, options='encrypt'):
                def Hex_to_Str(self):
                    hex = self.data.replace('-0x128', '')
                    if 0xaa in self.hex_logic and self.data[:2] == '0x':
                        hex = self.data[2:]
                    output = bytes.fromhex(hex).decode('utf-8')
                    return self.ciphertext(text=output, options='decrypt')

                def Str_to_hex(self):
                    if 0xaa in self.hex_logic:
                        self.data = self.ciphertext(text=self.data, options='encrypt')
                        output = f"{self.data}".encode('utf-8')
                        return str(output.hex()+'-0x128')
                    return None
                if options.lower()=='decrypt':
                    data = Hex_to_Str(self)
                    return data
                elif options.lower()=='encrypt':
                    data = Str_to_hex(self)
                    return data
                else:
                    return
class Magic_Data:
    """docstring for Magic_Data"""
    def __init__(self, msg):
        super(Magic_Data, self).__init__()
        self.msg = msg
        self.token = ''
        self.create_token(127)

    def create_token(self, lenght):
        alphabet = string.ascii_letters + string.digits
        while True:
            self.token = ''.join(secrets.choice(alphabet) for i in range(lenght))
            if any(c.islower() for c in self.token) and any(c.isupper() for c in self.token) and any(c.isdigit() for c in self.token):
                break
        self.token = self.token

    def string_2_bin(self, msg=None):
        data_bin, binary_output = [[],[]]
        if msg != None:
            if len(msg) !=0:
                self.msg = msg

        for x in self.msg:
            data_bin.append(ord(x))

        for data_b in data_bin:
            binary_output.append(int(bin(data_b)[2:]))
        self.msg = binary_output
        self.load()
        return self.msg

    def bin_2_string(self, msg=None):
        logic_bin, output_str = [[], '']
        if msg != None:
            if len(msg) !=0:
                self.msg = msg
        self.load()
        for i in self.msg:
            i = int(i)
            b = 0
            c = 0
            k = int(math.log10(i))+1
            for j in range(k):
                b = ((i%10)*(2**j))
                i = i//10
                c = c+b
            logic_bin.append(c)
        for x in logic_bin:
            output_str = output_str+chr(x)
        return output_str

    def load(self):
        time.sleep(1.2)
        if self.msg and isinstance(self.msg, list):
            self.msg = "-".join(map(str, self.msg))
        elif self.msg and isinstance(self.msg, str):
            self.msg = self.msg.strip().split('-')
        return self.msg, 200

class AESCipher:
    def __init__(self, key): 
        self.bs = AES.block_size
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, raw):
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw.encode()))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]

class AUTH_TOKEN:
    """docstring for AUTH_TOKEN"""
    def __init__(self, app):
        super(AUTH_TOKEN, self).__init__()
        self.token = None
        self.point = 0
        self.cookiename = None
        try:
            self.algorith = app.config['AUTH_TOKEN']
        except:
            self.algorith = app

        if self.algorith.lower() != "md5":
            raise TypeError(f"No value ({self.algorith}) in dictionary")
    
    def create(self, lenght):
        global token_api
        alphabet = string.ascii_letters + string.digits
        while True:
            self.token = ''.join(secrets.choice(alphabet) for i in range(lenght))
            if any(c.islower() for c in self.token) and any(c.isupper() for c in self.token) and any(c.isdigit() for c in self.token):
                break
        self.token = self.token
        token_api = self.token
        return self.token

    def check(self, token):
        global token_api
        if isinstance(token, str):
            if token == self.token:
                token_api = None
                self.token = None
                return True
            elif token == token_api:
                token_api = None
                self.token = None
                return True
            else:
                if self.is_json(token):
                    try:
                        data = json.load(token)
                    except:
                        data = json.loads(token)

                    for json_load in data:
                        if data[json_load] == self.token:
                            self.token = None
                            token_api = None
                            break
                            return True
                        elif data[json_load] == token_api:
                            self.token = None
                            token_api = None
                            break
                            return True
                    return False
                else:
                    try:
                        token = token.cookies.get(self.cookiename)
                        self.check(token)
                    except:
                        try:
                            for x in re.findall(r'[\w\.-]+=', token):
                                token = token.replace(x, "")
                            data = token.split(";")
                            if any(self.token in e for e in data):
                                self.token = None
                                token_api = None
                                return True
                            elif any(token_api in e for e in data):
                                self.token = None
                                token_api = None
                                return True
                            else:
                                return False
                        except TypeError:
                            return False
        else:
            self.check(str(token))

    def is_json(self, data):
        try:
            json.loads(data)
        except:
            try:
                json.load(data)
                return True
            except:
                return False
        return True	

from Crypto.Util.Padding import unpad,pad

class AESCipher_2:
    """docstring for AESCipher_2"""
    def __init__(self, secretKey, salt):
        super(AESCipher_2, self).__init__()
        self.private_key = self.get_private_key(secretKey, salt)

    def get_private_key(self, secretKey, salt):
        # _prf = lambda p,s: HMAC.new(p, s, SHA256).digest()
        # private_key = PBKDF2(secretKey, salt.encode(), dkLen=32,count=65536, prf=_prf )
        # above code is equivalent but slow
        key = hashlib.pbkdf2_hmac('SHA256', secretKey.encode(), salt.encode(), 65536, 32)
        # KeySpec spec = new PBEKeySpec(secretKey.toCharArray(), salt.getBytes(), 65536, 256);
        return key

    def encrypt(self, message):
        message = pad(message.encode(), AES.block_size)
        iv = "\x00"*AES.block_size  # 128-bit IV
        cipher = AES.new(self.private_key, AES.MODE_CBC, iv.encode())
        return base64.b64encode(cipher.encrypt(message))
    
    def decrypt(self, message):
        enc = base64.b64decode(message)
        iv = "\x00"*AES.block_size
        cipher = AES.new(self.private_key, AES.MODE_CBC, iv.encode())
        return unpad(cipher.decrypt(enc), AES.block_size).decode('utf-8')

def secreet_token(lenght):
    alphabet = string.ascii_letters + string.digits
    return ''.join([random.choice(alphabet) for _ in range(lenght)])
