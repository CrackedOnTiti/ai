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

class PlayerState:
    """Track player level and inventory for rituals"""
    def __init__(self):
        self.level = 1
        self.inventory = {
            "food": 10, "linemate": 0, "deraumere": 0, 
            "sibur": 0, "mendiane": 0, "phiras": 0, "thystame": 0
        }
        
        # Elevation requirements table
        self.elevation_requirements = {
            1: {"players": 1, "linemate": 1, "deraumere": 0, "sibur": 0, "mendiane": 0, "phiras": 0, "thystame": 0},
            2: {"players": 2, "linemate": 1, "deraumere": 1, "sibur": 1, "mendiane": 0, "phiras": 0, "thystame": 0},
            3: {"players": 2, "linemate": 2, "deraumere": 0, "sibur": 1, "mendiane": 0, "phiras": 2, "thystame": 0},
            4: {"players": 4, "linemate": 1, "deraumere": 1, "sibur": 2, "mendiane": 0, "phiras": 1, "thystame": 0},
            5: {"players": 4, "linemate": 1, "deraumere": 2, "sibur": 1, "mendiane": 3, "phiras": 0, "thystame": 0},
            6: {"players": 6, "linemate": 1, "deraumere": 2, "sibur": 3, "mendiane": 0, "phiras": 1, "thystame": 0},
            7: {"players": 6, "linemate": 2, "deraumere": 2, "sibur": 2, "mendiane": 2, "phiras": 2, "thystame": 1}
        }
        
    def update_from_inventory(self, inventory_response):
        """Parse inventory response and update state"""
        for resource in self.inventory.keys():
            match = re.search(rf'{resource} (\d+)', inventory_response)
            if match:
                old_count = self.inventory[resource]
                new_count = int(match.group(1))
                if old_count != new_count and resource != "food":
                    print(f"📦 {resource}: {old_count} → {new_count}")
                self.inventory[resource] = new_count
    
    def can_elevate(self):
        """Check if we have stones needed for next level"""
        if self.level >= 8:
            return False  # Max level
            
        requirements = self.elevation_requirements.get(self.level, {})
        for stone, needed in requirements.items():
            if stone != "players" and needed > 0:
                if self.inventory.get(stone, 0) < needed:
                    return False
        return True
    
    def get_missing_stones(self):
        """Get list of stones still needed"""
        if self.level >= 8:
            return []
            
        requirements = self.elevation_requirements.get(self.level, {})
        missing = []
        for stone, needed in requirements.items():
            if stone != "players" and needed > 0:
                have = self.inventory.get(stone, 0)
                if have < needed:
                    missing.extend([stone] * (needed - have))
        return missing

class BroadcastManager:
    """Handle team communication"""
    def __init__(self):
        self.last_broadcast = 0
        self.broadcast_interval = 15  # Broadcast every 15 seconds
        self.teammates = {}  # Track teammate status
        
    def should_broadcast(self):
        """Check if time to broadcast status"""
        return time.time() - self.last_broadcast > self.broadcast_interval
    
    def create_status_broadcast(self, player_state, mode):
        """Create status message for team"""
        ready = "READY" if player_state.can_elevate() else "NEED"
        missing = player_state.get_missing_stones()
        missing_str = ",".join(missing[:3]) if missing else "none"  # First 3 stones needed
        
        # Format: "L1:READY:none" or "L1:NEED:linemate,sibur"
        message = f"L{player_state.level}:{ready}:{missing_str}:{mode}"
        return message
    
    def parse_broadcast(self, direction, message):
        """Parse teammate broadcast"""
        try:
            # Parse: "L1:READY:none:SAFE"
            parts = message.split(":")
            if len(parts) >= 3:
                level = int(parts[0][1:])  # Remove 'L' prefix
                status = parts[1]  # READY or NEED
                missing = parts[2]  # stones needed
                
                print(f"📻 Teammate (dir {direction}): Level {level}, {status}")
                return {"level": level, "status": status, "direction": direction}
        except:
            pass
        return None

