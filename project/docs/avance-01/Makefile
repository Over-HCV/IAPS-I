LATEXMK   := latexmk
BUILDDIR  := build
MAIN      := main-es
FINALFLAG := .final-mode

# FINAL=1 oculta las cajas \limite y \nota (versión entregable) creando .final-mode.
# Los \TODO siguen visibles en rojo a propósito: un documento no se entrega con
# campos sin llenar.
.PHONY: es watch wordcount clean

# El flag .final-mode se lee con \IfFileExists desde common/macros.tex, pero latexmk
# NO puede saber que es una dependencia: cuando no existe no aparece en el .fls, y
# tocar el driver tampoco basta porque latexmk compara por hash, no por mtime. Por eso
# el modo se registra en build/.mode y, cuando cambia, se recompila con -g (forzado).
# Sin esto `make es FINAL=1` devuelve el PDF de borrador sin avisar de nada.
es:
	@mkdir -p $(BUILDDIR)
	@if [ -n "$(FINAL)" ]; then echo final > $(BUILDDIR)/.mode.new; touch $(FINALFLAG); \
	 else echo draft > $(BUILDDIR)/.mode.new; rm -f $(FINALFLAG); fi
	@if ! cmp -s $(BUILDDIR)/.mode.new $(BUILDDIR)/.mode 2>/dev/null; then \
	   echo "modo cambiado -> recompilación forzada"; echo FORCE > $(BUILDDIR)/.force; \
	 else rm -f $(BUILDDIR)/.force; fi
	@mv $(BUILDDIR)/.mode.new $(BUILDDIR)/.mode
	$(LATEXMK) $$([ -f $(BUILDDIR)/.force ] && echo -g) -pdfxe -outdir=$(BUILDDIR) $(MAIN).tex
	@rm -f $(BUILDDIR)/.force

watch:
	rm -f $(FINALFLAG)
	$(LATEXMK) -pdfxe -outdir=$(BUILDDIR) -pvc $(MAIN).tex

# Conteo de palabras por sección. Informativo: el curso no fija límites
# (wordlimits.txt todo en 0); sirve para no inflar el documento.
wordcount:
	@command -v texcount >/dev/null || { echo "texcount no está instalado (viene con TeXLive)"; exit 1; }
	@printf '%-34s %8s %8s   %s\n' SECCIÓN PALABRAS LÍMITE ESTADO
	@printf '%s\n' '---------------------------------------------------------------------'
	@total=0; over=0; \
	while IFS=: read -r file limit; do \
	  [ -f "secciones/$$file" ] || continue; \
	  n=$$(texcount -1 -sum -merge -q "secciones/$$file" 2>/dev/null | tr -d ' '); \
	  n=$${n:-0}; total=$$((total + n)); \
	  if [ "$$limit" = "0" ]; then \
	    printf '%-34s %8s %8s   %s\n' "$$file" "$$n" "--" "sin límite"; \
	  elif [ "$$n" -gt "$$limit" ]; then \
	    printf '%-34s %8s %8s   %s\n' "$$file" "$$n" "$$limit" "SE PASA POR $$((n - limit))"; over=1; \
	  else \
	    printf '%-34s %8s %8s   %s\n' "$$file" "$$n" "$$limit" "ok ($$((limit - n)) libres)"; \
	  fi; \
	done < wordlimits.txt; \
	printf '%s\n' '---------------------------------------------------------------------'; \
	printf '%-34s %8s\n' 'TOTAL' "$$total"; \
	[ "$$over" = "0" ] || { echo; echo "Hay secciones por encima del límite."; exit 1; }

clean:
	$(LATEXMK) -C -outdir=$(BUILDDIR) $(MAIN).tex 2>/dev/null || true
	rm -rf $(BUILDDIR)
	rm -f $(FINALFLAG)
	rm -f $(MAIN).aux $(MAIN).bbl $(MAIN).bcf $(MAIN).blg $(MAIN).fdb_latexmk \
	      $(MAIN).fls $(MAIN).log $(MAIN).out $(MAIN).run.xml $(MAIN).synctex.gz \
	      $(MAIN).toc $(MAIN).xdv $(MAIN).pdf 2>/dev/null || true
