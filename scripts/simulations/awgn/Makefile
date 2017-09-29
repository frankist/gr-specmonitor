SHELL=/bin/bash

SIM_NAME = sim0
SIMPATH = ./$(SIM_NAME)
SESSION_HANDLER_FILE = $(SIMPATH)/$(SIM_NAME)_handler.pkl
SIM_PARAM_FILE = sim_awgn_params.py
SIM_EXEC = python sim_awgn.py

RUN_CMD = $(SIM_EXEC) $(SESSION_HANDLER_FILE)
Tx_DATASET = $(shell $(RUN_CMD) get_filenames Tx)
WAVEFORM_DATASET = $(shell $(RUN_CMD) get_filenames waveform)

# PREPROCESSING STAGE
# NOTE: I needed to do this, bc makefile prerequisites do not allow stipulating an order.
#       If order is not stipulated, I can't guarantee that the cfg file exists before generating filenames

define SESSIONPRERUN
mkdir -p $(SIMPATH);
mkdir -p $(SIMPATH)/waveform;
mkdir -p $(SIMPATH)/Tx;
$(RUN_CMD) parse_config $(SIM_NAME) $(SIM_PARAM_FILE)
endef
PRERUN:=$(shell $(SESSIONPRERUN))
PRECIOUSFILES := $(WAVEFORM_DATASET)

# END PREPROCESSING STAGE

.PRECIOUS: $(WAVEFORM_DATASET)
# .SECONDARY:
.SECONDEXPANSION:

all: $(SESSION_HANDLER_FILE) $(Tx_DATASET)

clean:
	@echo Cleaning Simulation Files
	rm -rf $(SIMPATH)/*

restart: clean $(SESSION_HANDLER_FILE)
	@echo Making new session file

$(SESSION_HANDLER_FILE):
	@echo New session is being generated
	$(SESSIONPRERUN)

$(SIMPATH)/waveform/data_%.pkl: $(SESSION_HANDLER_FILE)
	$(RUN_CMD) generate_waveform $@

$(SIMPATH)/Tx/data_%.pkl: $$(shell $(RUN_CMD) get_dependencies $$@)
	$(RUN_CMD) apply_transformations $@

#$(shell $(RUN_CMD) get_filenames waveform) $(SESSION_HANDLER_FILE)
#@echo $(shell $(RUN_CMD) get_dependencies $@)
#$$(shell $(RUN_CMD) get_filenames $$@)
# python sim_awgn.py $(shell python sim_awgn.py command_args $@)
# python sim_manager.py print_filename $@
