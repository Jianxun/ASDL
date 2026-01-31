# ota_nmos

(ota_nmos_doc)=
```{asdl:doc} ota_nmos_doc
```

## Imports

```{asdl:import} ota_nmos::gf
```

| Alias | Path | Description |
| --- | --- | --- |
| gf | gf180mcu.asdl |  |

## Module `ota_nmos`

```{asdl:module} ota_nmos
```

### Interface

```{asdl:port} ota_nmos::$in<p|n>
```

```{asdl:port} ota_nmos::$out
```

```{asdl:port} ota_nmos::$vbn
```

```{asdl:port} ota_nmos::$vdd
```

```{asdl:port} ota_nmos::$vss
```

| Name | Kind | Direction | Description |
| --- | --- | --- | --- |
| $in<p\|n> |  |  |  |
| $out |  |  |  |
| $vbn |  |  |  |
| $vdd |  |  |  |
| $vss |  |  |  |

### Instances

```{asdl:inst} ota_nmos::mp_<ref|cs>
```

```{asdl:inst} ota_nmos::mn_in_<p|n>
```

```{asdl:inst} ota_nmos::mn_tail
```

| Instance | Ref | Params | Description |
| --- | --- | --- | --- |
| mp_<ref\|cs> | gf.pfet_03v3 | L=0.5u W=5u NF=6 m=3 |  |
| mn_in_<p\|n> | gf.nfet_03v3 | L=0.5u W=5u NF=6 m=1 |  |
| mn_tail | gf.nfet_03v3 | L=0.5u W=5u NF=6 m=2 |  |

### Nets

```{asdl:net} ota_nmos::$in<p|n>
```

```{asdl:net} ota_nmos::$out
```

```{asdl:net} ota_nmos::d
```

```{asdl:net} ota_nmos::tail
```

```{asdl:net} ota_nmos::$vbn
```

```{asdl:net} ota_nmos::$vdd
```

```{asdl:net} ota_nmos::$vss
```

| Name | Endpoints | Description |
| --- | --- | --- |
| $in<p\|n> | mn_in_<p\|n>.g |  |
| $out | mn_in_<n>.d, mp_<cs>.d |  |
| d | mn_in_<p>.d, mp_<ref>.d, mp_<ref\|cs>.g |  |
| tail | mn_tail.d, mn_in_<p\|n>.s |  |
| $vbn | mn_tail.g |  |
| $vdd | mp_<ref\|cs>.s, mp_<ref\|cs>.b |  |
| $vss | mn_tail.<s\|b>, mn_in_<p\|n>.b |  |
