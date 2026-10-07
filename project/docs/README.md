# `docs/` — template LaTeX de los documentos del curso

Tres carpetas compartidas + una carpeta por entregable. La estructura es el template:
crear un documento nuevo es crear una carpeta que cuelgue de aquí.

```
common/          preamble.tex, macros.tex, meta-es.tex — compartido por TODO documento
bib/refs.bib     bibliografía única (citar siempre desde aquí, nunca crear otro .bib)
assets/pics/     logo UR compartido
avance/          Avance de Proyecto 1 (calificado como quiz)
final/           documento final del proyecto (por crear)
```

## Cómo crear un documento nuevo (p. ej. `final/`)

1. Copiar de `avance/`: `Makefile`, `.latexmkrc`, `.gitignore` (los tres intactos).
2. Crear `main-es.tex` calcado del del avance: cambia `\docNombre` y la lista de
   `\input` de secciones. Nada más — el preámbulo, los macros y los metadatos vienen
   de `../common/`.
3. Crear `secciones/` y, si se quiere conteo por sección, `wordlimits.txt`.

## Reglas del template

- Las rutas de `common/preamble.tex` (`../common`, `../assets/pics`, `../bib/refs.bib`)
  son relativas a la carpeta del documento: mover algo las rompe.
- `\docNombre` lo define cada `main-es.tex` (sale en el encabezado de página);
  los metadatos del proyecto viven una sola vez en `common/meta-es.tex`.
- `make es` compila borrador; `make es FINAL=1` oculta las cajas `\limite`/`\nota`;
  `make watch` recompila en vivo; `make wordcount` cuenta por sección.
- La consigna oficial de cada entregable vive como `intro.md` dentro de su carpeta
  (la del avance es la del curso). Si la consigna cambia, ese archivo manda.
- Entradas bibliográficas: reutilizar las de `bib/refs.bib`; las que vengan del repo
  de Tesis-MACC se copian verbatim y se marca el origen en un comentario.
