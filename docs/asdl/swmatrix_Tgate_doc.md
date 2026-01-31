# swmatrix_Tgate

## Overview
Switch Matrix Tgate (swmatrix_Tgate)
Power: VDDd (3.3V), VSSd (0V)
Digital inputs: control, enable
Analog terminals: T1, T2 (symmetric, rail-to-rail)
Specs:
  - Ron < 100 ohms @ 3.3V
  - Cpar < 20 fF

## Imports
| Alias | Path | Description |
| --- | --- | --- |
| gf_std | gf180mcu_std.asdl | GF180 standard cell library |
| gf | gf180mcu.asdl | GF180 device library |

## Module `swmatrix_Tgate`

### Notes
Transmission-gate switch with control logic.

### Interface
| Name | Kind | Direction | Description |
| --- | --- | --- | --- |
| $VDDd |  |  | nominal 3.3V |
| $VSSd |  |  | nominal 0V |
| $control |  |  | active high control signal to close the Tgate |
| $enable |  |  | active high enable signal shared by all Tgates |
| $T1 |  |  | Tgate analog terminal 1 |
| $T2 |  |  | Tgate analog terminal 2 |

### Variables
| Name | Default | Description |
| --- | --- | --- |
| L | 0.28u | gate length |
| W | 8u | gate width |
| NF | 6 | fingers |

### Instances
| Instance | Ref | Params | Description |
| --- | --- | --- | --- |
| inv1 | gf_std.inv_1 |  |  |
| inv2 | gf_std.inv_1 |  |  |
| nand2 | gf_std.nand2_1 |  |  |
| mn | gf.nfet_03v3 | L={L} W={W} NF={NF} m=1 |  |
| mp | gf.pfet_03v3 | L={L} W={W} NF={NF} m=3 | PMOS/NMOS ratio is 3:1 |

### Nets
#### Power
| Name | Endpoints | Description |
| --- | --- | --- |
| $VDDd | <inv1\|inv2\|nand2>.<VPWR\|VNB>, mp.b | nominal 3.3V |
| $VSSd | <inv1\|inv2\|nand2>.<VPB\|VGND>, mn.b | nominal 0V |
| $control | nand2.A | active high control signal to close the Tgate |
| $enable | nand2.B | active high enable signal shared by all Tgates |
| net1 | nand2.Y, inv1.A | intermediate node for control signal |
| gated_control | inv1.Y, inv2.A, mn.g |  |
| gated_controlb | inv2.Y, mp.g |  |
#### Analog terminals
| Name | Endpoints | Description |
| --- | --- | --- |
| $T1 | <mn\|mp>.d | Tgate analog terminal 1 |
| $T2 | <mn\|mp>.s | Tgate analog terminal 2 |
