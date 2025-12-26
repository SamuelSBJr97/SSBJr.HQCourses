#!/usr/bin/env python3

r"""
Converter PDF em PNG por página usando PyMuPDF (fitz).

Uso básico (PowerShell/Windows):
    python .\scripts\pdf_to_png.py -i "C:\\caminho\\arquivo.pdf" -o .\saidas --dpi 200

Requerimentos:
    pip install PyMuPDF
"""

import argparse
from pathlib import Path
import sys

try:
    import fitz  # PyMuPDF
except Exception as exc:
    print("Erro: PyMuPDF não está instalado. Instale com: pip install PyMuPDF", file=sys.stderr)
    raise


def convert_pdf_to_png(
    input_pdf: Path,
    output_dir: Path,
    dpi: int = 200,
    start_page: int | None = None,
    end_page: int | None = None,
    transparent: bool = False,
    prefix: str = "",
    overwrite: bool = False,
) -> int:
    """Converte páginas do PDF para PNG.

    Retorna o número de imagens geradas.
    """
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

        # DPI para escala: 72 DPI é 1.0
        scale = dpi / 72.0
        matrix = fitz.Matrix(scale, scale)

        output_dir.mkdir(parents=True, exist_ok=True)

        generated = 0
        for page_index in range(start - 1, end):
            page = doc.load_page(page_index)
            # alpha=1 adiciona canal alpha (transparência)
            pix = page.get_pixmap(matrix=matrix, alpha=1 if transparent else 0)

            out_path = output_dir / f"{prefix}page_{page_index + 1:04d}.png"
            if out_path.exists() and not overwrite:
                # pula se já existe e overwrite=False
                continue

            pix.save(out_path.as_posix())
            generated += 1

        return generated
    finally:
        doc.close()


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Converte um PDF em imagens PNG por página (PyMuPDF)",
    )
    p.add_argument(
        "-i",
        "--input",
        type=Path,
        required=True,
        help="Caminho para o arquivo PDF de entrada",
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Diretório de saída para as PNG",
    )
    p.add_argument(
        "--dpi",
        type=int,
        default=200,
        help="Resolução (DPI) para renderização (padrão: 200)",
    )
    p.add_argument(
        "--start-page",
        type=int,
        default=None,
        help="Página inicial (1-index). Padrão: 1",
    )
    p.add_argument(
        "--end-page",
        type=int,
        default=None,
        help="Página final (1-index). Padrão: última",
    )
    p.add_argument(
        "--transparent",
        action="store_true",
        help="Gera PNG com fundo transparente (alpha)",
    )
    p.add_argument(
        "--prefix",
        type=str,
        default="",
        help="Prefixo para o nome dos arquivos gerados",
    )
    p.add_argument(
        "--overwrite",
        action="store_true",
        help="Sobrescreve arquivos existentes se já houver PNG gerada",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        count = convert_pdf_to_png(
            input_pdf=args.input,
            output_dir=args.output,
            dpi=args.dpi,
            start_page=args.start_page,
            end_page=args.end_page,
            transparent=args.transparent,
            prefix=args.prefix,
            overwrite=args.overwrite,
        )
        print(f"Conversão concluída: {count} PNG(s) gerada(s) em {args.output}")
        return 0
    except Exception as e:
        print(f"Falha na conversão: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
