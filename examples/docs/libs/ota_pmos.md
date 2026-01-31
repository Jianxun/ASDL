# ota_pmos

(ota_pmos_doc)=
```{asdl:doc} ota_pmos_doc
```

## Imports

```{asdl:import} ota_pmos::gf
```

| Alias | Path | Description |
| --- | --- | --- |
| gf | gf180mcu.asdl |  |

## Module `ota_pmos`

```{asdl:module} ota_pmos
```

### Interface

```{asdl:port} ota_pmos::$in<p|n>
```

```{asdl:port} ota_pmos::$out
```

```{asdl:port} ota_pmos::$vbn
```

```{asdl:port} ota_pmos::$vss
```

```{asdl:port} ota_pmos::$vdd
```

| Name | Kind | Direction | Description |
| --- | --- | --- | --- |
| $in<p\|n> |  |  |  |
| $out |  |  |  |
| $vbn |  |  |  |
| $vss |  |  |  |
| $vdd |  |  |  |

### Instances

```{asdl:inst} ota_pmos::mn_<ref|cs>
```

```{asdl:inst} ota_pmos::mp_in_<p|n>
```

```{asdl:inst} ota_pmos::mp_tail
```

| Instance | Ref | Params | Description |
| --- | --- | --- | --- |
| mn_<ref\|cs> | gf.nfet_03v3 | L=0.5u W=5u NF=6 m=1 |  |
| mp_in_<p\|n> | gf.pfet_03v3 | L=0.5u W=5u NF=6 m=3 |  |
| mp_tail | gf.pfet_03v3 | L=0.5u W=5u NF=6 m=6 |  |

### Nets

```{asdl:net} ota_pmos::$in<p|n>
```

```{asdl:net} ota_pmos::$out
```

```{asdl:net} ota_pmos::d
```

```{asdl:net} ota_pmos::tail
```

```{asdl:net} ota_pmos::$vbn
```

```{asdl:net} ota_pmos::$vss
```

```{asdl:net} ota_pmos::$vdd
```

| Name | Endpoints | Description |
| --- | --- | --- |
| $in<p\|n> | mp_in_<p\|n>.g |  |
| $out | mp_in_<n>.d, mn_<cs>.d |  |
| d | mp_in_<p>.d, mn_<ref>.d, mn_<ref\|cs>.g |  |
| tail | mp_tail.d, mp_in_<p\|n>.s |  |
| $vbn | mp_tail.g |  |
| $vss | mp_tail.<s\|b>, mp_in_<p\|n>.<b> |  |
| $vdd | mn_<ref\|cs>.<s\|b> |  |
