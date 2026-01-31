# current_mirror_array_pmos

(current_mirror_array_pmos_doc)=
```{asdl:doc} current_mirror_array_pmos_doc
```

## Imports

```{asdl:import} current_mirror_array_pmos::gf
```

| Alias | Path | Description |
| --- | --- | --- |
| gf | gf180mcu.asdl |  |

## Module `current_mirror_array_pmos`

```{asdl:module} current_mirror_array_pmos
```

### Interface

```{asdl:port} current_mirror_array_pmos::$iref
```

```{asdl:port} current_mirror_array_pmos::$iout_<@cm_size>x
```

```{asdl:port} current_mirror_array_pmos::$vdd
```

| Name | Kind | Direction | Description |
| --- | --- | --- | --- |
| $iref |  |  |  |
| $iout_<@cm_size>x |  |  |  |
| $vdd |  |  |  |

### Instances

```{asdl:inst} current_mirror_array_pmos::mn_ref
```

```{asdl:inst} current_mirror_array_pmos::mn_out<@cm_size>
```

| Instance | Ref | Params | Description |
| --- | --- | --- | --- |
| mn_ref | gf.pfet_03v3 | L=0.5u W=5u NF=6 m=3 |  |
| mn_out<@cm_size> | gf.pfet_03v3 | L=0.5u W=5u NF=6 m=3*<@cm_size> |  |

### Nets

```{asdl:net} current_mirror_array_pmos::$iref
```

```{asdl:net} current_mirror_array_pmos::$iout_<@cm_size>x
```

```{asdl:net} current_mirror_array_pmos::$vdd
```

| Name | Endpoints | Description |
| --- | --- | --- |
| $iref | mn_ref.<d\|g>, mn_out<@cm_size>.g |  |
| $iout_<@cm_size>x | mn_out<@cm_size>.d |  |
| $vdd | mn_ref.<s\|b>, mn_out<@cm_size>.<s\|b> |  |

### Patterns

```{asdl:pattern} current_mirror_array_pmos::cm_size
```

| Name | Expression | Axis | Description |
| --- | --- | --- | --- |
| cm_size | <1\|2\|4\|8\|16> | cm_size |  |
