# scraper.py
import requests
import re
import os
from datetime import datetime, timezone

MIX_PHP_URL = "https://mycentral.my.id/ctv999/evtttX/mix.php"
OUTPUT_FILENAME = "filtered_playlist.m3u" # Nama file output di repo
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def fetch_original_playlist():
    """Mengambil konten playlist asli."""
    print(f"Fetching original playlist from: {MIX_PHP_URL}")
    try:
        response = requests.get(MIX_PHP_URL, headers={"User-Agent": USER_AGENT}, timeout=20)
        response.raise_for_status() # Error jika status bukan 2xx
        print(f"Successfully fetched original playlist. Status: {response.status_code}")
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching original playlist: {e}")
        return None

def filter_playlist_content(original_content):
    """Memfilter playlist untuk hanya menyertakan channel CTV LIVE."""
    if not original_content or not original_content.strip().startswith("#EXTM3U"):
        print("Invalid or empty original content. Skipping filter.")
        return None

    lines = original_content.splitlines()
    filtered_lines = ["#EXTM3U"] # Selalu mulai dengan header

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF:"):
            # Cek apakah group-title mengandung "CTV LIVE"
            # Regex untuk group-title yang lebih aman
            group_match = re.search(r'group-title="([^"]*CTV LIVE[^"]*)"', line, re.IGNORECASE)
            
            if group_match:
                # Ini adalah entri CTV LIVE, simpan #EXTINF
                filtered_lines.append(line)
                
                # Cari baris #EXTVLCOPT dan URL stream berikutnya
                extinf_line = line
                extvlcopt_line = ""
                stream_url_line = ""

                # Cek baris berikutnya untuk #EXTVLCOPT atau URL
                if i + 1 < len(lines):
                    next_line_1 = lines[i+1].strip()
                    if next_line_1.startswith("#EXTVLCOPT:"):
                        extvlcopt_line = next_line_1
                        filtered_lines.append(extvlcopt_line)
                        if i + 2 < len(lines) and not lines[i+2].strip().startswith("#"):
                            stream_url_line = lines[i+2].strip()
                            filtered_lines.append(stream_url_line)
                            i += 2 # Lewati #EXTVLCOPT dan URL
                        else: # #EXTVLCOPT tapi tidak ada URL valid setelahnya
                            print(f"Warning: Found #EXTVLCOPT for '{extinf_line}' but no valid stream URL followed.")
                            # Hapus #EXTINF dan #EXTVLCOPT yang sudah ditambahkan jika tidak ada URL
                            if extvlcopt_line: filtered_lines.pop()
                            filtered_lines.pop()
                    elif not next_line_1.startswith("#"): # Langsung URL setelah #EXTINF
                        stream_url_line = next_line_1
                        filtered_lines.append(stream_url_line)
                        i += 1 # Lewati URL
                    else: # #EXTINF tapi tidak ada #EXTVLCOPT atau URL valid setelahnya
                        print(f"Warning: Found #EXTINF for CTV LIVE '{extinf_line}' but no valid stream URL or #EXTVLCOPT followed.")
                        filtered_lines.pop() # Hapus #EXTINF yang sudah ditambahkan
                else: # #EXTINF di akhir file tanpa URL
                    print(f"Warning: Found #EXTINF for CTV LIVE '{extinf_line}' at end of file without stream URL.")
                    filtered_lines.pop() # Hapus #EXTINF yang sudah ditambahkan
            
        i += 1
    
    if len(filtered_lines) > 1: # Lebih dari sekadar #EXTM3U
        print(f"Filtering complete. Found { (len(filtered_lines) -1 ) // 2 if not extvlcopt_line else (len(filtered_lines) -1 ) // 3 } CTV LIVE channels (approx).")
        return "\n".join(filtered_lines)
    else:
        print("No CTV LIVE channels found after filtering.")
        return "#EXTM3U\n#EXTINF:-1,No CTV LIVE Channels Found\n" # Playlist kosong tapi valid

def main():
    original_content = fetch_original_playlist()
    if original_content:
        filtered_content = filter_playlist_content(original_content)
        if filtered_content:
            # Cek apakah konten berubah dari file yang ada (jika ada)
            try:
                with open(OUTPUT_FILENAME, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
                if existing_content == filtered_content:
                    print(f"Content of {OUTPUT_FILENAME} has not changed. No update needed.")
                    # Set GITHUB_OUTPUT untuk memberitahu workflow agar tidak commit
                    if os.getenv('GITHUB_OUTPUT'):
                        with open(os.getenv('GITHUB_OUTPUT'), 'a') as f_output:
                            f_output.write("playlist_changed=false\n")
                    return # Keluar jika tidak ada perubahan
            except FileNotFoundError:
                print(f"{OUTPUT_FILENAME} not found, will create new.")
            
            with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
                f.write(filtered_content)
            print(f"Filtered playlist saved to {OUTPUT_FILENAME}")
            if os.getenv('GITHUB_OUTPUT'):
                with open(os.getenv('GITHUB_OUTPUT'), 'a') as f_output:
                    f_output.write("playlist_changed=true\n")

if __name__ == "__main__":
    main()
