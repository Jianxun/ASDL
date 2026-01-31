# top_mosbius_devices_v1_nmos

(top_mosbius_devices_v1_nmos_doc)=
```{asdl:doc} top_mosbius_devices_v1_nmos_doc
```

## Imports

```{asdl:import} top_mosbius_devices_v1_nmos::gf
```

```{asdl:import} top_mosbius_devices_v1_nmos::ota
```

```{asdl:import} top_mosbius_devices_v1_nmos::cm_array_nmos
```

```{asdl:import} top_mosbius_devices_v1_nmos::cm_nmos
```

```{asdl:import} top_mosbius_devices_v1_nmos::inv
```

| Alias | Path | Description |
| --- | --- | --- |
| gf | gf180mcu.asdl |  |
| ota | ../ota_nmos/ota_nmos.asdl |  |
| cm_array_nmos | ../current_mirror_array_nmos/current_mirror_array_nmos.asdl |  |
| cm_nmos | ../current_mirror_nmos/current_mirror_nmos.asdl |  |
| inv | ../inv/inv.asdl |  |

## Module `top_mosbius_devices_v1_nmos`

```{asdl:module} top_mosbius_devices_v1_nmos
```

### Interface

```{asdl:port} top_mosbius_devices_v1_nmos::$NMOS_CM_ARRAY_IOUT_<@cm_size>X
```

```{asdl:port} top_mosbius_devices_v1_nmos::$NMOS_CM_ARRAY_IREF
```

```{asdl:port} top_mosbius_devices_v1_nmos::$NMOS_OTA_<INP|INN|OUT>
```

```{asdl:port} top_mosbius_devices_v1_nmos::$NMOS_CM_<IREF|IOUT>
```

```{asdl:port} top_mosbius_devices_v1_nmos::$NMOS_DP_1X_<A|B>_<D|G|S>
```

```{asdl:port} top_mosbius_devices_v1_nmos::$NMOS_DP_4X_<A|B>_<D|G|S>
```

```{asdl:port} top_mosbius_devices_v1_nmos::$NMOS_CS_4X_<A|B>_<D|G>
```

```{asdl:port} top_mosbius_devices_v1_nmos::$INV_16X_A_<INN|OUT|INP>
```

```{asdl:port} top_mosbius_devices_v1_nmos::$VDD
```

```{asdl:port} top_mosbius_devices_v1_nmos::$VSS
```

| Name | Kind | Direction | Description |
| --- | --- | --- | --- |
| $NMOS_CM_ARRAY_IOUT_<@cm_size>X |  |  |  |
| $NMOS_CM_ARRAY_IREF |  |  |  |
| $NMOS_OTA_<INP\|INN\|OUT> |  |  |  |
| $NMOS_CM_<IREF\|IOUT> |  |  |  |
| $NMOS_DP_1X_<A\|B>_<D\|G\|S> |  |  |  |
| $NMOS_DP_4X_<A\|B>_<D\|G\|S> |  |  |  |
| $NMOS_CS_4X_<A\|B>_<D\|G> |  |  |  |
| $INV_16X_A_<INN\|OUT\|INP> |  |  |  |
| $VDD |  |  |  |
| $VSS |  |  |  |

### Instances

```{asdl:inst} top_mosbius_devices_v1_nmos::nmos_ota
```

```{asdl:inst} top_mosbius_devices_v1_nmos::nmos_cm_array
```

```{asdl:inst} top_mosbius_devices_v1_nmos::nmos_cm
```

```{asdl:inst} top_mosbius_devices_v1_nmos::mn_dp_1x_<a|b>
```

```{asdl:inst} top_mosbius_devices_v1_nmos::mn_dp_4x_<a|b>
```

```{asdl:inst} top_mosbius_devices_v1_nmos::mn_cs_4x_<a|b>
```

```{asdl:inst} top_mosbius_devices_v1_nmos::inv
```

```{asdl:inst} top_mosbius_devices_v1_nmos::mn_dummy
```

