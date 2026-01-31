# current_mirror_nmos

(current_mirror_nmos_doc)=
```{asdl:doc} current_mirror_nmos_doc
```

## Imports

```{asdl:import} current_mirror_nmos::gf
```

| Alias | Path | Description |
| --- | --- | --- |
| gf | gf180mcu.asdl |  |

## Module `current_mirror_nmos`

```{asdl:module} current_mirror_nmos
```

### Interface

```{asdl:port} current_mirror_nmos::$iref
```

```{asdl:port} current_mirror_nmos::$iout
```

```{asdl:port} current_mirror_nmos::$vss
```

| Name | Kind | Direction | Description |
| --- | --- | --- | --- |
| $iref |  |  |  |
| $iout |  |  |  |
| $vss |  |  |  |

### Instances

```{asdl:inst} current_mirror_nmos::mn_ref
```

```{asdl:inst} current_mirror_nmos::mn_out
```

| Instance | Ref | Params | Description |
| --- | --- | --- | --- |
| mn_ref | gf.nfet_03v3 | L=0.5u W=5u NF=6 m=1 |  |
| mn_out | gf.nfet_03v3 | L=0.5u W=5u NF=6 m=1 |  |

### Nets

```{asdl:net} current_mirror_nmos::$iref
```

```{asdl:net} current_mirror_nmos::$iout
```

```{asdl:net} current_mirror_nmos::$vss
```

| Name | Endpoints | Description |
| --- | --- | --- |
| $iref | mn_ref.<d\|g>, mn_out.g |  |
| $iout | mn_out.d |  |
| $vss | mn_ref.<s\|b>, mn_out.<s\|b> |  |
