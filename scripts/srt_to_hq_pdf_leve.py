"""
Script para gerar um PDF leve e apropriado para leitura, combinando texto (legenda) e imagem (frame do vídeo).
Utiliza a biblioteca fpdf2 para gerar PDFs compactos e otimizados para leitura digital e impressão.

Requisitos: opencv-python, pillow, numpy, fpdf2
"""

import cv2
import os
from PIL import Image
import numpy as np
import re
from fpdf import FPDF

# CONFIGURAÇÕES
video_path = 'video.mp4'  # Caminho do vídeo
srt_path = 'transcript.srt'  # Caminho do SRT
output_pdf = 'hq_livro_leve.pdf'
temp_dir = 'frames_hq_temp'
os.makedirs(temp_dir, exist_ok=True)

# Parâmetros de layout
pagina_largura_mm = 210  # A4 largura em mm
pagina_altura_mm = 297   # A4 altura em mm
margem_mm = 10
espaco_legenda_frame_mm = 6
fonte_tamanho = 14  # Tamanho padrão para leitura
fonte_nome = 'Arial'

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

def get_frame_at_time(video_cap, time_sec):
    fps = video_cap.get(cv2.CAP_PROP_FPS)
    frame_id = int(fps * time_sec)
    video_cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
    ret, frame = video_cap.read()
    if not ret:
        return None
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return Image.fromarray(frame)

def format_time(seg):
    h = int(seg // 3600)
    m = int((seg % 3600) // 60)
    s = int(seg % 60)
    return f"{h:02}:{m:02}:{s:02}"


def gerar_pdf_leve_grid(video_path, srt_path, output_pdf, colunas=2, linhas=3):
    dialogos = parse_srt(srt_path)
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f'Não foi possível abrir o vídeo: {video_path}')

    pdf = FPDF(format='A4', unit='mm')
    pdf.set_auto_page_break(auto=False)
    pdf.set_font(fonte_nome, size=fonte_tamanho)

    cell_w = (pagina_largura_mm - 2 * margem_mm) / colunas
    cell_h = (pagina_altura_mm - 2 * margem_mm) / linhas
    legenda_h = 0.22 * cell_h
    tempo_h = 0.13 * cell_h
    img_h = cell_h - legenda_h - tempo_h - espaco_legenda_frame_mm

    for i in range(0, len(dialogos), colunas * linhas):
        pdf.add_page()
        for j in range(colunas * linhas):
            idx = i + j
            if idx >= len(dialogos):
                break
            start, end, texto = dialogos[idx]
            img = get_frame_at_time(cap, start)
            if img is None:
                continue
            # Redimensiona imagem para caber na célula
            img_w, img_h_px = img.size
            ratio = min(cell_w / img_w * 3.78, img_h / img_h_px * 3.78)  # 1 px = 0.2646 mm, 1 mm = 3.78 px
            new_w = int(img_w * ratio)
            new_h = int(img_h_px * ratio)
            img_resized = img.resize((new_w, new_h), Image.LANCZOS)
            temp_img_path = os.path.join(temp_dir, f'frame_leve_grid_{idx:05d}.jpg')
            img_resized.save(temp_img_path, 'JPEG', quality=100)

            col = j % colunas
            row = j // colunas
            x0 = margem_mm + col * cell_w
            y0 = margem_mm + row * cell_h

            # Tempo
            tempo_str = f"{format_time(start)} - {format_time(end)}"
            pdf.set_xy(x0, y0)
            pdf.set_font(fonte_nome, style='B', size=fonte_tamanho-4)
            pdf.set_text_color(200, 0, 0)
            pdf.cell(cell_w, tempo_h, tempo_str, ln=2, align='C')
            # Legenda
            pdf.set_font(fonte_nome, size=fonte_tamanho)
            pdf.set_text_color(0, 0, 0)
            y_legenda = pdf.get_y()
            pdf.set_xy(x0 + 2, y_legenda)
            pdf.multi_cell(cell_w - 4, 6, texto, align='L')
            # Imagem
            y_img = y0 + tempo_h + legenda_h + espaco_legenda_frame_mm
            x_img = x0 + (cell_w - new_w / 3.78) / 2
            pdf.image(temp_img_path, x=x_img, y=y_img, w=new_w / 3.78, h=new_h / 3.78)

    cap.release()
    pdf.output(output_pdf)
    print(f"PDF leve em grid gerado: {output_pdf}")

if __name__ == '__main__':
    # 2x3 grid
    gerar_pdf_leve_grid(video_path, srt_path, 'hq_livro_leve_2x3.pdf', colunas=2, linhas=3)
    # 1x6 grid
    gerar_pdf_leve_grid(video_path, srt_path, 'hq_livro_leve_1x6.pdf', colunas=1, linhas=6)
