PYTHON ?= python3
.PHONY: validate smoke film tour watch glb
validate:
	$(PYTHON) tools/project.py validate
smoke:
	$(PYTHON) tools/project.py smoke
film:
	$(PYTHON) tools/project.py render film
	$(PYTHON) tools/project.py compose film
tour:
	$(PYTHON) tools/project.py render tour
	$(PYTHON) tools/project.py compose tour
	$(PYTHON) tools/project.py gif tour
watch:
	$(PYTHON) tools/project.py build watch
	$(PYTHON) tools/project.py render watch
	$(PYTHON) tools/project.py compose watch
	$(PYTHON) tools/project.py gif watch
glb:
	$(PYTHON) tools/project.py export
