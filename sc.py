# .github/workflows/update_playlist.yml
name: Update Filtered Playlist

on:
  schedule:
    # Jalankan setiap jam, pada menit ke-15 (misalnya 00:15, 01:15, dst.)
    # Anda bisa ubah jadwalnya. Minimal 5 menit.
    # '*/15 * * * *' = setiap 15 menit, tidak direkomendasikan jika terlalu sering
    - cron: '15 * * * *' 
  workflow_dispatch: # Tombol untuk menjalankan manual

jobs:
  update_playlist_job:
    runs-on: ubuntu-latest
    outputs:
      playlist_changed: ${{ steps.run_scraper.outputs.playlist_changed }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10' # Atau versi Python lain yang Anda inginkan

      - name: Install dependencies
        run: pip install requests

      - name: Run scraper script
        id: run_scraper # Memberi ID pada step ini agar bisa mengambil outputnya
        run: python scraper.py # Ganti path jika skrip Anda ada di subfolder, mis: python scripts/scraper.py
      
      - name: Commit and push if playlist changed
        # Hanya jalankan step ini jika output playlist_changed dari step run_scraper adalah 'true'
        if: steps.run_scraper.outputs.playlist_changed == 'true'
        run: |
          git config --global user.name "GitHub Action Bot"
          git config --global user.email "action@github.com"
          git add ${{ env.OUTPUT_FILENAME || 'filtered_playlist.m3u' }} # Gunakan variabel env atau nama file default
          # Cek apakah ada perubahan yang di-stage
          if ! git diff --staged --quiet; then
            git commit -m "Update filtered playlist - $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
            git push
            echo "Playlist updated and pushed."
          else
            echo "No changes to commit for the playlist."
          fi
        env:
          OUTPUT_FILENAME: filtered_playlist.m3u # Pastikan ini sama dengan di skrip Python
