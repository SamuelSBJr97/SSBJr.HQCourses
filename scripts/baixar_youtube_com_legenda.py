"""
Script para baixar vídeos do YouTube em MP4 e extrair legendas em inglês no formato .srv.
Requisitos: yt-dlp

Uso:
    python baixar_youtube_com_legenda.py <url_do_video>

O vídeo será salvo como <video_id>.mp4 e a legenda como <video_id>.en.srv
"""

import sys
import subprocess
import os


def baixar_youtube_com_legenda(url):
    # Obtém o ID do vídeo
    import re
    match = re.search(r"(?:v=|youtu.be/)([\w-]+)", url)
    if not match:
        print("URL inválida.")
        return
    video_id = match.group(1)
    # Comando yt-dlp para baixar vídeo e legenda em inglês (formato .srv)
    cmd = [
        "yt-dlp",
        "-f", "mp4",
        "--write-subs",
        "--sub-lang", "en",
        "--sub-format", "srv3/srv2/srv1/srv",
        "-o", f"{video_id}.%(ext)s",
        url
    ]
    print("Executando:", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"Download concluído: {video_id}.mp4 e legenda {video_id}.en.srv")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python baixar_youtube_com_legenda.py <url_do_video>")
        sys.exit(1)
    url = sys.argv[1]
    baixar_youtube_com_legenda(url)
