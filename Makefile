# Phase 1/Phase 2 CI targets.
#
# Most actual work lives in Python tests under tests/; this Makefile is a
# thin wrapper that is easier for CI pipelines to invoke than remembering
# the right python3 module path.

PY ?= python3

.PHONY: all test coverage check-struct-layout check-c-python-parity check-orbit-tables-gen check-golden-refs clean

all: test

test: check-struct-layout check-orbit-tables-gen check-c-python-parity check-golden-refs
	$(PY) -m unittest discover -v tests

check-struct-layout:
	./tests/test_struct_layout.sh

check-orbit-tables-gen:
	$(PY) -m unittest tests.test_orbit_tables_gen -v

check-c-python-parity:
	$(PY) -m unittest tests.test_c_python_parity -v

check-golden-refs:
	$(PY) -m unittest tests.test_golden_refs -v

# Optional: requires `python3 -m pip install coverage`
coverage:
	$(PY) -m coverage erase
	$(PY) -m coverage run --source=orbit_config,ddr_config_init,gui -m unittest discover -q tests
	$(PY) -m coverage report -m

clean:
	rm -f ddr_config_bin_exec ddr_config_bin_parity_exec dump_struct_layout
