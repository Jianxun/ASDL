# ASDL Workflow Guidelines

## Overview

## ASDL Schema
Read `doc/schema/AI_AGENT_GUIDE.md`
Read `doc/schema/schema.json`

## Compile and netlisting
Use `asdlc netlist {filename}.asdl` to generate the `{filename}.spice` netlist


## Running simulations
Use `ngspice -b {filename}.spice` to run simulation.