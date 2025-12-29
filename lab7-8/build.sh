echo "Building HTML Boolean Search System..."

mkdir -p obj bin data/html_documents

g++ -std=c++11 -I./include -c src/utils.cpp -o obj/utils.o
g++ -std=c++11 -I./include -c src/tokenizer.cpp -o obj/tokenizer.o
g++ -std=c++11 -I./include -c src/document_parser.cpp -o obj/document_parser.o
g++ -std=c++11 -I./include -c src/boolean_index.cpp -o obj/boolean_index.o
g++ -std=c++11 -I./include -c src/main.cpp -o obj/main.o

g++ obj/utils.o obj/tokenizer.o obj/document_parser.o \ obj/boolean_index.o obj/main.o -o bin/html_bool_search

echo "Build completed!"
echo "Executable: bin/html_bool_search"
echo ""
echo "Usage examples:"
echo "  ./bin/html_bool_search demo                    
echo "  ./bin/html_bool_search build data/html_documents index.idx  
echo "  ./bin/html_bool_search search index.idx rock   
echo "  ./bin/html_bool_search stats                   