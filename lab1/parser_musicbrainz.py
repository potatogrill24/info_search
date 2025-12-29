import requests
import json
import os
import time
import sys


class MusicBrainzParser:
    def __init__(self, output_dir="musicbrainz_data"):
        self.output_dir = output_dir
        self.base_url = "https://musicbrainz.org/ws/2"
        
        self.html_dir = os.path.join(output_dir, "html")
        self.metadata_dir = os.path.join(output_dir, "metadata")
        os.makedirs(self.html_dir, exist_ok=True)
        os.makedirs(self.metadata_dir, exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        })
        
        self.stats = {
            'total_downloaded': 0,
            'total_size_bytes': 0,
            'failed_downloads': 0,
            'total_processed': 0
        }

    def search_recordings_by_artist_api(self, artist, limit=5):
        try:
            url = f"{self.base_url}/recording/"
            params = {
                "query": f'artist:"{artist}" AND status:official',
                "fmt": "json",
                "limit": limit
            }
            
            response = self.session.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                recordings = data.get("recordings", [])
                
                if recordings:
                    recording_list = []
                    for recording in recordings[:3]:
                        title = recording.get("title", "")
                        recording_id = recording.get("id", "")
                        
                        if title and recording_id:
                            recording_list.append({
                                "artist": artist,
                                "title": title,
                                "id": recording_id,
                                "source": "api"
                            })
                    
                    return recording_list
                else:
                    return []
            else:
                return None
                
        except Exception:
            return None

    def get_recording_details(self, recording_id):
        try:
            url = f"{self.base_url}/recording/{recording_id}"
            params = {
                "fmt": "json",
                "inc": "artists+releases+tags"
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception:
            return None

    def save_recording_html(self, recording_data, recording_id):
        title = recording_data.get("title", "")
        
        artist_credit = recording_data.get("artist-credit", [])
        if artist_credit and artist_credit[0].get("artist"):
            artist_name = artist_credit[0]["artist"].get("name", "")
        else:
            artist_name = ""
        
        length = recording_data.get("length")
        if length:
            minutes = length // 60000
            seconds = (length % 60000) // 1000
            duration = f"{minutes}:{seconds:02d}"
        else:
            duration = ""
        
        genres = recording_data.get("genres", [])
        if genres:
            genre_list = ", ".join([g.get("name", "") for g in genres[:3]])
        else:
            genre_list = ""
        
        html_content = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - {artist_name}</title>
    <style>
        body {{
            font-family: 'Arial', sans-serif;
            margin: 20px;
            line-height: 1.6;
            background: #f5f5f5;
            color: #333;
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
            border-bottom: 3px solid #4CAF50;
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
        .section {{
            margin: 25px 0;
            padding: 20px;
            background: #f9f9f9;
            border-radius: 8px;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .info-item {{
            background: white;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #4CAF50;
        }}
        footer {{
            margin-top: 40px;
            text-align: center;
            color: #95a5a6;
            font-size: 0.9em;
            border-top: 1px solid #eee;
            padding-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <div class="artist">🎤 {artist_name}</div>
        </div>
        
        <div class="section">
            <h2>📊 Информация о записи</h2>
            <div class="info-grid">
                <div class="info-item">
                    <strong>Длительность:</strong><br>
                    {duration}
                </div>
                <div class="info-item">
                    <strong>Жанры:</strong><br>
                    {genre_list}
                </div>
                <div class="info-item">
                    <strong>ID записи:</strong><br>
                    <code>{recording_id}</code>
                </div>
            </div>
        </div>
        
        <footer>
            <p>Источник данных: MusicBrainz API</p>
            <p>Загружено: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </footer>
    </div>
</body>
</html>"""

        html_file = os.path.join(self.html_dir, f"recording_{recording_id}.html")
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        file_size = len(html_content.encode('utf-8'))
        self.stats['total_size_bytes'] += file_size
        self.stats['total_downloaded'] += 1

        return html_file, file_size

    def download_recordings(self, max_recordings=50):
        api_recordings = []
        
        test_artists = ["The Beatles", "Queen", "Michael Jackson"]
        
        for artist in test_artists:
            if len(api_recordings) >= 10:
                break
                
            recordings = self.search_recordings_by_artist_api(artist, limit=3)
            if recordings is None:
                break
            elif recordings:
                api_recordings.extend(recordings)
        
        if not api_recordings:
            return
        
        all_recordings = [{
            "artist": r["artist"],
            "title": r["title"],
            "id": r["id"],
            "source": "api"
        } for r in api_recordings]
        
        downloaded = 0
        
        for i, recording in enumerate(all_recordings, 1):
            if downloaded >= max_recordings:
                break
                
            artist = recording["artist"]
            title = recording["title"]
            recording_id = recording["id"]
            
            self.stats['total_processed'] += 1
            
            try:
                recording_data = self.get_recording_details(recording_id)
                
                if not recording_data:
                    self.stats['failed_downloads'] += 1
                    continue
                
                metadata = {
                    "recording_id": downloaded + 1,
                    "mbid": recording_id,
                    "artist": artist,
                    "title": title,
                    "source": recording["source"],
                    "download_time": time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                metadata_file = os.path.join(self.metadata_dir, f"recording_{downloaded+1}.json")
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                
                html_file, file_size = self.save_recording_html(recording_data, recording_id)
                
                downloaded += 1
                
                time.sleep(1)
                
                if downloaded % 10 == 0:
                    self.save_statistics()
                    
            except Exception as e:
                self.stats['failed_downloads'] += 1
                continue
        
        self.save_statistics()

    def save_statistics(self):
        stats_file = os.path.join(self.output_dir, "download_stats.json")

        stats_data = {
            **self.stats,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'success_rate': (self.stats['total_downloaded'] / max(self.stats['total_processed'], 1)) * 100
        }

        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats_data, f, indent=2, ensure_ascii=False)


def main():
    parser = MusicBrainzParser(output_dir="musicbrainz_corpus")
    
    try:
        parser.download_recordings(max_recordings=15000)
    except KeyboardInterrupt:
        parser.save_statistics()
    except Exception as e:
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()