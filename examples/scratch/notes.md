#

## Error PARSE-003: 
we should be clear what is going on. we should say "invalid section name <invalid_key>, valid names are: ports, parameters, backends

## LINT-001
(venv) jianxunzhu@Jianxuns-MacBook-Pro scratch % asdlc netlist tb.asdl  --backend sim.ngspice
warning LINT-001: Unused import namespace 'dut'.
  note: No source span available.

## PASS-001
MN<P> is not identified as part of MN<P,N>

## import system
need to resolve system env vars. say $PDK_MODEL_DIR

## Title
what netlist header do we need to emit? more placeholders?

## No source spans
(venv) jianxunzhu@Jianxuns-MacBook-Pro mosbius_devices % asdlc netlist ./ota_nmos.asdl
error EMIT-005: Instance 'MN_TAIL' is missing conns for ports: D
  note: No source span available.
warning LINT-001: Unused import namespace 'gf'.
  note: No source span available.
(venv) jianxunzhu@Jianxuns-MacBook-Pro mosbius_devices % 


## instantiation pin bindings 

```
MN_TAIL: mos.nmos_unit m=2 (B:$VSS, S:$VSS)
MN_IN_<P|N>: mos.nmos_unit m=1 (B:$VSS)
MP_<DIO|OUT>: mos.pmos_unit m=3 (B:$VDD, S:$VDD)
```