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
    bounding_box.py DESTINATION ${GR_PYTHON_DIR}/specmonitor/labeling_framework/labeling_tools
)
