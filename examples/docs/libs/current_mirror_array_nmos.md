# current_mirror_array_nmos

(current_mirror_array_nmos_doc)=
```{asdl:doc} current_mirror_array_nmos_doc
```

## Imports

```{asdl:import} current_mirror_array_nmos::gf
```

| Alias | Path | Description |
| --- | --- | --- |
| gf | gf180mcu.asdl |  |

## Module `current_mirror_array_nmos`

```{asdl:module} current_mirror_array_nmos
```

### Interface

```{asdl:port} current_mirror_array_nmos::$iref
```

```{asdl:port} current_mirror_array_nmos::$iout_<@cm_size>x
```

```{asdl:port} current_mirror_array_nmos::$vss
```

| Name | Kind | Direction | Description |
| --- | --- | --- | --- |
| $iref |  |  |  |
| $iout_<@cm_size>x |  |  |  |
| $vss |  |  |  |

### Instances

```{asdl:inst} current_mirror_array_nmos::mn_ref
```

```{asdl:inst} current_mirror_array_nmos::mn_out<@cm_size>
```

| Instance | Ref | Params | Description |
| --- | --- | --- | --- |
| mn_ref | gf.nfet_03v3 | L=0.5u W=5u NF=6 m=1 |  |
| mn_out<@cm_size> | gf.nfet_03v3 | L=0.5u W=5u NF=6 m=<@cm_size> |  |

### Nets

```{asdl:net} current_mirror_array_nmos::$iref
```

```{asdl:net} current_mirror_array_nmos::$iout_<@cm_size>x
```

```{asdl:net} current_mirror_array_nmos::$vss
```

| Name | Endpoints | Description |
| --- | --- | --- |
| $iref | mn_ref.<d\|g>, mn_out<@cm_size>.g |  |
| $iout_<@cm_size>x | mn_out<@cm_size>.d |  |
| $vss | mn_ref.<s\|b>, mn_out<@cm_size>.<s\|b> |  |

### Patterns

```{asdl:pattern} current_mirror_array_nmos::cm_size
```

| Name | Expression | Axis | Description |
| --- | --- | --- | --- |
| cm_size | <1\|2\|4\|8\|16> | cm_size |  |
