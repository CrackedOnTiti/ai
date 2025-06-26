import time
import sys
import random
import re
import json
from network_client import NetworkClient

class SimpleSurvivalManager:
    """Manages basic food collection and survival mode determination"""
    
    def __init__(self):
        self.food_count = 10
        self.food_collected = 0
        
    def record_food_collected(self):
        """Track when food is successfully collected"""
        self.food_collected += 1
        print(f"FOOD +1! Total: {self.food_collected}")
        
    def update_from_inventory(self, inventory_response):
        """Update internal food count from server inventory response"""
        food_match = re.search(r'food (\d+)', inventory_response)
        if food_match:
            new_count = int(food_match.group(1))
            if new_count != self.food_count:
                print(f"Food: {self.food_count} → {new_count}")
            self.food_count = new_count
    
    def get_mode(self):
        """Return current survival mode based on food count"""
        return "SAFE" if self.food_count >= 9 else "HUNGRY"

import time
from collections import Counter

class PlayerState:
    """Tracks player level, inventory, and team resources for elevation rituals"""
    
    def __init__(self, player_id=None):
        self.level = 1
        self.player_id = player_id if player_id is not None else str(time.time())
        self.inventory = {
            "food": 10, "linemate": 0, "deraumere": 0,
            "sibur": 0, "mendiane": 0, "phiras": 0, "thystame": 0
        }
        self.team_inventories = {}
        self.shared_inventory = self.inventory.copy()

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
        """Parse inventory response from server and update internal state"""
        changed = False
        for resource in self.inventory.keys():
            match = re.search(rf'{resource} (\d+)', inventory_response)
            if match:
                new_count = int(match.group(1))
                if self.inventory.get(resource, 0) != new_count:
                    if resource != "food":
                         print(f"My {resource}: {self.inventory.get(resource, 0)} → {new_count}")
                    self.inventory[resource] = new_count
                    changed = True
        if changed:
            self._recalculate_shared_inventory()

    def update_teammate_inventory(self, teammate_id, inventory_data):
        """Update a teammate's inventory data and recalculate shared resources"""
        if teammate_id == self.player_id:
            return

        self.team_inventories[teammate_id] = inventory_data.copy()
        self._recalculate_shared_inventory()

    def _recalculate_shared_inventory(self):
        """Recalculate the combined inventory of self and all teammates"""
        combined = Counter()
        combined.update(self.inventory)
        for teammate_inv in self.team_inventories.values():
            combined.update(teammate_inv)

        self.shared_inventory = {res: count for res, count in combined.items() if res != "food"}
        for stone in self.elevation_requirements[1].keys():
            if stone not in self.shared_inventory and stone != "players" and stone != "food":
                self.shared_inventory[stone] = 0
        self.shared_inventory["food"] = self.inventory.get("food", 0)

    def can_elevate(self, use_shared_inventory=True):
        """Check if required stones are available for next level elevation"""
        if self.level >= 8:
            return False

        requirements = self.elevation_requirements.get(self.level, {})
        inventory_to_check = self.shared_inventory if use_shared_inventory else self.inventory

        for stone, needed in requirements.items():
            if stone != "players" and needed > 0:
                if inventory_to_check.get(stone, 0) < needed:
                    return False
        return True

    def get_missing_stones(self, use_shared_inventory=True):
        """Get list of stones still needed for next level elevation"""
        if self.level >= 8:
            return []

        requirements = self.elevation_requirements.get(self.level, {})
        inventory_to_check = self.shared_inventory if use_shared_inventory else self.inventory
        missing = []

        for stone, needed in requirements.items():
            if stone != "players" and needed > 0:
                have = inventory_to_check.get(stone, 0)
                if have < needed:
                    missing.extend([stone] * (needed - have))
        return missing

