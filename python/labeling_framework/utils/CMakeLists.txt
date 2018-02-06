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
file(GLOB all_python_files
  "*.py"
)

GR_PYTHON_INSTALL(
    FILES
    ${all_python_files}
    DESTINATION ${GR_PYTHON_DIR}/specmonitor/labeling_framework/utils
)
