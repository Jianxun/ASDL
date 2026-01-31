# DFF_2phase_1

(DFF_2phase_1_doc)=
```{asdl:doc} DFF_2phase_1_doc
```

## Imports

```{asdl:import} DFF_2phase_1::gf_std
```

| Alias | Path | Description |
| --- | --- | --- |
| gf_std | gf180mcu_std.asdl |  |

## Module `DFF_2phase_1`

```{asdl:module} DFF_2phase_1
```

### Interface

```{asdl:port} DFF_2phase_1::$D
```

```{asdl:port} DFF_2phase_1::$Q
```

```{asdl:port} DFF_2phase_1::$PHI_1
```

```{asdl:port} DFF_2phase_1::$PHI_2
```

```{asdl:port} DFF_2phase_1::$VDDd
```

```{asdl:port} DFF_2phase_1::$VSSd
```

| Name | Kind | Direction | Description |
| --- | --- | --- | --- |
| $D |  |  |  |
| $Q |  |  |  |
| $PHI_1 |  |  |  |
| $PHI_2 |  |  |  |
| $VDDd |  |  |  |
| $VSSd |  |  |  |

### Instances

```{asdl:inst} DFF_2phase_1::latch_master
```

```{asdl:inst} DFF_2phase_1::latch_slave
```

| Instance | Ref | Params | Description |
| --- | --- | --- | --- |
| latch_master | gf_std.latq_1 |  |  |
| latch_slave | gf_std.latq_1 |  |  |

### Nets

```{asdl:net} DFF_2phase_1::$D
```

```{asdl:net} DFF_2phase_1::$Q
```

```{asdl:net} DFF_2phase_1::$PHI_1
```

```{asdl:net} DFF_2phase_1::$PHI_2
```

```{asdl:net} DFF_2phase_1::$VDDd
```

```{asdl:net} DFF_2phase_1::$VSSd
```

```{asdl:net} DFF_2phase_1::out_m
```

| Name | Endpoints | Description |
| --- | --- | --- |
| $D | latch_master.D |  |
| $Q | latch_slave.Q |  |
| $PHI_1 | latch_master.EN |  |
| $PHI_2 | latch_slave.EN |  |
| $VDDd | latch_<master\|slave>.<VNB\|VPWR> |  |
| $VSSd | latch_<master\|slave>.<VPB\|VGND> |  |
| out_m | latch_master.Q, latch_slave.D |  |
