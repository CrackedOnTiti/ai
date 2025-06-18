import time
import sys
import random
import re
from network_client import NetworkClient

class SimpleSurvivalManager:
    """Minimalist 2-level survival system"""
    def __init__(self):
        self.food_count = 10
        self.food_collected = 0
        
    def record_food_collected(self):
        """Track successful food collection"""
        self.food_collected += 1
        print(f"✅ FOOD +1! Total: {self.food_collected}")
        
    def update_from_inventory(self, inventory_response):
        """Update food count from inventory"""
        food_match = re.search(r'food (\d+)', inventory_response)
        if food_match:
            new_count = int(food_match.group(1))
            if new_count != self.food_count:
                print(f"🍖 Food: {self.food_count} → {new_count}")
            self.food_count = new_count
    
    def get_mode(self):
        """Simple 2-level system"""
        return "SAFE" if self.food_count >= 6 else "HUNGRY"

class FastVisionParser:
    """Ultra-fast vision parsing"""
    def parse_vision(self, vision_string):
        """Parse vision focusing only on food locations"""
        tiles = [tile.strip() for tile in vision_string.strip('[]').split(',')]
        
        food_locations = []
        for i, tile in enumerate(tiles):
            if tile and 'food' in tile:
                food_locations.append(i)
        
        return {
            'tiles': tiles,
            'food_locations': food_locations,
            'current_tile': tiles[0] if tiles else ''
        }
    
    def has_food_here(self, vision_data):
        """Check if food is on current tile"""
        return 0 in vision_data['food_locations']

class DirectMovement:
    """Direct, no-nonsense movement to food"""
    def get_action_for_food(self, food_locations):
        """Get direct action to reach closest food"""
        if not food_locations:
            return None
        
        # Target closest tile (lowest number)
        target = min(food_locations)
        
        # Simple movement mapping
        if target == 1:
            return "Forward"
        elif target == 2:
            return "Forward"  # From testing: Forward reaches tile 2
        elif target == 3:
            return "Left"
        else:
            return "Forward"  # Default

