#!/usr/bin/env python3
"""
Test script to validate your AI implementation
Run this to test different aspects of your AI
"""

import subprocess
import time
import sys
import threading
from test_server import TestZappyServer

class AITester:
    def __init__(self):
        self.server = None
        self.server_thread = None
        
    def start_test_server(self):
        """Start the test server in background"""
        print("Starting test server...")
        self.server = TestZappyServer(8080)
        self.server_thread = threading.Thread(target=self.server.start, daemon=True)
        self.server_thread.start()
        time.sleep(2)  # Give server time to start
        print("Test server started")
    
    def stop_test_server(self):
        """Stop the test server"""
        if self.server:
            self.server.stop()
            print("Test server stopped")
    
    def test_basic_connection(self):
        """Test 1: Basic connection and handshake"""
        print("\n=== TEST 1: Basic Connection ===")
        try:
            # Run your AI for a short time
            result = subprocess.run([
                sys.executable, "main.py", 
                "-p", "8080", 
                "-n", "test_team", 
                "-h", "localhost"
            ], timeout=10, capture_output=True, text=True)
            
            print("STDOUT:")
            print(result.stdout)
            if result.stderr:
                print("STDERR:")
                print(result.stderr)
            
            print(f"Exit code: {result.returncode}")
            
        except subprocess.TimeoutExpired:
            print("AI ran for 10 seconds (timeout - this is expected)")
        except Exception as e:
            print(f"Test error: {e}")
    
    def test_argument_parsing(self):
        """Test 2: Argument parsing"""
        print("\n=== TEST 2: Argument Parsing ===")
        
        # Test help
        print("Testing help...")
        try:
            result = subprocess.run([
                sys.executable, "main.py", "help"
            ], capture_output=True, text=True)
            print("Help output:")
            print(result.stdout)
        except Exception as e:
            print(f"Help test error: {e}")
        
        # Test invalid arguments
        print("\nTesting invalid arguments...")
        try:
            result = subprocess.run([
                sys.executable, "main.py", 
                "-p", "abc"  # Invalid port
            ], capture_output=True, text=True)
            print("Invalid args output:")
            print(result.stdout)
            print(result.stderr)
        except Exception as e:
            print(f"Invalid args test error: {e}")
    
    def test_network_components(self):
        """Test 3: Network components individually"""
        print("\n=== TEST 3: Network Components ===")
        
        # Test importing your modules
        try:
            from config import Config
            from network_client import NetworkClient
            from ai_controller import AIController
            
            print("✓ All modules import successfully")
            
            # Test config creation
            config = Config(port=8080, name="test", machine="127.0.0.1")
            print(f"✓ Config created: {config.port}, {config.name}, {config.machine}")
            
            # Test network client creation (don't connect)
            client = NetworkClient(config)
            print("✓ NetworkClient created successfully")
            
            # Test AI controller creation
            ai = AIController(config)
            print("✓ AIController created successfully")
            
        except Exception as e:
            print(f"✗ Module test failed: {e}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("Starting AI tests...")
        
        # Test 1: Components
        self.test_network_components()
        
        # Test 2: Arguments
        self.test_argument_parsing()
        
        # Test 3: Full connection (with test server)
        self.start_test_server()
        try:
            self.test_basic_connection()
        finally:
            self.stop_test_server()
        
        print("\n=== TESTS COMPLETED ===")

def main():
    tester = AITester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()