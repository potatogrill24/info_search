#include <iostream>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cctype>
#include <cmath>
#include <ctime>
#include <dirent.h>
#include <sys/stat.h>


#define MAX_WORD_LEN 256
#define MAX_WORDS 1500000
#define MAX_FILES 15000
#define HASH_TABLE_SIZE 150003
#define MAX_PATH_LEN 512




struct WordEntry {
    char word[MAX_WORD_LEN];
    int frequency;
    WordEntry* next;  
};


struct Statistics {
    int total_words;
    int unique_words;
    int total_tokens;
    double processing_time;
    double memory_used_mb;
};


struct Point {
    int rank;
    double frequency;
    double log_rank;
    double log_frequency;
};


class HashTable {
private:
    WordEntry** table;
    int size;
    int count;
    
    
    unsigned int hash(const char* str) const {
        unsigned int hash = 5381;
        int c;
        while ((c = *str++)) {
            hash = ((hash << 5) + hash) + c; 
        }
        return hash % size;
    }
    
    
    void toLower(char* str) {
        for (int i = 0; str[i]; i++) {
            str[i] = tolower((unsigned char)str[i]);
        }
    }
    
    
    bool isStopWord(const char* word) {
        const char* stop_words[] = {
            "the", "and", "to", "of", "in", "for", "on", "with", "at", "by",
            "a", "is", "that", "it", "i", "this", "be", "as", "are", "was",
            "you", "he", "she", "they", "we", "my", "your", "his", "her",
            "their", "our", "me", "him", "them", "us", "это", "и", "в", "на",
            "с", "по", "о", "у", "за", "из", "от", "до", "не", "но", "а",
            "же", "ли", "бы", "что", "как", "все", "его", "ее", "им", "них",
            nullptr
        };
        
        for (int i = 0; stop_words[i] != nullptr; i++) {
            if (strcmp(word, stop_words[i]) == 0) {
                return true;
            }
        }
        return false;
    }
    
public:
    HashTable(int table_size = HASH_TABLE_SIZE) {
        size = table_size;
        count = 0;
        table = new WordEntry*[size];
        for (int i = 0; i < size; i++) {
            table[i] = nullptr;
        }
    }
    
    ~HashTable() {
        clear();
        delete[] table;
    }
    
    
    void addWord(const char* word) {
        if (strlen(word) < 2 || isStopWord(word)) {
            return;
        }
        
        char lower_word[MAX_WORD_LEN];
        strcpy(lower_word, word);
        toLower(lower_word);
        
        unsigned int index = hash(lower_word);
        WordEntry* entry = table[index];
        
        
        while (entry != nullptr) {
            if (strcmp(entry->word, lower_word) == 0) {
                entry->frequency++;
                return;
            }
            entry = entry->next;
        }
        
        
        entry = new WordEntry();
        strcpy(entry->word, lower_word);
        entry->frequency = 1;
        entry->next = table[index];
        table[index] = entry;
        count++;
    }
    
    
    void getAllEntries(WordEntry** entries, int* num_entries) {
        *num_entries = 0;
        
        for (int i = 0; i < size; i++) {
            WordEntry* entry = table[i];
            while (entry != nullptr) {
                entries[*num_entries] = entry;
                (*num_entries)++;
                entry = entry->next;
            }
        }
    }
    
    
    static void quickSort(WordEntry** entries, int left, int right) {
        if (left >= right) return;
        
        int i = left;
        int j = right;
        WordEntry* pivot = entries[(left + right) / 2];
        
        while (i <= j) {
            while (entries[i]->frequency > pivot->frequency) i++;
            while (entries[j]->frequency < pivot->frequency) j--;
            
            if (i <= j) {
                WordEntry* temp = entries[i];
                entries[i] = entries[j];
                entries[j] = temp;
                i++;
                j--;
            }
        }
        
        if (left < j) quickSort(entries, left, j);
        if (i < right) quickSort(entries, i, right);
    }
    
    
    void clear() {
        for (int i = 0; i < size; i++) {
            WordEntry* entry = table[i];
            while (entry != nullptr) {
                WordEntry* next = entry->next;
                delete entry;
                entry = next;
            }
            table[i] = nullptr;
        }
        count = 0;
    }
    