class StreamlinedAI:
    def __init__(self, config):
        self.config = config
        self.client = None
        self.running = False
        
        # Minimal components
        self.survival = SimpleSurvivalManager()
        self.vision = FastVisionParser()
        self.movement = DirectMovement()
        
        # Essential state only
        self.last_vision = None
        self.commands_sent = 0
        self.start_time = time.time()
        self.last_command = None
        
        # Performance tracking
        self.inventory_checks = 0
        
    def run(self):
        """Main execution"""
        try:
            if not self._connect():
                return 84
            self._main_loop()
        except KeyboardInterrupt:
            print("\nInterrupted")
        except Exception as e:
            print(f"Error: {e}")
            return 84
        finally:
            self._cleanup()
        return 0
    
    def _connect(self):
        """Connect to server"""
        print(f"🏃 STREAMLINED AI - Pure Efficiency Mode")
        print(f"Connecting to {self.config.machine}:{self.config.port}...")
        
        self.client = NetworkClient(self.config)
        if not self.client.connect():
            return False
        
        print(f"Connected! Starting survival...")
        self.running = True
        return True
    
    def _main_loop(self):
        """Ultra-efficient main loop"""
        # Minimal startup
        self._send("Inventory")
        self._send("Look")
        
        while self.running and self.client.is_connected():
            try:
                # Process responses quickly
                self._process_responses()
                
                # Execute behavior
                self._execute_behavior()
                
                # Quick status every 25 commands
                if self.commands_sent % 25 == 0 and self.commands_sent > 0:
                    self._status_update()
                
                time.sleep(0.08)  # Ultra-fast loop
                
            except Exception as e:
                print(f"Loop error: {e}")
                time.sleep(0.5)
    
    def _execute_behavior(self):
        """Core behavior - streamlined decision making"""
        mode = self.survival.get_mode()
        
        # Priority 1: Get vision if needed
        if not self.last_vision:
            self._send("Look")
            return
        
        # Priority 2: Take food if here
        if self.vision.has_food_here(self.last_vision):
            if self.last_command != "Take food":  # Prevent spam
                print(f"🍖 TAKE! ({mode})")
                self._send("Take food")
                return
        
        # Priority 3: Move to visible food
        other_food = [loc for loc in self.last_vision['food_locations'] if loc != 0]
        if other_food:
            action = self.movement.get_action_for_food(other_food)
            if action:
                target = min(other_food)
                print(f"🎯 {action}→{target} ({mode})")
                self._send(action)
                self.last_vision = None  # Force vision refresh
                return
        
        # Priority 4: Inventory check (minimal - every 30 commands)
        if self.commands_sent - self.inventory_checks > 30:
            self._send("Inventory")
            self.inventory_checks = self.commands_sent
            return
        
        # Priority 5: Behavior based on mode
        if mode == "SAFE":
            # Can collect stones when safe
            current_tile = self.last_vision['current_tile']
            for stone in ['linemate', 'deraumere', 'sibur', 'mendiane', 'phiras', 'thystame']:
                if stone in current_tile:
                    print(f"💎 {stone} (SAFE)")
                    self._send(f"Take {stone}")
                    self.last_vision = None
                    return
            
            # Explore when safe
            print(f"🔍 Explore (SAFE)")
            self._send(random.choice(["Forward", "Right", "Left"]))
            self.last_vision = None
            
        else:  # HUNGRY
            # Only food when hungry
            print(f"🚨 Food search (HUNGRY)")
            self._send(random.choice(["Forward", "Right", "Left"]))
            self.last_vision = None
    
    def _send(self, command):
        """Send command with minimal tracking"""
        self.client.send_command(command)
        self.commands_sent += 1
        self.last_command = command
    
    def _process_responses(self):
        """Fast response processing"""
        # Process up to 3 responses per loop (reduced from 5)
        for _ in range(3):
            response = self.client.get_response(timeout=0.05)
            if response:
                self._handle_response(response)
            else:
                break
    
    def _handle_response(self, response):
        """Streamlined response handling"""
        if response == "ok":
            # Track successful food takes
            if self.last_command == "Take food":
                self.survival.record_food_collected()
                self.last_vision = None  # Force fresh vision
                
        elif response == "ko":
            # Force fresh vision on failure
            if self.last_command in ["Take food", "Forward", "Right", "Left"]:
                self.last_vision = None
                
        elif response == "dead":
            print("💀 DIED!")
            self._final_stats()
            self.running = False
            
        elif response.startswith("["):
            self._handle_data(response)
    
    def _handle_data(self, response):
        """Handle inventory and vision data"""
        # Simple detection: inventory has "food X" with numbers
        if re.search(r'food \d+', response):
            # Inventory
            self.survival.update_from_inventory(response)
        else:
            # Vision
            vision_data = self.vision.parse_vision(response)
            self.last_vision = vision_data
            
            # Quick feedback
            if vision_data['food_locations']:
                if 0 in vision_data['food_locations']:
                    print("🎯 FOOD HERE!")
                else:
                    nearby = [loc for loc in vision_data['food_locations'] if loc != 0]
                    print(f"🍖 Food: {nearby}")
    
    def _status_update(self):
        """Quick status update"""
        runtime = time.time() - self.start_time
        food_rate = self.survival.food_collected / (runtime/60) if runtime > 0 else 0
        mode = self.survival.get_mode()
        
        print(f"📊 {mode}: {food_rate:.1f} food/min, {self.survival.food_count} food")
    
    def _final_stats(self):
        """Final performance stats"""
        runtime = time.time() - self.start_time
        food_rate = self.survival.food_collected / (runtime/60) if runtime > 0 else 0
        efficiency = (self.survival.food_collected / self.commands_sent * 100) if self.commands_sent > 0 else 0
        
        print(f"\n🏃 STREAMLINED AI FINAL STATS:")
        print(f"Runtime: {runtime:.1f}s")
        print(f"Commands: {self.commands_sent}")
        print(f"Food collected: {self.survival.food_collected}")
        print(f"Collection rate: {food_rate:.1f} food/min")
        print(f"Efficiency: {efficiency:.1f}% food per command")
        print(f"Target rate: 47.6 food/min")
        print(f"Performance: {'✅ SUCCESS' if food_rate >= 47.6 else '❌ NEEDS OPTIMIZATION'}")
    
    def _cleanup(self):
        """Clean shutdown"""
        print("Shutting down...")
        if self.client:
            self.client.disconnect()

class AIController:
    """Compatibility wrapper"""
    def __init__(self, config):
        self.ai = StreamlinedAI(config)
    
    def run(self):
        return self.ai.run()