@default_files = ('main-es.tex');

# Fuerza xelatex + salida en build/ pase lo que pase (los editores pueden pasar
# flags que de otro modo pisan este archivo). Mismo esquema que project/.latexmkrc.
$pdf_mode  = 5;                       # 5 = xelatex
$out_dir   = 'build';
$aux_dir   = 'build';
$clean_ext = 'synctex.gz run.xml bbl bcf fls fdb_latexmk xdv';

$xelatex = 'xelatex -interaction=nonstopmode -synctex=1 %O %S';
$bibtex  = 'biber %O %S';
$maxrep  = 5;
