# Conversor PDF → PNG por página

Este utilitário converte arquivos PDF em imagens PNG, uma por página, usando a biblioteca PyMuPDF (fitz).

## Pré-requisitos
- Windows com Python 3.10+ instalado
- Biblioteca PyMuPDF

Instalação das dependências:

```powershell
python -m pip install -r requirements.txt
```

Alternativamente:

```powershell
python -m pip install PyMuPDF
```

## Uso
Exemplos em PowerShell, partindo do diretório do projeto:

- Converter todas as páginas com 200 DPI:
```powershell
python .\util\pdf_to_png.py -i "C:\caminho\para\arquivo.pdf" -o .\saidas --dpi 200
```

- Converter apenas um intervalo de páginas (da 3 à 10) com 300 DPI:
```powershell
python .\util\pdf_to_png.py -i "C:\caminho\para\arquivo.pdf" -o .\saidas --dpi 300 --start-page 3 --end-page 10
```

- Gerar PNG com fundo transparente e prefixo nos nomes:
```powershell
python .\util\pdf_to_png.py -i "C:\caminho\para\arquivo.pdf" -o .\saidas --dpi 200 --transparent --prefix "capitulo_"
```

## Saída
Os arquivos são salvos no diretório de saída com nomes no formato:
```
page_0001.png, page_0002.png, ...
```
Se você definir `--prefix`, o nome fica por exemplo:
```
capitulo_page_0001.png
```

## Observações
- `--overwrite` sobrescreve PNGs já existentes.
- A resolução é controlada por `--dpi` (72 DPI = escala 1.0). Valores maiores produzem imagens maiores e mais nítidas.
- O fundo transparente (`--transparent`) adiciona canal alpha às imagens geradas.
# Site (GitHub Pages)

Este repositório publica um site estático em `docs/` com catálogo de cursos e aulas em versão HQ.

Como funciona:
- Estrutura Jekyll em `docs/` com coleções de cursos (`_courses/`).
- Cada curso lista suas aulas com referência ao original em Markdown e link para o PDF `-hq`.

Adicionar um curso:
- Crie um arquivo em `docs/_courses/<slug>.md` com front matter e lista de aulas.
- Coloque o Markdown da aula em `docs/courses/<slug>/<aula>.md`.
- Coloque (ou referencie por URL) o PDF HQ em `docs/assets/courses/<slug>/<aula>-hq.pdf`.

Publicar no GitHub Pages:
1. Faça push para o GitHub.
2. Nas configurações do repositório, ative GitHub Pages com fonte "Deploy from a branch" e pasta `docs/`.
3. Acesse a URL gerada.
