#!/bin/bash

#PYTHONPATH='.' luigi --module sim_awgn_luigi AWGNCmdSession --local-scheduler --stages-to-run RF --session-args "{\"session_path\":\"sim0\",\"cfg_file\":\"sim_awgn_params.py\"}" --clean-first True
PYTHONPATH='.' luigi --module sim_awgn_luigi AWGNCmdSession --local-scheduler
