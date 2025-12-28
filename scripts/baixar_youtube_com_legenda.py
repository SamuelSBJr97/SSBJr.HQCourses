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
        "--write-auto-subs",
        "--sub-lang", "en",
        "--sub-format", "srv3/srv2/srv1/srv",
        "-o", f"{video_id}.%(ext)s",
        url
    ]
    print("Executando:", " ".join(cmd))
    subprocess.run(cmd, check=True)
    # Após o download, renomeia o MP4 baixado para _video.mp4
    downloaded_mp4 = f"{video_id}.mp4"
    target_mp4 = "_video.mp4"
    if os.path.exists(downloaded_mp4):
        try:
            os.replace(downloaded_mp4, target_mp4)
            print(f"Download concluído: {target_mp4} e legenda {video_id}.en.srv")
        except Exception as e:
            print(f"Falha ao renomear {downloaded_mp4} -> {target_mp4}: {e}")
    else:
        # tenta detectar qualquer .mp4 gerado e renomear
        for f in os.listdir('.'):
            if f.lower().endswith('.mp4'):
                try:
                    os.replace(f, target_mp4)
                    print(f"Download concluído: {target_mp4} (renomeado de {f}) e legenda {video_id}.en.srv")
                    break
                except Exception as e:
                    print(f"Falha ao renomear {f} -> {target_mp4}: {e}")

    # Renomeia a legenda gerada para transcript.<ext> (preserva a extensão que veio)
    import re as _re
    subtitle_found = False
    for f in os.listdir('.'):
        m = _re.match(rf"^{_re.escape(video_id)}(?:\.en)?\.(srv3|srv|srt|vtt)$", f, _re.IGNORECASE)
        if m:
            ext = m.group(1).lower()
            target_sub = f"transcript.{ext}"
            try:
                os.replace(f, target_sub)
                print(f"Legenda renomeada: {target_sub}")
            except Exception as e:
                print(f"Falha ao renomear legenda {f} -> {target_sub}: {e}")
            subtitle_found = True
            break
    if not subtitle_found:
        print("Nenhuma legenda compatível encontrada para renomear.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python baixar_youtube_com_legenda.py <url_do_video>")
        sys.exit(1)
    url = sys.argv[1]
    baixar_youtube_com_legenda(url)
