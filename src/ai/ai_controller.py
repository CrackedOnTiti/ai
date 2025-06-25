import time
import sys
import random
import re
import json # Moved import json to the top
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

import time # Required for PlayerState.player_id
from collections import Counter # Required for PlayerState._recalculate_shared_inventory

class PlayerState:
    """Track player level, inventory, and team's collective resources for rituals"""
    def __init__(self, player_id=None): # Added player_id
        self.level = 1
        # Assign a unique ID to this player instance, could be improved with server-provided ID
        self.player_id = player_id if player_id is not None else str(time.time()) # Simple unique ID
        self.inventory = {
            "food": 10, "linemate": 0, "deraumere": 0,
            "sibur": 0, "mendiane": 0, "phiras": 0, "thystame": 0
        }
        # Stores inventories of teammates, e.g., {"teammate_id_1": {...}, "teammate_id_2": {...}}
        self.team_inventories = {}
        # Stores the sum of this player's inventory and all known team_inventories
        self.shared_inventory = self.inventory.copy()

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
        """Parse inventory response and update state. Recalculates shared_inventory."""
        changed = False
        for resource in self.inventory.keys(): # Use current inventory keys as canonical
            match = re.search(rf'{resource} (\d+)', inventory_response)
            if match:
                new_count = int(match.group(1))
                if self.inventory.get(resource, 0) != new_count:
                    if resource != "food": # Don't print for food to reduce noise
                         print(f"📦 My {resource}: {self.inventory.get(resource, 0)} → {new_count}")
                    self.inventory[resource] = new_count
                    changed = True
        if changed:
            self._recalculate_shared_inventory()

    def update_teammate_inventory(self, teammate_id, inventory_data):
        """Update a teammate's inventory and recalculate shared_inventory."""
        # inventory_data should be a dict similar to self.inventory
        # We assume inventory_data is already parsed if coming from a broadcast
        if teammate_id == self.player_id: # Should not happen if IDs are managed well
            return

        self.team_inventories[teammate_id] = inventory_data.copy() # Store a copy
        self._recalculate_shared_inventory()
        # Optional: print statement for debugging teammate inventory updates

    def _recalculate_shared_inventory(self):
        """Recalculate the shared_inventory based on self and team inventories."""
        combined = Counter()
        combined.update(self.inventory)
        for teammate_inv in self.team_inventories.values():
            combined.update(teammate_inv)

        # Filter out 'food' from shared_inventory as it's typically not shared for rituals
        self.shared_inventory = {res: count for res, count in combined.items() if res != "food"}
        # Ensure all stone types are present, even if count is 0
        for stone in self.elevation_requirements[1].keys():
            if stone not in self.shared_inventory and stone != "players" and stone != "food":
                self.shared_inventory[stone] = 0
        # Add own food back for local reference if needed, but shared_inventory primarily for stones
        self.shared_inventory["food"] = self.inventory.get("food", 0)
        # print(f"🔄 Shared inventory updated: {self.shared_inventory}")


    def can_elevate(self, use_shared_inventory=True):
        """
        Check if stones needed for the next level are available.
        By default, uses the shared_inventory.
        """
        if self.level >= 8:
            return False  # Max level

        requirements = self.elevation_requirements.get(self.level, {})
        inventory_to_check = self.shared_inventory if use_shared_inventory else self.inventory

        for stone, needed in requirements.items():
            if stone != "players" and needed > 0:
                if inventory_to_check.get(stone, 0) < needed:
                    # print(f"⚠️ Cannot elevate: Need {needed} {stone}, Team Has: {inventory_to_check.get(stone, 0)}")
                    return False
        return True

    def get_missing_stones(self, use_shared_inventory=True):
        """
        Get list of stones still needed for the next level.
        By default, uses the shared_inventory.
        """
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
    """Handle team communication"""
    def __init__(self, player_id, player_state_ref): # Added player_id and player_state_ref
        self.player_id = player_id
        self.player_state = player_state_ref # Reference to PlayerState for inventory access
        self.last_broadcast = 0
        self.broadcast_interval = 15  # Broadcast every 15 seconds
        self.teammates = {}  # Track teammate status (will likely need more structure)
        
    def should_broadcast(self):
        """Check if time to broadcast status"""
        return time.time() - self.last_broadcast > self.broadcast_interval
    
    # --- New Broadcast Message Creation Methods ---

    def create_inventory_broadcast(self):
        """Creates a broadcast message sharing the player's current inventory and level."""
        essential_inventory = {
            k: v for k, v in self.player_state.inventory.items() if k != "food"
        }
        inv_str = json.dumps(essential_inventory)
        message = f"BCAST_INV_SHARE;pid={self.player_id};lvl={self.player_state.level};inv={inv_str}"
        return message

    def create_incantation_initiate_broadcast(self):
        """Broadcasts intent to start an incantation for the player's current level."""
        message = f"BCAST_INC_INIT;pid={self.player_id};lvl={self.player_state.level}"
        return message

    def create_incantation_join_broadcast(self, initiator_id):
        """Broadcasts intent to join an incantation."""
        message = f"BCAST_INC_JOIN;pid={self.player_id};target_lvl={self.player_state.level};init_pid={initiator_id}"
        return message

    def create_incantation_ready_broadcast(self, tile_checksum="not_impl"):
        """Broadcasts readiness for incantation at current location."""
        message = f"BCAST_INC_READY;pid={self.player_id};lvl={self.player_state.level};chksum={tile_checksum}"
        return message

    def create_incantation_confirm_broadcast(self):
        """Broadcasts confirmation that incantation is starting (by initiator)."""
        message = f"BCAST_INC_CONFIRM;pid={self.player_id};lvl={self.player_state.level}"
        return message

    def create_legacy_status_broadcast(self, mode):
        """Maintains a similar format to the old status broadcast for basic info,
           but uses shared inventory for 'NEED' status."""
        ready_for_elevation_team = "READY_TEAM" if self.player_state.can_elevate(use_shared_inventory=True) else "NEED_TEAM"
        missing_team = self.player_state.get_missing_stones(use_shared_inventory=True)
        missing_team_str = ",".join(missing_team[:3]) if missing_team else "none"
        message = f"L{self.player_state.level}:{ready_for_elevation_team}:{missing_team_str}:{mode}"
        return message

    # --- Updated Parse Broadcast Method ---

    def parse_broadcast(self, direction, raw_message):
        """
        Parse teammate broadcast. Handles new message formats.
        Updates PlayerState.team_inventories for inventory shares.
        Returns structured info for ElevationManager or other systems.
        """
        # print(f"DEBUG: Parsing broadcast from dir {direction}: {raw_message}")
        try:
            parts = raw_message.split(";", 1)
            msg_type = parts[0]
            payload = parts[1] if len(parts) > 1 else ""

            # Simple key-value parser for payload (e.g., "key1=val1;key2=val2")
            data = {}
            if payload:
                for item in payload.split(";"):
                    kv = item.split("=", 1)
                    if len(kv) == 2:
                        data[kv[0]] = kv[1]

            sender_pid = data.get("pid")
            if not sender_pid or sender_pid == self.player_id: # Ignore own broadcasts or malformed
                return None

            # --- Handle New Message Types ---
            if msg_type == "BCAST_INV_SHARE":
                # print(f"DEBUG: Received BCAST_INV_SHARE from {sender_pid}")
                level = int(data.get("lvl", 0))
                inv_str = data.get("inv")
                if inv_str:
                    try:
                        inventory = json.loads(inv_str)
                        # Add food:0 because PlayerState expects it, though not strictly for sharing
                        if "food" not in inventory: inventory["food"] = 0
                        self.player_state.update_teammate_inventory(sender_pid, inventory)
                        print(f"📻 INV from {sender_pid} (L{level}): {inventory}")
                        # Could return something for ElevationManager if needed, e.g. teammate level
                        return {"type": "INV_SHARE", "pid": sender_pid, "level": level, "inventory": inventory, "direction": direction}
                    except json.JSONDecodeError:
                        print(f"⚠️ Failed to parse inventory JSON from {sender_pid}: {inv_str}")
                return None # Or specific error

            elif msg_type == "BCAST_INC_INIT":
                level = int(data.get("lvl", 0))
                print(f"📻 INC_INIT from {sender_pid} (L{level})")
                return {"type": "INC_INIT", "pid": sender_pid, "level": level, "direction": direction}

            elif msg_type == "BCAST_INC_JOIN":
                target_level = int(data.get("target_lvl", 0))
                initiator_pid = data.get("init_pid")
                print(f"📻 INC_JOIN from {sender_pid} for L{target_level} (init: {initiator_pid})")
                return {"type": "INC_JOIN", "pid": sender_pid, "target_level": target_level, "initiator_pid": initiator_pid, "direction": direction}

            elif msg_type == "BCAST_INC_READY":
                level = int(data.get("lvl", 0))
                checksum = data.get("chksum")
                print(f"📻 INC_READY from {sender_pid} (L{level}, chksum: {checksum})")
                return {"type": "INC_READY", "pid": sender_pid, "level": level, "checksum": checksum, "direction": direction}

            elif msg_type == "BCAST_INC_CONFIRM":
                level = int(data.get("lvl",0))
                print(f"📻 INC_CONFIRM from {sender_pid} (L{level})")
                return {"type": "INC_CONFIRM", "pid": sender_pid, "level": level, "direction": direction}

            # --- Handle Legacy Status (for basic teammate info, can be phased out or adapted) ---
            # Attempt to parse as legacy if not matched above (e.g. "L1:READY:none:SAFE")
            # This part needs to be robust or we decide to fully switch.
            # For now, let's assume new format messages are distinct enough.
            # If raw_message matches old "L{level}:{status}:{missing}:{mode}"
            legacy_parts = raw_message.split(":")
            if len(legacy_parts) >= 3 and legacy_parts[0].startswith("L"):
                try:
                    level = int(legacy_parts[0][1:])
                    status = legacy_parts[1] # e.g. READY_TEAM, NEED_TEAM (or old READY/NEED)
                    # This is just for basic awareness, main coordination via new messages
                    print(f"📻 Legacy Teammate Status (dir {direction}): Level {level}, {status}")
                    # We don't have a unique PID here, so using direction as key for basic tracking
                    # This is limited, new PID-based system is better.
                    # self.teammates[direction] = {"level": level, "status": status} # Old way
                    return {"type": "LEGACY_STATUS", "level": level, "status": status, "direction": direction, "pid": f"legacy_dir_{direction}"}
                except ValueError:
                    pass # Not a valid legacy message

        except Exception as e:
            print(f"⚠️ Error parsing broadcast: '{raw_message}' - {e}")
        return None

