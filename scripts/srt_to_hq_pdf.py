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
# Fonte HQ-friendly: Comic Neue (baixe o arquivo .ttf e coloque na pasta do script ou ajuste o caminho)
fonte_path = "ComicNeue-Bold.ttf"  # https://fonts.google.com/specimen/Comic+Neue

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



# Função para desenhar texto com quebra de linha automática e centralização
# Desenha texto HQ com antialiasing e centralização
def draw_multiline_text(draw, text, box, font, fill, padding=10, align="center"):
    from textwrap import wrap
    x0, y0, x1, y1 = box
    max_width = x1 - x0 - 2*padding
    max_height = y1 - y0 - 2*padding
    bbox_A = font.getbbox('A')
    avg_char_width = bbox_A[2] - bbox_A[0]
    chars_per_line = max(1, max_width // avg_char_width)
    lines = []
    for paragraph in text.split('\n'):
        lines.extend(wrap(paragraph, width=chars_per_line))
    bbox_line = font.getbbox('Ag')
    line_height = (bbox_line[3] - bbox_line[1]) + 8  # Mais espaçamento
    max_lines = max_height // line_height
    lines = lines[:max_lines]
    total_text_height = len(lines) * line_height
    y_text = y0 + padding + (max_height - total_text_height) // 2
    for line in lines:
        bbox = font.getbbox(line)
        w = bbox[2] - bbox[0]
        if align == "center":
            x_text = x0 + (max_width - w)//2 + padding
        else:
            x_text = x0 + padding
        # Usa antialiasing (draw.text já faz, mas pode melhorar com RGBA)
        draw.text((x_text, y_text), line, font=font, fill=fill)
        y_text += line_height



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

# Gera imagens com legenda, borda, tempo e compressão JPEG
frames_legenda = []
for idx, (start, end, texto) in enumerate(dialogos):
    img = get_frame_at_time(cap, start)
    if img is None:
        continue
    largura, altura = img.size
    # Proporção do quadro: legenda 80%, imagem 20% (legenda ocupa 80% do quadro)
    quadro_w = largura + 32  # 16px padding/borda cada lado
    quadro_h = altura + int(4*altura) + 32 + 60  # 80% legenda, 20% imagem, + espaço tempo
    legenda_h = int(0.8*quadro_h)
    img_h = quadro_h - legenda_h - 16 - 60
    img_resized = img.resize((quadro_w-32, img_h), Image.LANCZOS)
    quadro = Image.new('RGB', (quadro_w, quadro_h), (255,255,255))
    draw = ImageDraw.Draw(quadro)
    # Desenha borda preta grossa
    border_color = (0,0,0)
    border_width = 6
    draw.rectangle([0,0,quadro_w-1,quadro_h-1], outline=border_color, width=border_width)
    # Área da legenda
    legenda_box = (16, 16, quadro_w-16, 16+legenda_h-8)
    draw.rectangle(legenda_box, fill=(255,255,255))
    draw_multiline_text(draw, texto, legenda_box, fonte, fill=(0,0,0), padding=10, align="center")
    # Cola imagem na parte inferior
    quadro.paste(img_resized, (16, 16+legenda_h))
    # Tempo da legenda em vermelho, centralizado, abaixo do frame
    tempo_str = f"{format_time(start)} - {format_time(end)}"
    tempo_y = 16 + legenda_h + img_h + 8
    tempo_x = quadro_w // 2
    draw.text((tempo_x, tempo_y), tempo_str, font=fonte_tempo, fill=(220,0,0), anchor="ma")
    # Compressão JPEG
    temp_path = os.path.join(temp_dir, f'frame_{idx:05d}.jpg')
    quadro.save(temp_path, 'JPEG', quality=90, optimize=True)
    frames_legenda.append(temp_path)

cap.release()


# Função para montar e salvar PDF HQ

# PDF pesquisável: adiciona camada de texto usando PyMuPDF
def montar_pdf(frames_legenda, colunas, linhas, output_pdf):
    from PIL import Image
    import fitz  # PyMuPDF
    paginas = []
    frame_w = (pagina_tamanho[0] - 2*margem_x - (colunas-1)*espacamento_x) // colunas
    frame_h = (pagina_tamanho[1] - 2*margem_y - (linhas-1)*espacamento_y) // linhas
    temp_pdf = output_pdf + ".tmp.pdf"
    # Gera PDF de imagens
    for i in range(0, len(frames_legenda), colunas*linhas):
        page = Image.new('RGB', pagina_tamanho, (255,255,255))
        legenda_texts = []
        for j, frame_path in enumerate(frames_legenda[i:i+colunas*linhas]):
            img = Image.open(frame_path)
            img = img.resize((frame_w, frame_h), Image.LANCZOS)
            linha = j // colunas
            coluna = j % colunas
            x = margem_x + coluna * (frame_w + espacamento_x)
            y = margem_y + linha * (frame_h + espacamento_y)
            page.paste(img, (x, y))
            # Extrai texto da legenda do nome do arquivo
            idx_frame = int(os.path.basename(frame_path).split('_')[1].split('.')[0])
            legenda_texts.append((x, y, frame_w, frame_h, dialogos[idx_frame][2]))
        paginas.append((page, legenda_texts))
    # Salva PDF de imagens
    if paginas:
        img_pages = [p[0] for p in paginas]
        img_pages[0].save(
            temp_pdf,
            "PDF",
            resolution=300,
            save_all=True,
            append_images=img_pages[1:],
            quality=90,
            optimize=True
        )
        # Adiciona camada de texto pesquisável
        doc = fitz.open(temp_pdf)
        for i, (page, legenda_texts) in enumerate(paginas):
            pdfpage = doc[i]
            for (x, y, w, h, texto) in legenda_texts:
                # A legenda ocupa o topo do quadro (80%)
                legenda_box_h = int(h * 0.8)
                # Ajusta box para o texto
                rect = fitz.Rect(x+20, y+20, x+w-20, y+legenda_box_h-10)
                pdfpage.insert_textbox(rect, texto, fontsize=fonte_tamanho, fontname="helv", color=(0,0,0), align=1)
        doc.save(output_pdf, garbage=4, deflate=True)
        doc.close()
        os.remove(temp_pdf)
        print(f"PDF HQ pesquisável gerado: {output_pdf}")
    else:
        print(f"Nenhuma página gerada para {output_pdf}!")

# Gera PDF 2x3
montar_pdf(frames_legenda, 2, 3, output_pdf_2x3)
# Gera PDF 1x6
montar_pdf(frames_legenda, 1, 6, output_pdf_1x6)
