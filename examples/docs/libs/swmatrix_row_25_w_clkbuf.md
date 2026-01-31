# swmatrix_row_25_w_clkbuf

(swmatrix_row_25_w_clkbuf_doc)=
```{asdl:doc} swmatrix_row_25_w_clkbuf_doc
```

## Imports

```{asdl:import} swmatrix_row_25_w_clkbuf::ShiftReg_row_25
```

```{asdl:import} swmatrix_row_25_w_clkbuf::swmatrix_Tgate
```

```{asdl:import} swmatrix_row_25_w_clkbuf::gf_std
```

| Alias | Path | Description |
| --- | --- | --- |
| ShiftReg_row_25 | ../ShiftReg_row_25/ShiftReg_row_25.asdl |  |
| swmatrix_Tgate | ../swmatrix_Tgate/swmatrix_Tgate.asdl |  |
| gf_std | gf180mcu_std.asdl |  |

## Module `swmatrix_row_25_w_clkbuf`

```{asdl:module} swmatrix_row_25_w_clkbuf
```

### Interface

```{asdl:port} swmatrix_row_25_w_clkbuf::$D_in
```

```{asdl:port} swmatrix_row_25_w_clkbuf::$D_out
```

```{asdl:port} swmatrix_row_25_w_clkbuf::$<PHI_1|PHI_2|enable>
```

```{asdl:port} swmatrix_row_25_w_clkbuf::$pin
```

```{asdl:port} swmatrix_row_25_w_clkbuf::$bus<25:1>
```

```{asdl:port} swmatrix_row_25_w_clkbuf::$VDDd
```

```{asdl:port} swmatrix_row_25_w_clkbuf::$VSSd
```

| Name | Kind | Direction | Description |
| --- | --- | --- | --- |
| $D_in |  |  |  |
| $D_out |  |  |  |
| $<PHI_1\|PHI_2\|enable> |  |  |  |
| $pin |  |  |  |
| $bus<25:1> |  |  |  |
| $VDDd |  |  |  |
| $VSSd |  |  |  |

### Instances

```{asdl:inst} swmatrix_row_25_w_clkbuf::SR_row
```

```{asdl:inst} swmatrix_row_25_w_clkbuf::Tgate<25:1>
```

```{asdl:inst} swmatrix_row_25_w_clkbuf::clkbuf_<phi_1|phi_2|enable>
```

| Instance | Ref | Params | Description |
| --- | --- | --- | --- |
| SR_row | ShiftReg_row_25.ShiftReg_row_25 |  |  |
| Tgate<25:1> | swmatrix_Tgate.swmatrix_Tgate |  |  |
| clkbuf_<phi_1\|phi_2\|enable> | clkbuf |  |  |

### Nets

```{asdl:net} swmatrix_row_25_w_clkbuf::$D_in
```

```{asdl:net} swmatrix_row_25_w_clkbuf::$D_out
```

```{asdl:net} swmatrix_row_25_w_clkbuf::Q<24:1>
```

```{asdl:net} swmatrix_row_25_w_clkbuf::$<PHI_1|PHI_2|enable>
```

```{asdl:net} swmatrix_row_25_w_clkbuf::<phi_1|phi_2>_buf
```

```{asdl:net} swmatrix_row_25_w_clkbuf::enable_buf
```

```{asdl:net} swmatrix_row_25_w_clkbuf::$pin
```

```{asdl:net} swmatrix_row_25_w_clkbuf::$bus<25:1>
```

```{asdl:net} swmatrix_row_25_w_clkbuf::$VDDd
```

```{asdl:net} swmatrix_row_25_w_clkbuf::$VSSd
```

| Name | Endpoints | Description |
| --- | --- | --- |
| $D_in | SR_row.D_in |  |
| $D_out | SR_row.Q<25>, Tgate<25>.control |  |
| Q<24:1> | SR_row.Q<24:1>, Tgate<24:1>.control |  |
| $<PHI_1\|PHI_2\|enable> | clkbuf_<phi_1\|phi_2\|enable>.A |  |
| <phi_1\|phi_2>_buf | clkbuf_<phi_1\|phi_2>.Y, SR_row.<PHI_1\|PHI_2> |  |
| enable_buf | clkbuf_enable.Y, Tgate<25:1>.enable |  |
| $pin | Tgate<25:1>.T1 |  |
| $bus<25:1> | Tgate<25:1>.T2 |  |
| $VDDd | SR_row.VDDd, Tgate<25:1>.VDDd, clkbuf_<phi_1\|phi_2\|enable>.VDDd |  |
| $VSSd | SR_row.VSSd, Tgate<25:1>.VSSd, clkbuf_<phi_1\|phi_2\|enable>.VSSd |  |


## Module `clkbuf`

```{asdl:module} clkbuf
```

### Interface

```{asdl:port} clkbuf::$A
```

```{asdl:port} clkbuf::$Y
```

```{asdl:port} clkbuf::$VDDd
```

```{asdl:port} clkbuf::$VSSd
```

| Name | Kind | Direction | Description |
| --- | --- | --- | --- |
| $A |  |  |  |
| $Y |  |  |  |
| $VDDd |  |  |  |
| $VSSd |  |  |  |

### Instances

```{asdl:inst} clkbuf::inv1
```

```{asdl:inst} clkbuf::inv2
```

```{asdl:inst} clkbuf::inv3
```

```{asdl:inst} clkbuf::inv4
```

| Instance | Ref | Params | Description |
| --- | --- | --- | --- |
| inv1 | gf_std.inv_4 |  |  |
| inv2 | gf_std.inv_8 |  |  |
| inv3 | gf_std.inv_12 |  |  |
| inv4 | gf_std.inv_20 |  |  |

### Nets

```{asdl:net} clkbuf::$A
```

```{asdl:net} clkbuf::net1
```

```{asdl:net} clkbuf::net2
```

```{asdl:net} clkbuf::net3
```

```{asdl:net} clkbuf::$Y
```

```{asdl:net} clkbuf::$VDDd
```

```{asdl:net} clkbuf::$VSSd
```

| Name | Endpoints | Description |
| --- | --- | --- |
| $A | inv1.A |  |
| net1 | inv1.Y, inv2.A |  |
| net2 | inv2.Y, inv3.A |  |
| net3 | inv3.Y, inv4.A |  |
| $Y | inv4.Y |  |
| $VDDd | inv<1\|2\|3\|4>.<VPWR\|VPB> |  |
| $VSSd | inv<1\|2\|3\|4>.<VNB\|VGND> |  |
