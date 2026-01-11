#!/bin/bash

# MUST BE SOURCED IN THIS DIRECTORY
export PROJECT_ROOT=$(pwd)

# ASDL Backend Config
export ASDL_BACKEND_CONFIG=$PROJECT_ROOT/config/backends.yaml

# PDK
export PDK=gf180mcu
export PDK_PATH=$PROJECT_ROOT/pdks/$PDK

# ASDL common libs
export ASDL_COMMON_LIBS_PATH=$PROJECT_ROOT/libs_common

# ASDL common libs
export ASDL_ANALOGLIB_PATH=$PROJECT_ROOT/libs_common/analoglib

# ASDL design libs
export ASDL_DESIGN_LIBS_PATH=$PROJECT_ROOT/libs

# ASDL path
export ASDL_PATH=$ASDL_ANALOGLIB_PATH:$PDK_ASDL_PATH:$ASDL_COMMON_LIBS_PATH:$ASDL_DESIGN_LIBS_PATH


