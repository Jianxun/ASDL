#!/bin/bash
export PROJECT_ROOT=$(pwd)

# PDK
export PDK=gf180mcu
export PDK_PATH=$PROJECT_ROOT/pdks/$PDK
export PDK_ASDL_PATH=$PDK_PATH/asdl
export PDK_MODEL_PATH=$PDK_PATH/ngspice

# ASDL common libs
export ASDL_COMMON_LIBS_PATH=$PROJECT_ROOT/libs_common

# ASDL design libs
export ASDL_DESIGN_LIBS_PATH=$PROJECT_ROOT/libs

# ASDL path
export ASDL_PATH=$PDK_ASDL_PATH:$ASDL_COMMON_LIBS_PATH:$ASDL_DESIGN_LIBS_PATH


