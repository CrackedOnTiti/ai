import time
import sys
from network_client import NetworkClient

class AIController:
    def __init__(self, config):
        self.config = config
        self.client = None
        self.world_info = None
        self.running = False
    
    def run(self):
        """Main AI execution - handles everything from connection to shutdown"""
        try:
            # Initialize and connect
            if not self._initialize():
                return 84  # Connection failed
            
            # Main AI loop
            self._ai_loop()
            
        except KeyboardInterrupt:
            print("\nAI interrupted by user")
        except Exception as e:
            print(f"AI error: {e}")
            return 84
        finally:
            self._cleanup()
        
        return 0
    
    def _initialize(self):
        """Initialize network connection and get world info"""
        print(f"Connecting to {self.config.machine}:{self.config.port} as team '{self.config.name}'...")
        
        # Create and connect network client
        self.client = NetworkClient(self.config)
        
        if not self.client.connect():
            print("Failed to connect to server")
            return False
        
        # Get world information
        self.world_info = self.client.get_world_info()
        print(f"Connected successfully! World: {self.world_info['width']}x{self.world_info['height']}")
        print(f"Available slots: {self.world_info['available_slots']}")
        
        self.running = True
        return True
    
    def _ai_loop(self):
        """Main AI behavior loop"""
        print("Starting AI behavior...")
        
        # Initial commands to understand our situation
        self._initial_reconnaissance()
        
        # Main game loop
        while self.running and self.client.is_connected():
            # Basic survival and exploration behavior
            self._basic_behavior()
            
            # Process any responses
            self._process_responses()
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.5)
    
    def _initial_reconnaissance(self):
        """Send initial commands to understand our situation"""
        print("Performing initial reconnaissance...")
        
        # Check our inventory
        self.client.send_command("Inventory")
        
        # Look around
        self.client.send_command("Look")
        
        # Check team connections
        self.client.send_command("Connect_nbr")
        
        # Process initial responses
        for i in range(3):
            response = self.client.get_response(timeout=5)
            if response:
                print(f"Initial response {i+1}: {response}")
                self._handle_response(response)
            else:
                print(f"No initial response {i+1} received")
    
    def _basic_behavior(self):
        """Basic AI behavior - move and explore"""
        # For now, just move forward occasionally
        # This is where you'll implement your AI strategy later
        
        # Simple movement pattern
        import random
        action = random.choice(["Forward", "Right", "Left", "Look"])
        
        self.client.send_command(action)
        print(f"AI action: {action}")
    
    def _process_responses(self):
        """Process any pending responses"""
        # Check for responses without blocking
        response = self.client.get_response(timeout=0.1)
        if response:
            print(f"Response: {response}")
            self._handle_response(response)
    
    def _handle_response(self, response):
        """Handle specific responses from server"""
        if response == "ok":
            # Command executed successfully
            pass
        elif response == "ko":
            # Command failed
            print("Last command failed")
        elif response == "dead":
            # We died!
            print("AI died! Shutting down...")
            self.running = False
        elif response.startswith("["):
            # Inventory or Look response
            self._handle_data_response(response)
        elif "message" in response:
            # Broadcast message
            self._handle_broadcast(response)
        # Add more response handlers as needed
    
    def _handle_data_response(self, response):
        """Handle data responses like inventory or look"""
        if "food" in response:
            # Inventory response
            print(f"Current inventory: {response}")
        else:
            # Look response
            print(f"Vision: {response}")
    
    def _handle_broadcast(self, response):
        """Handle broadcast messages from other players"""
        print(f"Broadcast received: {response}")
    
    def _cleanup(self):
        """Clean shutdown"""
        print("Shutting down AI...")
        self.running = False
        if self.client:
            self.client.disconnect()
        print("AI shut down complete")