"""
Script para Blender 3.6: Adiciona legendas a um vídeo usando transcrição e exporta frames legendados.

Como usar:
1. Abra Blender 3.6, troque para o workspace Video Editing.
2. No Video Sequence Editor, adicione seu vídeo.
3. Execute este script no Scripting workspace (ajuste os caminhos e parâmetros).

Requisitos:
- Blender 3.6
- O vídeo já adicionado na timeline.
- Transcrição em formato [(start_time, end_time, texto), ...] (pode ser adaptado para .srt ou .csv)

"""

import bpy
import os

# CONFIGURAÇÕES


# Caminho do vídeo a ser adicionado
video_path = bpy.path.abspath('//video.mp4')  # Altere para o nome do seu vídeo

# Pasta de saída para frames legendados
output_dir = bpy.path.abspath('//frames_legendados')
os.makedirs(output_dir, exist_ok=True)

# Adiciona o vídeo ao Video Sequence Editor se não existir
def ensure_video_in_vse(video_path):
    vse = bpy.context.scene.sequence_editor_create()
    # Verifica se já existe strip de vídeo
    for s in vse.sequences_all:
        if s.type == 'MOVIE' and bpy.path.abspath(s.filepath) == video_path:
            return s
    # Remove outros strips para evitar sobreposição
    for s in list(vse.sequences_all):
        vse.sequences.remove(s)
    # Adiciona strip de vídeo
    strip = vse.sequences.new_movie(
        name="Video",
        filepath=video_path,
        channel=1,
        frame_start=1
    )
    # Ajusta o range de frames da cena
    bpy.context.scene.frame_start = int(strip.frame_start)
    bpy.context.scene.frame_end = int(strip.frame_start + strip.frame_final_duration - 1)
    return strip

# Garante que o vídeo está na timeline
ensure_video_in_vse(video_path)

def parse_srt(srt_path):
    import re
    transcription = []
    with open(srt_path, encoding='utf-8') as f:
        content = f.read()
    blocks = re.split(r'\n\s*\n', content)
    for block in blocks:
        lines = block.strip().splitlines()
        if len(lines) >= 3:
            times = re.findall(r'(\d{2}):(\d{2}):(\d{2}),\d{3}', lines[1])
            if len(times) == 2:
                start = int(times[0][0]) * 3600 + int(times[0][1]) * 60 + int(times[0][2])
                end = int(times[1][0]) * 3600 + int(times[1][1]) * 60 + int(times[1][2])
                text = ' '.join(lines[2:]).replace('\n', ' ').strip()
                transcription.append((start, end, text))
    return transcription

# Caminho para o arquivo SRT
srt_path = bpy.path.abspath('//transcript.srt')
transcription = parse_srt(srt_path)

# Parâmetros de legenda
font_size = 48
subtitle_y = 200
subtitle_color = (1, 1, 1, 1)
balloon_color = (0, 0, 0, 0.7)
balloon_padding = 40



# Função para adicionar legendas como strips de texto no VSE

# Função para adicionar/remover texto da legenda (apenas texto 2D)


def add_vse_subtitle_strip(text, frame, vse):
    # Remove strip de legenda anterior
    for s in list(vse.sequences_all):
        if s.type == 'TEXT' and s.name.startswith('Legenda_'):
            vse.sequences.remove(s)
    if not text:
        return None
    strip = vse.sequences.new_effect(
        name=f"Legenda_{frame}",
        type='TEXT',
        channel=2,
        frame_start=frame,
        frame_end=frame+1
    )
    strip.text = text
    strip.font_size = font_size
    strip.location[0] = 0.5
    strip.location[1] = 0.15
    strip.color = subtitle_color[:4]
    strip.use_box = True
    strip.box_color = balloon_color
    strip.wrap_width = 0.8
    strip.box_margin = 0.05
    return strip


def get_subtitle_for_frame(frame, fps, transcription):
    time = frame / fps
    for start, end, text in transcription:
        if start <= time < end:
            return text
    return None



scene = bpy.context.scene
fps = scene.render.fps
start_frame = scene.frame_start
end_frame = scene.frame_end


# Renderiza apenas o frame inicial de cada legenda
scene.render.image_settings.file_format = 'PNG'
scene.render.use_sequencer = True





vse = scene.sequence_editor_create()
for idx, (start, end, text) in enumerate(transcription):
    frame = int(start * fps)
    scene.frame_set(frame)
    strip = add_vse_subtitle_strip(text, frame, vse)
    frame_path = os.path.join(output_dir, f"frame_{frame:05d}.png")
    scene.render.filepath = frame_path
    bpy.ops.render.render(write_still=True)
    # Remove strip de legenda após renderizar
    if strip:
        vse.sequences.remove(strip)

print(f"Frames legendados exportados em: {output_dir}")
