# inv

(inv_doc)=
```{asdl:doc} inv_doc
```

## Imports

```{asdl:import} inv::gf
```

| Alias | Path | Description |
| --- | --- | --- |
| gf | gf180mcu.asdl |  |

## Module `inv`

```{asdl:module} inv
```

### Interface

```{asdl:port} inv::$inp
```

```{asdl:port} inv::$inn
```

```{asdl:port} inv::$out
```

```{asdl:port} inv::$vss
```

```{asdl:port} inv::$vdd
```

| Name | Kind | Direction | Description |
| --- | --- | --- | --- |
| $inp |  |  |  |
| $inn |  |  |  |
| $out |  |  |  |
| $vss |  |  |  |
| $vdd |  |  |  |

### Instances

```{asdl:inst} inv::mn
```

```{asdl:inst} inv::mp
```

| Instance | Ref | Params | Description |
| --- | --- | --- | --- |
| mn | gf.nfet_03v3 | L=0.5u W=5u NF=6 m=16 |  |
| mp | gf.pfet_03v3 | L=0.5u W=5u NF=6 m=3*16 |  |

### Nets

```{asdl:net} inv::$inp
```

```{asdl:net} inv::$inn
```

```{asdl:net} inv::$out
```

```{asdl:net} inv::$vss
```

```{asdl:net} inv::$vdd
```

| Name | Endpoints | Description |
| --- | --- | --- |
| $inp | mp.g |  |
| $inn | mn.g |  |
| $out | mn.d, mp.d |  |
| $vss | mn.<s\|b> |  |
| $vdd | mp.<s\|b> |  |
