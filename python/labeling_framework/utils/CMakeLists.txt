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
    basic_utils.py
    logging_utils.py DESTINATION ${GR_PYTHON_DIR}/specmonitor/labeling_framework/utils
)
