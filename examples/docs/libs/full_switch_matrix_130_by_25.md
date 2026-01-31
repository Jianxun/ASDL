# full_switch_matrix_130_by_25_no_probes

(full_switch_matrix_130_by_25_doc)=
```{asdl:doc} full_switch_matrix_130_by_25_doc
```

## Imports

```{asdl:import} full_switch_matrix_130_by_25::sw_row
```

| Alias | Path | Description |
| --- | --- | --- |
| sw_row | ../swmatrix_row_25_w_clkbuf/swmatrix_row_25_w_clkbuf.asdl |  |

## Module `full_switch_matrix_130_by_25_no_probes`

```{asdl:module} full_switch_matrix_130_by_25_no_probes
```

### Interface

```{asdl:port} full_switch_matrix_130_by_25_no_probes::$data
```

```{asdl:port} full_switch_matrix_130_by_25_no_probes::$D_out
```

```{asdl:port} full_switch_matrix_130_by_25_no_probes::$PHI_1_in
```

```{asdl:port} full_switch_matrix_130_by_25_no_probes::$PHI_2_in
```

```{asdl:port} full_switch_matrix_130_by_25_no_probes::$enable_in
```

```{asdl:port} full_switch_matrix_130_by_25_no_probes::$BUS<@BUS>
```

```{asdl:port} full_switch_matrix_130_by_25_no_probes::$pin<@ROW>
```

```{asdl:port} full_switch_matrix_130_by_25_no_probes::$VDDd
```

```{asdl:port} full_switch_matrix_130_by_25_no_probes::$VSSd
```

| Name | Kind | Direction | Description |
| --- | --- | --- | --- |
| $data |  |  |  |
| $D_out |  |  |  |
| $PHI_1_in |  |  |  |
| $PHI_2_in |  |  |  |
| $enable_in |  |  |  |
| $BUS<@BUS> |  |  | bus broadcast to all rows |
| $pin<@ROW> |  |  |  |
| $VDDd |  |  |  |
| $VSSd |  |  |  |

### Instances

```{asdl:inst} full_switch_matrix_130_by_25_no_probes::sw_row<@ROW>
```

| Instance | Ref | Params | Description |
| --- | --- | --- | --- |
| sw_row<@ROW> | sw_row.swmatrix_row_25_w_clkbuf |  |  |

### Nets
#### data chain

```{asdl:net} full_switch_matrix_130_by_25_no_probes::$data
```

```{asdl:net} full_switch_matrix_130_by_25_no_probes::$D_out
```

```{asdl:net} full_switch_matrix_130_by_25_no_probes::D<129:1>
```

| Name | Endpoints | Description |
| --- | --- | --- |
| $data | sw_row<1>.D_in |  |
| $D_out | sw_row<130:130>.D_out |  |
| D<129:1> | sw_row<130:2>.D_in, sw_row<129:1>.D_out |  |
#### clock broadcast

```{asdl:net} full_switch_matrix_130_by_25_no_probes::$PHI_1_in
```

```{asdl:net} full_switch_matrix_130_by_25_no_probes::$PHI_2_in
```

```{asdl:net} full_switch_matrix_130_by_25_no_probes::$enable_in
```

| Name | Endpoints | Description |
| --- | --- | --- |
| $PHI_1_in | sw_row<@ROW>.PHI_1 |  |
| $PHI_2_in | sw_row<@ROW>.PHI_2 |  |
| $enable_in | sw_row<@ROW>.enable |  |
#### buses and pins

```{asdl:net} full_switch_matrix_130_by_25_no_probes::$BUS<@BUS>
```

```{asdl:net} full_switch_matrix_130_by_25_no_probes::$pin<@ROW>
```

| Name | Endpoints | Description |
| --- | --- | --- |
| $BUS<@BUS> | sw_row<@ROW>.bus<@BUS> | bus broadcast to all rows |
| $pin<@ROW> | sw_row<@ROW>.pin |  |
#### power

```{asdl:net} full_switch_matrix_130_by_25_no_probes::$VDDd
```

```{asdl:net} full_switch_matrix_130_by_25_no_probes::$VSSd
```

| Name | Endpoints | Description |
| --- | --- | --- |
| $VDDd | sw_row<@ROW>.VDDd |  |
| $VSSd | sw_row<@ROW>.VSSd |  |

### Patterns

```{asdl:pattern} full_switch_matrix_130_by_25_no_probes::ROW
```

```{asdl:pattern} full_switch_matrix_130_by_25_no_probes::BUS
```

| Name | Expression | Axis | Description |
| --- | --- | --- | --- |
| ROW | <130:1> | ROW |  |
| BUS | <25:1> | BUS |  |
