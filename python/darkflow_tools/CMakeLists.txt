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
file(GLOB LOCAL_PYTHON_FILES
    "*.py"
)
GR_PYTHON_INSTALL(
    FILES
    ${LOCAL_PYTHON_FILES}
    DESTINATION ${GR_PYTHON_DIR}/specmonitor/darkflow_tools
)
