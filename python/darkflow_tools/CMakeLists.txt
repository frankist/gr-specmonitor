########################################################################
# Include python install macros
########################################################################
include(GrPython)
if(NOT PYTHONINTERP_FOUND)
    return()
endif()

########################################################################
# Install python sources
########################################################################
GR_PYTHON_INSTALL(
    FILES
    __init__.py
    darkflow_ckpt_classifier.py
    parse_yolo_cfg.py DESTINATION ${GR_PYTHON_DIR}/specmonitor/darkflow_tools
)
