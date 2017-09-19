SHELL=/bin/bash

SIM_DATASET = $(shell python sim_manager.py generate_filenames)

all:	$(SIM_DATASET)

%.pkl:
	python sim_manager.py print_filename $@
	mkdir -p results
	python sim.py $(shell python sim_manager.py command_args $@)