    int getCount() const { return count; }
};


class ZipfAnalyzer {
private:
    HashTable hash_table;
    Statistics stats;
    Point* points;
    int points_count;
    
    
    char* readFile(const char* filename, long* file_size) {
        FILE* file = fopen(filename, "rb");
        if (!file) return nullptr;
        
        fseek(file, 0, SEEK_END);
        *file_size = ftell(file);
        fseek(file, 0, SEEK_SET);
        
        char* content = new char[*file_size + 1];
        fread(content, 1, *file_size, file);
        content[*file_size] = '\0';
        
        fclose(file);
        return content;
    }
    
    
    void tokenizeText(const char* text) {
        char word[MAX_WORD_LEN];
        int word_len = 0;
        
        for (int i = 0; text[i] != '\0'; i++) {
            char c = text[i];
            
            if (isalpha((unsigned char)c) || c == '\'' || c == '-') {
                if (word_len < MAX_WORD_LEN - 1) {
                    word[word_len++] = c;
                }
            } else {
                if (word_len > 0) {
                    word[word_len] = '\0';
                    hash_table.addWord(word);
                    stats.total_tokens++;
                    word_len = 0;
                }
            }
        }
        
        
        if (word_len > 0) {
            word[word_len] = '\0';
            hash_table.addWord(word);
            stats.total_tokens++;
        }
    }
    
    
    void getFilesInDirectory(const char* dir_path, char*** files, int* count) {
        DIR* dir = opendir(dir_path);
        if (!dir) return;
        
        struct dirent* entry;
        char** file_list = new char*[MAX_FILES];
        *count = 0;
        
        while ((entry = readdir(dir)) != nullptr && *count < MAX_FILES) {
            if (entry->d_name[0] == '.') continue;
            
            char full_path[MAX_PATH_LEN];
            snprintf(full_path, MAX_PATH_LEN, "%s/%s", dir_path, entry->d_name);
            
            struct stat stat_buf;
            if (stat(full_path, &stat_buf) == 0) {
                if (S_ISREG(stat_buf.st_mode)) {
                    
                    const char* ext = strrchr(entry->d_name, '.');
                    if (ext && (strcmp(ext, ".txt") == 0 || 
                               strcmp(ext, ".html") == 0 ||
                               strcmp(ext, ".htm") == 0)) {
                        file_list[*count] = new char[strlen(full_path) + 1];
                        strcpy(file_list[*count], full_path);
                        (*count)++;
                    }
                } else if (S_ISDIR(stat_buf.st_mode)) {
                    
                    char** sub_files;
                    int sub_count;
                    getFilesInDirectory(full_path, &sub_files, &sub_count);
                    
                    for (int i = 0; i < sub_count && *count < MAX_FILES; i++) {
                        file_list[*count] = sub_files[i];
                        (*count)++;
                    }
                    delete[] sub_files;
                }
            }
        }
        
        closedir(dir);
        *files = file_list;
    }
    
    
    double zipfLaw(int rank, double C, double alpha = 1.0) {
        return C / pow((double)rank, alpha);
    }
    
    
    double mandelbrotLaw(int rank, double C, double alpha = 1.0, double beta = 2.7) {
        return C / pow((double)rank + beta, alpha);
    }
    
    
    void fitZipfParameters(double* C, double* alpha) {
        double sum_log_rank = 0.0;
        double sum_log_freq = 0.0;
        double sum_log_rank_sq = 0.0;
        double sum_log_rank_freq = 0.0;
        int n = points_count;
        
        
        if (n > 1000) n = 1000;
        
        for (int i = 0; i < n; i++) {
            double log_r = log(points[i].rank);
            double log_f = log(points[i].frequency);
            
            sum_log_rank += log_r;
            sum_log_freq += log_f;
            sum_log_rank_sq += log_r * log_r;
            sum_log_rank_freq += log_r * log_f;
        }
        
        
        double denom = n * sum_log_rank_sq - sum_log_rank * sum_log_rank;
        if (fabs(denom) > 1e-10) {
            *alpha = (n * sum_log_rank_freq - sum_log_rank * sum_log_freq) / denom;
            *C = exp((sum_log_freq + *alpha * sum_log_rank) / n);
        } else {
            *alpha = 1.0;
            *C = points[0].frequency;
        }
    }
    
    
    void fitMandelbrotParameters(double* C, double* alpha, double* beta) {
        
        *C = points[0].frequency * 2.0;
        *alpha = 1.0;
        *beta = 2.7;
        
        double learning_rate = 0.01;
        int iterations = 1000;
        
        for (int iter = 0; iter < iterations; iter++) {
            double grad_C = 0.0;
            double grad_alpha = 0.0;
            double grad_beta = 0.0;
            
            
            int n = (points_count < 500) ? points_count : 500;
            
            for (int i = 0; i < n; i++) {
                int rank = points[i].rank;
                double actual = points[i].frequency;
                double predicted = mandelbrotLaw(rank, *C, *alpha, *beta);
                double error = predicted - actual;
                
                
                double denom = pow(rank + *beta, *alpha);
                grad_C += error / denom;
                grad_alpha += error * (-*C * log(rank + *beta) / denom);
                grad_beta += error * (-*alpha * *C / pow(rank + *beta, *alpha + 1));
            }
            
            
            *C -= learning_rate * grad_C / n;
            *alpha -= learning_rate * grad_alpha / n;
            *beta -= learning_rate * grad_beta / n;
            
            
            if (*C < 0.1) *C = 0.1;
            if (*alpha < 0.1) *alpha = 0.1;
            if (*alpha > 3.0) *alpha = 3.0;
            if (*beta < 0.1) *beta = 0.1;
            if (*beta > 10.0) *beta = 10.0;
        }
    }
    
public:
    ZipfAnalyzer() : points(nullptr), points_count(0) {
        memset(&stats, 0, sizeof(Statistics));
    }
    
