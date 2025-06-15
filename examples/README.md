# ASDL Examples

This directory contains example ASDL (Analog Structural Description Language) files that demonstrate the usage of the ASDL schema v0.4.

## Available Examples

1. **inverter.yml**
   - A basic CMOS inverter design
   - Demonstrates simple device instantiation and port mapping
   - Shows basic intent specification for operation and layout

2. **two_stage_ota.yml**
   - A two-stage Miller-compensated operational transconductance amplifier
   - Demonstrates hierarchical module composition
   - Shows complex port constraints and differential pair patterns
   - Includes Miller compensation network
   - Demonstrates parameter propagation and device multiplicity

## Schema Version

All examples follow the ASDL schema v0.4 specification, which includes:
- Design information and metadata
- Model definitions with port ordering
- Module hierarchy with ports, nets, and instances
- Intent specification for operation and layout
- Parameter propagation and device multiplicity
- Pattern expansion rules for differential and bus structures 