class BroadcastManager:
    """Handles team communication through broadcast messages"""
    
    def __init__(self, player_id, player_state_ref):
        self.player_id = player_id
        self.player_state = player_state_ref
        self.last_broadcast = 0
        self.broadcast_interval = 15
        self.teammates = {}
        
    def should_broadcast(self):
        """Check if enough time has passed since last broadcast"""
        return time.time() - self.last_broadcast > self.broadcast_interval
    
    def create_inventory_broadcast(self):
        """Create broadcast message sharing current inventory and level"""
        essential_inventory = {
            k: v for k, v in self.player_state.inventory.items() if k != "food"
        }
        inv_str = json.dumps(essential_inventory, separators=(',', ':'))
        message = f"BCAST_INV_SHARE;pid={self.player_id};lvl={self.player_state.level};inv={inv_str}"
        return message

    def create_incantation_initiate_broadcast(self):
        """Create broadcast announcing intent to start an incantation"""
        message = f"BCAST_INC_INIT;pid={self.player_id};lvl={self.player_state.level}"
        return message

    def create_incantation_join_broadcast(self, initiator_id):
        """Create broadcast announcing intent to join someone's incantation"""
        message = f"BCAST_INC_JOIN;pid={self.player_id};target_lvl={self.player_state.level};init_pid={initiator_id}"
        return message

    def create_incantation_ready_broadcast(self, tile_checksum="not_impl"):
        """Create broadcast announcing readiness for incantation at current location"""
        message = f"BCAST_INC_READY;pid={self.player_id};lvl={self.player_state.level};chksum={tile_checksum}"
        return message

    def create_incantation_confirm_broadcast(self):
        """Create broadcast confirming that incantation is starting"""
        message = f"BCAST_INC_CONFIRM;pid={self.player_id};lvl={self.player_state.level}"
        return message

    def create_legacy_status_broadcast(self, mode):
        """Create legacy format status broadcast for basic teammate information"""
        ready_for_elevation_team = "READY_TEAM" if self.player_state.can_elevate(use_shared_inventory=True) else "NEED_TEAM"
        missing_team = self.player_state.get_missing_stones(use_shared_inventory=True)
        missing_team_str = ",".join(missing_team[:3]) if missing_team else "none"
        message = f"L{self.player_state.level}:{ready_for_elevation_team}:{missing_team_str}:{mode}"
        return message

    def parse_broadcast(self, direction, raw_message):
        """Parse incoming broadcast messages and update team state accordingly"""
        try:
            parts = raw_message.split(";", 1)
            msg_type = parts[0]
            payload = parts[1] if len(parts) > 1 else ""

            data = {}
            if payload:
                for item in payload.split(";"):
                    kv = item.split("=", 1)
                    if len(kv) == 2:
                        data[kv[0]] = kv[1]

            sender_pid = data.get("pid")
            if not sender_pid or sender_pid == self.player_id:
                return None

            if msg_type == "BCAST_INV_SHARE":
                level = int(data.get("lvl", 0))
                inv_str = data.get("inv")
                if inv_str:
                    try:
                        inventory = json.loads(inv_str)
                        if "food" not in inventory: inventory["food"] = 0
                        self.player_state.update_teammate_inventory(sender_pid, inventory)
                        print(f"INV from {sender_pid} (L{level}): {inventory}")
                        return {"type": "INV_SHARE", "pid": sender_pid, "level": level, "inventory": inventory, "direction": direction}
                    except json.JSONDecodeError:
                        print(f"Failed to parse inventory JSON from {sender_pid}: {inv_str}")
                return None

            elif msg_type == "BCAST_INC_INIT":
                level = int(data.get("lvl", 0))
                print(f"INC_INIT from {sender_pid} (L{level})")
                return {"type": "INC_INIT", "pid": sender_pid, "level": level, "direction": direction}

            elif msg_type == "BCAST_INC_JOIN":
                target_level = int(data.get("target_lvl", 0))
                initiator_pid = data.get("init_pid")
                print(f"INC_JOIN from {sender_pid} for L{target_level} (init: {initiator_pid})")
                return {"type": "INC_JOIN", "pid": sender_pid, "target_level": target_level, "initiator_pid": initiator_pid, "direction": direction}

            elif msg_type == "BCAST_INC_READY":
                level = int(data.get("lvl", 0))
                checksum = data.get("chksum")
                print(f"INC_READY from {sender_pid} (L{level}, chksum: {checksum})")
                return {"type": "INC_READY", "pid": sender_pid, "level": level, "checksum": checksum, "direction": direction}

            elif msg_type == "BCAST_INC_CONFIRM":
                level = int(data.get("lvl",0))
                print(f"INC_CONFIRM from {sender_pid} (L{level})")
                return {"type": "INC_CONFIRM", "pid": sender_pid, "level": level, "direction": direction}

            legacy_parts = raw_message.split(":")
            if len(legacy_parts) >= 3 and legacy_parts[0].startswith("L"):
                try:
                    level = int(legacy_parts[0][1:])
                    status = legacy_parts[1]
                    print(f"Legacy Teammate Status (dir {direction}): Level {level}, {status}")
                    return {"type": "LEGACY_STATUS", "level": level, "status": status, "direction": direction, "pid": f"legacy_dir_{direction}"}
                except ValueError:
                    pass

        except Exception as e:
            print(f"Error parsing broadcast: '{raw_message}' - {e}")
        return None