    ~ZipfAnalyzer() {
        if (points) delete[] points;
    }
    
    
    void processDirectory(const char* dir_path) {
        clock_t start_time = clock();
        
        char** files;
        int file_count;
        getFilesInDirectory(dir_path, &files, &file_count);
        
        std::cout << "Найдено файлов: " << file_count << std::endl;
        
        for (int i = 0; i < file_count; i++) {
            if (i % 100 == 0 && i > 0) {
                std::cout << "Обработано " << i << " из " << file_count << " файлов..." << std::endl;
            }
            
            long file_size;
            char* content = readFile(files[i], &file_size);
            
            if (content) {
                tokenizeText(content);
                delete[] content;
            }
            
            delete[] files[i];
        }
        
        delete[] files;
        
        clock_t end_time = clock();
        stats.processing_time = (double)(end_time - start_time) / CLOCKS_PER_SEC;
        stats.unique_words = hash_table.getCount();
    }
    
    
    void analyzeDistribution() {
        
        WordEntry** entries = new WordEntry*[stats.unique_words];
        int num_entries;
        hash_table.getAllEntries(entries, &num_entries);
        
        
        HashTable::quickSort(entries, 0, num_entries - 1);
        
        
        points_count = num_entries;
        points = new Point[points_count];
        
        for (int i = 0; i < points_count; i++) {
            points[i].rank = i + 1;
            points[i].frequency = entries[i]->frequency;
            points[i].log_rank = log(points[i].rank);
            points[i].log_frequency = log(points[i].frequency);
        }
        
        delete[] entries;
    }
    
    
    void savePlotData(const char* filename) {
        FILE* file = fopen(filename, "w");
        if (!file) {
            std::cerr << "Ошибка открытия файла: " << filename << std::endl;
            return;
        }
        
        fprintf(file, "Rank\tFrequency\tLogRank\tLogFreq\n");
        
        for (int i = 0; i < points_count; i++) {
            fprintf(file, "%d\t%.2f\t%.6f\t%.6f\n", 
                   points[i].rank, 
                   points[i].frequency,
                   points[i].log_rank,
                   points[i].log_frequency);
        }
        
        fclose(file);
        std::cout << "Данные для графика сохранены в: " << filename << std::endl;
    }
    
    
    void saveTopWords(const char* filename, int top_n = 50) {
        FILE* file = fopen(filename, "w");
        if (!file) {
            std::cerr << "Ошибка открытия файла: " << filename << std::endl;
            return;
        }
        
        WordEntry** entries = new WordEntry*[stats.unique_words];
        int num_entries;
        hash_table.getAllEntries(entries, &num_entries);
        HashTable::quickSort(entries, 0, num_entries - 1);
        
        fprintf(file, "Rank\tWord\tFrequency\tRelative%%\n");
        
        double total = (double)stats.total_tokens;
        int n = (top_n < num_entries) ? top_n : num_entries;
        
        for (int i = 0; i < n; i++) {
            double percentage = (entries[i]->frequency / total) * 100.0;
            fprintf(file, "%d\t%s\t%d\t%.4f%%\n", 
                   i + 1, 
                   entries[i]->word, 
                   entries[i]->frequency,
                   percentage);
        }
        
        fclose(file);
        delete[] entries;
        std::cout << "Топ-" << n << " слов сохранены в: " << filename << std::endl;
    }
    
    
    void saveParameters(const char* filename) {
        FILE* file = fopen(filename, "w");
        if (!file) {
            std::cerr << "Ошибка открытия файла: " << filename << std::endl;
            return;
        }
        
        
        double zipf_C, zipf_alpha;
        fitZipfParameters(&zipf_C, &zipf_alpha);
        
        
        double mandel_C, mandel_alpha, mandel_beta;
        fitMandelbrotParameters(&mandel_C, &mandel_alpha, &mandel_beta);
        
        fprintf(file, "=== ПАРАМЕТРЫ РАСПРЕДЕЛЕНИЯ ===\n\n");
        
        fprintf(file, "Статистика корпуса:\n");
        fprintf(file, "  Всего слов (токенов): %d\n", stats.total_tokens);
        fprintf(file, "  Уникальных слов: %d\n", stats.unique_words);
        fprintf(file, "  Время обработки: %.2f сек\n", stats.processing_time);
        fprintf(file, "  Коэффициент сжатия: %.2f:1\n", 
               (double)stats.total_tokens / stats.unique_words);
        
        fprintf(file, "\nЗакон Ципфа:\n");
        fprintf(file, "  Формула: frequency = C / rank^alpha\n");
        fprintf(file, "  Параметры: C = %.4f, alpha = %.4f\n", zipf_C, zipf_alpha);
        fprintf(file, "  Ожидаемая частота 1-го слова: %.2f (реальная: %.2f)\n", 
               zipf_C, points[0].frequency);
        fprintf(file, "  Ожидаемая частота 10-го слова: %.2f (реальная: %.2f)\n",
               zipfLaw(10, zipf_C, zipf_alpha), points[9].frequency);
        
        fprintf(file, "\nЗакон Мандельброта:\n");
        fprintf(file, "  Формула: frequency = C / (rank + beta)^alpha\n");
        fprintf(file, "  Параметры: C = %.4f, alpha = %.4f, beta = %.4f\n", 
               mandel_C, mandel_alpha, mandel_beta);
        fprintf(file, "  Ожидаемая частота 1-го слова: %.2f\n",
               mandelbrotLaw(1, mandel_C, mandel_alpha, mandel_beta));
        fprintf(file, "  Ожидаемая частота 10-го слова: %.2f\n",
               mandelbrotLaw(10, mandel_C, mandel_alpha, mandel_beta));
        
        fprintf(file, "\n=== АНАЛИЗ РАСХОЖДЕНИЙ ===\n\n");
        
        fprintf(file, "Причины расхождения с законом Ципфа:\n");
        fprintf(file, "1. Ограниченный размер корпуса\n");
        fprintf(file, "2. Неоднородность текстов (тексты песен + метаданные)\n");
        fprintf(file, "3. Наличие стоп-слов и специальной лексики\n");
        fprintf(file, "4. Эффект длинного хвоста (редкие слова)\n");
        fprintf(file, "5. Влияние удаления стоп-слов\n");
        
        fprintf(file, "\nДля улучшения соответствия:\n");
        fprintf(file, "1. Увеличить размер корпуса\n");
        fprintf(file, "2. Обрабатывать тексты одного типа отдельно\n");
        fprintf(file, "3. Использовать стемминг/лемматизацию\n");
        fprintf(file, "4. Применять закон Мандельброта для лучшей аппроксимации\n");
        
        
        fprintf(file, "\n=== ПРОГНОЗ И РЕАЛЬНОСТЬ (первые 20 слов) ===\n\n");
        fprintf(file, "Rank\tWord\tReal\tZipf\tMandel\tDiffZipf\tDiffMandel\n");
        
        WordEntry** entries = new WordEntry*[stats.unique_words];
        int num_entries;
        hash_table.getAllEntries(entries, &num_entries);
        HashTable::quickSort(entries, 0, num_entries - 1);
        
        int n = (20 < num_entries) ? 20 : num_entries;
        for (int i = 0; i < n; i++) {
            double real_freq = points[i].frequency;
            double zipf_freq = zipfLaw(i+1, zipf_C, zipf_alpha);
            double mandel_freq = mandelbrotLaw(i+1, mandel_C, mandel_alpha, mandel_beta);
            
            fprintf(file, "%d\t%s\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\n",
                   i+1, entries[i]->word, real_freq, zipf_freq, mandel_freq,
                   fabs(real_freq - zipf_freq), fabs(real_freq - mandel_freq));
        }
        
        fclose(file);
        delete[] entries;
        std::cout << "Параметры законов сохранены в: " << filename << std::endl;
    }
    
    
    void generateGnuplotScript(const char* filename) {
        FILE* file = fopen(filename, "w");
        if (!file) {
            std::cerr << "Ошибка открытия файла: " << filename << std::endl;
            return;
        }
        
        
        double zipf_C, zipf_alpha;
        fitZipfParameters(&zipf_C, &zipf_alpha);
        
        double mandel_C, mandel_alpha, mandel_beta;
        fitMandelbrotParameters(&mandel_C, &mandel_alpha, &mandel_beta);
        
        fprintf(file, "# GNUplot скрипт для визуализации закона Ципфа\n");
        fprintf(file, "set terminal png size 1200,800 enhanced font 'Verdana,10'\n");
        fprintf(file, "set output 'zipf_plot.png'\n\n");
        
        fprintf(file, "set multiplot layout 2,2 title 'Анализ закона Ципфа для музыкального корпуса'\n\n");
        
        
        fprintf(file, "set title 'Распределение частот слов (линейная шкала)'\n");
        fprintf(file, "set xlabel 'Ранг слова'\n");
        fprintf(file, "set ylabel 'Частота'\n");
        fprintf(file, "set grid\n");
        fprintf(file, "plot 'plot_data.dat' using 1:2 with points pt 7 ps 0.5 lc rgb 'blue' title 'Реальные данные', \\\n");
        fprintf(file, "     %f/(x**%f) with lines lw 2 lc rgb 'red' title 'Закон Ципфа (C=%.2f, α=%.2f)', \\\n",
               zipf_C, zipf_alpha, zipf_C, zipf_alpha);
        fprintf(file, "     %f/(x+%f)**%f with lines lw 2 lc rgb 'green' title 'Закон Мандельброта (C=%.2f, α=%.2f, β=%.2f)'\n\n",
               mandel_C, mandel_beta, mandel_alpha, mandel_C, mandel_alpha, mandel_beta);
        
        
        fprintf(file, "set title 'Распределение частот слов (логарифмическая шкала)'\n");
        fprintf(file, "set logscale xy\n");
        fprintf(file, "set xlabel 'log(Ранг)'\n");
        fprintf(file, "set ylabel 'log(Частота)'\n");
        fprintf(file, "set grid\n");
        fprintf(file, "plot 'plot_data.dat' using 3:4 with points pt 7 ps 0.5 lc rgb 'blue' title 'Реальные данные', \\\n");
        fprintf(file, "     %f/(x**%f) with lines lw 2 lc rgb 'red' title 'Закон Ципфа', \\\n",
               zipf_C, zipf_alpha);
        fprintf(file, "     %f/(x+%f)**%f with lines lw 2 lc rgb 'green' title 'Закон Мандельброта'\n\n",
               mandel_C, mandel_beta, mandel_alpha);
        
        
        fprintf(file, "unset logscale\n");
        fprintf(file, "set title 'Относительная ошибка аппроксимации'\n");
        fprintf(file, "set xlabel 'Ранг слова'\n");
        fprintf(file, "set ylabel 'Ошибка (%% реального значения)'\n");
        fprintf(file, "set grid\n");
        fprintf(file, "set yrange [0:100]\n");
        
        fprintf(file, "zipf_error(x) = 100*abs((%f/(x**%f)) - column(2))/column(2)\n", zipf_C, zipf_alpha);
        fprintf(file, "mandel_error(x) = 100*abs((%f/(x+%f)**%f) - column(2))/column(2)\n\n",
               mandel_C, mandel_beta, mandel_alpha);
        
        fprintf(file, "plot 'plot_data.dat' using 1:(zipf_error($1)) with lines lw 2 lc rgb 'red' title 'Ошибка Ципфа', \\\n");
        fprintf(file, "     '' using 1:(mandel_error($1)) with lines lw 2 lc rgb 'green' title 'Ошибка Мандельброта'\n\n");
        
        
        fprintf(file, "set title 'Кумулятивное распределение частот'\n");
        fprintf(file, "set xlabel 'Ранг слова'\n");
        fprintf(file, "set ylabel 'Накопленная частота (%% от общего числа)'\n");
        fprintf(file, "set grid\n");
        
        fprintf(file, "stats 'plot_data.dat' using 2 name 'F'\n");
        fprintf(file, "cumulative(x) = (sum [i=1:x] column(2))/F_sum*100\n\n");
        
        fprintf(file, "plot 'plot_data.dat' using 1:(cumulative($1)) with lines lw 2 lc rgb 'purple' title 'Кумулятивная частота', \\\n");
        fprintf(file, "     50 with lines lw 1 lc rgb 'gray' dt 2 title '50%%', \\\n");
        fprintf(file, "     90 with lines lw 1 lc rgb 'gray' dt 2 title '90%%'\n\n");
        
        fprintf(file, "unset multiplot\n");
        
        fclose(file);
        std::cout << "Скрипт для GNUplot сохранен в: " << filename << std::endl;
        std::cout << "Для построения графиков выполните: gnuplot " << filename << std::endl;
    }
    
    
    void printStatistics() {
        std::cout << "\n=== СТАТИСТИКА КОРПУСА ===" << std::endl;
        std::cout << "Всего слов (токенов): " << stats.total_tokens << std::endl;
        std::cout << "Уникальных слов: " << stats.unique_words << std::endl;
        std::cout << "Коэффициент сжатия: " 
                 << (double)stats.total_tokens / stats.unique_words << ":1" << std::endl;
        std::cout << "Время обработки: " << stats.processing_time << " сек" << std::endl;
        
        if (points_count > 0) {
            std::cout << "\n=== ТОП-10 САМЫХ ЧАСТЫХ СЛОВ ===" << std::endl;
            
            WordEntry** entries = new WordEntry*[stats.unique_words];
            int num_entries;
            hash_table.getAllEntries(entries, &num_entries);
            HashTable::quickSort(entries, 0, num_entries - 1);
            
            int n = (10 < num_entries) ? 10 : num_entries;
            double total = (double)stats.total_tokens;
            
            for (int i = 0; i < n; i++) {
                double percentage = (entries[i]->frequency / total) * 100.0;
                printf("%2d. %-20s %6d (%.2f%%)\n", 
                       i + 1, entries[i]->word, entries[i]->frequency, percentage);
            }
            
            delete[] entries;
        }
    }
    
    
    void analyzeZipfLaw() {
        if (points_count == 0) {
            std::cout << "Сначала выполните анализ распределения!" << std::endl;
            return;
        }
        
        std::cout << "\n=== АНАЛИЗ ЗАКОНА ЦИПФА ===" << std::endl;
        
        
        double zipf_C, zipf_alpha;
        fitZipfParameters(&zipf_C, &zipf_alpha);
        
        double mandel_C, mandel_alpha, mandel_beta;
        fitMandelbrotParameters(&mandel_C, &mandel_alpha, &mandel_beta);
        
        std::cout << "\nПараметры закона Ципфа:" << std::endl;
        std::cout << "  Формула: frequency = C / rank^alpha" << std::endl;
        std::cout << "  C = " << zipf_C << ", alpha = " << zipf_alpha << std::endl;
        
        std::cout << "\nПараметры закона Мандельброта:" << std::endl;
        std::cout << "  Формула: frequency = C / (rank + beta)^alpha" << std::endl;
        std::cout << "  C = " << mandel_C << ", alpha = " << mandel_alpha 
                 << ", beta = " << mandel_beta << std::endl;
        
        
        std::cout << "\nСравнение для первых 5 слов:" << std::endl;
        std::cout << "Rank\tReal\tZipf\t\tMandel\t\tErrZipf\t\tErrMandel" << std::endl;
        
        for (int i = 0; i < 5 && i < points_count; i++) {
            double real = points[i].frequency;
            double zipf = zipfLaw(i+1, zipf_C, zipf_alpha);
            double mandel = mandelbrotLaw(i+1, mandel_C, mandel_alpha, mandel_beta);
            double err_zipf = fabs(real - zipf) / real * 100.0;
            double err_mandel = fabs(real - mandel) / real * 100.0;
            
            printf("%d\t%.1f\t%.1f\t\t%.1f\t\t%.1f%%\t\t%.1f%%\n",
                   i+1, real, zipf, mandel, err_zipf, err_mandel);
        }
        
        std::cout << "\n=== ПРИЧИНЫ РАСХОЖДЕНИЯ ===" << std::endl;
        std::cout << "1. Ограниченный размер корпуса (идеальный закон работает на бесконечном)" << std::endl;
        std::cout << "2. Неоднородность текстов (тексты песен + метаданные о музыке)" << std::endl;
        std::cout << "3. Наличие стоп-слов (они удаляются, что искажает распределение)" << std::endl;
        std::cout << "4. Частые повторы в текстах песен (куплеты, припевы)" << std::endl;
        std::cout << "5. Специальная лексика (названия песен, имена исполнителей)" << std::endl;
        
        std::cout << "\n=== РЕКОМЕНДАЦИИ ===" << std::endl;
        std::cout << "• Закон Мандельброта лучше аппроксимирует данные (меньшая ошибка)" << std::endl;
        std::cout << "• Для более точного анализа разделить тексты песен и метаданные" << std::endl;
        std::cout << "• Увеличить размер корпуса до 1+ млн слов для лучшего соответствия" << std::endl;
        std::cout << "• Использовать лемматизацию для приведения слов к начальной форме" << std::endl;
    }
};


