"""
Script para montar páginas de revista HQ a partir de frames PNG.
- Junta frames em páginas (A4), adiciona cabeçalho e rodapé (texto ou imagem).
- Salva como PDF.

Requisitos: Pillow, PyMuPDF (pip install pillow pymupdf)
"""

import os
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF

# CONFIGURAÇÕES
frames_dir = 'frames_legendados'  # Pasta com os frames PNG
output_pdf = 'hq_comic.pdf'
frames_por_pagina = 6  # 2 colunas x 3 linhas por página
pagina_tamanho = (2480, 3508)  # A4 em pixels a 300dpi (vertical)
cabecalho_texto = 'Minha HQ - Título do Capítulo'
rodape_texto = 'SamuelSBJr97 - 2025'
# Para usar imagem, defina cabecalho_imagem = 'caminho.png' (ou None)
cabecalho_imagem = None
rodape_imagem = None
fonte_path = None  # Ou caminho para .ttf
fonte_tamanho = 60

# Carrega frames
frames = [os.path.join(frames_dir, f) for f in sorted(os.listdir(frames_dir), key=str.lower) if f.lower().endswith('.png')]

# Fonte
try:
    fonte = ImageFont.truetype(fonte_path or "arial.ttf", fonte_tamanho)
except:
    fonte = ImageFont.load_default()

paginas = []
if frames:
    # Carrega o primeiro frame para referência de tamanho
    ref_img = Image.open(frames[0])
    frame_w, frame_h = ref_img.size
    # Espaço vertical útil
    y = 40
    if cabecalho_imagem:
        cab_img = Image.open(cabecalho_imagem)
        y += cab_img.height + 20
    elif cabecalho_texto:
        y += fonte_tamanho + 20
    h_util = pagina_tamanho[1] - y - (fonte_tamanho + 60)
    # Calcula quantos frames cabem na vertical (sem distorcer, com margem)
    # Layout HQ: 2 colunas x 3 linhas
    colunas = 2
    linhas = 3
    espacamento_x = 20
    espacamento_y = 20
    largura_util = pagina_tamanho[0] - 2*60 - (colunas-1)*espacamento_x
    altura_util = h_util - (linhas-1)*espacamento_y
    frame_w_hq = largura_util // colunas
    frame_h_hq = altura_util // linhas

    for i in range(0, len(frames), frames_por_pagina):
        page = Image.new('RGB', pagina_tamanho, (255, 255, 255))
        draw = ImageDraw.Draw(page)

        # Cabeçalho
        y_top = 40
        if cabecalho_imagem:
            cab_img = Image.open(cabecalho_imagem)
            page.paste(cab_img, (int((pagina_tamanho[0]-cab_img.width)/2), y_top))
            y_top += cab_img.height + 20
        elif cabecalho_texto:
            draw.text((pagina_tamanho[0]//2, y_top), cabecalho_texto, font=fonte, fill=(0,0,0), anchor="ma")
            y_top += fonte_tamanho + 20

        # Espaço útil para frames

            for j, frame_path in enumerate(frames[i:i+frames_por_pagina]):
                img = Image.open(frame_path)
                # Recorta para mostrar apenas a área da legenda e imagem principal
                legenda_pct = 0.20
                borda_pct = 0.05
                left = int(img.width * borda_pct)
                right = img.width - int(img.width * borda_pct)
                top = int(img.height * borda_pct)
                bottom = img.height
                img_cropped = img.crop((left, top, right, bottom))
                # Redimensiona para HQ
                img_cropped = img_cropped.resize((frame_w_hq, frame_h_hq), Image.LANCZOS)
                img_rgb = img_cropped.convert("RGB")
                from io import BytesIO
                buffer = BytesIO()
                img_rgb.save(buffer, format='JPEG', quality=80, optimize=True)
                buffer.seek(0)
                img_jpeg = Image.open(buffer)
                # Calcula posição (coluna, linha)
                linha = j // colunas
                coluna = j % colunas
                x_pos = 60 + coluna * (frame_w_hq + espacamento_x)
                y_pos = y_top + linha * (frame_h_hq + espacamento_y)
                page.paste(img_jpeg, (x_pos, y_pos))

        # Rodapé
        y_rodape = pagina_tamanho[1] - fonte_tamanho - 40
        if rodape_imagem:
            rod_img = Image.open(rodape_imagem)
            page.paste(rod_img, (int((pagina_tamanho[0]-rod_img.width)/2), y_rodape))
        elif rodape_texto:
            draw.text((pagina_tamanho[0]//2, y_rodape), rodape_texto, font=fonte, fill=(0,0,0), anchor="ma")

        paginas.append(page)

# Salva como PDF usando apenas Pillow
if paginas:
    paginas[0].save(
        output_pdf,
        "PDF",
        resolution=300,
        save_all=True,
        append_images=paginas[1:],
        quality=80,
        optimize=True
    )
    print(f"PDF HQ gerado: {output_pdf}")
else:
    print("Nenhuma página gerada!")
