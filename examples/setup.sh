#!/bin/bash

# MUST BE SOURCED IN THIS DIRECTORY
export PROJECT_ROOT=$(pwd)

# ASDL Backend Config
export ASDL_BACKEND_CONFIG=$PROJECT_ROOT/config/backends.yaml

# PDK
export PDK=gf180mcu
export PDK_PATH=$PROJECT_ROOT/pdks/$PDK
export PDK_ASDL_PATH=$PDK_PATH/asdl
# ASDL design libs
export ASDL_DESIGN_LIBS_PATH=$PROJECT_ROOT/libs

# ASDL path
export ASDL_LIB_PATH=$PDK_ASDL_PATH:$ASDL_DESIGN_LIBS_PATH


