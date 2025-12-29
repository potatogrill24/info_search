CC = g++
CFLAGS = -std=c++11 -O3 -Wall -Wextra -march=native
TARGET = zipf_analyzer
SOURCES = zipf_law.cpp

all: $(TARGET)

$(TARGET): $(SOURCES)
	$(CC) $(CFLAGS) -o $(TARGET) $(SOURCES) -lm

debug:
	$(CC) $(CFLAGS) -g -o $(TARGET)_debug $(SOURCES) -lm

release:
	$(CC) $(CFLAGS) -O3 -ffast-math -o $(TARGET)_release $(SOURCES) -lm

clean:
	rm -f $(TARGET) $(TARGET)_debug $(TARGET)_release *.dat *.txt *.gp *.png

run: $(TARGET)
	./$(TARGET) lyrics_corpus/

run-musicbrainz: $(TARGET)
	./$(TARGET) musicbrainz_corpus/

test: $(TARGET)
	./$(TARGET) test_data/

plot:
	gnuplot plot_zipf.gp

.PHONY: all clean run plot