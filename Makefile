# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    Makefile                                           :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: Zappy Team <zappy@epitech.eu>              +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2025/05/26 00:00:00 by zappy           #+#    #+#              #
#    Updated: 2025/05/26 00:00:00 by zappy          ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

# ================================ COLORS ==================================== #
RESET		= \033[0m
BOLD		= \033[1m
RED			= \033[31m
GREEN		= \033[32m
YELLOW		= \033[33m
BLUE		= \033[34m
MAGENTA		= \033[35m
CYAN		= \033[36m
WHITE		= \033[37m

# ============================== PROJECT INFO =============================== #
NAME_SERVER	= zappy_server
NAME_GUI	= zappy_gui
NAME_AI		= zappy_ai

# =============================== DIRECTORIES ============================== #
SRC_DIR		= src
OBJ_DIR		= obj
INC_DIR		= include

SERVER_SRC_DIR	= $(SRC_DIR)/server
GUI_SRC_DIR		= $(SRC_DIR)/gui
AI_SRC_DIR		= $(SRC_DIR)/ai

SERVER_OBJ_DIR	= $(OBJ_DIR)/server
GUI_OBJ_DIR		= $(OBJ_DIR)/gui
AI_OBJ_DIR		= $(OBJ_DIR)/ai

# ================================ COMPILERS ================================= #
CC			= gcc
CXX			= g++
PYTHON		= python3

# ================================= FLAGS ==================================== #
CFLAGS		= -Wall -Wextra -Werror -std=c99
CXXFLAGS	= -Wall -Wextra -Werror -std=c++17
LDFLAGS		= 

# Network flags for server
SERVER_CFLAGS	= $(CFLAGS) -D_GNU_SOURCE
SERVER_LDFLAGS	= $(LDFLAGS)

# SFML flags for GUI
GUI_CXXFLAGS	= $(CXXFLAGS) `pkg-config --cflags sfml-all 2>/dev/null || echo ""`
GUI_LDFLAGS		= $(LDFLAGS) `pkg-config --libs sfml-all 2>/dev/null || echo "-lsfml-graphics -lsfml-window -lsfml-system"`

# ============================ INCLUDE DIRECTORIES ========================= #
INCLUDES	= 
ifneq ($(wildcard $(INC_DIR)),)
	INCLUDES += -I$(INC_DIR)
endif
ifneq ($(wildcard $(SERVER_SRC_DIR)/include),)
	INCLUDES += -I$(SERVER_SRC_DIR)/include
endif
ifneq ($(wildcard $(GUI_SRC_DIR)/include),)
	INCLUDES += -I$(GUI_SRC_DIR)/include
endif

# ================================= SOURCES ================================== #
SERVER_SRCS	= $(shell find $(SERVER_SRC_DIR) -name "*.c" 2>/dev/null || true)
GUI_SRCS	= $(shell find $(GUI_SRC_DIR) -name "*.cpp" 2>/dev/null || true)
AI_SRCS		= $(shell find $(AI_SRC_DIR) -name "*.py" 2>/dev/null || true)

# ================================= OBJECTS ================================== #
SERVER_OBJS	= $(SERVER_SRCS:$(SERVER_SRC_DIR)/%.c=$(SERVER_OBJ_DIR)/%.o)
GUI_OBJS	= $(GUI_SRCS:$(GUI_SRC_DIR)/%.cpp=$(GUI_OBJ_DIR)/%.o)

# ================================== RULES =================================== #

.PHONY: all clean fclean re server gui ai help

# Default target
all: banner $(NAME_SERVER) $(NAME_GUI) $(NAME_AI)
	@echo "$(GREEN)$(BOLD)✨ All components compiled successfully!$(RESET)"
	@echo "$(CYAN)📦 Binaries created: $(WHITE)$(NAME_SERVER) $(NAME_GUI) $(NAME_AI)$(RESET)"

# Individual targets
server: banner $(NAME_SERVER)
	@echo "$(GREEN)$(BOLD)🖥️  Server compiled successfully!$(RESET)"

gui: banner $(NAME_GUI)
	@echo "$(GREEN)$(BOLD)🎮 GUI compiled successfully!$(RESET)"

ai: banner $(NAME_AI)
	@echo "$(GREEN)$(BOLD)🤖 AI prepared successfully!$(RESET)"

# Server compilation
$(NAME_SERVER): $(SERVER_OBJS) | check_server_sources
	@echo "$(YELLOW)$(BOLD)🔗 Linking server...$(RESET)"
	@$(CC) $(SERVER_OBJS) -o $@ $(SERVER_LDFLAGS)
	@echo "$(GREEN)✅ $(NAME_SERVER) created$(RESET)"

# GUI compilation
$(NAME_GUI): $(GUI_OBJS) | check_gui_sources
	@echo "$(YELLOW)$(BOLD)🔗 Linking GUI...$(RESET)"
	@$(CXX) $(GUI_OBJS) -o $@ $(GUI_LDFLAGS)
	@echo "$(GREEN)✅ $(NAME_GUI) created$(RESET)"

# AI preparation
$(NAME_AI): check_ai_sources
	@echo "$(YELLOW)$(BOLD)🐍 Preparing Python AI...$(RESET)"
	@echo "#!/bin/bash" > $(NAME_AI)
	@echo "# Zappy AI Launcher" >> $(NAME_AI)
	@echo "cd \$$(dirname \$$0)" >> $(NAME_AI)
	@echo "exec $(PYTHON) src/ai/main.py \"\$$@\"" >> $(NAME_AI)
	@chmod +x $(NAME_AI)
	@echo "$(GREEN)✅ $(NAME_AI) launcher created$(RESET)"

# Object compilation rules
$(SERVER_OBJ_DIR)/%.o: $(SERVER_SRC_DIR)/%.c
	@mkdir -p $(dir $@)
	@echo "$(BLUE)🔨 Compiling $(notdir $<)...$(RESET)"
	@$(CC) $(SERVER_CFLAGS) $(INCLUDES) -c $< -o $@

$(GUI_OBJ_DIR)/%.o: $(GUI_SRC_DIR)/%.cpp
	@mkdir -p $(dir $@)
	@echo "$(BLUE)🔨 Compiling $(notdir $<)...$(RESET)"
	@$(CXX) $(GUI_CXXFLAGS) $(INCLUDES) -c $< -o $@

# Source verification
check_server_sources:
	@if [ -z "$(SERVER_SRCS)" ]; then \
		echo "$(RED)$(BOLD)❌ No C source files found in $(SERVER_SRC_DIR)$(RESET)"; \
		exit 1; \
	fi

check_gui_sources:
	@if [ -z "$(GUI_SRCS)" ]; then \
		echo "$(RED)$(BOLD)❌ No C++ source files found in $(GUI_SRC_DIR)$(RESET)"; \
		exit 1; \
	fi

check_ai_sources:
	@if [ -z "$(AI_SRCS)" ]; then \
		echo "$(RED)$(BOLD)❌ No Python source files found in $(AI_SRC_DIR)$(RESET)"; \
		exit 1; \
	fi

# Cleaning rules
clean:
	@echo "$(YELLOW)$(BOLD)🧹 Cleaning object files...$(RESET)"
	@rm -rf $(OBJ_DIR)
	@echo "$(GREEN)✅ Object files cleaned$(RESET)"

fclean: clean
	@echo "$(YELLOW)$(BOLD)🗑️  Removing binaries...$(RESET)"
	@rm -f $(NAME_SERVER) $(NAME_GUI) $(NAME_AI)
	@echo "$(GREEN)✅ Binaries removed$(RESET)"

re: fclean all

# Banner
banner:
	@echo "$(CYAN)$(BOLD)"
	@echo "╔══════════════════════════════════════════════════════════════╗"
	@echo "║                                                              ║"
	@echo "║                       ZAPPY BUILD SYSTEM                     ║"
	@echo "║                                                              ║"
	@echo "║                          $(RED)OI HUGHIE$(CYAN)                           ║"
	@echo "║                                                              ║"
	@echo "╚══════════════════════════════════════════════════════════════╝"
	@echo "$(RESET)"
	@echo "$(RED)"
	@echo "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡄⠒⠂⢴⡢⢠⡀⢀⡀⣀⢰⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"
	@echo "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠄⠀⠠⠐⠀⢘⣸⣣⣥⣉⡘⢺⠌⠗⡻⢿⠁⠀⠀⠀⠀⠄⠐⠀⠀⠀⠀⠀⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"
	@echo "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣤⡴⢸⢿⠿⠝⡏⢹⣿⡕⣔⡆⣶⡄⠀⠀⠀⠀⠠⠀⠂⠀⠀⠀⠀⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"
	@echo "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⠜⠊⢀⣠⠒⣾⢥⡾⣷⣼⣟⡼⢻⣿⡆⠀⠀⠀⠀⠀⠄⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"
	@echo "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠘⡀⡀⡚⡌⠽⡣⣿⣯⣝⣕⣽⣻⠇⠀⠀⠀⠀⠀⠀⠌⠀⠀⠀⡁⠀⠀⠀⠀⠀⠀⣀⡠⣴⢶⣶⣖⢦⡱⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"
	@echo "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢁⢁⠲⠀⠟⡿⢨⣿⣿⣯⣿⢧⡝⡰⠀⠀⠠⠀⠀⠀⠀⠀⠀⠐⠀⢂⠀⠀⠀⢀⠳⣜⣳⣭⣿⣻⣮⠷⡱⠱⡀⠀⠀⠀⠀⣀⠄⣾⣿⣶⣤⠀⠀⠀"
	@echo "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡈⡄⡄⠦⡾⣜⢯⣿⣿⣿⣿⣹⢳⠄⠀⠀⠄⠀⠀⠀⠀⠀⠀⠌⠐⠀⠀⠀⠀⢀⠳⡾⣵⣾⠟⠛⢉⣀⣤⣁⣨⠡⠀⠀⢠⡉⠀⣼⣿⣿⠏⠀⠀⠀"
	@echo "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡃⠃⡀⠃⣄⡤⠻⢸⣿⣿⣿⣿⡇⡇⠼⠀⠀⠀⠘⠀⠀⠀⠀⠀⠀⠀⠀⠠⢀⠀⠀⠛⠃⠇⣿⠤⠜⣠⠀⣀⡼⣇⠧⠀⠘⠿⢃⢸⣿⠿⠛⠀⢀⠀⠀"
	@echo "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⢋⠃⣀⢩⢲⠳⡾⣿⣿⣦⣾⣿⡧⠉⠀⠀⠈⠀⡐⠀⠀⠀⠀⠀⠤⠑⡠⢂⠄⠀⢁⡀⠀⣼⣳⢧⣤⣽⣻⣿⣽⢊⠁⡀⠨⠣⠛⠁⡀⠂⠌⡀⠂⠄"
	@echo "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢉⢀⠤⣤⢠⡿⣼⣯⣽⣟⣞⡿⠲⠁⠀⠀⠀⠀⠀⠀⠀⠀⠠⡘⣐⠣⠔⣃⣤⠀⣳⢤⢃⢯⣳⣁⢿⣿⣿⣿⣏⡖⠠⠀⠀⠀⡀⡐⢀⠡⠐⠠⢁⠂"
	@echo "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠌⠃⢃⠘⠃⠚⡉⡛⣇⠛⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣧⣀⣮⣥⣾⣭⣕⡆⠘⣫⠈⣚⣡⣦⣾⣿⣿⣿⡳⢎⡁⠂⠀⠀⠄⡀⠆⡐⢈⡐⠂⠌"
	@echo "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠂⠙⠀⠙⠢⠑⠌⠌⠀⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⢐⣨⣗⠳⣿⣯⡽⡿⣿⣿⣿⣄⠣⠁⠉⠒⠩⠉⢡⢯⣗⣏⠣⢀⠁⠀⠀⠌⡐⠤⠐⠀⢄⠃⠌"
	@echo "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠀⠄⡀⢀⡀⠀⡀⠀⠀⠀⠀⢀⠀⠆⠀⢀⡠⢴⢻⣿⣿⣧⠷⠉⠚⠒⠊⠛⠿⠿⠂⠡⢀⢒⣂⣴⣿⣟⠮⠄⢡⠂⠠⠀⠀⠀⠐⠂⠠⢁⠢⠌⢂"
	@echo "⠀⠀⠀⠀⠀⠀⠀⠠⠐⡈⡀⠂⠌⡐⠠⡁⢄⠡⠄⣀⠈⠀⠷⠀⠈⠀⣴⠃⡐⣮⣽⡿⠋⠁⠠⡐⠄⡂⢂⠐⠀⠀⠀⠀⠈⢘⡿⡿⠟⠈⠠⠎⡅⢬⣑⠢⠀⡈⢀⠀⡀⠀⠠⢾⣾"
	@echo "⠀⠀⠀⠀⠀⠐⠠⠁⠤⢀⠁⢃⠒⠤⡑⡈⠆⡱⣈⠔⡠⠄⠀⠠⠀⠄⡿⢱⣷⢮⠂⠀⣄⢎⡱⠈⠐⡀⠂⠄⢂⡐⢄⠢⢄⠠⣀⠀⡀⠉⢀⠃⡈⢀⠈⠠⠀⢀⠀⠀⠀⠀⠀⠀⠀"
	@echo "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠂⠌⡀⠊⠔⢡⡑⢎⠴⣀⢋⠴⣈⠆⡑⢢⢶⣶⣷⣷⠃⠠⣝⠾⡌⠀⠀⠐⠠⡁⢎⠰⡌⣆⠳⣌⠳⣄⠓⡄⢣⠀⢆⡐⠢⠌⠤⡁⢆⠠⣁⢂⠡⢈⠄⢃"
	@echo "⠀⠀⠀⠀⠀⠀⠀⠀⠄⠀⡀⠀⢁⠈⠄⡐⢈⠒⠌⢎⡒⣌⠳⠥⠊⡜⣬⠳⠁⢠⡝⣞⡻⠆⠀⠀⢡⢢⡱⢎⡷⣹⢎⡿⣜⢧⢏⡵⡘⢤⢋⡖⡼⣡⢟⡴⣱⢪⡕⣎⢦⡹⡄⢎⠰"
	@echo "⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⠀⠌⠀⠀⠂⢀⢠⣤⣬⠀⢉⠄⠛⠚⠳⠥⠀⠀⣄⠳⣼⢯⣟⠁⠀⢠⢃⠶⣹⢏⡾⣭⣿⣳⣽⣮⢟⡴⣹⢎⡷⣞⣳⢯⣟⣾⣭⡷⣽⢎⡷⣣⠝⡌⢂"
	@echo "⠀⠀⠀⠀⣶⣿⡄⠀⠀⢀⠠⠀⠈⠀⢠⣾⠺⣿⣿⣿⡄⢈⠡⡉⠂⠀⣄⢣⣬⢻⣼⣟⡾⠀⠀⢂⠎⡝⣧⢿⣽⣷⣿⣿⣿⣾⢯⡿⣭⣟⣷⣻⣽⣿⣿⡷⢯⠽⢳⢯⢷⣙⠎⡔⠁"
	@echo "⠀⠀⠀⠀⠈⢛⣴⣿⡄⠀⢀⠠⠁⠀⠈⢩⢷⣮⣿⡿⢷⡀⠁⠀⣄⠳⣬⢷⡾⣯⣷⢻⠜⠀⠀⠠⠘⡈⢇⠛⡾⣹⢟⣾⢻⡽⣏⡿⣵⢾⣾⣿⣿⣿⣿⣿⣇⠂⠀⢙⢮⠣⠍⡀⠀"
	@echo "⣴⣦⣤⡀⠀⠀⠙⢳⣿⣧⣄⠀⠈⠴⣲⣌⢛⣻⣿⣿⣗⡂⠠⢸⣔⣻⢾⣻⣿⢯⡝⡃⠀⠀⠀⠀⠁⠐⠂⡑⢤⣡⢚⡜⣣⠟⡼⡹⢞⡿⣻⣿⣿⣿⣿⢾⡜⢧⡒⢬⢂⠃⠄⠀⢠"
	@echo "⠈⠛⠻⣻⣿⣦⣀⠀⠙⢿⣿⣷⣶⣄⠿⠿⠀⣱⢿⣿⡿⣵⠈⢓⡾⣽⡟⣧⢛⠎⠀⠀⠀⠐⠀⠌⡰⠍⢾⣱⡞⡜⢣⠘⣤⣙⠶⣽⣾⣵⣿⡽⣟⡿⣹⠮⡝⢣⠜⡂⠆⠠⠀⠀⡖"
	@echo "⠀⠀⠀⠙⠛⠻⣿⡶⣤⣨⣿⣿⡿⣿⣖⠀⠠⣋⣼⣿⣷⡋⠄⢈⠳⣏⠷⡉⠎⠀⠀⠀⠀⠀⡀⢄⠡⣄⡌⣉⠓⠳⣬⢶⣭⣟⣦⣝⠻⣿⢿⣷⣿⢧⣏⠶⣑⠎⡴⢁⠢⢀⠀⠰⡱"
	@echo "⣠⣤⣂⣀⢂⣀⠈⠚⢕⣿⣿⣿⡇⡿⣵⠀⢰⣿⣿⣿⣿⣟⡄⠀⠰⠈⠂⠀⠀⠀⠀⠀⠀⠐⠈⠆⡳⣎⢿⡵⢪⡴⣌⣍⡳⣿⣿⣿⣿⡴⣫⢽⡞⡿⣜⡻⡜⡜⡰⠃⠔⡀⠀⠢⡝"
	@echo "⠙⠛⠛⠼⠿⠿⣿⣶⣾⣿⣿⡿⣹⣇⣿⡇⠨⣸⣿⣿⣿⣿⣞⠀⠀⠄⠀⠀⠄⠡⠈⠠⠘⢤⡙⢦⢢⡙⠂⠌⣱⢯⣟⣾⣷⣭⣟⡿⣿⣿⣷⣿⣾⣝⣮⢳⡝⡲⣁⠣⢀⠀⠀⠑⡸"
	@echo "⣌⠫⡝⢢⣓⡴⣀⠉⠻⣿⡿⣽⣿⣿⣿⣿⡀⠨⣝⡻⠭⡗⣡⢆⡀⠠⠀⠄⢂⠐⢠⡑⡬⢶⣹⠦⣅⣬⣟⣽⣲⣝⡿⣿⣿⣿⣾⣽⣹⢿⣿⣿⣿⣿⣎⢷⣩⠓⡤⠃⠀⠀⢀⠠⢑"
	@echo "⢰⡩⣜⣣⠷⣩⣗⣳⢦⣌⣚⠿⠿⢿⣿⠿⢃⠀⠹⠽⣏⡵⣣⢶⡭⠀⡡⠈⠄⡌⢦⣱⢭⢷⣋⣾⢿⣿⣾⣿⣿⣾⣽⢯⣝⣻⢾⣳⣯⡿⣟⡿⣿⣿⣞⡳⣌⠓⠤⠁⠀⡐⢂⠀⠌"
	@echo "⢢⡝⣮⢵⣻⡵⣾⡽⣿⣾⠿⠓⠙⠀⠠⢀⠈⣷⠀⠻⣑⠖⡾⣫⣾⡁⠤⣉⠲⣭⢷⣽⣻⣷⣿⣽⣿⣿⣿⣿⣿⣿⣟⡿⣾⣹⣞⡿⣶⢿⣹⢽⣫⠷⣏⠷⡨⠑⠂⠁⢠⠑⡊⠄⢈"
	@echo "⣣⣛⣞⣯⣳⠿⠋⠋⢉⡀⡀⠠⢀⠐⠠⢂⠐⢺⡆⠈⢭⠫⢞⡮⣕⡷⠐⡄⠣⠘⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣟⣾⣷⣯⢿⡝⣾⡹⡞⡵⡛⣌⠣⠁⠈⢠⠒⡍⢎⠱⡁⠀"
	@echo "⡳⠽⠊⠁⢀⡠⣔⡺⢶⣹⣥⠐⠠⢈⠐⠠⠈⠄⣷⠀⢣⡙⢮⡽⣽⣟⡆⢅⢻⣷⣤⣤⣭⣽⣛⣛⣛⣻⠿⢿⣿⣿⣿⣿⣿⣿⣿⣟⣾⡱⢫⡕⢣⠑⡀⠂⢀⡜⠄⠋⠀⠈⢀⠀⡀"
	@echo "⠀⡀⡔⣬⢧⣳⣽⣻⣯⣷⣿⡄⠂⠄⢂⠁⢈⠐⠈⠁⠐⣎⠦⡹⣷⣫⣿⣀⢰⢍⣛⠻⠿⣿⣿⣿⢟⣭⣭⣷⣖⣦⣭⣭⣭⣼⣭⣮⣥⣭⣥⣬⣤⣲⣤⢦⣄⣤⢠⢆⡱⡌⢆⡜⡰"
	@echo "⢰⡱⡽⢮⣷⢯⣟⣷⡿⣯⣿⡇⠀⡈⠄⢂⠠⠀⡐⠌⡄⢣⠠⢑⣺⣻⣽⣷⣞⣳⣿⢟⡳⠒⣈⣤⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣟⣿⣺⣽⢮⣳⡝⡶⣌⠱"
	@echo "⣜⡳⣟⢿⣞⣿⢿⣻⣿⡿⣿⣧⠀⠠⠐⠠⠀⠐⣈⠒⠬⡈⢆⠡⢓⣛⣱⠿⠿⠛⣈⣥⣶⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⣿⣿⢿⣻⣿⣻⢯⡷⣽⠳⣌⠓"
	@echo "⣺⢽⣞⣯⣾⣿⣿⣿⣿⣻⣿⣿⡆⠐⡀⢁⠂⡀⠄⡙⢢⠙⠢⠈⣐⣤⣶⣶⣿⣘⢿⡿⡿⡛⢻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⢿⢾⢻⠳⠝⡜⢣⠙⠄⢋⠠⠈"
	@echo "⡾⣽⢾⣿⣷⣿⣿⣽⣿⣿⣿⣿⡧⢦⡐⠀⡎⡀⠄⠀⡁⢚⠀⣾⣯⢻⠿⠛⠋⢈⠀⢉⣡⣾⣿⣿⣫⣿⣿⣿⣿⣿⣿⣿⣿⢋⡿⠛⣋⣍⢀⡤⣤⢠⣤⣀⣄⣐⣀⣀⣈⣀⣀⣀⢀"
	@echo "⢿⣽⣻⢾⣽⢾⣿⣿⣽⣿⣿⣿⣿⡜⣿⣆⠡⠐⢈⠀⠄⡀⠈⠐⠀⠂⡀⠁⢌⣄⣴⣿⣿⡿⠿⢛⣿⣿⣿⣿⣿⣿⣿⡟⣵⠟⠡⢁⠈⢉⣾⣽⣛⡷⣾⣝⣮⢳⢯⣎⠷⡜⢦⡜⢢"
	@echo "⡟⣼⢳⣿⣽⢻⣿⢺⡟⣿⣯⢻⡝⢣⢹⣿⣴⡖⠀⠈⠐⢠⠁⠂⢡⠐⢠⣾⣿⣿⡟⠋⠉⣶⡄⡄⣼⣿⠛⢻⣿⣿⡏⣾⠋⠀⢰⠀⠀⣼⣿⣿⣿⣿⣷⣿⡞⣿⣦⡏⢻⢹⣶⠘⢣"
	@echo "⠽⣱⢏⡾⣽⢳⣫⠟⣽⢣⡛⢮⠑⡋⠄⢿⣧⠀⠀⠀⠐⠀⢈⠐⡠⣶⡝⣿⠿⣻⢕⣵⣾⡯⠧⢀⣠⣴⣾⣿⣻⠯⠙⠀⠠⢈⠸⠀⢰⣿⣿⣿⣿⣿⣿⣿⣿⣭⣟⡻⢷⣏⣖⢫⢓"
	@echo "⠳⣩⠞⣱⢬⡓⢧⠹⢨⠑⡈⠀⠐⠀⠀⣬⡷⣷⣤⣦⣄⠀⢀⢺⣿⠎⡋⠐⣨⡶⣿⡿⠛⢀⣤⣾⡟⠉⣩⣐⡶⣶⣦⣔⠠⠀⡘⢀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣟⣮⡽⢮⢧"
	@echo "⠱⢡⠚⢡⠂⡑⠂⠁⠀⠀⡀⣄⠲⣞⣻⢛⣼⢿⣻⡟⠁⠠⡘⣖⢯⣎⢾⢿⠞⢟⡤⣢⣶⣿⠎⣫⣴⣿⣿⣿⣿⡷⣏⠻⣷⣄⠀⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣻⡼"
	@echo "⠐⠀⠁⠀⠀⠀⠀⡀⢠⠓⡜⢤⡛⣜⠦⣏⡳⣭⣛⠀⢀⠲⣙⡞⣿⣿⣶⣭⣾⣿⣧⣛⣭⣵⣾⣿⣿⣿⣿⣿⣿⣟⢾⡩⠌⢻⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢿⣽"
	@echo "⠀⠀⠀⠀⠀⠤⡑⢠⠃⡭⠘⢤⠛⣌⠞⣬⠳⡼⠁⠀⢌⡱⣭⣞⣷⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢿⣟⡾⣣⠕⠂⢸⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢿⣿⣿⡿⣟⣾"
	@echo "⠀⠀⢀⠂⢉⠰⠈⢄⠓⡰⠉⢆⡹⢄⠫⡔⡹⠄⠀⠐⡌⢲⡳⣞⣯⡿⣿⣿⡿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣾⢿⣽⡹⢥⠊⠄⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢿⣿⣿⣿⣯⣟⡿⣿⣽"
	@echo "⠀⠈⠀⢀⠂⠄⡉⠄⢊⠄⡑⢢⠐⣊⠱⡈⠅⠀⠀⠜⣈⠧⠻⣜⣷⣻⢿⡽⣿⣿⣿⣿⣿⣿⡿⣿⣻⡽⣯⢟⡶⡙⢆⠡⢀⣯⡿⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣻⢿⣿⣻⣼⢹"
	@echo "$(RESET)"
	@echo "$(MAGENTA)Building components:$(RESET)"
	@echo "$(WHITE)  🖥️  Server  (C)     → $(NAME_SERVER)$(RESET)"
	@echo "$(WHITE)  🎮 GUI     (C++)   → $(NAME_GUI)$(RESET)"
	@echo "$(WHITE)  🤖 AI      (Python) → $(NAME_AI)$(RESET)"
	@echo ""

# Help
help:
	@echo "$(CYAN)$(BOLD)Zappy Makefile Help$(RESET)"
	@echo ""
	@echo "$(YELLOW)Available targets:$(RESET)"
	@echo "  $(GREEN)make$(RESET) / $(GREEN)make all$(RESET)  - Build all components"
	@echo "  $(GREEN)make server$(RESET)       - Build only the server"
	@echo "  $(GREEN)make gui$(RESET)          - Build only the GUI"
	@echo "  $(GREEN)make ai$(RESET)           - Prepare only the AI"
	@echo "  $(GREEN)make clean$(RESET)        - Remove object files"
	@echo "  $(GREEN)make fclean$(RESET)       - Remove object files and binaries"
	@echo "  $(GREEN)make re$(RESET)           - Clean and rebuild everything"
	@echo "  $(GREEN)make help$(RESET)         - Show this help message"
	@echo ""
	@echo "$(YELLOW)Project Structure:$(RESET)"
	@echo "  $(WHITE)src/server/$(RESET)   - C source files for server"
	@echo "  $(WHITE)src/gui/$(RESET)      - C++ source files for GUI"
	@echo "  $(WHITE)src/ai/$(RESET)       - Python source files for AI"
	@echo "  $(WHITE)obj/$(RESET)          - Object files (auto-created)"
	@echo "  $(WHITE)include/$(RESET)      - Header files (optional)"