from enum import Enum

class ElevationState(Enum):
    IDLE = 0
    INITIATING = 1
    JOINING = 2
    GATHERING_AT_SITE = 3
    PREPARING_RITUAL = 4
    AWAITING_SERVER_RESPONSE = 5
    COOLDOWN = 6

class ElevationManager:
    """Manages multi-stage elevation ritual coordination using broadcasts"""
    
    def __init__(self, player_id, player_state_ref, broadcast_manager_ref, send_command_callback):
        self.player_id = player_id
        self.player_state = player_state_ref
        self.broadcast_manager = broadcast_manager_ref
        self.send_command = send_command_callback

        self.state = ElevationState.IDLE
        self.current_ritual_initiator_pid = None
        self.current_ritual_level = 0
        self.participants = {}

        self.state_start_time = time.time()
        self.ritual_timeout = 60
        self.general_cooldown_duration = 30
        self.last_ritual_end_time = 0

        self.last_look_before_incantation_str = None
        self.pending_actions = []

    def reset_ritual_state(self, success=False):
        """Reset all ritual-related state variables"""
        print(f"Ritual reset. Success: {success}. Current state: {self.state}")
        self.state = ElevationState.IDLE
        self.current_ritual_initiator_pid = None
        self.current_ritual_level = 0
        self.participants.clear()
        self.last_look_before_incantation_str = None
        self.pending_actions.clear()
        self.last_ritual_end_time = time.time()
        self.state_start_time = time.time()
        if not success:
             self.state = ElevationState.COOLDOWN

    def _can_start_or_join_ritual(self):
        """Check if player is eligible to participate in rituals"""
        if self.player_state.level >= 8: return False
        if time.time() - self.last_ritual_end_time < self.general_cooldown_duration:
            return False
        return True

    def handle_teammate_broadcast(self, bcast_data):
        """Process elevation-related broadcasts from other players"""
        msg_type = bcast_data.get("type")
        sender_pid = bcast_data.get("pid")
        level = bcast_data.get("level") or bcast_data.get("target_level")
        
        if not sender_pid or sender_pid == self.player_id:
            return

        if self.state == ElevationState.IDLE and self._can_start_or_join_ritual():
            if msg_type == "BCAST_INC_INIT" and level == self.player_state.level:
                print(f"Received INC_INIT from {sender_pid} for our L{self.player_state.level}. Considering joining.")
                if self.player_state.can_elevate(use_shared_inventory=False):
                    self.state = ElevationState.JOINING
                    self.current_ritual_initiator_pid = sender_pid
                    self.current_ritual_level = level
                    self.participants[self.player_id] = {"status": "SELF_JOINING"}
                    join_msg = self.broadcast_manager.create_incantation_join_broadcast(sender_pid)
                    self.pending_actions.append(f"Broadcast {join_msg}")
                    print(f"Transitioning to JOINING ritual by {sender_pid} for L{level}.")
                else:
                    print(f"Don't have my personal share of stones for L{level}, won't join {sender_pid}'s ritual yet.")

        elif self.state == ElevationState.INITIATING and self.current_ritual_initiator_pid == self.player_id:
            if msg_type == "BCAST_INC_JOIN" and bcast_data.get("init_pid") == self.player_id and level == self.current_ritual_level:
                print(f"Player {sender_pid} is JOINING our ritual for L{self.current_ritual_level}.")
                self.participants[sender_pid] = {"status": "JOINED", "direction": bcast_data.get("direction")}
                required_players = self.player_state.elevation_requirements[self.current_ritual_level]["players"]
                if len(self.participants) + 1 >= required_players:
                    print(f"Enough players ({len(self.participants) + 1}/{required_players}) joined. Moving to GATHERING_AT_SITE.")
                    self.state = ElevationState.GATHERING_AT_SITE
                    self.state_start_time = time.time()

        elif self.state == ElevationState.GATHERING_AT_SITE:
            if msg_type == "BCAST_INC_READY" and level == self.current_ritual_level:
                if sender_pid == self.current_ritual_initiator_pid or sender_pid in self.participants:
                    print(f"Player {sender_pid} is READY for L{self.current_ritual_level} ritual.")
                    if sender_pid == self.current_ritual_initiator_pid:
                         self.participants[sender_pid] = {**self.participants.get(sender_pid,{}), "status": "READY_INITIATOR"}
                    else:
                         self.participants[sender_pid] = {**self.participants.get(sender_pid,{}), "status": "READY_PARTICIPANT"}
                else:
                    print(f"Received BCAST_INC_READY from {sender_pid} who is not part of current ritual for L{self.current_ritual_level}.")

        elif self.state == ElevationState.JOINING and self.current_ritual_initiator_pid == sender_pid:
            if msg_type == "BCAST_INC_CONFIRM" and level == self.current_ritual_level:
                print(f"Initiator {sender_pid} confirmed ritual start for L{level}. Awaiting server.")
                self.state = ElevationState.AWAITING_SERVER_RESPONSE
                self.state_start_time = time.time()

    def update_and_get_command(self):
        """Main decision logic for elevation manager, returns commands to execute"""
        if self.state in [ElevationState.INITIATING, ElevationState.JOINING, ElevationState.GATHERING_AT_SITE, ElevationState.PREPARING_RITUAL]:
            if time.time() - self.state_start_time > self.ritual_timeout:
                print(f"Ritual timeout in state {self.state}. Resetting.")
                self.reset_ritual_state(success=False)

        if self.state == ElevationState.COOLDOWN:
            if time.time() - self.last_ritual_end_time >= self.general_cooldown_duration:
                print("Cooldown finished.")
                self.state = ElevationState.IDLE
                self.state_start_time = time.time()

        if self.state == ElevationState.IDLE:
            if self._can_start_or_join_ritual():
                if self.player_state.can_elevate(use_shared_inventory=True):
                    my_level = self.player_state.level
                    requirements = self.player_state.elevation_requirements.get(my_level, {})
                    required_players = requirements.get("players", 1)

                    available_teammates_count = 0
                    for pid, data in self.broadcast_manager.teammates.items():
                        if pid != self.player_id and data.get('level') == my_level and \
                           (time.time() - data.get('last_seen', 0)) < 30:
                            available_teammates_count +=1

                    if my_level == 1 and self.player_state.can_elevate(use_shared_inventory=False):
                         print(f"Ready for SOLO elevation (L{my_level}→{my_level + 1})")
                         self.current_ritual_initiator_pid = self.player_id
                         self.current_ritual_level = my_level
                         self.participants[self.player_id] = {"status": "SELF_INITIATING"}
                         self.state = ElevationState.PREPARING_RITUAL
                         self.state_start_time = time.time()
                         print(f"Transitioning to PREPARING_RITUAL (SOLO L1)")
                         self.pending_actions.append("Look")

                    elif available_teammates_count + 1 >= required_players:
                        print(f"Potential to INITIATE for L{my_level}. Have {available_teammates_count+1}/{required_players} players. Team has stones.")
                        self.state = ElevationState.INITIATING
                        self.current_ritual_initiator_pid = self.player_id
                        self.current_ritual_level = my_level
                        self.participants[self.player_id] = {"status": "SELF_INITIATING"}
                        self.state_start_time = time.time()
                        init_msg = self.broadcast_manager.create_incantation_initiate_broadcast()
                        self.pending_actions.append(f"Broadcast {init_msg}")
                        print(f"Transitioning to INITIATING ritual for L{my_level}.")

        elif self.state == ElevationState.INITIATING:
            pass

        elif self.state == ElevationState.JOINING:
            if time.time() - self.state_start_time > 5:
                print(f"Arrived at ritual site (simulated) for L{self.current_ritual_level}. Setting stones.")
                ready_msg = self.broadcast_manager.create_incantation_ready_broadcast()
                self.pending_actions.append(f"Broadcast {ready_msg}")
                self.state = ElevationState.GATHERING_AT_SITE
                self.state_start_time = time.time()
                print(f"Sent READY for L{self.current_ritual_level}. Now in GATHERING_AT_SITE (as participant).")

        elif self.state == ElevationState.GATHERING_AT_SITE:
            if self.current_ritual_initiator_pid == self.player_id:
                requirements = self.player_state.elevation_requirements[self.current_ritual_level]
                required_players = requirements["players"]

                ready_participants_count = 0
                for pid, data in self.participants.items():
                    if data.get("status") == "READY_PARTICIPANT" or data.get("status") == "READY_INITIATOR" \
                       or (pid == self.player_id and data.get("status") == "SELF_INITIATING"):
                        ready_participants_count += 1

                if ready_participants_count >= required_players:
                    print(f"All {required_players} players ready for L{self.current_ritual_level}. Initiator moving to PREPARING_RITUAL.")
                    self.state = ElevationState.PREPARING_RITUAL
                    self.state_start_time = time.time()
                    self.pending_actions.append("Look")

        elif self.state == ElevationState.PREPARING_RITUAL:
            if self.current_ritual_initiator_pid == self.player_id:
                if self.last_look_before_incantation_str:
                    print(f"Initiator has vision: {self.last_look_before_incantation_str[:50]}...")
                    all_stones_present = self._check_stones_on_tile(self.last_look_before_incantation_str)

                    if all_stones_present:
                        print(f"Stones verified on tile for L{self.current_ritual_level}. Starting Incantation!")
                        confirm_msg = self.broadcast_manager.create_incantation_confirm_broadcast()
                        self.pending_actions.append(f"Broadcast {confirm_msg}")
                        self.pending_actions.append("Incantation")
                        self.state = ElevationState.AWAITING_SERVER_RESPONSE
                        self.state_start_time = time.time()
                        self.last_look_before_incantation_str = None
                    else:
                        print(f"Stones NOT correct on tile for L{self.current_ritual_level}! Resetting ritual.")
                        self.reset_ritual_state(success=False)
                elif not any(cmd == "Look" for cmd in self.pending_actions):
                    self.pending_actions.append("Look")
            else:
                print("ERROR: Participant in PREPARING_RITUAL state!")
                self.reset_ritual_state(success=False)

        elif self.state == ElevationState.AWAITING_SERVER_RESPONSE:
            if time.time() - self.state_start_time > 15:
                print("Timeout waiting for server response to Incantation. Resetting.")
                self.reset_ritual_state(success=False)

        if self.pending_actions:
            actions_to_send = self.pending_actions.copy()
            self.pending_actions.clear()
            return actions_to_send[0] if len(actions_to_send) == 1 else actions_to_send
        return None

    def _check_stones_on_tile(self, vision_tile_zero_str):
        """Check if required stones are present on current tile for elevation"""
        if vision_tile_zero_str is None: return False
        
        requirements = self.player_state.elevation_requirements.get(self.current_ritual_level, {})
        if not requirements: return False

        tile_contents = vision_tile_zero_str.lower().split()

        for stone, needed_count in requirements.items():
            if stone == "players" or needed_count == 0:
                continue

            if stone not in tile_contents and needed_count > 0:
                 print(f"Stone check fail: Need {stone} (count {needed_count}), not found in '{vision_tile_zero_str}'")
                 return False

        print(f"Stone check (simplified) PASSED for L{self.current_ritual_level} on tile '{vision_tile_zero_str}'")
        return True

    def set_vision_for_incantation_check(self, vision_str):
        """Store vision data for pre-incantation stone verification"""
        if self.state == ElevationState.PREPARING_RITUAL and self.current_ritual_initiator_pid == self.player_id:
            try:
                tile0_content = vision_str.strip('[]').split(',', 1)[0].strip()
                self.last_look_before_incantation_str = tile0_content
            except Exception as e:
                print(f"ERROR parsing vision for incantation check: {e}")
                self.last_look_before_incantation_str = None

    def handle_elevation_response(self, response):
        """Process server response to incantation command"""
        if self.state != ElevationState.AWAITING_SERVER_RESPONSE:
            return None

        if "Elevation underway" in response:
            print("Elevation in progress...")
            self.state_start_time = time.time()
            return None
        elif "Current level:" in response:
            level_match = re.search(r'Current level: (\d+)', response)
            if level_match:
                new_level = int(level_match.group(1))
                print(f"ELEVATION SUCCESS! Now level {new_level}")
                self.player_state.level = new_level
                self.reset_ritual_state(success=True)
                self.state = ElevationState.COOLDOWN
                self.last_ritual_end_time = time.time()
                return new_level
        elif response == "ko":
            print("Elevation failed! (Server responded KO)")
            self.reset_ritual_state(success=False)
            self.state = ElevationState.COOLDOWN
            self.last_ritual_end_time = time.time()

        return None

