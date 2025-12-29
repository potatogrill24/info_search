echo "Анализ закона Ципфа для музыкального корпуса"
echo "=========================================="

echo "1. Сборка программы..."
make release

echo -e "\n2. Анализ текстов песен (Lyrics.ovh)..."
./zipf_analyzer_release lyrics_corpus/

echo -e "\n3. Анализ метаданных (MusicBrainz)..."
./zipf_analyzer_release musicbrainz_corpus/

echo -e "\n4. Построение графиков..."
gnuplot plot_zipf.gp

echo -e "\n5. Генерация отчета..."
echo "=== ОТЧЕТ ОБ АНАЛИЗЕ ЗАКОНА ЦИПФА ===" > analysis_report.txt
echo "Дата: $(date)" >> analysis_report.txt
echo "" >> analysis_report.txt

cat zipf_parameters.txt >> analysis_report.txt

echo -e "\nАнализ завершен!"
echo "Результаты сохранены в:"
echo "  - analysis_report.txt (полный отчет)"
echo "  - plot_data.dat (данные для графиков)"
echo "  - top_words.txt (топ слов)"
echo "  - zipf_parameters.txt (параметры законов)"
echo "  - plot_zipf.gp (скрипт GNUplot)"
echo "  - zipf_plot.png (графики)"

echo -e "\nДля просмотра графиков откройте файл zipf_plot.png"