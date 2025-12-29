import requests
import json
import os
import time
import sys
from urllib.parse import quote_plus


class LyricsOvhParser:
    def __init__(self, output_dir="lyrics_data"):
        self.output_dir = output_dir
        self.base_url = "https://api.lyrics.ovh/v1"

        self.html_dir = os.path.join(output_dir, "html")
        self.metadata_dir = os.path.join(output_dir, "metadata")
        os.makedirs(self.html_dir, exist_ok=True)
        os.makedirs(self.metadata_dir, exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        self.stats = {
            'total_downloaded': 0,
            'total_size_bytes': 0,
            'failed_downloads': 0,
            'total_processed': 0
        }

    def get_popular_tracks(self, page=1, page_size=20):
        api_key = "c2b4e5f9e6c8d7a3b5f8e9c2d4a6b7e1"
        
        try:
            url = "http://ws.audioscrobbler.com/2.0/"
            params = {
                "method": "chart.gettoptracks",
                "api_key": api_key,
                "format": "json",
                "page": page,
                "limit": page_size
            }
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                tracks = data.get("tracks", {}).get("track", [])
                
                track_list = []
                for track in tracks:
                    artist = track.get("artist", {}).get("name", "")
                    title = track.get("name", "")
                    if artist and title:
                        track_list.append((artist, title))
                
                return track_list
            else:
                print(f"[WARNING] Last.fm API недоступен", file=sys.stderr)
                return []
                
        except Exception as e:
            print(f"[WARNING] Ошибка Last.fm API: {e}", file=sys.stderr)
            return []

    def get_lyrics(self, artist, title):
        try:
            encoded_artist = quote_plus(artist)
            encoded_title = quote_plus(title)
            
            url = f"{self.base_url}/{encoded_artist}/{encoded_title}"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                lyrics = data.get("lyrics", "")
                
                if lyrics and len(lyrics.strip()) > 50:
                    return lyrics.strip()
                else:
                    return None
            elif response.status_code == 404:
                print(f"[INFO] Текст не найден: {artist} - {title}", file=sys.stderr)
                return None
            else:
                print(f"[WARNING] Ошибка {response.status_code} для {artist} - {title}", file=sys.stderr)
                return None
                
        except Exception as e:
            print(f"[ERROR] Ошибка при запросе {artist} - {title}: {e}", file=sys.stderr)
            return None

    def save_lyrics_html(self, artist, title, lyrics, track_id):
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - {artist}</title>
    <style>
        body {{ 
            font-family: 'Arial', sans-serif; 
            margin: 40px; 
            line-height: 1.8;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            border-bottom: 3px solid #2c3e50;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        h1 {{
            color: #2c3e50;
            margin: 0;
        }}
        .artist {{
            color: #7f8c8d;
            font-size: 1.2em;
            margin-top: 5px;
        }}
        .lyrics {{
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            font-size: 1.1em;
            line-height: 1.8;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 5px;
            border-left: 4px solid #3498db;
        }}
        .stats {{
            margin-top: 30px;
            padding: 15px;
            background: #ecf0f1;
            border-radius: 5px;
            font-size: 0.9em;
            color: #7f8c8d;
        }}
        footer {{
            margin-top: 40px;
            text-align: center;
            font-size: 0.9em;
            color: #95a5a6;
            border-top: 1px solid #ecf0f1;
            padding-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <div class="artist">by {artist}</div>
        </div>
        
        <div class="lyrics">{lyrics}</div>
        
        <div class="stats">
            <p><strong>Статистика:</strong> {len(lyrics)} символов, {len(lyrics.split())} слов</p>
        </div>
        
        <footer>
            <p>Источник: Lyrics.ovh API | Бесплатный доступ без API ключа</p>
            <p>Загружено: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </footer>
    </div>
</body>
</html>"""

        html_file = os.path.join(self.html_dir, f"track_{track_id}.html")
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        file_size = len(html_content.encode('utf-8'))
        self.stats['total_size_bytes'] += file_size
        self.stats['total_downloaded'] += 1

        return html_file, file_size

    def download_lyrics(self, max_tracks=15000, page_size=20):
        print(f"[INFO] Начинаем загрузку текстов песен с Lyrics.ovh...", file=sys.stderr)
        print(f"[INFO] Целевое количество треков: {max_tracks}", file=sys.stderr)

        page = 1
        downloaded = 0
        
        while downloaded < max_tracks:
            try:
                print(f"[INFO] Загружаем страницу {page} списка треков...", file=sys.stderr)
                
                tracks = self.get_popular_tracks(page, page_size)
                
                if not tracks:
                    print(f"[INFO] На странице {page} нет треков, завершаем...", file=sys.stderr)
                    break
                
                print(f"[INFO] Загружено {len(tracks)} треков со страницы {page}", file=sys.stderr)
                
                metadata = {
                    "page": page,
                    "page_size": page_size,
                    "tracks": [{"artist": a, "title": t} for a, t in tracks],
                    "download_time": time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                metadata_file = os.path.join(self.metadata_dir, f"tracks_page_{page}.json")
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                
                for i, (artist, title) in enumerate(tracks, 1):
                    if downloaded >= max_tracks:
                        break
                        
                    self.stats['total_processed'] += 1
                    track_num = downloaded + 1
                    
                    try:
                        print(f"[INFO] Загружаем трек {track_num}/{max_tracks}: {artist} - {title}", file=sys.stderr)

                        lyrics = self.get_lyrics(artist, title)
                        
                        if lyrics:
                            track_metadata = {
                                "track_id": track_num,
                                "artist": artist,
                                "title": title,
                                "lyrics_length": len(lyrics),
                                "word_count": len(lyrics.split()),
                                "download_time": time.strftime('%Y-%m-%d %H:%M:%S'),
                                "source": "lyrics.ovh",
                                "page": page,
                                "position": i
                            }
                            
                            metadata_file = os.path.join(self.metadata_dir, f"track_{track_num}_full.json")
                            with open(metadata_file, 'w', encoding='utf-8') as f:
                                json.dump(track_metadata, f, indent=2, ensure_ascii=False)

                            html_file, file_size = self.save_lyrics_html(artist, title, lyrics, track_num)
                            
                            print(f"[INFO] Сохранено: {html_file} ({file_size} bytes)", file=sys.stderr)
                            downloaded += 1
                        else:
                            print(f"[WARNING] Не удалось загрузить текст для: {artist} - {title}", file=sys.stderr)
                            self.stats['failed_downloads'] += 1

                        if track_num % 5 == 0:
                            print(f"[INFO] Прогресс: {downloaded}/{max_tracks} треков", file=sys.stderr)
                            time.sleep(2)
                        else:
                            time.sleep(1)

                        if track_num % 100 == 0:
                            self.save_statistics()
                            print(f"[INFO] Обработано {track_num} треков, успешно: {self.stats['total_downloaded']}", file=sys.stderr)

                    except KeyboardInterrupt:
                        print("\n[INFO] Загрузка прервана пользователем", file=sys.stderr)
                        self.save_statistics()
                        return
                    except Exception as e:
                        print(f"[ERROR] Ошибка при обработке трека {artist} - {title}: {e}", file=sys.stderr)
                        self.stats['failed_downloads'] += 1
                        continue
                
                page += 1
                time.sleep(2)

            except Exception as e:
                print(f"[ERROR] Ошибка при загрузке страницы {page}: {e}", file=sys.stderr)
                time.sleep(5)
                continue

        self.save_statistics()

        print(f"[INFO] Загрузка завершена!", file=sys.stderr)
        print(f"[INFO] Всего обработано: {self.stats['total_processed']} треков", file=sys.stderr)
        print(f"[INFO] Успешно загружено: {self.stats['total_downloaded']} треков", file=sys.stderr)
        print(f"[INFO] Ошибок загрузки: {self.stats['failed_downloads']}", file=sys.stderr)
        print(f"[INFO] Успешность: {(self.stats['total_downloaded'] / max(self.stats['total_processed'], 1)) * 100:.1f}%", file=sys.stderr)
        print(f"[INFO] Общий размер: {self.stats['total_size_bytes'] / (1024 * 1024):.2f} MB", file=sys.stderr)

    def save_statistics(self):
        stats_file = os.path.join(self.output_dir, "download_stats.json")

        stats_with_timestamp = {
            **self.stats,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'average_file_size': self.stats['total_size_bytes'] / max(self.stats['total_downloaded'], 1),
            'success_rate': (self.stats['total_downloaded'] / max(self.stats['total_processed'], 1)) * 100
        }

        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats_with_timestamp, f, indent=2, ensure_ascii=False)


def main():
    parser = LyricsOvhParser(
        output_dir="lyrics_corpus"
    )

    try:
        parser.download_lyrics(
            max_tracks=15000,
            page_size=20
        )
    except KeyboardInterrupt:
        print("\n[INFO] Программа завершена", file=sys.stderr)
        parser.save_statistics()
    except Exception as e:
        print(f"[ERROR] Критическая ошибка: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()