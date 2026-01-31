# swmatrix_Tgate

(swmatrix_Tgate_doc)=
```{asdl:doc} swmatrix_Tgate_doc
```

## Overview
Switch Matrix Tgate
power:
  VDDd: nominal 3.3V
  VSSd: nominal 0V
digital:
  inputs:
    - control: active high control signal to close the Tgate
    - enable: active high enable signal shared by all Tgates
analog:
  T1, T2: symmetric analog terminals, rail-to-rail compliance.
specs:
  - Ron < 100 ohms @ 3.3V
  - Cpar < 20fF

## Imports

```{asdl:import} swmatrix_Tgate::gf_std
```

```{asdl:import} swmatrix_Tgate::gf
```

| Alias | Path | Description |
| --- | --- | --- |
| gf_std | gf180mcu_std.asdl |  |
| gf | gf180mcu.asdl |  |

## Module `swmatrix_Tgate`

```{asdl:module} swmatrix_Tgate
```

### Interface

```{asdl:port} swmatrix_Tgate::$VDDd
```

```{asdl:port} swmatrix_Tgate::$VSSd
```

```{asdl:port} swmatrix_Tgate::$control
```

```{asdl:port} swmatrix_Tgate::$enable
```

```{asdl:port} swmatrix_Tgate::$T1
```

```{asdl:port} swmatrix_Tgate::$T2
```

| Name | Kind | Direction | Description |
| --- | --- | --- | --- |
| $VDDd |  |  | nominal 3.3V |
| $VSSd |  |  |  |
| $control |  |  | active high control signal to close the Tgate |
| $enable |  |  |  |
| $T1 |  |  | Tgate analog terminal 1 |
| $T2 |  |  | Tgate analog terminal 2 |

### Variables

```{asdl:var} swmatrix_Tgate::L
```

```{asdl:var} swmatrix_Tgate::W
```

```{asdl:var} swmatrix_Tgate::NF
```

| Name | Default | Description |
| --- | --- | --- |
| L | 0.28u |  |
| W | 8u |  |
| NF | 6 |  |

### Instances

```{asdl:inst} swmatrix_Tgate::inv1
```

```{asdl:inst} swmatrix_Tgate::inv2
```

```{asdl:inst} swmatrix_Tgate::nand2
```

```{asdl:inst} swmatrix_Tgate::mn
```

```{asdl:inst} swmatrix_Tgate::mp
```

| Instance | Ref | Params | Description |
| --- | --- | --- | --- |
| inv1 | gf_std.inv_1 |  |  |
| inv2 | gf_std.inv_1 |  |  |
| nand2 | gf_std.nand2_1 |  |  |
| mn | gf.nfet_03v3 | L={L} W={W} NF={NF} m=1 |  |
| mp | gf.pfet_03v3 | L={L} W={W} NF={NF} m=3 | PMOS/NMOS ratio is 3:1 |

### Nets

```{asdl:net} swmatrix_Tgate::$VDDd
```

```{asdl:net} swmatrix_Tgate::$VSSd
```

```{asdl:net} swmatrix_Tgate::$control
```

```{asdl:net} swmatrix_Tgate::$enable
```

```{asdl:net} swmatrix_Tgate::net1
```

```{asdl:net} swmatrix_Tgate::gated_control
```

```{asdl:net} swmatrix_Tgate::gated_controlb
```

```{asdl:net} swmatrix_Tgate::$T1
```

```{asdl:net} swmatrix_Tgate::$T2
```

| Name | Endpoints | Description |
| --- | --- | --- |
| $VDDd | <inv1\|inv2\|nand2>.<VPWR\|VNB>, mp.b | nominal 3.3V |
| $VSSd | <inv1\|inv2\|nand2>.<VPB\|VGND>, mn.b |  |
| $control | nand2.A | active high control signal to close the Tgate |
| $enable | nand2.B |  |
| net1 | nand2.Y, inv1.A | intermediate node for control signal |
| gated_control | inv1.Y, inv2.A, mn.g |  |
| gated_controlb | inv2.Y, mp.g |  |
| $T1 | <mn\|mp>.d | Tgate analog terminal 1 |
| $T2 | <mn\|mp>.s | Tgate analog terminal 2 |
