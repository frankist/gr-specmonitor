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
  DESTINATION ${GR_PYTHON_DIR}/specmonitor/labeling_framework
)

add_subdirectory(core)
add_subdirectory(data_representation)
add_subdirectory(utils)
add_subdirectory(labeling_tools)
add_subdirectory(waveform_generators)
add_subdirectory(general_tasks)