from enum import Enum # For ElevationState

class ElevationState(Enum):
    IDLE = 0
    INITIATING = 1  # This AI is starting a ritual
    JOINING = 2     # This AI is joining another's ritual
    GATHERING_AT_SITE = 3 # All participants moving/at site, initiator waiting for READYs
    PREPARING_RITUAL = 4  # Initiator: received enough READYs, checking stones, about to start
    AWAITING_SERVER_RESPONSE = 5 # Incantation command sent
    COOLDOWN = 6    # Cooldown after success/failure/timeout

class ElevationManager:
    """Handles multi-stage elevation ritual coordination using broadcasts."""
    def __init__(self, player_id, player_state_ref, broadcast_manager_ref, send_command_callback):
        self.player_id = player_id
        self.player_state = player_state_ref
        self.broadcast_manager = broadcast_manager_ref
        self.send_command = send_command_callback # Callback to AI's _send() method

        self.state = ElevationState.IDLE
        self.current_ritual_initiator_pid = None
        self.current_ritual_level = 0
        self.participants = {} # {pid: {"status": "JOINED" / "READY", "direction": X, ...}}

        self.state_start_time = time.time()
        self.ritual_timeout = 60  # Max time for a ritual from INIT to start
        self.general_cooldown_duration = 30 # Cooldown after any ritual conclusion
        self.last_ritual_end_time = 0

        # For initiator: to store 'Look' result before Incantation
        self.last_look_before_incantation_str = None
        self.pending_actions = [] # List of commands to execute by AI

    def reset_ritual_state(self, success=False):
        print(f"🎭 Ritual reset. Success: {success}. Current state: {self.state}")
        self.state = ElevationState.IDLE # Or COOLDOWN
        self.current_ritual_initiator_pid = None
        self.current_ritual_level = 0
        self.participants.clear()
        self.last_look_before_incantation_str = None
        self.pending_actions.clear()
        self.last_ritual_end_time = time.time()
        self.state_start_time = time.time()
        if not success: # Apply longer cooldown on failure to re-evaluate
             self.state = ElevationState.COOLDOWN


    def _can_start_or_join_ritual(self):
        """Basic checks before participating in any ritual."""
        if self.player_state.level >= 8: return False # Max level
        if time.time() - self.last_ritual_end_time < self.general_cooldown_duration:
            # print("DEBUG_ELEV: In general cooldown.")
            return False
        # Add food check? if self.player_state.inventory['food'] < SOME_THRESHOLD: return False
        return True

    def handle_teammate_broadcast(self, bcast_data):
        """Process incantation-related broadcasts from teammates."""
        msg_type = bcast_data.get("type")
        sender_pid = bcast_data.get("pid")
        level = bcast_data.get("level") or bcast_data.get("target_level") # Handles INC_JOIN's target_level
        
        if not sender_pid or sender_pid == self.player_id:
            return # Ignore own or malformed

        # print(f"DEBUG_ELEV: Handling broadcast {msg_type} from {sender_pid} for L{level}")

        if self.state == ElevationState.IDLE and self._can_start_or_join_ritual():
            if msg_type == "BCAST_INC_INIT" and level == self.player_state.level:
                # Another player initiated for our current level. Let's consider joining.
                print(f"🎭 Received INC_INIT from {sender_pid} for our L{self.player_state.level}. Considering joining.")
                # Decision to join:
                # 1. Do we have the stones OURSELVES for this level? (The team might, but we need to contribute)
                #    For simplicity now, let's assume if team has it, we are willing.
                #    A better check: Do I have *my share* of stones, or am I a "player" slot filler?
                if self.player_state.can_elevate(use_shared_inventory=False): # Check if *I* have my stones
                    self.state = ElevationState.JOINING
                    self.current_ritual_initiator_pid = sender_pid
                    self.current_ritual_level = level
                    self.participants[self.player_id] = {"status": "SELF_JOINING"} # Add self
                    # TODO: Add initiator to participants if not already?
                    join_msg = self.broadcast_manager.create_incantation_join_broadcast(sender_pid)
                    self.pending_actions.append(f"Broadcast {join_msg}")
                    print(f"🎭 Transitioning to JOINING ritual by {sender_pid} for L{level}.")
                    # TODO: Add logic to move towards initiator (direction needed from bcast_data)
                else:
                    print(f"😕 Don't have my personal share of stones for L{level}, won't join {sender_pid}'s ritual yet.")

        elif self.state == ElevationState.INITIATING and self.current_ritual_initiator_pid == self.player_id:
            if msg_type == "BCAST_INC_JOIN" and bcast_data.get("init_pid") == self.player_id and level == self.current_ritual_level:
                print(f"🎭 Player {sender_pid} is JOINING our ritual for L{self.current_ritual_level}.")
                self.participants[sender_pid] = {"status": "JOINED", "direction": bcast_data.get("direction")}
                # Check if enough players have joined + self
                required_players = self.player_state.elevation_requirements[self.current_ritual_level]["players"]
                if len(self.participants) + 1 >= required_players: # +1 for self (initiator)
                    print(f"👥 Enough players ({len(self.participants) + 1}/{required_players}) joined. Moving to GATHERING_AT_SITE.")
                    self.state = ElevationState.GATHERING_AT_SITE
                    self.state_start_time = time.time()
                    # Initiator is already at site, others will move.
                    # Initiator might need to 'Set' stones if not already there.

        elif self.state == ElevationState.GATHERING_AT_SITE:
            # Both initiator and participants listen for READY messages
            if msg_type == "BCAST_INC_READY" and level == self.current_ritual_level:
                # Check if this sender is part of our current ritual participants or the initiator
                if sender_pid == self.current_ritual_initiator_pid or sender_pid in self.participants:
                    print(f"👍 Player {sender_pid} is READY for L{self.current_ritual_level} ritual.")
                    if sender_pid == self.current_ritual_initiator_pid: # Initiator declared ready
                         self.participants[sender_pid] = {**self.participants.get(sender_pid,{}), "status": "READY_INITIATOR"}
                    else:
                         self.participants[sender_pid] = {**self.participants.get(sender_pid,{}), "status": "READY_PARTICIPANT"}
                else:
                    print(f"⚠️ Received BCAST_INC_READY from {sender_pid} who is not part of current ritual for L{self.current_ritual_level}.")


        elif self.state == ElevationState.JOINING and self.current_ritual_initiator_pid == sender_pid:
            if msg_type == "BCAST_INC_CONFIRM" and level == self.current_ritual_level:
                # Initiator confirmed, we should be at the site and have set our stones.
                print(f"✅ Initiator {sender_pid} confirmed ritual start for L{level}. Awaiting server.")
                self.state = ElevationState.AWAITING_SERVER_RESPONSE
                self.state_start_time = time.time() # Reset timer for server response
        
        # TODO: Handle players dying or leaving ritual (e.g. no recent INV_SHARE)

    def update_and_get_command(self):
        """Main logic loop for ElevationManager. Decides actions based on state."""
        # print(f"DEBUG_ELEV: Update. State: {self.state}, Time in state: {time.time() - self.state_start_time:.1f}s")
        
        # Handle timeouts for states that expect responses or actions
        if self.state in [ElevationState.INITIATING, ElevationState.JOINING, ElevationState.GATHERING_AT_SITE, ElevationState.PREPARING_RITUAL]:
            if time.time() - self.state_start_time > self.ritual_timeout:
                print(f"⏰ Ritual timeout in state {self.state}. Resetting.")
                self.reset_ritual_state(success=False)
                # No command, just reset. AI will revert to other behaviors.

        if self.state == ElevationState.COOLDOWN:
            if time.time() - self.last_ritual_end_time >= self.general_cooldown_duration:
                print("❄️ Cooldown finished.")
                self.state = ElevationState.IDLE
                self.state_start_time = time.time()


        # --- State-specific logic ---
        if self.state == ElevationState.IDLE:
            if self._can_start_or_join_ritual():
                # Check if this AI can initiate a ritual
                # 1. Does the TEAM have enough stones for my NEXT level?
                # 2. Do *I* have my required stones? (Simpler: if team has it, I am willing to start)
                # 3. Are there enough players of my level available? (Estimate from broadcast_manager.teammates)
                if self.player_state.can_elevate(use_shared_inventory=True): # Team has stones
                    my_level = self.player_state.level
                    requirements = self.player_state.elevation_requirements.get(my_level, {})
                    required_players = requirements.get("players", 1)

                    # Estimate available teammates of the same level
                    available_teammates_count = 0
                    for pid, data in self.broadcast_manager.teammates.items():
                        if pid != self.player_id and data.get('level') == my_level and \
                           (time.time() - data.get('last_seen', 0)) < 30: # Active recently
                            available_teammates_count +=1

                    # If I am level 1, I only need myself and my own stones.
                    if my_level == 1 and self.player_state.can_elevate(use_shared_inventory=False): # Solo with own stones
                         print(f"🎭 Ready for SOLO elevation (L{my_level}→{my_level + 1})")
                         self.current_ritual_initiator_pid = self.player_id
                         self.current_ritual_level = my_level
                         self.participants[self.player_id] = {"status": "SELF_INITIATING"} # Add self
                         self.state = ElevationState.PREPARING_RITUAL # Skip to preparing for L1
                         self.state_start_time = time.time()
                         print(f"🎭 Transitioning to PREPARING_RITUAL (SOLO L1)")
                         self.pending_actions.append("Look") # Look before incantation

                    elif available_teammates_count + 1 >= required_players:
                        print(f"🌟 Potential to INITIATE for L{my_level}. Have {available_teammates_count+1}/{required_players} players. Team has stones.")
                        self.state = ElevationState.INITIATING
                        self.current_ritual_initiator_pid = self.player_id
                        self.current_ritual_level = my_level
                        self.participants[self.player_id] = {"status": "SELF_INITIATING"} # Add self
                        self.state_start_time = time.time()
                        init_msg = self.broadcast_manager.create_incantation_initiate_broadcast()
                        self.pending_actions.append(f"Broadcast {init_msg}")
                        print(f"🎭 Transitioning to INITIATING ritual for L{my_level}.")
                    # else:
                        # print(f"DEBUG_ELEV: Can elevate by team, but not enough players ({available_teammates_count+1}/{required_players}) for L{my_level}")
                # else:
                    # print(f"DEBUG_ELEV: Team cannot elevate for L{self.player_state.level} yet.")

        elif self.state == ElevationState.INITIATING:
            # Waiting for INC_JOIN broadcasts, handled by handle_teammate_broadcast
            # Timeout is handled above.
            # If enough players join, handle_teammate_broadcast transitions to GATHERING_AT_SITE
            pass

        elif self.state == ElevationState.JOINING:
            # Action: Move towards initiator. This needs more advanced pathfinding.
            # For now, assume we are "moving". If target direction is known:
            # Example: self.pending_actions.append(command_to_move_towards_direction)
            # After some time or when at "location" (how to know?), set stones and broadcast READY.
            # This is a placeholder for movement and stone setting logic.
            if time.time() - self.state_start_time > 5 : # Simulate time to "arrive" and set stones
                print(f"🤝 Arrived at ritual site (simulated) for L{self.current_ritual_level}. Setting stones.")
                # TODO: Actual stone setting: Iterate self.player_state.elevation_requirements[self.current_ritual_level]
                # For each stone type, if self.player_state.inventory has it, and it's needed on tile:
                # self.pending_actions.append(f"Set {stone_name}")
                # This needs to be done carefully based on what's already on the tile (from Look)
                # For now, let's assume stones are magically set by participants if they have them.
                ready_msg = self.broadcast_manager.create_incantation_ready_broadcast()
                self.pending_actions.append(f"Broadcast {ready_msg}")
                self.state = ElevationState.GATHERING_AT_SITE # Now wait for initiator's CONFIRM
                self.state_start_time = time.time()
                print(f"👍 Sent READY for L{self.current_ritual_level}. Now in GATHERING_AT_SITE (as participant).")


        elif self.state == ElevationState.GATHERING_AT_SITE:
            # If this AI is the initiator:
            if self.current_ritual_initiator_pid == self.player_id:
                requirements = self.player_state.elevation_requirements[self.current_ritual_level]
                required_players = requirements["players"]

                ready_participants_count = 0
                for pid, data in self.participants.items():
                    if data.get("status") == "READY_PARTICIPANT" or data.get("status") == "READY_INITIATOR" \
                       or (pid == self.player_id and data.get("status") == "SELF_INITIATING"): # Initiator counts as ready
                        ready_participants_count += 1

                # print(f"DEBUG_ELEV: Initiator at GATHERING. Ready count: {ready_participants_count}/{required_players}")

                if ready_participants_count >= required_players:
                    print(f"👥 All {required_players} players ready for L{self.current_ritual_level}. Initiator moving to PREPARING_RITUAL.")
                    self.state = ElevationState.PREPARING_RITUAL
                    self.state_start_time = time.time()
                    self.pending_actions.append("Look") # Crucial: Look at the tile now
                # else:
                    # print(f"⏳ Waiting for more READY messages. Have {ready_participants_count}/{required_players}.")
            # else (participant): Waiting for INC_CONFIRM from initiator (handled by handle_teammate_broadcast)
            # Or timeout.
            pass

        elif self.state == ElevationState.PREPARING_RITUAL:
            # Only initiator should be in this state.
            if self.current_ritual_initiator_pid == self.player_id:
                if self.last_look_before_incantation_str:
                    print(f"🔍 Initiator has vision: {self.last_look_before_incantation_str[:50]}...")
                    # TODO: Parse self.last_look_before_incantation_str
                    # Verify all required stones for self.current_ritual_level are on tile 0.
                    # This requires FastVisionParser to be enhanced or a new parser here.
                    # Placeholder: Assume stones are correct based on players broadcasting READY.
                    all_stones_present = self._check_stones_on_tile(self.last_look_before_incantation_str)

                    if all_stones_present:
                        print(f"✅ Stones verified on tile for L{self.current_ritual_level}. Starting Incantation!")
                        confirm_msg = self.broadcast_manager.create_incantation_confirm_broadcast()
                        self.pending_actions.append(f"Broadcast {confirm_msg}")
                        self.pending_actions.append("Incantation")
                        self.state = ElevationState.AWAITING_SERVER_RESPONSE
                        self.state_start_time = time.time()
                        self.last_look_before_incantation_str = None # Clear it
                    else:
                        print(f"❌ Stones NOT correct on tile for L{self.current_ritual_level}! Resetting ritual.")
                        # TODO: Broadcast a failure/reset message?
                        self.reset_ritual_state(success=False)
                elif not any(cmd == "Look" for cmd in self.pending_actions):
                    print("DEBUG_ELEV: Initiator in PREPARING_RITUAL, needs to Look.")
                    self.pending_actions.append("Look")
            else: # Should not happen for participant
                print("ERROR: Participant in PREPARING_RITUAL state!")
                self.reset_ritual_state(success=False)

        elif self.state == ElevationState.AWAITING_SERVER_RESPONSE:
            # Waiting for server "Elevation underway", "ko", or "Current level: X"
            # Handled by handle_elevation_response. Timeout also handled.
            if time.time() - self.state_start_time > 15: # Server response timeout
                print("⏰ Timeout waiting for server response to Incantation. Resetting.")
                self.reset_ritual_state(success=False)


        # Return and clear pending actions
        if self.pending_actions:
            actions_to_send = self.pending_actions.copy()
            self.pending_actions.clear()
            # print(f"DEBUG_ELEV: Pending actions: {actions_to_send}")
            return actions_to_send[0] if len(actions_to_send) == 1 else actions_to_send
        return None

    def _check_stones_on_tile(self, vision_tile_zero_str):
        """Helper to check if required stones are on the current tile based on 'Look' string for tile 0."""
        if vision_tile_zero_str is None: return False
        
        requirements = self.player_state.elevation_requirements.get(self.current_ritual_level, {})
        if not requirements: return False # Should not happen

        # Naive check: just see if stone names are present. A real parser would count them.
        # vision_tile_zero_str example: "player linemate food"
        # For L1: needs 1 linemate.
        # This is a simplified check. A robust solution would parse counts.
        tile_contents = vision_tile_zero_str.lower().split()

        for stone, needed_count in requirements.items():
            if stone == "players" or needed_count == 0:
                continue

            # This simple check only sees if stone is present, not count
            # actual_count_on_tile = tile_contents.count(stone)
            # if actual_count_on_tile < needed_count:
            #     print(f"DEBUG_ELEV: Stone check fail: Need {needed_count} {stone}, found {actual_count_on_tile} in '{vision_tile_zero_str}'")
            #     return False
            if stone not in tile_contents and needed_count > 0 : # Simplified: if needed, must be present
                 print(f"DEBUG_ELEV: Stone check fail: Need {stone} (count {needed_count}), not found in '{vision_tile_zero_str}'")
                 return False


        print(f"DEBUG_ELEV: Stone check (simplified) PASSED for L{self.current_ritual_level} on tile '{vision_tile_zero_str}'")
        return True # Placeholder

    def set_vision_for_incantation_check(self, vision_str):
        """Called by AI when it receives 'Look' response, if EM is in PREPARING_RITUAL."""
        if self.state == ElevationState.PREPARING_RITUAL and self.current_ritual_initiator_pid == self.player_id:
            # Assuming vision_str is the full "[tile0, tile1, ...]" string
            try:
                # Extract just tile 0 content
                tile0_content = vision_str.strip('[]').split(',', 1)[0].strip()
                self.last_look_before_incantation_str = tile0_content
                print(f"DEBUG_ELEV: Initiator received vision for pre-incantation check: '{tile0_content}'")
            except Exception as e:
                print(f"ERROR parsing vision for incantation check: {e}")
                self.last_look_before_incantation_str = None # Clear if error


    def handle_elevation_response(self, response):
        """Handle server response to 'Incantation' command."""
        if self.state != ElevationState.AWAITING_SERVER_RESPONSE:
            # print(f"DEBUG_ELEV: Received elevation response '{response}' but not in AWAITING_SERVER_RESPONSE state (current: {self.state}). Ignoring.")
            return None # No level change to report

        if "Elevation underway" in response:
            print("✨ Elevation in progress...")
            # Stay in AWAITING_SERVER_RESPONSE for "Current level:"
            self.state_start_time = time.time() # Reset timer for this part
            return None
        elif "Current level:" in response:
            level_match = re.search(r'Current level: (\d+)', response)
            if level_match:
                new_level = int(level_match.group(1))
                print(f"🎉 ELEVATION SUCCESS! Now level {new_level}")
                self.player_state.level = new_level # Update player state directly
                self.reset_ritual_state(success=True)
                self.state = ElevationState.COOLDOWN # Go to cooldown after success
                self.last_ritual_end_time = time.time()
                return new_level # Inform AI of level change
        elif response == "ko":
            print("❌ Elevation failed! (Server responded KO)")
            self.reset_ritual_state(success=False)
            self.state = ElevationState.COOLDOWN # Go to cooldown after failure
            self.last_ritual_end_time = time.time()

        return None # No level change or already handled

