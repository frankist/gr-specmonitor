SHELL=/bin/bash

SIM_NAME = sim0
SIM_PARAM_FILE = sim_awgn_params.py
SIM_EXEC = python sim_awgn.py
RUN_CMD = $(SIM_EXEC) $(SIM_NAME)
SIM_DATASET = $(shell $(RUN_CMD) get_filenames Tx)

all:	start_session $(SIM_DATASET)

start_session:
	mkdir -p $(SIM_NAME)
	cd $(SIM_NAME)
	$(RUN_CMD) start_session $(SIM_PARAM_FILE)

waveform/data_%.pkl: start
	mkdir -p $(SIM_NAME)/waveform
	$(RUN_CMD) generate_waveform $@

Tx/data_%.pkl: $(shell $(RUN_CMD) get_dependency $@)
	mkdir -p $(SIM_NAME)/Tx
	$(RUN_CMD) apply_transformations $@

clean:
	rm $(SIM_NAME)/waveform/*
	rm $(SIM_NAME)/*.pkl

# python sim_awgn.py $(shell python sim_awgn.py command_args $@)
# python sim_manager.py print_filename $@
