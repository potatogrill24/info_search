#include "../include/utils.h"
#include <cstdlib>

void to_lowercase(char* str) {
    if (!str) return;
    
    for (int i = 0; str[i]; i++) {
        str[i] = std::tolower(str[i]);
    }
}

bool is_alpha(char c) {
    return (c >= 'a' && c <= 'z') || 
           (c >= 'A' && c <= 'Z') ||
           (c >= 'а' && c <= 'я') ||
           (c >= 'А' && c <= 'Я');
}

void clean_string(char* str) {
    if (!str) return;
    
    char* dest = str;
    char* src = str;
    
    while (*src) {
        if (is_alpha(*src) || *src == ' ' || *src == '-') {
            *dest = *src;
            dest++;
        }
        src++;
    }
    *dest = '\0';
}

char** split_string(const char* str, const char* delimiters, int* count) {
    if (!str || !delimiters || !count) return nullptr;
    
    
    *count = 0;
    const char* ptr = str;
    while (*ptr) {
        
        while (*ptr && strchr(delimiters, *ptr)) ptr++;
        
        if (!*ptr) break;
        
        
        (*count)++;
        
        
        while (*ptr && !strchr(delimiters, *ptr)) ptr++;
    }
    
    if (*count == 0) return nullptr;
    
    
    char** tokens = (char**)malloc(*count * sizeof(char*));
    if (!tokens) return nullptr;
    
    
    ptr = str;
    int token_index = 0;
    while (*ptr) {
        
        while (*ptr && strchr(delimiters, *ptr)) ptr++;
        
        if (!*ptr) break;
        
        
        const char* token_start = ptr;
        
        
        while (*ptr && !strchr(delimiters, *ptr)) ptr++;
        
        
        int token_len = ptr - token_start;
        
        
        tokens[token_index] = (char*)malloc(token_len + 1);
        if (!tokens[token_index]) {
            
            for (int i = 0; i < token_index; i++) {
                free(tokens[i]);
            }
            free(tokens);
            return nullptr;
        }
        
        
        strncpy(tokens[token_index], token_start, token_len);
        tokens[token_index][token_len] = '\0';
        
        token_index++;
    }
    
    return tokens;
}

void free_string_array(char** arr, int count) {
    if (!arr) return;
    
    for (int i = 0; i < count; i++) {
        free(arr[i]);
    }
    free(arr);
}

char* strdup(const char* src) {
    if (!src) return nullptr;
    
    size_t len = strlen(src) + 1;
    char* dst = (char*)malloc(len);
    if (!dst) return nullptr;
    
    strcpy(dst, src);
    return dst;
}