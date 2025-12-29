CC = g++
CFLAGS = -std=c++11 -I./include -Wall -Wextra -O2
LDFLAGS = 

SRC_DIR = src
OBJ_DIR = obj
BIN_DIR = bin

SOURCES = $(wildcard $(SRC_DIR)/*.cpp)
OBJECTS = $(patsubst $(SRC_DIR)/%.cpp,$(OBJ_DIR)/%.o,$(SOURCES))
TARGET = $(BIN_DIR)/bool_search

all: $(TARGET)

$(TARGET): $(OBJECTS)
	@mkdir -p $(BIN_DIR)
	$(CC) $(OBJECTS) -o $(TARGET) $(LDFLAGS)

$(OBJ_DIR)/%.o: $(SRC_DIR)/%.cpp
	@mkdir -p $(OBJ_DIR)
	$(CC) $(CFLAGS) -c $< -o $@


build: $(TARGET)
	@echo "System built successfully"

clean:
	rm -rf $(OBJ_DIR) $(BIN_DIR)
	@echo "Clean completed"

run: $(TARGET)
	./$(BIN_DIR)/bool_search demo


$(OBJ_DIR)/main.o: $(SRC_DIR)/main.cpp \
                   include/boolean_index.h \
                   include/document_parser.h \
                   include/tokenizer.h \
                   include/utils.h

$(OBJ_DIR)/boolean_index.o: $(SRC_DIR)/boolean_index.cpp \
                            include/boolean_index.h \
                            include/utils.h

$(OBJ_DIR)/document_parser.o: $(SRC_DIR)/document_parser.cpp \
                              include/document_parser.h \
                              include/utils.h

$(OBJ_DIR)/tokenizer.o: $(SRC_DIR)/tokenizer.cpp \
                        include/tokenizer.h \
                        include/utils.h

$(OBJ_DIR)/utils.o: $(SRC_DIR)/utils.cpp \
                    include/utils.h

.PHONY: all build clean run