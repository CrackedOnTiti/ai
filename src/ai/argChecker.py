# import sys
# from config import Config

# def helper(args):
#     if len(args) == 2:
#         if args[1] == "-help":
#             print("./zappy_ai help\nUSAGE: ./zappy_ai -p port -n name -h machin")
#             print("\noption      description")
#             print("----------  -----------------------------------")
#             print("-p port     port number")
#             print("-n name     name of the team")
#             print("-h machine  name of the machine; localhost by default")
#             sys.exit(0)

# def flagChecker(args):
#     if args[1] == "-p" and args[3] == "-n" and args[5] == "-h":
#         return 1
#     return 0

# def inputCleaner(args):
#     if len(args) != 7:
#         print("Error: Invalid number of arguments.")
#         sys.exit(84)
#     if flagChecker(args) != 1:
#         print("Error: Arguments must be in format '-p port -n name -h machine'")
#         sys.exit(84)

#     try:
#         port = int(args[2])
#     except ValueError:
#         print("Error: Port must be an integer.")
#         sys.exit(84)
#     name = args[4]
#     machineInput = args[6]
#     if machineInput.lower() == "localhost":
#         machine = "127.0.0.1"
#     else:
#         machine = machineInput
#     return Config(port=port, name=name, machine=machine)

import sys
from config import Config

def helper(args):
    if len(args) == 2:
        if args[1] == "-help" or args[1] == "help":
            print("USAGE: ./zappy_ai -p port -n name -h machine")
            print("")
            print("option     description")
            print("-p port    port number")
            print("-n name    name of the team")
            print("-h machine name of the machine; localhost by default")
            sys.exit(0)

def flagChecker(args):
    if len(args) == 7 and args[1] == "-p" and args[3] == "-n" and args[5] == "-h":
        return 1
    # Also accept different orders (more flexible)
    valid_flags = ["-p", "-n", "-h"]
    flags_found = []
    for i in range(1, len(args), 2):
        if i < len(args) and args[i] in valid_flags:
            flags_found.append(args[i])
    
    if len(set(flags_found)) == 3 and len(args) == 7:  # All 3 unique flags present
        return 1
    return 0

def inputCleaner(args):
    if len(args) != 7:
        print("Error: Invalid number of arguments.")
        print("Usage: ./zappy_ai -p port -n name -h machine")
        sys.exit(84)
    
    if flagChecker(args) != 1:
        print("Error: Arguments must include -p port -n name -h machine")
        sys.exit(84)
    
    # Parse arguments more flexibly
    port = None
    name = None
    machine = None
    
    for i in range(1, len(args), 2):
        if i + 1 < len(args):
            flag = args[i]
            value = args[i + 1]
            
            if flag == "-p":
                try:
                    port = int(value)
                except ValueError:
                    print("Error: Port must be an integer.")
                    sys.exit(84)
            elif flag == "-n":
                name = value
            elif flag == "-h":
                machine = value if value.lower() != "localhost" else "127.0.0.1"
    
    if port is None or name is None or machine is None:
        print("Error: Missing required arguments")
        sys.exit(84)
    
    return Config(port=port, name=name, machine=machine)