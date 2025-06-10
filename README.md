# ZAPPY
*A Tribute to Zaphod Beeblebrox*

Welcome to **Zappy**, an immersive network-based strategy game where multiple teams battle for supremacy on the planet Trantor. The goal is simple yet challenging: be the first team to elevate at least 6 players to the maximum level through resource management, strategic coordination, and ancient elevation rituals.

## Table of Contents
- [Project Overview](#project-overview)
- [Game Mechanics](#game-mechanics)
- [Architecture](#architecture)
- [Installation & Compilation](#installation--compilation)
- [Usage](#usage)
- [Game Rules](#game-rules)
- [Communication Protocols](#communication-protocols)
- [Team](#team)
- [Technical Requirements](#technical-requirements)

## Project Overview

Zappy is a multi-component network game consisting of three main programs:
- **Server** (`zappy_server`) - The game engine managing the world state
- **Graphical Client** (`zappy_gui`) - Visual representation of the game world
- **AI Client** (`zappy_ai`) - Autonomous player controlling individual inhabitants

The game takes place on Trantor, a spherical world where players (Trantorians) must collect resources, perform elevation rituals, and work together to achieve the highest level possible.

## Game Mechanics

### The World of Trantor
- **Spherical Map**: Players who exit one side reappear on the opposite side
- **Resource-Rich Environment**: Six types of stones plus food scattered across the terrain
- **Peaceful Inhabitants**: Players are pacifist beings focused on survival and elevation

### Resources
The world contains seven types of resources with specific spawn densities:

| Resource | Density | Purpose |
|----------|---------|---------|
| Food | 0.5 | Survival (1 unit = 126 time units of life) |
| Linemate | 0.3 | Elevation rituals |
| Deraumere | 0.15 | Elevation rituals |
| Sibur | 0.1 | Elevation rituals |
| Mendiane | 0.1 | Elevation rituals |
| Phiras | 0.08 | Elevation rituals |
| Thystame | 0.05 | Elevation rituals |

*Formula: `map_width × map_height × density = total_resource_quantity`*

### Elevation System
Players advance through 8 levels using specific combinations of resources and teammates:

| Level | Players | Linemate | Deraumere | Sibur | Mendiane | Phiras | Thystame |
|-------|---------|----------|-----------|-------|----------|--------|----------|
| 1→2 | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| 2→3 | 2 | 1 | 1 | 1 | 0 | 0 | 0 |
| 3→4 | 2 | 2 | 0 | 1 | 0 | 2 | 0 |
| 4→5 | 4 | 1 | 1 | 2 | 0 | 1 | 0 |
| 5→6 | 4 | 1 | 2 | 1 | 3 | 0 | 0 |
| 6→7 | 6 | 1 | 2 | 3 | 0 | 1 | 0 |
| 7→8 | 6 | 2 | 2 | 2 | 2 | 2 | 1 |

### Vision & Communication
- **Limited Vision**: Expands with each level advancement
- **Broadcast System**: Players can send messages with directional sound
- **Team Coordination**: Essential for higher-level elevations

## Architecture

The project consists of three interconnected components:

### Server (C)
- **Single-threaded**: Uses `poll()` for socket multiplexing
- **World Management**: Handles resource spawning, player actions, and game state
- **Protocol Handler**: Manages communication between AI clients and GUI

### Graphical Client (C++)
- **Real-time Visualization**: 2D/3D representation of the game world
- **SFML Integration**: Recommended graphics library for rendering
- **Live Updates**: Receives and displays world state changes

### AI Client (Python)
- **Autonomous Behavior**: Independent decision-making algorithms
- **Strategic Planning**: Resource collection and elevation coordination
- **Team Communication**: Uses broadcast system for coordination

## Installation & Compilation

### Prerequisites
- GCC compiler for C/C++
- Python 3.x for AI client
- SFML library (recommended for GUI)
- Make utility

### Compilation
```bash
# Clone the repository
git clone [repository-url]
cd zappy

# Compile all components
make

# Or compile individually
make zappy_server    # Server component
make zappy_gui      # Graphical client
make zappy_ai       # AI client
```

## Usage

### Starting the Server
```bash
./zappy_server -p 4242 -x 10 -y 10 -n team1 team2 team3 -c 3 -f 100
```

**Parameters:**
- `-p port`: Port number for connections
- `-x width`: World width
- `-y height`: World height  
- `-n name1 name2...`: Team names
- `-c clientsNb`: Maximum clients per team
- `-f freq`: Time unit frequency (default: 100)

### Launching the GUI
```bash
./zappy_gui -p 4242 -h localhost
```

**Parameters:**
- `-p port`: Server port number
- `-h machine`: Server hostname

### Running AI Clients
```bash
./zappy_ai -p 4242 -n team1 -h localhost
```

**Parameters:**
- `-p port`: Server port number
- `-n name`: Team name
- `-h machine`: Server hostname (default: localhost)

## Game Rules

### Victory Condition
The first team to have **6 players reach level 8** wins the game.

### Player Lifecycle
1. **Spawn**: Players start at level 1 with 10 food units (1260 time units of life)
2. **Survival**: Must continuously collect food to avoid starvation
3. **Collection**: Gather stones required for elevation rituals
4. **Elevation**: Coordinate with teammates to perform level-up ceremonies
5. **Reproduction**: Use `fork` command to create new team slots

### Available Commands
| Command | Time Cost | Description |
|---------|-----------|-------------|
| `Forward` | 7/f | Move forward one tile |
| `Right` | 7/f | Turn 90° clockwise |
| `Left` | 7/f | Turn 90° counter-clockwise |
| `Look` | 7/f | Survey surrounding tiles |
| `Inventory` | 1/f | Check current resources |
| `Broadcast text` | 7/f | Send message to all players |
| `Connect_nbr` | - | Check available team slots |
| `Fork` | 42/f | Create new team slot (egg) |
| `Eject` | 7/f | Push other players away |
| `Take object` | 7/f | Pick up resource |
| `Set object` | 7/f | Drop resource |
| `Incantation` | 300/f | Begin elevation ritual |

## Communication Protocols

### AI Client ↔ Server
TCP socket communication with command buffering (max 10 pending commands).

**Connection Handshake:**
```
Server: WELCOME\n
Client: TEAM-NAME\n
Server: CLIENT-NUM\n
Server: X Y\n
```

### GUI ↔ Server
Specialized protocol for real-time world state updates (see GUI protocol documentation).

**Authentication:**
```
Server: WELCOME\n
GUI: GRAPHIC\n
```

## Team

This project is developed by a talented team of four developers, each specializing in different components:

- **[Thierry Bungaroo]** - AI Client Development (Python)
- **[Aymeric Lamanda]** - Server Architecture & Implementation (C) - *Team Lead*
- **[Jules de Rus]** - Graphical User Interface (C++)
- **[Aurelien Peres]**

## Technical Requirements

### Server Requirements
- **Language**: C
- **Architecture**: Single-threaded with `poll()` multiplexing
- **Libraries**: Standard C library
- **Network**: TCP socket handling

### GUI Requirements  
- **Language**: C++
- **Graphics**: SFML (recommended)
- **Features**: Real-time 2D visualization (3D bonus)
- **Protocol**: Custom GUI communication protocol

### AI Requirements
- **Language**: Python (free choice)
- **Behavior**: Fully autonomous operation
- **Strategy**: Resource management and team coordination
- **Communication**: Server-mediated only

## Development Philosophy

The Zappy project emphasizes:
- **Network Programming**: Multi-client server architecture
- **Real-time Systems**: Efficient event handling and state management
- **Game Design**: Balanced mechanics promoting strategic gameplay
- **Team Collaboration**: Coordinated development across multiple components

## Future Enhancements

Potential improvements and extensions:
- Advanced AI strategies and machine learning integration
- Enhanced 3D graphics and visual effects
- Tournament mode with leaderboards
- Replay system for game analysis
- Web-based spectator interface

---

*"The game must go on, and the elevation must be achieved!"* - Inspired by the Hitchhiker's Guide to the Galaxy