# Orphaned block removed. The correct ForkManager class definition follows.

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
        stone_locations = [] # List of (tile_index, stone_name)
        player_locations = [] # List of tile_index where players are found
        
        for i, tile_content in enumerate(tiles):
            if not tile_content: # Skip empty tile strings
                continue

            if 'food' in tile_content:
                food_locations.append(i)

            for stone in ['linemate', 'deraumere', 'sibur', 'mendiane', 'phiras', 'thystame']:
                if stone in tile_content:
                    stone_locations.append((i, stone))

            if 'player' in tile_content:
                player_locations.append(i)
        
        return {
            'tiles': tiles, # Raw tile strings
            'food_locations': food_locations, # List of tile indices
            'stone_locations': stone_locations, # List of (tile_index, stone_name)
            'player_locations': player_locations, # List of tile indices
            'current_tile': tiles[0] if tiles else '' # Raw string of current tile
        }
    
    def has_food_here(self, vision_data):
        """Check if food is on current tile"""
        return 0 in vision_data['food_locations']

class DirectMovement:
    """Direct movement logic"""
    def get_action_for_food(self, food_locations):
        """Get action to reach closest food"""
        if not food_locations:
            return [] # Return list for consistency
        
        # This method is now simplified as a specific case of reaching a food tile.
        # The main AI loop will use get_actions_to_reach_tile for more general movement.
        target_tile_index = min(food_locations)
        return self.get_actions_to_reach_tile(target_tile_index)

    def get_actions_to_reach_tile(self, target_tile_index: int) -> list[str]:
        """
        Calculates a sequence of commands (Forward, Left, Right) to reach a given tile index.
        Tile indices are from the 'Look' command's array.
        Assumes standard Zappy tile layout:
        Level 0: 0 (current)
        Level 1: 1, 2, 3 ( सामने )
        Level 2: 4, 5, 6, 7, 8 ( और सामने )
        ...and so on.
        Returns a list of commands.
        """
        if target_tile_index == 0:
            return [] # Already at the target tile

        # Determine level and position within level for the target tile
        level = 0
        start_index_of_level = 0
        tiles_in_level = 1
        while start_index_of_level + tiles_in_level <= target_tile_index:
            start_index_of_level += tiles_in_level
            level += 1
            tiles_in_level = 2 * level + 1

        if level == 0: # Should be caught by target_tile_index == 0
             return []

        actions = []

        # 1. Move Forward 'level' times to reach the start of the target row
        for _ in range(level):
            actions.append("Forward")

        # 2. Turn and move towards the specific tile in that row
        # 'position_in_level' is 0 for the leftmost tile of that level, up to 'tiles_in_level - 1'
        position_in_level = target_tile_index - start_index_of_level
        center_of_level = tiles_in_level // 2

        if position_in_level < center_of_level: # Target is to the left of straight ahead
            actions.append("Left")
            for _ in range(center_of_level - position_in_level):
                actions.append("Forward")
        elif position_in_level > center_of_level: # Target is to the right of straight ahead
            actions.append("Right")
            for _ in range(position_in_level - center_of_level):
                actions.append("Forward")
        # If position_in_level == center_of_level, it's straight ahead, no further turn/move needed after initial Forwards.

        return actions