int main(int argc, char* argv[]) {
    std::cout << "АНАЛИЗАТОР ЗАКОНА ЦИПФА ДЛЯ МУЗЫКАЛЬНОГО КОРПУСА" << std::endl;
    std::cout << "==============================================" << std::endl;
    
    if (argc < 2) {
        std::cout << "Использование: " << argv[0] << " <директория_с_текстами>" << std::endl;
        std::cout << "Пример: " << argv[0] << " lyrics_corpus/" << std::endl;
        std::cout << "        " << argv[0] << " musicbrainz_corpus/" << std::endl;
        return 1;
    }
    
    ZipfAnalyzer analyzer;
    
    std::cout << "\nОбработка директории: " << argv[1] << std::endl;
    analyzer.processDirectory(argv[1]);
    
    std::cout << "\nАнализ распределения частот..." << std::endl;
    analyzer.analyzeDistribution();
    
    analyzer.printStatistics();
    analyzer.analyzeZipfLaw();
    
    
    analyzer.savePlotData("plot_data.dat");
    analyzer.saveTopWords("top_words.txt", 50);
    analyzer.saveParameters("zipf_parameters.txt");
    analyzer.generateGnuplotScript("plot_zipf.gp");
    
    std::cout << "\n=== РЕЗУЛЬТАТЫ СОХРАНЕНЫ ===" << std::endl;
    std::cout << "1. plot_data.dat - данные для построения графиков" << std::endl;
    std::cout << "2. top_words.txt - топ-50 самых частых слов" << std::endl;
    std::cout << "3. zipf_parameters.txt - параметры законов и анализ" << std::endl;
    std::cout << "4. plot_zipf.gp - скрипт для GNUplot" << std::endl;
    std::cout << "\nДля построения графиков выполните: gnuplot plot_zipf.gp" << std::endl;
    
    return 0;
}