class ForkManager:
    """Manages team reproduction strategy through forking"""
    
    def __init__(self):
        self.last_fork_time = 0
        self.fork_cooldown = 60
        self.team_size_target = 6
        
    def should_fork(self, player_state, mode):
        """Determine if player should fork to expand team size"""
        if mode != "SAFE" or player_state.level < 2:
            return False
            
        if time.time() - self.last_fork_time < self.fork_cooldown:
            return False
            
        if player_state.level >= 6:
            return True
        elif player_state.level == 2 and random.random() < 0.20:
            return True
        elif player_state.level >= 3 and player_state.level < 6 and random.random() < 0.30:
            return True
            
        return False
    
    def attempt_fork(self):
        """Execute fork command and update internal state"""
        self.last_fork_time = time.time()
        print("Forking to expand team!")
        return "Fork"

class FastVisionParser:
    """Efficiently parse vision data from server Look command"""
    
    def parse_vision(self, vision_string):
        """Parse vision string and extract locations of resources and players"""
        tiles = [tile.strip() for tile in vision_string.strip('[]').split(',')]
        
        food_locations = []
        stone_locations = []
        player_locations = []
        
        for i, tile_content in enumerate(tiles):
            if not tile_content:
                continue

            if 'food' in tile_content:
                food_locations.append(i)

            for stone in ['linemate', 'deraumere', 'sibur', 'mendiane', 'phiras', 'thystame']:
                if stone in tile_content:
                    stone_locations.append((i, stone))

            if 'player' in tile_content:
                player_locations.append(i)
        
        return {
            'tiles': tiles,
            'food_locations': food_locations,
            'stone_locations': stone_locations,
            'player_locations': player_locations,
            'current_tile': tiles[0] if tiles else ''
        }
    
    def has_food_here(self, vision_data):
        """Check if food is present on current tile"""
        return 0 in vision_data['food_locations']