class ElevationManager:
    """Handle elevation ritual coordination"""
    def __init__(self):
        self.attempting_elevation = False
        self.elevation_start_time = 0
        self.elevation_timeout = 45  # Give up after 45 seconds
        self.elevation_cooldown = 30  # Wait 30s before retry after failure
        self.last_failed_elevation = 0
        
    def should_attempt_elevation(self, player_state, teammates):
        """Decide if we should try elevation now"""
        if not player_state.can_elevate():
            return False
            
        if self.attempting_elevation:
            # Check timeout
            if time.time() - self.elevation_start_time > self.elevation_timeout:
                print("⏰ Elevation timeout - giving up")
                self.attempting_elevation = False
                return False
            return False  # Still attempting
        
        # Check cooldown after failure
        if time.time() - self.last_failed_elevation < self.elevation_cooldown:
            return False
        
        # For level 1->2, we only need ourselves (1 player required)
        if player_state.level == 1:
            print(f"🎭 Ready for solo elevation (Level {player_state.level}→{player_state.level + 1})")
            return True
        
        # For higher levels, check if we have enough team members
        required_players = player_state.elevation_requirements.get(player_state.level, {}).get("players", 1)
        
        # Count ready teammates at same level
        same_level_ready = 0
        for teammate in teammates.values():
            if teammate.get("level") == player_state.level and teammate.get("status") == "READY":
                same_level_ready += 1
        
        # Include ourselves
        total_ready = same_level_ready + 1
        
        if total_ready >= required_players:
            print(f"🎭 Can attempt elevation! Have {total_ready}/{required_players} players")
            return True
        else:
            print(f"⏳ Need {required_players - total_ready} more ready level {player_state.level} players")
            return False
    
    def start_elevation(self):
        """Begin elevation attempt"""
        self.attempting_elevation = True
        self.elevation_start_time = time.time()
        print("🎭 STARTING ELEVATION RITUAL!")
        return "Incantation"
    
    def handle_elevation_response(self, response):
        """Handle server response to elevation"""
        if "Elevation underway" in response:
            print("✨ Elevation in progress...")
            return None
        elif "Current level:" in response:
            # Extract new level
            level_match = re.search(r'Current level: (\d+)', response)
            if level_match:
                new_level = int(level_match.group(1))
                print(f"🎉 ELEVATION SUCCESS! Now level {new_level}")
                self.attempting_elevation = False
                return new_level
        elif response == "ko":
            print("❌ Elevation failed! (Not enough players or missing stones)")
            self.attempting_elevation = False
            self.last_failed_elevation = time.time()
        
        return None

class ForkManager:
    """Handle team reproduction strategy"""
    def __init__(self):
        self.last_fork_time = 0
        self.fork_cooldown = 60  # Fork every 60 seconds max
        self.team_size_target = 6  # Want 6 players for level 6→7 rituals
        
    def should_fork(self, player_state, mode):
        """Decide if we should fork to expand team"""
        # Only fork when safe and high level
        if mode != "SAFE" or player_state.level < 2:
            return False
            
        # Don't fork too often
        if time.time() - self.last_fork_time < self.fork_cooldown:
            return False
            
        # Fork more aggressively at higher levels (need team for win condition)
        if player_state.level >= 6:
            return True
        elif player_state.level >= 3 and random.random() < 0.3:  # 30% chance
            return True
            
        return False
    
    def attempt_fork(self):
        """Attempt to fork"""
        self.last_fork_time = time.time()
        print("🥚 Forking to expand team!")
        return "Fork"

class FastVisionParser:
    """Ultra-fast vision parsing"""
    def parse_vision(self, vision_string):
        """Parse vision focusing on food and stones"""
        tiles = [tile.strip() for tile in vision_string.strip('[]').split(',')]
        
        food_locations = []
        stone_locations = []
        
        for i, tile in enumerate(tiles):
            if tile and 'food' in tile:
                food_locations.append(i)
            # Check for any stones
            for stone in ['linemate', 'deraumere', 'sibur', 'mendiane', 'phiras', 'thystame']:
                if stone in tile:
                    stone_locations.append((i, stone))
        
        return {
            'tiles': tiles,
            'food_locations': food_locations,
            'stone_locations': stone_locations,
            'current_tile': tiles[0] if tiles else ''
        }
    
    def has_food_here(self, vision_data):
        """Check if food is on current tile"""
        return 0 in vision_data['food_locations']

