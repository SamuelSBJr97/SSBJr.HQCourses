#!/usr/bin/env python3

"""
Extrai parágrafos de um PDF e renderiza cada parágrafo em uma imagem PNG.

Baseado em PyMuPDF para extração de texto e Pillow para renderização.

Exemplos (PowerShell/Windows):
  python .\scripts\pdf_paragraphs_to_images.py -i "C:\\caminho\\arquivo.pdf" -o .\out
  python .\scripts\pdf_paragraphs_to_images.py -i .\docs\exemplo.pdf -o .\out --width 1024 --font-size 22

Requisitos:
  pip install PyMuPDF Pillow
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable, List

import sys

try:
    import fitz  # PyMuPDF
except Exception as exc:
    print("Erro: PyMuPDF não está instalado. Instale com: pip install PyMuPDF", file=sys.stderr)
    raise

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception as exc:
    print("Erro: Pillow não está instalado. Instale com: pip install Pillow", file=sys.stderr)
    raise


def _load_font(font_path: Path | None, font_size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if font_path is not None:
        try:
            return ImageFont.truetype(font_path.as_posix(), font_size)
        except Exception:
            pass
    # fallback para fonte padrão do Pillow
    return ImageFont.load_default()


def _normalize_block_text(text: str) -> str:
    # junta hifenizações no final da linha e converte quebras simples em espaços
    text = re.sub(r"-\n\s*", "", text)
    text = re.sub(r"\n+", " ", text)
    # normaliza espaços múltiplos
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_paragraphs_from_page(page: "fitz.Page") -> List[str]:
    """Extrai parágrafos aproximados a partir de blocos de texto do PyMuPDF.

    Observação: Considera cada bloco de texto (type=0) como um parágrafo.
    Para a maioria dos PDFs, isso oferece um agrupamento razoável.
    """
    paragraphs: List[str] = []
    data = page.get_text("dict")
    for block in data.get("blocks", []):
        if block.get("type") != 0:  # não é texto
            continue
        lines = block.get("lines", [])
        parts: List[str] = []
        for line in lines:
            spans = line.get("spans", [])
            for sp in spans:
                parts.append(sp.get("text", ""))
            parts.append("\n")
        text = _normalize_block_text("".join(parts))
        if text:
            paragraphs.append(text)
    return paragraphs


def wrap_text_to_width(text: str, font: ImageFont.ImageFont, max_width: int, draw: ImageDraw.ImageDraw) -> List[str]:
    words = text.split(" ")
    lines: List[str] = []
    current: List[str] = []

    def text_width(s: str) -> int:
        # usa textbbox para medição precisa
        bbox = draw.textbbox((0, 0), s, font=font)
        return bbox[2] - bbox[0]

    for w in words:
        candidate = (" ".join(current + [w])).strip()
        if not candidate:
            continue
        if text_width(candidate) <= max_width:
            current.append(w)
        else:
            if current:
                lines.append(" ".join(current))
                current = [w]
            else:
                # palavra isolada maior que max_width: força quebra
                lines.append(w)
                current = []
    if current:
        lines.append(" ".join(current))
    return lines


def render_paragraph(
    text: str,
    out_path: Path,
    width: int,
    font: ImageFont.ImageFont,
    margin: int = 32,
    line_spacing: float = 1.35,
    fg_color: str = "#000000",
    bg_color: str = "#FFFFFF",
) -> None:
    # imagem temporária para medir
    temp_img = Image.new("RGB", (width, 10), bg_color)
    draw = ImageDraw.Draw(temp_img)

    lines = wrap_text_to_width(text, font, width - 2 * margin, draw)

    # altura da linha baseada no bbox de uma amostra
    ascent, descent = font.getmetrics() if hasattr(font, "getmetrics") else (font.size, int(font.size * 0.25))
    base_line_height = ascent + descent
    line_height = int(base_line_height * line_spacing)

    height = max(1, len(lines)) * line_height + 2 * margin
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    y = margin
    for ln in lines:
        draw.text((margin, y), ln, fill=fg_color, font=font)
        y += line_height

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path.as_posix())


def convert_pdf_paragraphs_to_images(
    input_pdf: Path,
    output_dir: Path,
    width: int = 1024,
    font_path: Path | None = None,
    font_size: int = 22,
    margin: int = 32,
    line_spacing: float = 1.35,
    fg_color: str = "#000000",
    bg_color: str = "#FFFFFF",
    start_page: int | None = None,
    end_page: int | None = None,
    min_length: int = 1,
    overwrite: bool = False,
    prefix: str = "",
) -> int:
    """Processa o PDF e gera imagens por parágrafo. Retorna quantidade gerada."""
    if not input_pdf.exists():
        raise FileNotFoundError(f"PDF não encontrado: {input_pdf}")

    doc = fitz.open(input_pdf.as_posix())
    try:
        total_pages = doc.page_count
        start = start_page or 1
        end = end_page or total_pages
        if start < 1 or end < 1 or start > total_pages or end > total_pages or start > end:
            raise ValueError(
                f"Intervalo de páginas inválido: start={start}, end={end}, total={total_pages}"
            )

        output_dir.mkdir(parents=True, exist_ok=True)
        font = _load_font(font_path, font_size)
        generated = 0

        for page_index in range(start - 1, end):
            page = doc.load_page(page_index)
            paragraphs = extract_paragraphs_from_page(page)
            para_idx = 0
            for para in paragraphs:
                if len(para.strip()) < min_length:
                    continue
                para_idx += 1
                out_path = output_dir / f"{prefix}page_{page_index + 1:04d}_para_{para_idx:04d}.png"
                if out_path.exists() and not overwrite:
                    continue
                render_paragraph(
                    para,
                    out_path,
                    width=width,
                    font=font,
                    margin=margin,
                    line_spacing=line_spacing,
                    fg_color=fg_color,
                    bg_color=bg_color,
                )
                generated += 1

        return generated
    finally:
        doc.close()


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Converte parágrafos de um PDF em imagens PNG")
    p.add_argument("-i", "--input", type=Path, required=True, help="Caminho para o PDF de entrada")
    p.add_argument("-o", "--output", type=Path, required=True, help="Diretório de saída")
    p.add_argument("--width", type=int, default=1024, help="Largura da imagem (px). Padrão: 1024")
    p.add_argument("--font-path", type=Path, default=None, help="Caminho para arquivo .ttf/.otf da fonte (opcional)")
    p.add_argument("--font-size", type=int, default=22, help="Tamanho da fonte em px. Padrão: 22")
    p.add_argument("--margin", type=int, default=32, help="Margem interna em px. Padrão: 32")
    p.add_argument("--line-spacing", type=float, default=1.35, help="Espaçamento entre linhas. Padrão: 1.35")
    p.add_argument("--fg", type=str, default="#000000", help="Cor do texto (hex). Padrão: #000000")
    p.add_argument("--bg", type=str, default="#FFFFFF", help="Cor do fundo (hex). Padrão: #FFFFFF")
    p.add_argument("--start-page", type=int, default=None, help="Página inicial (1-index). Padrão: 1")
    p.add_argument("--end-page", type=int, default=None, help="Página final (1-index). Padrão: última")
    p.add_argument("--min-length", type=int, default=1, help="Descarta parágrafos com menos caracteres que isso")
    p.add_argument("--overwrite", action="store_true", help="Sobrescreve imagens já existentes")
    p.add_argument("--prefix", type=str, default="", help="Prefixo para nomes de arquivos gerados")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        count = convert_pdf_paragraphs_to_images(
            input_pdf=args.input,
            output_dir=args.output,
            width=args.width,
            font_path=args.font_path,
            font_size=args.font_size,
            margin=args.margin,
            line_spacing=args.line_spacing,
            fg_color=args.fg,
            bg_color=args.bg,
            start_page=args.start_page,
            end_page=args.end_page,
            min_length=args.min_length,
            overwrite=args.overwrite,
            prefix=args.prefix,
        )
        print(f"Concluído: {count} imagem(ns) de parágrafos gerada(s) em {args.output}")
        return 0
    except Exception as e:
        print(f"Falha: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
