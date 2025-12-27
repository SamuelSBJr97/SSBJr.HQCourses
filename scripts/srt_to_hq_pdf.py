"""
Script para gerar um livro HQ (PDF) a partir de um vídeo e um arquivo SRT de legendas.
- Para cada legenda, extrai o frame do vídeo no tempo inicial da legenda.
- Monta páginas em layout 2x3 (duas colunas, três linhas por página).
- A legenda aparece como texto acima da imagem do frame.

Requisitos: opencv-python, pillow, numpy
"""

import cv2
import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import re

# CONFIGURAÇÕES
video_path = 'video.mp4'  # Caminho do vídeo
srt_path = 'transcript.srt'  # Caminho do SRT

output_pdf_2x3 = 'hq_livro_2x3.pdf'
output_pdf_1x6 = 'hq_livro_1x6.pdf'
temp_dir = 'frames_hq_temp'  # Pasta temporária para frames
os.makedirs(temp_dir, exist_ok=True)


# Parâmetros comuns
pagina_tamanho = (2480, 3508)  # A4 300dpi
margem_x = 60
margem_y = 60
espacamento_x = 20
espacamento_y = 20
fonte_tamanho = 96  # Fonte maior para HQ
# Fonte comum de leitura: Arial (ou padrão do sistema)
fonte_path = None  # None = fonte padrão do sistema (Arial, DejaVu, etc)

# Função para ler SRT
def parse_srt(srt_path):
    with open(srt_path, encoding='utf-8') as f:
        content = f.read()
    blocks = re.split(r'\n\s*\n', content)
    legendas = []
    for block in blocks:
        lines = block.strip().splitlines()
        if len(lines) >= 3:
            times = re.findall(r'(\d{2}):(\d{2}):(\d{2}),\d{3}', lines[1])
            if len(times) == 2:
                start = int(times[0][0]) * 3600 + int(times[0][1]) * 60 + int(times[0][2])
                end = int(times[1][0]) * 3600 + int(times[1][1]) * 60 + int(times[1][2])
                text = ' '.join(lines[2:]).replace('\n', ' ').strip()
                legendas.append((start, end, text))
    return legendas

# Função para extrair frame do vídeo em um tempo específico (segundos)
def get_frame_at_time(video_cap, time_sec):
    fps = video_cap.get(cv2.CAP_PROP_FPS)
    frame_id = int(fps * time_sec)
    video_cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
    ret, frame = video_cap.read()
    if not ret:
        return None
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return Image.fromarray(frame)

# Carrega legendas
dialogos = parse_srt(srt_path)

# Carrega vídeo
cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    raise RuntimeError(f'Não foi possível abrir o vídeo: {video_path}')

# Fonte
try:
    fonte = ImageFont.truetype(fonte_path or "arial.ttf", fonte_tamanho)
except:
    fonte = ImageFont.load_default()