class DirectMovement:
    """Calculate movement commands to reach specific map tiles"""
    
    def get_action_for_food(self, food_locations):
        """Get movement commands to reach closest food tile"""
        if not food_locations:
            return []
        
        target_tile_index = min(food_locations)
        return self.get_actions_to_reach_tile(target_tile_index)

    def get_actions_to_reach_tile(self, target_tile_index: int) -> list[str]:
        """Calculate sequence of movement commands to reach specified tile index"""
        if target_tile_index == 0:
            return []

        level = 0
        start_index_of_level = 0
        tiles_in_level = 1
        while start_index_of_level + tiles_in_level <= target_tile_index:
            start_index_of_level += tiles_in_level
            level += 1
            tiles_in_level = 2 * level + 1

        if level == 0:
             return []

        actions = []

        for _ in range(level):
            actions.append("Forward")

        position_in_level = target_tile_index - start_index_of_level
        center_of_level = tiles_in_level // 2

        if position_in_level < center_of_level:
            actions.append("Left")
            for _ in range(center_of_level - position_in_level):
                actions.append("Forward")
        elif position_in_level > center_of_level:
            actions.append("Right")
            for _ in range(position_in_level - center_of_level):
                actions.append("Forward")

        return actions

class AdvancedAI:
    """Main AI controller with broadcast communication, elevation rituals, and team management"""
    
    def __init__(self, config):
        self.config = config; self.client = None; self.running = False
        self.survival = SimpleSurvivalManager()
        player_id = f"{getattr(config, 'team_name', 'p')}_{int(time.time()*1000)}"
        self.player_state = PlayerState(player_id=player_id)
        self.broadcast_manager = BroadcastManager(player_id=player_id, player_state_ref=self.player_state)
        self.elevation_manager = ElevationManager(player_id=player_id, player_state_ref=self.player_state,
                                                  broadcast_manager_ref=self.broadcast_manager, send_command_callback=self._send)
        self.fork_manager = ForkManager()
        self.vision = FastVisionParser(); self.movement = DirectMovement()
        self.last_vision = None; self.commands_sent = 0; self.start_time = time.time()
        self.last_command = None; self.inventory_checks = 0; self.action_queue = []
        
    def run(self):
        """Main entry point for AI execution"""
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
        """Establish connection to game server"""
        print(f"ADVANCED AI - Broadcast, Rituals & Forking")
        print(f"Connecting to {self.config.machine}:{self.config.port}...")
        
        self.client = NetworkClient(self.config)
        if not self.client.connect():
            return False
        
        print(f"Connected! Starting advanced gameplay...")
        self.running = True
        return True
    
    def _main_loop(self):
        """Main game loop handling server communication and decision making"""
        self._send("Inventory")
        self._send("Look")
        
        while self.running and self.client.is_connected():
            try:
                self._process_responses()
                self._execute_advanced_behavior()
                
                if self.commands_sent % 25 == 0 and self.commands_sent > 0:
                    self._status_update()
                
                time.sleep(0.08)
                
            except Exception as e:
                print(f"Loop error: {e}")
                time.sleep(0.5)
    
    def _execute_advanced_behavior(self):
        """Execute AI decision-making logic with prioritized behaviors"""
        mode = self.survival.get_mode()

        em_command_or_commands = self.elevation_manager.update_and_get_command()
        if em_command_or_commands:
            if isinstance(em_command_or_commands, list):
                for cmd in em_command_or_commands:
                    self._send(cmd)
            else:
                self._send(em_command_or_commands)
            return

        if self.broadcast_manager.should_broadcast() and not (self.last_command and self.last_command.startswith("Broadcast")):
            inv_message = self.broadcast_manager.create_inventory_broadcast()
            self._send(f"Broadcast {inv_message}")
            status_message = self.broadcast_manager.create_legacy_status_broadcast(mode)
            self._send(f"Broadcast {status_message}")
            self.broadcast_manager.last_broadcast = time.time()
            return
        
        if self.fork_manager.should_fork(self.player_state, mode):
            command = self.fork_manager.attempt_fork()
            self._send(command)
            return
        
        if not self.last_vision:
            self._send("Look")
            return
        
        if self.vision.has_food_here(self.last_vision):
            if self.last_command != "Take food":
                print(f"TAKE! ({mode})")
                self._send("Take food")
                return
        
        other_food = [loc for loc in self.last_vision['food_locations'] if loc != 0]
        if other_food:
            action = self.movement.get_action_for_food(other_food)
            if action:
                target = min(other_food)
                print(f"Planning to move to food at tile {target} via {action} ({mode})")
                for cmd_step in action:
                    self._send(cmd_step)
                self.last_vision = None
                return
        
        if mode == "SAFE" and self.last_vision and self.elevation_manager.state == ElevationState.IDLE:
            current_tile_content = self.last_vision['current_tile']
            
            team_missing_for_my_elevation = self.player_state.get_missing_stones(use_shared_inventory=True)
            
            if team_missing_for_my_elevation:
                needed_counts = Counter(team_missing_for_my_elevation)
                sorted_needed_stones = sorted(needed_counts.keys(), key=lambda x: (needed_counts[x], x), reverse=True)

                for stone in sorted_needed_stones:
                    if stone in current_tile_content:
                        print(f"Targeting {stone} (Team needs for my L{self.player_state.level+1}) on current tile.")
                        self._send(f"Take {stone}")
                        self.last_vision = None
                        return

            generic_stones = ['linemate', 'deraumere', 'sibur', 'mendiane', 'phiras', 'thystame']
            random.shuffle(generic_stones)

            for stone in generic_stones:
                if stone in current_tile_content and self.player_state.shared_inventory.get(stone, 0) < 3:
                    if stone not in team_missing_for_my_elevation:
                        print(f"Opportunistically taking {stone} (Team shared: {self.player_state.shared_inventory.get(stone, 0)}).")
                        self._send(f"Take {stone}")
                        self.last_vision = None
                        return

            for stone in generic_stones:
                if stone in current_tile_content and self.player_state.inventory.get(stone, 0) == 0:
                    if stone not in team_missing_for_my_elevation :
                        was_opportunistically_targeted = (stone in generic_stones and self.player_state.shared_inventory.get(stone, 0) < 3)
                        if not was_opportunistically_targeted:
                            print(f"Taking {stone} (I have 0, opportunistic fallback).")
                            self._send(f"Take {stone}")
                            self.last_vision = None
                            return
        
        if self.commands_sent - self.inventory_checks > 30:
            self._send("Inventory")
            self.inventory_checks = self.commands_sent
            return
        
        if mode == "SAFE":
            print(f"Explore (SAFE) - Level {self.player_state.level}")
        else:
            print(f"Food search (HUNGRY)")
        
        self._send(random.choice(["Forward", "Right", "Left"]))
        self.last_vision = None
    
    def _send(self, command):
        """Send command to server and update internal counters"""
        self.client.send_command(command)
        self.commands_sent += 1
        self.last_command = command
    
    def _process_responses(self):
        """Process incoming responses from server"""
        for _ in range(3):
            response = self.client.get_response(timeout=0.05)
            if response:
                self._handle_response(response)
            else:
                break
    
    def _handle_response(self, response):
        """Handle specific server response messages"""
        if response == "ok":
            if self.last_command == "Take food":
                self.survival.record_food_collected()
                self.last_vision = None
        
        elif response == "ko":
            if self.last_command == "Incantation":
                self.elevation_manager.handle_elevation_response(response)
            elif self.last_command in ["Take food", "Forward", "Right", "Left"]:
                self.last_vision = None
        
        elif response == "dead":
            print("DIED!")
            self._final_stats()
            self.running = False
        
        elif response.startswith("message"):
            parts = response.split(", ", 1)
            if len(parts) == 2:
                direction_str = parts[0].split()[1]
                message_content = parts[1]

                parsed_broadcast_data = self.broadcast_manager.parse_broadcast(direction_str, message_content)

                if parsed_broadcast_data:
                    sender_pid = parsed_broadcast_data.get("pid")
                    if sender_pid:
                        current_teammate_status = self.broadcast_manager.teammates.get(sender_pid, {})
                        current_teammate_status['last_seen'] = time.time()
                        current_teammate_status['direction'] = direction_str

                        if parsed_broadcast_data['type'] == 'INV_SHARE':
                            current_teammate_status['level'] = parsed_broadcast_data.get('level')
                        elif parsed_broadcast_data['type'] == 'LEGACY_STATUS':
                            current_teammate_status['level'] = parsed_broadcast_data.get('level')
                            current_teammate_status['status_legacy'] = parsed_broadcast_data.get('status')

                        if parsed_broadcast_data['type'].startswith('INC_'):
                            current_teammate_status['last_inc_msg'] = parsed_broadcast_data['type']
                            current_teammate_status['inc_level_target'] = parsed_broadcast_data.get('level') or parsed_broadcast_data.get('target_level')
                            self.elevation_manager.handle_teammate_broadcast(parsed_broadcast_data)

                        self.broadcast_manager.teammates[sender_pid] = current_teammate_status

        elif "Elevation underway" in response or "Current level:" in response:
            new_level = self.elevation_manager.handle_elevation_response(response)
            if new_level:
                self.player_state.level = new_level
        
        elif response.startswith("["):
            self._handle_data(response)
    
    def _handle_data(self, response):
        """Handle inventory and vision data responses from server"""
        if re.search(r'food \d+', response):
            self.survival.update_from_inventory(response)
            self.player_state.update_from_inventory(response)
        else:
            if self.elevation_manager.state == ElevationState.PREPARING_RITUAL and \
               self.elevation_manager.current_ritual_initiator_pid == self.player_state.player_id:
                self.elevation_manager.set_vision_for_incantation_check(response)

            vision_data = self.vision.parse_vision(response)
            self.last_vision = vision_data
            
            if vision_data['food_locations']:
                if 0 in vision_data['food_locations']:
                    print("FOOD HERE!")
                else:
                    nearby = [loc for loc in vision_data['food_locations'] if loc != 0]
                    if nearby:
                        print(f"Food: {nearby}")
    
    def _status_update(self):
        """Print current status and performance metrics"""
        runtime = time.time() - self.start_time
        food_rate = self.survival.food_collected / (runtime/60) if runtime > 0 else 0
        mode = self.survival.get_mode()
        
        missing = self.player_state.get_missing_stones()
        can_elevate = "READY" if self.player_state.can_elevate() else f"Need: {','.join(missing[:2])}"
        
        print(f"L{self.player_state.level} {mode}: {food_rate:.1f} food/min, {can_elevate}")
    
    def _final_stats(self):
        """Print final performance statistics"""
        runtime = time.time() - self.start_time
        food_rate = self.survival.food_collected / (runtime/60) if runtime > 0 else 0
        
        print(f"\nADVANCED AI FINAL STATS:")
        print(f"Runtime: {runtime:.1f}s")
        print(f"Final Level: {self.player_state.level}")
        print(f"Food rate: {food_rate:.1f} food/min")
        print(f"Commands: {self.commands_sent}")
        print(f"Stone inventory: {dict((k,v) for k,v in self.player_state.inventory.items() if k != 'food' and v > 0)}")
    
    def _cleanup(self):
        """Clean shutdown and resource cleanup"""
        print("Shutting down advanced AI...")
        if self.client:
            self.client.disconnect()

class AIController:
    """Compatibility wrapper for AdvancedAI"""
    
    def __init__(self, config):
        self.ai = AdvancedAI(config)
    
    def run(self):
        """Run the AI controller"""
        return self.ai.run()