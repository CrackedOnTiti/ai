import socket
import threading
import queue
import time
from collections import deque

class CommandBuffer:
    def __init__(self, max_size=10):
        self.max_size = max_size
        self.pending_commands = deque()  # Commands waiting to be sent
        self.sent_commands = deque()     # Commands sent but waiting for response
        self.responses = queue.Queue()   # Received responses
        self.lock = threading.RLock()     # Thread safety
    
    def can_send_command(self):
        """Check if we can send another command (max 10 pending)"""
        with self.lock:
            return len(self.sent_commands) < self.max_size
    
    def add_command(self, command):
        """Add command to pending queue"""
        with self.lock:
            self.pending_commands.append(command)
    
    def get_next_command(self):
        """Get next command to send"""
        with self.lock:
            # New logs
            if self.pending_commands and self.can_send_command():
                command = self.pending_commands.popleft()
                self.sent_commands.append(command)
                return command
            # New log
            return None
    
    def add_response(self, response):
        """Add received response"""
        self.responses.put(response)
        
        # Remove one command from sent queue (FIFO order)
        with self.lock:
            if self.sent_commands:
                self.sent_commands.popleft()
    
    def get_response(self, timeout=None):
        """Get next response (blocking)"""
        try:
            return self.responses.get(timeout=timeout)
        except queue.Empty:
            return None

class NetworkClient:
    def __init__(self, config):
        self.host = config.machine
        self.port = config.port
        self.team_name = config.name
        self.socket = None
        self.connected = False
        self.buffer = CommandBuffer()
        
        # Threading for continuous communication
        self.receive_thread = None
        self.send_thread = None
        self.running = False
        
        # Received data buffer (for handling partial messages)
        self.receive_buffer = ""
        
        # World information from handshake
        self.world_width = 0
        self.world_height = 0
        self.available_slots = 0
    
    def connect(self):
        """Connect and perform handshake"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10.0)  # 10 second timeout
            self.socket.connect((self.host, self.port))
            self.connected = True
            print(f"Connected to {self.host}:{self.port}")
            
            # Start communication threads
            self.running = True
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.send_thread = threading.Thread(target=self._send_loop, daemon=True)
            
            self.receive_thread.start()
            self.send_thread.start()
            
            # Perform handshake
            return self._handshake()
            
        except socket.error as e:
            print(f"Connection failed: {e}")
            return False
    
    def _handshake(self):
        """Perform Zappy handshake protocol"""
        print("Starting handshake...")
        
        # Wait for WELCOME
        print("Waiting for WELCOME message...")
        welcome = self.buffer.get_response(timeout=5)
        if not welcome:
            print("Handshake Error: Did not receive WELCOME (timeout or empty).")
            return False
        if welcome != "WELCOME":
            print(f"Handshake Error: Expected WELCOME, got: '{welcome}'")
            return False
        print(f"Handshake: Received '{welcome}'")
        
        # Send team name
        try:
            self.send_command(self.team_name)
            print(f"Handshake: Successfully queued team name for sending: '{self.team_name}'") # Modified log
        except Exception as e:
            print(f"Handshake Error: Exception during send_command for team name: {e}")
            # Optionally, include traceback:
            # import traceback
            # print(traceback.format_exc())
            return False # Or handle error appropriately

        # Wait for client number
        print("Handshake: Waiting for client number...")
        client_num_response = self.buffer.get_response(timeout=5)
        if not client_num_response:
            print("Handshake Error: Did not receive client number (timeout or empty).")
            return False
        print(f"Handshake: Received client number response: '{client_num_response}'")
        
        try:
            self.available_slots = int(client_num_response)
            print(f"Handshake: Parsed available slots: {self.available_slots}")
        except ValueError:
            print(f"Handshake Error: Invalid client number format: '{client_num_response}'")
            return False
        
        # Wait for world dimensions
        print("Handshake: Waiting for world dimensions...")
        dimensions = self.buffer.get_response(timeout=5)
        if not dimensions:
            print("Handshake Error: Did not receive world dimensions (timeout or empty).")
            return False
        print(f"Handshake: Received world dimensions response: '{dimensions}'")
        
        try:
            # Handle potential multiple spaces in dimensions string if necessary, though protocol implies "X Y"
            parts = dimensions.split()
            if len(parts) != 2:
                raise ValueError("Dimensions string does not contain exactly two parts.")
            width, height = parts
            self.world_width = int(width)
            self.world_height = int(height)
            print(f"Handshake: Parsed world dimensions: {self.world_width}x{self.world_height}")
        except ValueError as e:
            print(f"Handshake Error: Invalid world dimensions format ('{dimensions}'): {e}")
            return False
        
        print("Handshake completed successfully!")
        return True
    
    def _receive_loop(self):
        """Continuous receiving loop (runs in separate thread)"""
        while self.running and self.connected:
            try:
                # Set a short timeout to allow checking self.running
                self.socket.settimeout(1.0)
                data = self.socket.recv(1024)
                
                if not data:
                    print("Server closed connection")
                    break
                
                # Add to buffer and process complete messages
                self.receive_buffer += data.decode('utf-8')
                self._process_received_data()
                
            except socket.timeout:
                continue  # Check if we should keep running
            except socket.error as e:
                print(f"Receive error: {e}")
                break
        
        self.connected = False
        print("Receive loop ended")
    
    def _process_received_data(self):
        """Process complete messages from receive buffer"""
        while '\n' in self.receive_buffer:
            # Extract one complete message
            message, self.receive_buffer = self.receive_buffer.split('\n', 1)
            message = message.strip()
            
            if message:
                print(f"Received: {message}")
                self.buffer.add_response(message)
    
    def _send_loop(self):
        """Continuous sending loop (runs in separate thread)"""
        while self.running and self.connected:
            command = self.buffer.get_next_command()
            
            if command:
                try:
                    message = command + '\n'
                    self.socket.sendall(message.encode('utf-8'))
                    print(f"Sent: {command}") # Existing log, crucial for confirmation
                except socket.error as e:
                    print(f"Send error: {e}")
                    self.connected = False
                    break
            else:
                # No commands to send, wait a bit
                # print("Send Loop: No command to send, sleeping.") # Optional: can be noisy
                time.sleep(0.1)
        
        print(f"Send loop ended. self.running={self.running}, self.connected={self.connected}") # Modified log
    
    def send_command(self, command):
        """Add command to send queue"""
        if not self.connected:
            print(f"Cannot send command '{command}': not connected")
            return False
        
        self.buffer.add_command(command)
        return True
    
    def get_response(self, timeout=None):
        """Get next response"""
        return self.buffer.get_response(timeout)
    
    def is_connected(self):
        """Check if still connected"""
        return self.connected
    
    def get_world_info(self):
        """Get world information from handshake"""
        return {
            'width': self.world_width,
            'height': self.world_height,
            'available_slots': self.available_slots
        }
    
    def disconnect(self):
        """Clean shutdown"""
        print("Disconnecting...")
        self.running = False
        
        if self.socket:
            self.socket.close()
        
        # Wait for threads to finish (with timeout)
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=2)
        if self.send_thread and self.send_thread.is_alive():
            self.send_thread.join(timeout=2)
        
        self.connected = False
        print("Disconnected")