# Função para ajustar dinamicamente o tamanho da fonte para caber no quadro
def fit_text_to_box(text, font_path, box_width, box_height, min_font=10, max_font=300, padding=10):
    from textwrap import wrap
    def try_truetype(size):
        try:
            return ImageFont.truetype(font_path or "arial.ttf", size)
        except OSError:
            return None
    for size in range(max_font, min_font, -2):
        font = try_truetype(size)
        if font is None:
            font = ImageFont.load_default()
        bbox_A = font.getbbox('A')
        avg_char_width = bbox_A[2] - bbox_A[0]
        chars_per_line = max(1, (box_width - 2*padding) // avg_char_width)
        lines = []
        for paragraph in text.split('\n'):
            lines.extend(wrap(paragraph, width=chars_per_line))
        bbox_line = font.getbbox('Ag')
        line_height = (bbox_line[3] - bbox_line[1]) + 8
        total_text_height = len(lines) * line_height
        if total_text_height + 2*padding <= box_height:
            return font, lines, line_height
    # Se não couber, retorna o menor tamanho
    font = try_truetype(min_font)
    if font is None:
        font = ImageFont.load_default()
    lines = []
    for paragraph in text.split('\n'):
        lines.extend(wrap(paragraph, width=chars_per_line))
    bbox_line = font.getbbox('Ag')
    line_height = (bbox_line[3] - bbox_line[1]) + 8
    return font, lines, line_height



# Fonte para tempo da legenda (legenda de imagem, monoespaçada)
try:
    fonte_tempo = ImageFont.truetype("DejaVuSansMono-Bold.ttf", 48)
except:
    fonte_tempo = ImageFont.load_default()

def format_time(seg):
    h = int(seg // 3600)
    m = int((seg % 3600) // 60)
    s = int(seg % 60)
    return f"{h:02}:{m:02}:{s:02}"



# Gera imagens com legenda, sem borda, tempo e compressão JPEG (texto ajustado ao quadro)
frames_legenda = []
for idx, (start, end, texto) in enumerate(dialogos):
    img = get_frame_at_time(cap, start)
    if img is None:
        continue
    largura, altura = img.size
    quadro_w = largura
    # Espaço para tempo da legenda
    tempo_h = fonte_tempo.size + 24
    # Espaço disponível para legenda: metade do quadro
    legenda_h = altura // 2
    quadro_h = altura + legenda_h + tempo_h
    img_y = legenda_h
    quadro = Image.new('RGB', (quadro_w, quadro_h), (255,255,255))
    draw = ImageDraw.Draw(quadro)
    # Ajusta fonte para caber perfeitamente
    font_path = fonte_path or "arial.ttf"
    font_legenda, legenda_lines, line_height = fit_text_to_box(texto, font_path, quadro_w, legenda_h, min_font=16, max_font=fonte_tamanho)
    # Renderiza as linhas da legenda
    y_text = (legenda_h - (len(legenda_lines)*line_height))//2
    for line in legenda_lines:
        bbox = font_legenda.getbbox(line)
        w = bbox[2] - bbox[0]
        x_text = (quadro_w - w)//2
        draw.text((x_text, y_text), line, font=font_legenda, fill=(0,0,0))
        y_text += line_height
    # Cola imagem logo abaixo da legenda
    img_resized = img.resize((quadro_w, altura), Image.LANCZOS)
    quadro.paste(img_resized, (0, img_y))
    # Tempo da legenda em vermelho, centralizado, abaixo do frame
    tempo_str = f"{format_time(start)} - {format_time(end)}"
    tempo_y = img_y + altura + 8
    tempo_x = quadro_w // 2
    draw.text((tempo_x, tempo_y), tempo_str, font=fonte_tempo, fill=(220,0,0), anchor="ma")
    # Compressão JPEG
    temp_path = os.path.join(temp_dir, f'frame_{idx:05d}.jpg')
    quadro.save(temp_path, 'JPEG', quality=90, optimize=True)
    frames_legenda.append(temp_path)

cap.release()


# Função para montar e salvar PDF HQ


# PDF apenas com imagens (sem camada de texto pesquisável)
def montar_pdf(frames_legenda, colunas, linhas, output_pdf):
    paginas = []
    frame_w = (pagina_tamanho[0] - 2*margem_x - (colunas-1)*espacamento_x) // colunas
    frame_h = (pagina_tamanho[1] - 2*margem_y - (linhas-1)*espacamento_y) // linhas
    for i in range(0, len(frames_legenda), colunas*linhas):
        page = Image.new('RGB', pagina_tamanho, (255,255,255))
        for j, frame_path in enumerate(frames_legenda[i:i+colunas*linhas]):
            img = Image.open(frame_path)
            img = img.resize((frame_w, frame_h), Image.LANCZOS)
            linha = j // colunas
            coluna = j % colunas
            x = margem_x + coluna * (frame_w + espacamento_x)
            y = margem_y + linha * (frame_h + espacamento_y)
            page.paste(img, (x, y))
        paginas.append(page)
    # Salva PDF de imagens
    if paginas:
        paginas[0].save(
            output_pdf,
            "PDF",
            resolution=300,
            save_all=True,
            append_images=paginas[1:],
            quality=90,
            optimize=True
        )
        print(f"PDF HQ gerado: {output_pdf}")
    else:
        print(f"Nenhuma página gerada para {output_pdf}!")

# Gera PDF 2x3
montar_pdf(frames_legenda, 2, 3, output_pdf_2x3)
# Gera PDF 1x6
montar_pdf(frames_legenda, 1, 6, output_pdf_1x6)
