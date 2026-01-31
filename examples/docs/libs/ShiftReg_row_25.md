# ShiftReg_row_25

(ShiftReg_row_25_doc)=
```{asdl:doc} ShiftReg_row_25_doc
```

## Imports

```{asdl:import} ShiftReg_row_25::dff
```

| Alias | Path | Description |
| --- | --- | --- |
| dff | ../DFF_2phase_1/DFF_2phase_1.asdl |  |

## Module `ShiftReg_row_25`

```{asdl:module} ShiftReg_row_25
```

### Interface

```{asdl:port} ShiftReg_row_25::$D_in
```

```{asdl:port} ShiftReg_row_25::$Q<25:25>
```

```{asdl:port} ShiftReg_row_25::$Q<24:1>
```

```{asdl:port} ShiftReg_row_25::$PHI_1
```

```{asdl:port} ShiftReg_row_25::$PHI_2
```

```{asdl:port} ShiftReg_row_25::$VDDd
```

```{asdl:port} ShiftReg_row_25::$VSSd
```

| Name | Kind | Direction | Description |
| --- | --- | --- | --- |
| $D_in |  |  |  |
| $Q<25:25> |  |  |  |
| $Q<24:1> |  |  |  |
| $PHI_1 |  |  |  |
| $PHI_2 |  |  |  |
| $VDDd |  |  |  |
| $VSSd |  |  |  |

### Instances

```{asdl:inst} ShiftReg_row_25::dff<25:1>
```

| Instance | Ref | Params | Description |
| --- | --- | --- | --- |
| dff<25:1> | dff.DFF_2phase_1 |  |  |

### Nets

```{asdl:net} ShiftReg_row_25::$D_in
```

```{asdl:net} ShiftReg_row_25::$Q<25:25>
```

```{asdl:net} ShiftReg_row_25::$Q<24:1>
```

```{asdl:net} ShiftReg_row_25::$PHI_1
```

```{asdl:net} ShiftReg_row_25::$PHI_2
```

```{asdl:net} ShiftReg_row_25::$VDDd
```

```{asdl:net} ShiftReg_row_25::$VSSd
```

| Name | Endpoints | Description |
| --- | --- | --- |
| $D_in | dff<1>.D |  |
| $Q<25:25> | dff<25:25>.Q |  |
| $Q<24:1> | dff<24:1>.Q, dff<25:2>.D |  |
| $PHI_1 | dff<25:1>.PHI_1 |  |
| $PHI_2 | dff<25:1>.PHI_2 |  |
| $VDDd | dff<25:1>.VDDd |  |
| $VSSd | dff<25:1>.VSSd |  |