class DirectMovement:
    """Direct movement logic"""
    def get_action_for_food(self, food_locations):
        """Get action to reach closest food"""
        if not food_locations:
            return None
        
        target = min(food_locations)
        if target == 1:
            return "Forward"
        elif target == 2:
            return "Forward"
        elif target == 3:
            return "Left"
        else:
            return "Forward"

class AdvancedAI:
    """Advanced AI with broadcast, rituals, and forking"""
    def __init__(self, config):
        self.config = config
        self.client = None
        self.running = False
        
        # Core systems
        self.survival = SimpleSurvivalManager()
        self.player_state = PlayerState()
        self.broadcast_manager = BroadcastManager()
        self.elevation_manager = ElevationManager()
        self.fork_manager = ForkManager()
        self.vision = FastVisionParser()
        self.movement = DirectMovement()
        
        # State
        self.last_vision = None
        self.commands_sent = 0
        self.start_time = time.time()
        self.last_command = None
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
        print(f"🚀 ADVANCED AI - Broadcast, Rituals & Forking")
        print(f"Connecting to {self.config.machine}:{self.config.port}...")
        
        self.client = NetworkClient(self.config)
        if not self.client.connect():
            return False
        
        print(f"Connected! Starting advanced gameplay...")
        self.running = True
        return True
    
    def _main_loop(self):
        """Main game loop"""
        self._send("Inventory")
        self._send("Look")
        
        while self.running and self.client.is_connected():
            try:
                self._process_responses()
                self._execute_advanced_behavior()
                
                # Status every 25 commands
                if self.commands_sent % 25 == 0 and self.commands_sent > 0:
                    self._status_update()
                
                time.sleep(0.08)
                
            except Exception as e:
                print(f"Loop error: {e}")
                time.sleep(0.5)
    
    def _execute_advanced_behavior(self):
        """Enhanced behavior with advanced features"""
        mode = self.survival.get_mode()
        
        # Priority 1: Handle elevation if attempting
        if self.elevation_manager.attempting_elevation:
            print("⏳ Elevation in progress...")
            return
        
        # Priority 2: Attempt elevation if ready
        if self.elevation_manager.should_attempt_elevation(self.player_state, self.broadcast_manager.teammates):
            command = self.elevation_manager.start_elevation()
            self._send(command)
            return
        
        # Priority 3: Broadcast status to team
        if self.broadcast_manager.should_broadcast():
            message = self.broadcast_manager.create_status_broadcast(self.player_state, mode)
            self._send(f"Broadcast {message}")
            self.broadcast_manager.last_broadcast = time.time()
            return
        
        # Priority 4: Fork for team expansion
        if self.fork_manager.should_fork(self.player_state, mode):
            command = self.fork_manager.attempt_fork()
            self._send(command)
            return
        
        # Priority 5: Get vision if needed
        if not self.last_vision:
            self._send("Look")
            return
        
        # Priority 6: Take food if here
        if self.vision.has_food_here(self.last_vision):
            if self.last_command != "Take food":
                print(f"🍖 TAKE! ({mode})")
                self._send("Take food")
                return
        
        # Priority 7: Move to visible food
        other_food = [loc for loc in self.last_vision['food_locations'] if loc != 0]
        if other_food:
            action = self.movement.get_action_for_food(other_food)
            if action:
                target = min(other_food)
                print(f"🎯 {action}→{target} ({mode})")
                self._send(action)
                self.last_vision = None
                return
        
        # Priority 8: Collect needed stones when safe
        if mode == "SAFE" and self.last_vision:
            current_tile = self.last_vision['current_tile']
            
            # Prioritize stones we actually need for elevation
            missing_stones = self.player_state.get_missing_stones()
            for stone in missing_stones:
                if stone in current_tile:
                    print(f"💎 {stone} (NEEDED for elevation)")
                    self._send(f"Take {stone}")
                    self.last_vision = None
                    return
            
            # Also collect other stones opportunistically
            for stone in ['linemate', 'deraumere', 'sibur', 'mendiane', 'phiras', 'thystame']:
                if stone in current_tile:
                    print(f"💎 {stone} (SAFE)")
                    self._send(f"Take {stone}")
                    self.last_vision = None
                    return
        
        # Priority 9: Inventory check
        if self.commands_sent - self.inventory_checks > 30:
            self._send("Inventory")
            self.inventory_checks = self.commands_sent
            return
        
        # Priority 10: Explore
        if mode == "SAFE":
            print(f"🔍 Explore (SAFE) - Level {self.player_state.level}")
        else:
            print(f"🚨 Food search (HUNGRY)")
        
        self._send(random.choice(["Forward", "Right", "Left"]))
        self.last_vision = None
    
    def _send(self, command):
        """Send command"""
        self.client.send_command(command)
        self.commands_sent += 1
        self.last_command = command
    
    def _process_responses(self):
        """Process server responses"""
        for _ in range(3):
            response = self.client.get_response(timeout=0.05)
            if response:
                self._handle_response(response)
            else:
                break
    
    def _handle_response(self, response):
        """Handle server responses"""
        if response == "ok":
            if self.last_command == "Take food":
                self.survival.record_food_collected()
                self.last_vision = None
        
        elif response == "ko":
            # FIXED: Handle elevation failure properly
            if self.last_command == "Incantation":
                self.elevation_manager.handle_elevation_response(response)
            elif self.last_command in ["Take food", "Forward", "Right", "Left"]:
                self.last_vision = None
        
        elif response == "dead":
            print("💀 DIED!")
            self._final_stats()
            self.running = False
        
        elif response.startswith("message"):
            # Handle broadcast: "message 3, L1:READY:none:SAFE"
            parts = response.split(", ", 1)
            if len(parts) == 2:
                direction = parts[0].split()[1]
                message = parts[1]
                teammate_info = self.broadcast_manager.parse_broadcast(direction, message)
                if teammate_info:
                    self.broadcast_manager.teammates[direction] = teammate_info
        
        elif "Elevation underway" in response or "Current level:" in response:
            new_level = self.elevation_manager.handle_elevation_response(response)
            if new_level:
                self.player_state.level = new_level
        
        elif response.startswith("["):
            self._handle_data(response)
    
    def _handle_data(self, response):
        """Handle inventory and vision data"""
        if re.search(r'food \d+', response):
            # Inventory
            self.survival.update_from_inventory(response)
            self.player_state.update_from_inventory(response)
        else:
            # Vision
            vision_data = self.vision.parse_vision(response)
            self.last_vision = vision_data
            
            if vision_data['food_locations']:
                if 0 in vision_data['food_locations']:
                    print("🎯 FOOD HERE!")
                else:
                    nearby = [loc for loc in vision_data['food_locations'] if loc != 0]
                    if nearby:
                        print(f"🍖 Food: {nearby}")
    
    def _status_update(self):
        """Status update"""
        runtime = time.time() - self.start_time
        food_rate = self.survival.food_collected / (runtime/60) if runtime > 0 else 0
        mode = self.survival.get_mode()
        
        missing = self.player_state.get_missing_stones()
        can_elevate = "✅ READY" if self.player_state.can_elevate() else f"❌ Need: {','.join(missing[:2])}"
        
        print(f"📊 L{self.player_state.level} {mode}: {food_rate:.1f} food/min, {can_elevate}")
    
    def _final_stats(self):
        """Final stats"""
        runtime = time.time() - self.start_time
        food_rate = self.survival.food_collected / (runtime/60) if runtime > 0 else 0
        
        print(f"\n🚀 ADVANCED AI FINAL STATS:")
        print(f"Runtime: {runtime:.1f}s")
        print(f"Final Level: {self.player_state.level}")
        print(f"Food rate: {food_rate:.1f} food/min")
        print(f"Commands: {self.commands_sent}")
        print(f"Stone inventory: {dict((k,v) for k,v in self.player_state.inventory.items() if k != 'food' and v > 0)}")
    
    def _cleanup(self):
        """Clean shutdown"""
        print("Shutting down advanced AI...")
        if self.client:
            self.client.disconnect()

class AIController:
    """Compatibility wrapper"""
    def __init__(self, config):
        self.ai = AdvancedAI(config)
    
    def run(self):
        return self.ai.run()