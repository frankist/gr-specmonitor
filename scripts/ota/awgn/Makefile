SHELL:=/bin/bash

SIM_NAME = sim0
SIMPATH = ./$(SIM_NAME)
SESSION_HANDLER_FILE = $(SIMPATH)/$(SIM_NAME)_handler.pkl
SIM_PARAM_FILE = sim_awgn_params.py

SIM_EXEC = /usr/bin/python2 -u sim_awgn.py
RUN_CMD = $(SIM_EXEC) $(SESSION_HANDLER_FILE) $(SIM_PARAM_FILE)

# PREPROCESSING STAGE
# NOTE: I needed to do this, bc makefile prerequisites do not allow stipulating an order.
#       If order is not stipulated, I can't guarantee that the cfg file exists before generating filenames

define SESSIONPRERUN
$(RUN_CMD) load_session ;
#mkdir -p $(SIMPATH);
#mkdir -p $(SIMPATH)/waveform;
#mkdir -p $(SIMPATH)/Tx;
#mkdir -p $(SIMPATH)/RF;
$(RUN_CMD) check_handler
endef
PRERUN:=$(shell $(SESSIONPRERUN))
Tx_DATASET := $(shell $(RUN_CMD) get_filenames Tx)
RF_DATASET := $(shell $(RUN_CMD) get_filenames RF)
WAVEFORM_DATASET := $(shell $(RUN_CMD) get_filenames waveform)
PRECIOUSFILES := $(WAVEFORM_DATASET)

# END PREPROCESSING STAGE

.PRECIOUS: PRECIOUSFILES
# .SECONDARY:
.SECONDEXPANSION:

all: RF

clean:
	@echo Cleaning Simulation Files
	rm -rf $(SIMPATH)/*

restart: clean
	@echo Making new session file
	$(RUNCMD) setup_new_session

waveform: $(WAVEFORM_DATASET)

Tx: $(Tx_DATASET)

RF: $(RF_DATASET)

$(SIMPATH)/waveform/data_%.pkl:
	$(RUN_CMD) generate_waveform $@

$(SIMPATH)/Tx/data_%.pkl: $$(shell $(RUN_CMD) get_dependencies $$@)
# sim0/Tx/data_%.pkl: $$(patsubst %,,$$@)sim0/waveform/data_.pkl
	$(RUN_CMD) apply_tx_transformations $@
	mkdir -p $(SIMPATH)/Tx/img
	$(RUN_CMD) get_spectrogram_img $@ True True

$(SIMPATH)/RF/data_%.pkl: $$(shell $(RUN_CMD) get_dependencies $$@)
	@idx=0 ; \
	while [ ! -f $@ ] ; do \
		$(RUN_CMD) run_RF_channel $@ ; \
		if [ $$idx -ne 0 ] ; then \
			echo "Repeating the RF+sync for $@. Trial number: $$idx" ; \
			if [ $$idx -gt 2 ] ; then \
				exit 1 ; \
			fi ; \
		fi ; \
		idx=`expr $$idx + 1` ; \
	done
	mkdir -p $(SIMPATH)/RF/img
	$(RUN_CMD) get_spectrogram_img $@ True True

# while [ ! -f $@ ]; do \
# 	@if [ $(idx) -ht 0 ]; then \
# 		@echo 'Repeating the RF+sync for $@' ; \
# 	fi \
# 	$(RUN_CMD) run_RF_channel $@ ; \
# 	idx=`expr $(idx) + 1` ; \
# done

# Need to make a while loop that goes on until the file is generated

#$(shell $(RUN_CMD) get_filenames waveform) $(SESSION_HANDLER_FILE)
#@echo $(shell $(RUN_CMD) get_dependencies $@)
#$$(shell $(RUN_CMD) get_filenames $$@)
# python sim_awgn.py $(shell python sim_awgn.py command_args $@)
# python sim_manager.py print_filename $@
