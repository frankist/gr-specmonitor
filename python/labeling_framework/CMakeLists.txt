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
    __init__.py DESTINATION ${GR_PYTHON_DIR}/specmonitor/labeling_framework
)

add_subdirectory(data_representation)
add_subdirectory(utils)
add_subdirectory(labeling_tools)
