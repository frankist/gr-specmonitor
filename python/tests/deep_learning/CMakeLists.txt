########################################################################
# Include python install macros
########################################################################
include(GrPython)
if(NOT PYTHONINTERP_FOUND)
    return()
endif()

########################################################################
# Handle the unit tests
########################################################################

add_test(test_voc_setup ${PYTHON_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/test_voc_setup.py)

