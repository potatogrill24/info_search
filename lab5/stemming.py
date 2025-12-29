import re
import json
import os
import sys
import math
import time
import argparse
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple, Optional, Any
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
from dataclasses import dataclass
from enum import Enum
import warnings
warnings.filterwarnings('ignore')


class StemmerType(Enum):
    PORTER = "porter"
    SNOWBALL = "snowball"
    SIMPLE = "simple"
    CUSTOM = "custom"


@dataclass
class StemmingResult:
    doc_id: str
    original_tokens: List[str]
    stemmed_tokens: List[str]
    reduction_ratio: float  
    processing_time: float


@dataclass
class SearchResult:
    """Результат поиска"""
    query: str
    with_stemming: List[Tuple[str, float]]  
    without_stemming: List[Tuple[str, float]]  
    improvement_score: float  


class SimpleStemmer:
    """
    Простой стеммер для русского и английского языков
    Реализует базовые алгоритмы стемминга
    """
    
    def __init__(self, stemmer_type: StemmerType = StemmerType.SIMPLE, 
                 language: str = 'both'):
        self.stemmer_type = stemmer_type
        self.language = language
        self.cache = {}
        self.stats = defaultdict(int)
        
        
        self.common_words_cache = {
            
            'любовь': 'любов', 'любить': 'люб', 'любимый': 'любим',
            'песня': 'песн', 'песни': 'песн', 'петь': 'п',
            'музыка': 'музык', 'музыкальный': 'музыкальн',
            'группа': 'групп', 'группы': 'групп',
            'альбом': 'альбом', 'альбомы': 'альбом',
            'исполнитель': 'исполнител', 'исполнители': 'исполнител',
            
            
            'love': 'lov', 'loving': 'lov', 'loved': 'lov',
            'song': 'song', 'songs': 'song', 'singing': 'sing',
            'music': 'music', 'musical': 'music',
            'band': 'band', 'bands': 'band',
            'album': 'album', 'albums': 'album',
            'artist': 'artist', 'artists': 'artist',
            'rock': 'rock', 'pop': 'pop', 'jazz': 'jazz',
        }
        
        
        self.exceptions = {
            'ru': {'и', 'в', 'на', 'с', 'по', 'о', 'у', 'к'},
            'en': {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at'}
        }
    
    def detect_language(self, word: str) -> str:
        """Определение языка слова"""
        if re.search(r'[а-яёА-ЯЁ]', word):
            return 'ru'
        elif re.search(r'[a-zA-Z]', word):
            return 'en'
        return 'unknown'
    
    def simple_stem_ru(self, word: str) -> str:
        """Простой русский стеммер"""
        if len(word) < 3:
            return word
        
        
        if word in self.exceptions['ru']:
            return word
        
        
        if word in self.common_words_cache:
            return self.common_words_cache[word]
        
        
        endings = [
            'ый', 'ий', 'ой', 'ая', 'яя', 'ое', 'ее',  
            'ов', 'ев', 'ин', 'ын',                    
            'ость', 'есть', 'ство', 'ствие',           
            'ать', 'ять', 'еть', 'ить', 'уть', 'ти',   
            'л', 'ла', 'ло', 'ли',                     
            'ю', 'ешь', 'ет', 'ем', 'ете', 'ут', 'ют', 
            'я', 'и', 'ы', 'е', 'у', 'ю', 'ь',         
        ]
        
        stem = word
        for ending in endings:
            if stem.endswith(ending) and len(stem) > len(ending) + 1:
                stem = stem[:-len(ending)]
                break
        
        
        if stem.endswith('ь'):
            stem = stem[:-1]
        
        return stem
    
    def simple_stem_en(self, word: str) -> str:
        """Простой английский стеммер"""
        if len(word) < 3:
            return word
        
        
        if word in self.exceptions['en']:
            return word
        
        
        if word in self.common_words_cache:
            return self.common_words_cache[word]
        
        
        if word.endswith('sses'):
            word = word[:-2]
        elif word.endswith('ies'):
            word = word[:-2]
        elif word.endswith('ss'):
            pass
        elif word.endswith('s'):
            word = word[:-1]
        
        
        if word.endswith('ing'):
            if len(word) > 5:
                word = word[:-3]
                
                if word.endswith('at') or word.endswith('bl') or word.endswith('iz'):
                    word += 'e'
        
        
        elif word.endswith('ed'):
            if len(word) > 4:
                word = word[:-2]
        
        
        if word.endswith('y'):
            word = word[:-1] + 'i'
        
        
        if len(word) > 3 and word[-1] == word[-2] and word[-1] in 'bcdfghjklmnpqrstvwxz':
            word = word[:-1]
        
        return word
    
    def stem(self, word: str) -> str:
        """Основная функция стемминга"""
        
        if word in self.cache:
            self.stats['cache_hits'] += 1
            return self.cache[word]
        
        self.stats['total_words'] += 1
        
        
        lang = self.detect_language(word)
        
        
        if lang == 'ru' and self.language in ['ru', 'both']:
            stemmed = self.simple_stem_ru(word.lower())
        elif lang == 'en' and self.language in ['en', 'both']:
            stemmed = self.simple_stem_en(word.lower())
        else:
            stemmed = word.lower()
        
        
        self.cache[word] = stemmed
        
        
        if stemmed != word.lower():
            self.stats['stemmed_words'] += 1
        
        return stemmed
    
    def stem_text(self, text: str) -> str:
        """Стемминг всего текста"""
        tokens = re.findall(r'\b[\w\'-]+\b', text.lower())
        stemmed_tokens = [self.stem(token) for token in tokens]
        return ' '.join(stemmed_tokens)
    
    def get_statistics(self) -> Dict:
        """Получение статистики"""
        stats = dict(self.stats)
        if stats['total_words'] > 0:
            stats['stemming_ratio'] = (stats['stemmed_words'] / stats['total_words']) * 100
            stats['cache_hit_ratio'] = (stats.get('cache_hits', 0) / stats['total_words']) * 100
        
        return stats


class StemmingAnalyzer:
    """
    Анализатор влияния стемминга на поисковую систему
    """
    
    def __init__(self, corpus_dir: str = None):
        self.corpus_dir = corpus_dir
        self.stemmer = SimpleStemmer()
        
        
        self.documents = {}  
        self.queries = []    
        self.relevance_judgments = {}  
        
        
        self.stemming_results = []
        self.search_results = []
        
        
        self.stats = defaultdict(float)
        
        
        self._load_test_data()
    
    def _load_test_data(self):
        self.documents = {
            'doc1': "Back in black I hit the sack I've been too long I'm glad to be back",
            'doc2': "Bohemian Rhapsody song by Queen from album A Night at the Opera",
            'doc3': "Love me do you know I love you I'll always be true",
            'doc4': "Музыкальный альбом содержит песни разных жанров рок поп джаз",
            'doc5': "Любовь это прекрасное чувство которое вдохновляет на создание песен",
        }
        
        
        self.queries = [
            ("back black", ['doc1']),
            ("love song", ['doc3']),
            ("музыкальный альбом", ['doc4']),
            ("рок музыка", ['doc4']),
            ("queen music", ['doc2']),
            ("любовь вдохновение", ['doc5']),
        ]
        
        
        for query, relevant_docs in self.queries:
            self.relevance_judgments[query] = set(relevant_docs)
    
    def analyze_stemming_effect(self):
        """Анализ эффекта стемминга на корпусе"""
        print("\n" + "="*60)
        print("АНАЛИЗ ВЛИЯНИЯ СТЕММИНГА")
        print("="*60)
        
        results = []
        
        for doc_id, text in self.documents.items():
            
            tokens = re.findall(r'\b[\w\'-]+\b', text.lower())
            
            
            start_time = time.time()
            stemmed_tokens = [self.stemmer.stem(token) for token in tokens]
            processing_time = time.time() - start_time
            
            
            unique_original = len(set(tokens))
            unique_stemmed = len(set(stemmed_tokens))
            reduction_ratio = (unique_original - unique_stemmed) / unique_original * 100 if unique_original > 0 else 0
            
            result = StemmingResult(
                doc_id=doc_id,
                original_tokens=tokens,
                stemmed_tokens=stemmed_tokens,
                reduction_ratio=reduction_ratio,
                processing_time=processing_time
            )
            results.append(result)
            
            print(f"\nДокумент: {doc_id}")
            print(f"  Оригинальных токенов: {len(tokens)}")
            print(f"  Уникальных токенов: {unique_original}")
            print(f"  Уникальных после стемминга: {unique_stemmed}")
            print(f"  Сокращение словаря: {reduction_ratio:.1f}%")
            print(f"  Время обработки: {processing_time:.4f} сек")
        
        self.stemming_results = results
        
        
        avg_reduction = np.mean([r.reduction_ratio for r in results])
        avg_time = np.mean([r.processing_time for r in results])
        
        print(f"\nСредние показатели:")
        print(f"  Среднее сокращение словаря: {avg_reduction:.1f}%")
        print(f"  Среднее время обработки: {avg_time:.4f} сек")
        
        return results
    
    def build_index(self, use_stemming: bool = False) -> Dict:
        """Построение поискового индекса"""
        index = defaultdict(lambda: defaultdict(int))
        
        for doc_id, text in self.documents.items():
            tokens = re.findall(r'\b[\w\'-]+\b', text.lower())
            
            if use_stemming:
                tokens = [self.stemmer.stem(token) for token in tokens]
            
            
            for token in tokens:
                index[token][doc_id] += 1
        
        return index
    
    def search(self, query: str, index: Dict, use_stemming: bool = False) -> List[Tuple[str, float]]:
        """Поиск по индексу"""
        
        query_tokens = re.findall(r'\b[\w\'-]+\b', query.lower())
        
        if use_stemming:
            query_tokens = [self.stemmer.stem(token) for token in query_tokens]
        
        
        scores = defaultdict(float)
        
        for token in query_tokens:
            if token in index:
                for doc_id, tf in index[token].items():
                    
                    df = len(index[token])  
                    idf = math.log(len(self.documents) / (df + 1)) + 1
                    scores[doc_id] += tf * idf
        
        
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_results
    
    def evaluate_search(self):
        """Оценка качества поиска со стеммингом и без"""
        print("\n" + "="*60)
        print("ОЦЕНКА КАЧЕСТВА ПОИСКА")
        print("="*60)
        
        
        index_without = self.build_index(use_stemming=False)
        index_with = self.build_index(use_stemming=True)
        
        metrics = {
            'with_stemming': {'precision': [], 'recall': [], 'f1': []},
            'without_stemming': {'precision': [], 'recall': [], 'f1': []}
        }
        
        for query, relevant_docs in self.queries:
            
            results_without = self.search(query, index_without, use_stemming=False)
            metrics_without = self._calculate_metrics(results_without, relevant_docs)
            
            
            results_with = self.search(query, index_with, use_stemming=True)
            metrics_with = self._calculate_metrics(results_with, relevant_docs)
            
            
            for metric in ['precision', 'recall', 'f1']:
                metrics['without_stemming'][metric].append(metrics_without[metric])
                metrics['with_stemming'][metric].append(metrics_with[metric])
            
            
            search_result = SearchResult(
                query=query,
                with_stemming=results_with,
                without_stemming=results_without,
                improvement_score=metrics_with['f1'] - metrics_without['f1']
            )
            self.search_results.append(search_result)
            
            print(f"\nЗапрос: '{query}'")
            print(f"  Релевантные документы: {relevant_docs}")
            print(f"  Без стемминга: P={metrics_without['precision']:.3f}, "
                  f"R={metrics_without['recall']:.3f}, F1={metrics_without['f1']:.3f}")
            print(f"  Со стеммингом:   P={metrics_with['precision']:.3f}, "
                  f"R={metrics_with['recall']:.3f}, F1={metrics_with['f1']:.3f}")
            improvement = (metrics_with['f1'] - metrics_without['f1']) / metrics_without['f1'] * 100 if metrics_without['f1'] > 0 else 0
            print(f"  Изменение F1: {improvement:+.1f}%")
        
        
        avg_metrics = {}
        for mode in ['with_stemming', 'without_stemming']:
            avg_metrics[mode] = {
                'precision': np.mean(metrics[mode]['precision']),
                'recall': np.mean(metrics[mode]['recall']),
                'f1': np.mean(metrics[mode]['f1'])
            }
        
        print(f"\nСредние метрики:")
        print(f"  Без стемминга: P={avg_metrics['without_stemming']['precision']:.3f}, "
              f"R={avg_metrics['without_stemming']['recall']:.3f}, "
              f"F1={avg_metrics['without_stemming']['f1']:.3f}")
        print(f"  Со стеммингом:   P={avg_metrics['with_stemming']['precision']:.3f}, "
              f"R={avg_metrics['with_stemming']['recall']:.3f}, "
              f"F1={avg_metrics['with_stemming']['f1']:.3f}")
        
        overall_improvement = (avg_metrics['with_stemming']['f1'] - 
                              avg_metrics['without_stemming']['f1']) / avg_metrics['without_stemming']['f1'] * 100
        
        print(f"\nОбщее улучшение F1: {overall_improvement:+.1f}%")
        
        return avg_metrics
    
    def _calculate_metrics(self, results: List[Tuple[str, float]], 
                          relevant_docs: List[str]) -> Dict:
        """Вычисление метрик качества"""
        if not results:
            return {'precision': 0, 'recall': 0, 'f1': 0}
        
        relevant_set = set(relevant_docs)
        retrieved_set = set([doc_id for doc_id, _ in results[:3]])  
        
        
        precision = len(retrieved_set & relevant_set) / len(retrieved_set) if retrieved_set else 0
        
        
        recall = len(retrieved_set & relevant_set) / len(relevant_set) if relevant_set else 0
        
        
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        return {'precision': precision, 'recall': recall, 'f1': f1}
    
    def analyze_problematic_queries(self):
        """Анализ проблемных запросов"""
        print("\n" + "="*60)
        print("АНАЛИЗ ПРОБЛЕМНЫХ ЗАПРОСОВ")
        print("="*60)
        
        problematic = []
        
        for result in self.search_results:
            if result.improvement_score < -0.1:  
                problematic.append(result)
        
        if not problematic:
            print("Проблемных запросов не обнаружено!")
            return
        
        print(f"Найдено проблемных запросов: {len(problematic)}")
        
        for i, result in enumerate(problematic, 1):
            print(f"\n{i}. Запрос: '{result.query}'")
            print(f"   Ухудшение F1: {result.improvement_score:.3f}")
            
            
            causes = self._analyze_causes(result)
            print(f"   Возможные причины:")
            for cause in causes:
                print(f"   - {cause}")
            
            
            recommendations = self._suggest_improvements(result)
            print(f"   Рекомендации:")
            for rec in recommendations:
                print(f"   - {rec}")
    
    def _analyze_causes(self, result: SearchResult) -> List[str]:
        """Анализ причин ухудшения"""
        causes = []
        
        
        query_tokens = re.findall(r'\b[\w\'-]+\b', result.query.lower())
        stemmed_tokens = [self.stemmer.stem(t) for t in query_tokens]
        
        
        for orig, stemmed in zip(query_tokens, stemmed_tokens):
            if stemmed == orig:
                causes.append(f"Слово '{orig}' не было простеммировано")
            elif len(stemmed) < len(orig) * 0.5:
                causes.append(f"Сильное стеммирование слова '{orig}' -> '{stemmed}'")
        
        
        if len(set(stemmed_tokens)) < len(set(query_tokens)):
            causes.append("Потеря уникальности токенов после стемминга")
        
        return causes[:3]  
    
    def _suggest_improvements(self, result: SearchResult) -> List[str]:
        """Предложения по улучшению"""
        suggestions = [
            "Использовать словарь исключений для частых слов",
            "Комбинировать точное совпадение и стемминг с весами",
            "Давать бонус за точное совпадение слова",
            "Использовать лемматизацию вместо стемминга для критичных слов",
            "Настроить порог стемминга в зависимости от длины слова"
        ]
        return suggestions[:3]
    
    def plot_analysis(self, output_dir: str = "."):
        """Построение графиков анализа"""
        os.makedirs(output_dir, exist_ok=True)
        
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        
        ax1 = axes[0, 0]
        doc_ids = [r.doc_id for r in self.stemming_results]
        reductions = [r.reduction_ratio for r in self.stemming_results]
        
        bars = ax1.bar(doc_ids, reductions, color='skyblue', edgecolor='black')
        ax1.axhline(y=np.mean(reductions), color='red', linestyle='--', 
                   linewidth=2, label=f'Среднее: {np.mean(reductions):.1f}%')
        
        ax1.set_xlabel('Документ', fontsize=12)
        ax1.set_ylabel('Сокращение словаря (%)', fontsize=12)
        ax1.set_title('Влияние стемминга на размер словаря', fontsize=14, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        
        for bar, reduction in zip(bars, reductions):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{reduction:.1f}%', ha='center', va='bottom', fontsize=9)
        
        
        ax2 = axes[0, 1]
        metrics_data = []
        
        if self.search_results:
            
            f1_without = np.mean([self._calculate_metrics(r.without_stemming, 
                                                         self.relevance_judgments[r.query])['f1'] 
                                 for r in self.search_results])
            f1_with = np.mean([self._calculate_metrics(r.with_stemming,
                                                      self.relevance_judgments[r.query])['f1'] 
                              for r in self.search_results])
            
            metrics_data = [f1_without, f1_with]
            labels = ['Без стемминга', 'Со стеммингом']
            
            bars = ax2.bar(labels, metrics_data, color=['lightcoral', 'lightgreen'], 
                          edgecolor='black')
            
            ax2.set_ylabel('F1-мера', fontsize=12)
            ax2.set_title('Качество поиска', fontsize=14, fontweight='bold')
            ax2.grid(True, alpha=0.3)
            
            
            for bar, value in zip(bars, metrics_data):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                        f'{value:.3f}', ha='center', va='bottom', fontsize=10)
        
        
        ax3 = axes[1, 0]
        times = [r.processing_time for r in self.stemming_results]
        
        ax3.plot(doc_ids, times, 'go-', linewidth=2, markersize=8)
        ax3.fill_between(doc_ids, 0, times, alpha=0.3, color='green')
        
        ax3.set_xlabel('Документ', fontsize=12)
        ax3.set_ylabel('Время обработки (сек)', fontsize=12)
        ax3.set_title('Производительность стемминга', fontsize=14, fontweight='bold')
        ax3.grid(True, alpha=0.3)
        
        
        ax4 = axes[1, 1]
        if self.search_results:
            queries = [r.query[:15] + '...' if len(r.query) > 15 else r.query 
                      for r in self.search_results]
            improvements = [r.improvement_score for r in self.search_results]
            
            colors = ['red' if imp < 0 else 'green' for imp in improvements]
            bars = ax4.barh(queries, improvements, color=colors, edgecolor='black')
            
            ax4.axvline(x=0, color='black', linewidth=1)
            ax4.set_xlabel('Изменение F1-меры', fontsize=12)
            ax4.set_title('Влияние стемминга на отдельные запросы', 
                         fontsize=14, fontweight='bold')
            ax4.grid(True, alpha=0.3)
            
            
            for bar, improvement in zip(bars, improvements):
                width = bar.get_width()
                ax4.text(width + (0.01 if width >= 0 else -0.03), 
                        bar.get_y() + bar.get_height()/2,
                        f'{improvement:+.3f}', 
                        va='center', fontsize=9,
                        color='black' if abs(width) > 0.05 else 'gray')
        
        plt.tight_layout()
        output_path = os.path.join(output_dir, "stemming_analysis.png")
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"\nГрафики сохранены в: {output_path}")
        
        return fig
    
    def generate_report(self, output_file: str = "stemming_report.txt"):
        """Генерация текстового отчета"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write("ОТЧЕТ О ВНЕДРЕНИИ СТЕММИНГА\n")
            f.write("="*60 + "\n\n")
            
            f.write("1. ОБЩАЯ СТАТИСТИКА\n")
            f.write("-" * 40 + "\n")
            f.write(f"Количество документов: {len(self.documents)}\n")
            f.write(f"Количество тестовых запросов: {len(self.queries)}\n")
            
            stemmer_stats = self.stemmer.get_statistics()
            f.write(f"Обработано слов: {stemmer_stats.get('total_words', 0)}\n")
            f.write(f"Стеммированных слов: {stemmer_stats.get('stemmed_words', 0)}\n")
            if 'stemming_ratio' in stemmer_stats:
                f.write(f"Процент стеммирования: {stemmer_stats['stemming_ratio']:.1f}%\n\n")
            
            f.write("2. ВЛИЯНИЕ НА РАЗМЕР СЛОВАРЯ\n")
            f.write("-" * 40 + "\n")
            
            for result in self.stemming_results:
                f.write(f"{result.doc_id}:\n")
                f.write(f"  Уникальных токенов до: {len(set(result.original_tokens))}\n")
                f.write(f"  Уникальных токенов после: {len(set(result.stemmed_tokens))}\n")
                f.write(f"  Сокращение: {result.reduction_ratio:.1f}%\n\n")
            
            avg_reduction = np.mean([r.reduction_ratio for r in self.stemming_results])
            f.write(f"Среднее сокращение словаря: {avg_reduction:.1f}%\n\n")
            
            f.write("3. КАЧЕСТВО ПОИСКА\n")
            f.write("-" * 40 + "\n")
            
            
            if self.search_results:
                metrics_without = []
                metrics_with = []
                
                for result in self.search_results:
                    metrics_without.append(
                        self._calculate_metrics(result.without_stemming, 
                                              self.relevance_judgments[result.query])['f1']
                    )
                    metrics_with.append(
                        self._calculate_metrics(result.with_stemming,
                                              self.relevance_judgments[result.query])['f1']
                    )
                
                avg_without = np.mean(metrics_without)
                avg_with = np.mean(metrics_with)
                improvement = ((avg_with - avg_without) / avg_without * 100 
                             if avg_without > 0 else 0)
                
                f.write(f"F1-мера без стемминга: {avg_without:.3f}\n")
                f.write(f"F1-мера со стеммингом: {avg_with:.3f}\n")
                f.write(f"Изменение качества: {improvement:+.1f}%\n\n")
                
                
                f.write("4. АНАЛИЗ ЗАПРОСОВ\n")
                f.write("-" * 40 + "\n")
                
                improved = sum(1 for r in self.search_results if r.improvement_score > 0)
                worsened = sum(1 for r in self.search_results if r.improvement_score < 0)
                unchanged = sum(1 for r in self.search_results if r.improvement_score == 0)
                
                f.write(f"Улучшилось: {improved} запросов\n")
                f.write(f"Ухудшилось: {worsened} запросов\n")
                f.write(f"Без изменений: {unchanged} запросов\n\n")
                
                
                problematic = [r for r in self.search_results if r.improvement_score < -0.1]
                if problematic:
                    f.write("Проблемные запросы (ухудшение >10%):\n")
                    for result in problematic:
                        f.write(f"  - '{result.query}' (ухудшение: {result.improvement_score:.3f})\n")
                    f.write("\n")
            
            f.write("5. ВЫВОДЫ И РЕКОМЕНДАЦИИ\n")
            f.write("-" * 40 + "\n")
            
            if avg_reduction > 20:
                f.write("✓ Стемминг значительно сокращает размер словаря\n")
            else:
                f.write("⚠ Стемминг слабо влияет на размер словаря\n")
            
            if improvement > 5:
                f.write("✓ Стемминг улучшает качество поиска\n")
            elif improvement < -5:
                f.write("⚠ Стемминг ухудшает качество поиска\n")
                f.write("  Рекомендации:\n")
                f.write("  1. Использовать словарь исключений\n")
                f.write("  2. Комбинировать с точным поиском\n")
                f.write("  3. Настроить параметры стемминга\n")
            else:
                f.write("⚠ Стемминг незначительно влияет на качество поиска\n")
            
            f.write("\nОбщие рекомендации:\n")
            f.write("1. Для музыкальных текстов важно сохранять названия групп и песен\n")
            f.write("2. Использовать гибридный подход: стемминг + точное совпадение\n")
            f.write("3. Настроить веса: точное совпадение > стемминг\n")
            f.write("4. Создать словарь музыкальных терминов-исключений\n")
        
        print(f"\nОтчет сохранен в: {output_file}")


def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='Анализатор стемминга для поисковой системы')
    parser.add_argument('--mode', choices=['analyze', 'evaluate', 'demo', 'report'],
                       default='analyze', help='Режим работы')
    parser.add_argument('--output-dir', default='./output',
                       help='Директория для результатов')
    parser.add_argument('--corpus-dir', default=None,
                       help='Директория с документами корпуса')
    
    args = parser.parse_args()
    
    
    analyzer = StemmingAnalyzer(args.corpus_dir)
    
    if args.mode == 'analyze':
        
        analyzer.analyze_stemming_effect()
        analyzer.evaluate_search()
        analyzer.analyze_problematic_queries()
        analyzer.plot_analysis(args.output_dir)
        analyzer.generate_report(os.path.join(args.output_dir, "stemming_report.txt"))
    
    elif args.mode == 'evaluate':
        
        analyzer.evaluate_search()
        analyzer.analyze_problematic_queries()
    
    elif args.mode == 'demo':
        
        stemmer = SimpleStemmer()
        
        test_words = [
            "любовь", "любить", "любимый",
            "песня", "песни", "петь",
            "singing", "songs", "music",
            "рок-группа", "хит-парад"
        ]
        
        print("\n" + "="*60)
        print("ДЕМОНСТРАЦИЯ СТЕММИНГА")
        print("="*60)
        
        for word in test_words:
            stemmed = stemmer.stem(word)
            print(f"{word:15} -> {stemmed}")
        
        test_text = "Я люблю петь песни о любви и слушать музыку рок-групп"
        print(f"\nТекст: {test_text}")
        print(f"Стемминг: {stemmer.stem_text(test_text)}")
    
    elif args.mode == 'report':
        
        analyzer.analyze_stemming_effect()
        analyzer.evaluate_search()
        analyzer.generate_report(os.path.join(args.output_dir, "stemming_report.txt"))
    
    print("\n" + "="*60)
    print("АНАЛИЗ ЗАВЕРШЕН")
    print("="*60)


if __name__ == "__main__":
    main()