```{asdl:inst} top_mosbius_devices_v1_nmos::mp_dummy
```

| Instance | Ref | Params | Description |
| --- | --- | --- | --- |
| nmos_ota | ota.ota_nmos |  |  |
| nmos_cm_array | cm_array_nmos.current_mirror_array_nmos |  |  |
| nmos_cm | cm_nmos.current_mirror_nmos |  |  |
| mn_dp_1x_<a\|b> | gf.nfet_03v3 | L=0.5u W=5u NF=6 m=1 |  |
| mn_dp_4x_<a\|b> | gf.nfet_03v3 | L=0.5u W=5u NF=6 m=4 |  |
| mn_cs_4x_<a\|b> | gf.nfet_03v3 | L=0.5u W=5u NF=6 m=4 |  |
| inv | inv.inv |  |  |
| mn_dummy | gf.nfet_03v3 | L=0.5u W=5u NF=6 m=32 |  |
| mp_dummy | gf.pfet_03v3 | L=0.5u W=5u NF=6 m=18 |  |

### Nets

```{asdl:net} top_mosbius_devices_v1_nmos::$NMOS_CM_ARRAY_IOUT_<@cm_size>X
```

```{asdl:net} top_mosbius_devices_v1_nmos::$NMOS_CM_ARRAY_IREF
```

```{asdl:net} top_mosbius_devices_v1_nmos::$NMOS_OTA_<INP|INN|OUT>
```

```{asdl:net} top_mosbius_devices_v1_nmos::$NMOS_CM_<IREF|IOUT>
```

```{asdl:net} top_mosbius_devices_v1_nmos::$NMOS_DP_1X_<A|B>_<D|G|S>
```

```{asdl:net} top_mosbius_devices_v1_nmos::$NMOS_DP_4X_<A|B>_<D|G|S>
```

```{asdl:net} top_mosbius_devices_v1_nmos::$NMOS_CS_4X_<A|B>_<D|G>
```

```{asdl:net} top_mosbius_devices_v1_nmos::$INV_16X_A_<INN|OUT|INP>
```

```{asdl:net} top_mosbius_devices_v1_nmos::$VDD
```

```{asdl:net} top_mosbius_devices_v1_nmos::$VSS
```

| Name | Endpoints | Description |
| --- | --- | --- |
| $NMOS_CM_ARRAY_IOUT_<@cm_size>X | nmos_cm_array.iout_<@cm_size>x |  |
| $NMOS_CM_ARRAY_IREF | nmos_cm_array.iref, nmos_ota.vbn |  |
| $NMOS_OTA_<INP\|INN\|OUT> | nmos_ota.<inp\|inn\|out> |  |
| $NMOS_CM_<IREF\|IOUT> | nmos_cm.<iref\|iout> |  |
| $NMOS_DP_1X_<A\|B>_<D\|G\|S> | mn_dp_1x_<a\|b>.<d\|g\|s> |  |
| $NMOS_DP_4X_<A\|B>_<D\|G\|S> | mn_dp_4x_<a\|b>.<d\|g\|s> |  |
| $NMOS_CS_4X_<A\|B>_<D\|G> | mn_cs_4x_<a\|b>.<d\|g> |  |
| $INV_16X_A_<INN\|OUT\|INP> | inv.<inn\|out\|inp> |  |
| $VDD | nmos_ota.vdd, inv.vdd, mp_dummy.<d\|g\|s\|b> |  |
| $VSS | nmos_ota.vss, inv.vss, nmos_cm_array.vss, nmos_cm.vss, mn_dp_1x_<a\|b>.b, mn_dp_4x_<a\|b>.b, mn_cs_4x_<a\|b>.<s\|b>, mn_dummy.<d\|g\|s\|b> |  |

### Patterns

```{asdl:pattern} top_mosbius_devices_v1_nmos::cm_size
```

| Name | Expression | Axis | Description |
| --- | --- | --- | --- |
| cm_size | <1\|2\|4\|8\|16> | cm_size |  |
