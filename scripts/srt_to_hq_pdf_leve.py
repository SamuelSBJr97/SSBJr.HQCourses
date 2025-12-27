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
margem_mm = 18  # margem vertical maior
espaco_legenda_frame_mm = 2  # margem menor entre texto e frame
fonte_tamanho = 14  # Tamanho padrão para leitura
fonte_nome = 'helvetica'

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
    tempo_h = 0.13 * cell_h
    min_fonte_legenda = 9
    max_fonte_legenda = fonte_tamanho

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
            img_w, img_h_px = img.size
            col = j % colunas
            row = j // colunas
            x0 = margem_mm + col * cell_w
            y0 = margem_mm + row * cell_h

            # --- CÉLULA DA LEGENDA (TOPO) ---
            legenda_font = max_fonte_legenda
            line_spacing = 1
            max_legenda_h = cell_h * 0.22
            while legenda_font >= min_fonte_legenda:
                pdf.set_font(fonte_nome, size=legenda_font)
                lines = pdf.multi_cell(cell_w - 4, legenda_font + line_spacing, texto, align='L', split_only=True)
                legenda_h = len(lines) * (legenda_font + line_spacing)
                if legenda_h <= max_legenda_h:
                    break
                legenda_font -= 1
            pdf.set_font(fonte_nome, size=legenda_font)
            pdf.set_text_color(0, 0, 0)
            y_legenda = y0 + 2
            pdf.set_xy(x0 + 2, y_legenda)
            max_lines = int(max_legenda_h // (legenda_font + line_spacing))
            if len(lines) > max_lines:
                lines = lines[:max_lines]
                if lines:
                    lines[-1] = lines[-1].rstrip() + '...'
            for line in lines:
                pdf.set_xy(x0 + 2, y_legenda)
                pdf.cell(cell_w - 4, legenda_font + line_spacing, line, ln=2, align='L')
                y_legenda += legenda_font + line_spacing

            # --- CÉLULA DO FRAME+TEMPO (ABAIXO) ---
            frame_cell_y = y0 + max_legenda_h + 4
            frame_cell_h = cell_h - max_legenda_h - 4
            # Redimensionar imagem para caber na célula do frame
            tempo_font_size = max(fonte_tamanho-6, 8)
            tempo_h = tempo_font_size + 2
            max_img_h = frame_cell_h - tempo_h - 4
            ratio = min(cell_w / img_w * 3.78, max_img_h / img_h_px * 3.78)
            new_w = int(img_w * ratio)
            new_h = int(img_h_px * ratio)
            img_resized = img.resize((new_w, new_h), Image.LANCZOS)
            temp_img_path = os.path.join(temp_dir, f'frame_leve_grid_{idx:05d}.jpg')
            img_resized.save(temp_img_path, 'JPEG', quality=100)
            x_img = x0 + (cell_w - new_w / 3.78) / 2
            y_img = frame_cell_y
            pdf.image(temp_img_path, x=x_img, y=y_img, w=new_w / 3.78, h=new_h / 3.78)
            # Tempo logo abaixo do frame
            tempo_str = f"{format_time(start)} - {format_time(end)}"
            tempo_margin = 8
            y_tempo = y_img + (new_h / 3.78) + 2
            pdf.set_xy(x0 + tempo_margin, y_tempo)
            pdf.set_font(fonte_nome, style='B', size=tempo_font_size)
            pdf.set_text_color(200, 0, 0)
            pdf.cell(cell_w - 2*tempo_margin, tempo_h, tempo_str, ln=0, align='C')

    cap.release()
    pdf.output(output_pdf)
    print(f"PDF leve em grid gerado: {output_pdf}")

if __name__ == '__main__':
    # 2x3 grid
    gerar_pdf_leve_grid(video_path, srt_path, 'hq_livro_leve_2x3.pdf', colunas=2, linhas=3)
    # 1x6 grid
    gerar_pdf_leve_grid(video_path, srt_path, 'hq_livro_leve_1x6.pdf', colunas=1, linhas=6)