class AdvancedAI:
    """Advanced AI with broadcast, rituals, and forking"""
    def __init__(self, config):
        self.config = config; self.client = None; self.running = False
        self.survival = SimpleSurvivalManager()
        player_id = f"{getattr(config, 'team_name', 'p')}_{int(time.time()*1000)}" # Ensure player_id is robust
        self.player_state = PlayerState(player_id=player_id)
        self.broadcast_manager = BroadcastManager(player_id=player_id, player_state_ref=self.player_state)
        self.elevation_manager = ElevationManager(player_id=player_id, player_state_ref=self.player_state,
                                                  broadcast_manager_ref=self.broadcast_manager, send_command_callback=self._send)
        self.fork_manager = ForkManager()
        self.vision = FastVisionParser(); self.movement = DirectMovement()
        self.last_vision = None; self.commands_sent = 0; self.start_time = time.time()
        self.last_command = None; self.inventory_checks = 0; self.action_queue = [] # Ensure action_queue is initialized
        
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

        # Priority 1: Elevation Manager decides and acts
        # The ElevationManager's update method will now return a command or list of commands if any action is needed.
        em_command_or_commands = self.elevation_manager.update_and_get_command()
        if em_command_or_commands:
            if isinstance(em_command_or_commands, list):
                for cmd in em_command_or_commands:
                    self._send(cmd)
                    # Potentially add a small delay or check if server allows rapid commands
            else: # Single command
                self._send(em_command_or_commands)
            # print(f"DEBUG_AI: Sent command(s) from ElevationManager: {em_command_or_commands}")
            return # Give EM priority and time for its actions to be processed.

        # If ElevationManager is IDLE or has no immediate action, proceed with other behaviors.
        # The old direct calls to EM's should_attempt and start_elevation are now handled internally by EM.

        # Priority 2: Broadcast inventory and status to team (if EM didn't just broadcast)
        # Check if last command was a broadcast to avoid spamming
        if self.broadcast_manager.should_broadcast() and not (self.last_command and self.last_command.startswith("Broadcast")):
            # Send comprehensive inventory data less frequently or based on change
            # For now, just sending it along with status update
            inv_message = self.broadcast_manager.create_inventory_broadcast()
            self._send(f"Broadcast {inv_message}")
            # Potentially send a simpler status message more often, or combine
            # For now, let's use the legacy one for general status
            status_message = self.broadcast_manager.create_legacy_status_broadcast(mode) # Changed method name
            self._send(f"Broadcast {status_message}")
            self.broadcast_manager.last_broadcast = time.time()
            # print(f"DEBUG: Sent broadcasts: INV={inv_message}, STATUS={status_message}")
            return # Return after broadcasting to give server time to process
        
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
        
        # Priority 8: Collect stones when safe (Targeted and Opportunistic)
        if mode == "SAFE" and self.last_vision and self.elevation_manager.state == ElevationState.IDLE: # Only collect if not in a ritual
            current_tile_content = self.last_vision['current_tile']
            
            # 1. Prioritize stones specifically needed for THIS AI's next level, considering shared inventory.
            #    get_missing_stones(use_shared_inventory=True) gives what the TEAM lacks for THIS AI's elevation.
            #    This means if the stone is on the list, the team needs it for *me*.
            team_missing_for_my_elevation = self.player_state.get_missing_stones(use_shared_inventory=True)
            
            if team_missing_for_my_elevation:
                # Create a count of needed stones to pick them up fairly if multiple types are present
                needed_counts = Counter(team_missing_for_my_elevation)
                # Sort by how many are needed, then alphabetically for determinism
                sorted_needed_stones = sorted(needed_counts.keys(), key=lambda x: (needed_counts[x], x), reverse=True)

                for stone in sorted_needed_stones:
                    if stone in current_tile_content:
                        print(f"💎 Targeting {stone} (Team needs for my L{self.player_state.level+1}) on current tile.")
                        self._send(f"Take {stone}")
                        self.last_vision = None # Assume vision changes after taking
                        return

            # 2. Opportunistic collection: If no stones specifically needed for *my* elevation are here,
            #    consider picking up any stone if team's overall shared quantity is low for that stone type
            #    (e.g., less than 3-4 of any particular stone type in shared_inventory, excluding food).
            #    This helps accumulate for future levels or other teammates.
            #    This is a simpler heuristic than calculating for all teammates' levels.
            generic_stones = ['linemate', 'deraumere', 'sibur', 'mendiane', 'phiras', 'thystame']
            random.shuffle(generic_stones) # Add some variability to opportunistic collection

            for stone in generic_stones:
                # Check if stone is on current tile AND if shared inventory has a low amount of it
                # Define "low amount" - e.g. less than needed for a typical higher level ritual component (e.g. < 3)
                # Or, simply, if it's there and not one we just tried to take for targeted needs.
                if stone in current_tile_content and self.player_state.shared_inventory.get(stone, 0) < 3:
                    # Avoid picking if it was in team_missing_for_my_elevation but we skipped it (e.g. not present)
                    if stone not in team_missing_for_my_elevation: # Ensure it's not a "needed" one we couldn't find
                        print(f"💎 Opportunistically taking {stone} (Team shared: {self.player_state.shared_inventory.get(stone, 0)}).")
                        self._send(f"Take {stone}")
                        self.last_vision = None
                        return

            # 3. Fallback: If still nothing taken, and there are *any* stones here not needed by team for me,
            #    but maybe I personally have none of it. (Original opportunistic logic)
            #    This is now partly covered by point 2. We can make it more explicit:
            #    If a stone is here, and I have 0, take it.
            for stone in generic_stones: # Iterate again or use a different list
                if stone in current_tile_content and self.player_state.inventory.get(stone, 0) == 0:
                    if stone not in team_missing_for_my_elevation : # and not just opportunistically taken
                         # Check if it was already picked by the opportunistic logic above
                        was_opportunistically_targeted = (stone in generic_stones and self.player_state.shared_inventory.get(stone, 0) < 3)
                        if not was_opportunistically_targeted:
                            print(f"💎 Taking {stone} (I have 0, opportunistic fallback).")
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
                direction_str = parts[0].split()[1] # This is the direction from server "message X, ..."
                message_content = parts[1]

                parsed_broadcast_data = self.broadcast_manager.parse_broadcast(direction_str, message_content)

                if parsed_broadcast_data:
                    # The parse_broadcast method already updates shared inventory via player_state reference.
                    # Now, we need to decide what to do with other types of broadcast info.
                    # ElevationManager will eventually consume INC_* type messages.
                    # We can update a general 'teammates' status dict in BroadcastManager or here.

                    sender_pid = parsed_broadcast_data.get("pid")
                    if sender_pid: # Should always be there for new formats
                        # Store/update general status of this teammate
                        # This is separate from detailed inventory which is in PlayerState.team_inventories
                        current_teammate_status = self.broadcast_manager.teammates.get(sender_pid, {})
                        current_teammate_status['last_seen'] = time.time()
                        current_teammate_status['direction'] = direction_str # Last known direction

                        if parsed_broadcast_data['type'] == 'INV_SHARE':
                            current_teammate_status['level'] = parsed_broadcast_data.get('level')
                        elif parsed_broadcast_data['type'] == 'LEGACY_STATUS': # if we keep it
                            current_teammate_status['level'] = parsed_broadcast_data.get('level')
                            current_teammate_status['status_legacy'] = parsed_broadcast_data.get('status')

                        # For incantation messages, ElevationManager will need to react.
                        # For now, we can just log them or store basic info.
                        if parsed_broadcast_data['type'].startswith('INC_'):
                            current_teammate_status['last_inc_msg'] = parsed_broadcast_data['type']
                            current_teammate_status['inc_level_target'] = parsed_broadcast_data.get('level') or parsed_broadcast_data.get('target_level')
                            # print(f"DEBUG_AI: Teammate {sender_pid} incantation activity: {parsed_broadcast_data}")
                            self.elevation_manager.handle_teammate_broadcast(parsed_broadcast_data) # Pass to EM

                        self.broadcast_manager.teammates[sender_pid] = current_teammate_status
                    # else:
                        # print(f"DEBUG: Parsed broadcast from dir {direction_str} but no PID or not relevant for general tracking: {parsed_broadcast_data}")

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
        else: # Vision data
            # If ElevationManager is preparing ritual and this AI is initiator, pass vision to it
            if self.elevation_manager.state == ElevationState.PREPARING_RITUAL and \
               self.elevation_manager.current_ritual_initiator_pid == self.player_state.player_id:
                self.elevation_manager.set_vision_for_incantation_check(response) # response is vision string

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