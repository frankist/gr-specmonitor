SHELL=/bin/bash

SIM_NAME = AWGN
SIM_PARAM_FILE = sim_awgn_params.py
SIM_DATASET = $(shell python sim_awgn.py get_filenames)

all:	$(SIM_DATASET)

start:
	mkdir -p $(SIM_NAME)
	sim_awgn.py start_sim $(SIM_PARAM_FILE)

%.pkl:
	mkdir -p results
	python sim.py $(shell python sim_manager.py command_args $@)

# python sim_manager.py print_filename $@
