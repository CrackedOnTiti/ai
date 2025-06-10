#!/usr/bin/env python3
"""
Simple test server to simulate Zappy server behavior
This helps test your AI without needing the actual Zappy server
"""

import socket
import threading
import time

class TestZappyServer:
    def __init__(self, port=8080):
        self.port = port
        self.socket = None
        self.clients = []
        self.running = False
        
    def start(self):
        """Start the test server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('localhost', self.port))
            self.socket.listen(5)
            self.running = True
            
            print(f"Test Zappy server started on port {self.port}")
            print("Waiting for connections...")
            
            while self.running:
                try:
                    client_socket, addr = self.socket.accept()
                    print(f"Client connected from {addr}")
                    
                    # Handle each client in a separate thread
                    client_thread = threading.Thread(
                        target=self.handle_client, 
                        args=(client_socket, addr),
                        daemon=True
                    )
                    client_thread.start()
                    
                except socket.error:
                    if self.running:
                        print("Socket error occurred")
                    break
                    
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.cleanup()
    
    def handle_client(self, client_socket, addr):
        """Handle individual client connection"""
        try:
            print(f"Starting handshake with {addr}")
            
            # Send WELCOME
            self.send_message(client_socket, "WELCOME")
            time.sleep(0.1)  # Small delay to ensure message is sent
            
            # Wait for team name
            team_name = self.receive_message(client_socket)
            if not team_name:
                print(f"No team name received from {addr}")
                return
            
            print(f"Client {addr} joined team: {team_name}")
            
            # Send client number (available slots)
            time.sleep(0.1)  # Small delay
            self.send_message(client_socket, "5")  # 5 available slots
            
            # Send world dimensions
            time.sleep(0.1)  # Small delay
            self.send_message(client_socket, "10 10")  # 10x10 world
            
            print(f"Handshake completed for {addr}")
            time.sleep(0.1)  # Give client time to process
            
            # Handle game commands
            while self.running:
                command = self.receive_message(client_socket)
                if not command:
                    break
                
                print(f"Received command from {addr}: {command}")
                response = self.process_command(command)
                
                if response:
                    self.send_message(client_socket, response)
                    
        except Exception as e:
            print(f"Error handling client {addr}: {e}")
        finally:
            client_socket.close()
            print(f"Client {addr} disconnected")
    
    def send_message(self, client_socket, message):
        """Send message to client"""
        try:
            full_message = message + "\n"
            client_socket.send(full_message.encode('utf-8'))
            print(f"Sent: {message}")
        except Exception as e:
            print(f"Send error: {e}")
    
    def receive_message(self, client_socket):
        """Receive message from client"""
        try:
            client_socket.settimeout(30.0)  # 30 second timeout
            data = client_socket.recv(1024)
            if data:
                message = data.decode('utf-8').strip()
                print(f"Received: {message}")
                return message
            return None
        except socket.timeout:
            print("Client timeout")
            return None
        except Exception as e:
            print(f"Receive error: {e}")
            return None
    
    def process_command(self, command):
        """Process game commands and return appropriate responses"""
        command = command.lower().strip()
        
        # Simulate responses based on Zappy protocol
        if command == "forward":
            return "ok"
        elif command == "right" or command == "left":
            return "ok"
        elif command == "look":
            # Simulate look response - empty tiles with some food
            return "[player,,food,,,,,,,]"
        elif command == "inventory":
            # Simulate inventory response
            return "[food 10, linemate 0, deraumere 0, sibur 0, mendiane 0, phiras 0, thystame 0]"
        elif command == "connect_nbr":
            return "3"  # 3 connections available
        elif command.startswith("broadcast"):
            return "ok"
        elif command == "fork":
            return "ok"
        elif command.startswith("take"):
            return "ok"  # or "ko" randomly
        elif command.startswith("set"):
            return "ok"
        elif command == "incantation":
            return "ko"  # Not enough players/resources
        else:
            return "ko"  # Unknown command
    
    def stop(self):
        """Stop the server"""
        self.running = False
        if self.socket:
            self.socket.close()
    
    def cleanup(self):
        """Clean up resources"""
        if self.socket:
            self.socket.close()
        print("Test server stopped")

def main():
    server = TestZappyServer(8080)
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down test server...")
        server.stop()

if __name__ == "__main__":
    main()