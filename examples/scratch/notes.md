#

## Error PARSE-003: 
we should be clear what is going on. we should say "invalid section name <invalid_key>, valid names are: ports, parameters, backends

## [BUG?] required `top` field even if the ASDL file has only a single module (importing other ASDL files)

## suppress same type of errors beyond a certain threshold? (don't want 2000 same type of errors swamping out the meaningful ones)

## in general we should provide more information on "how to fix it", like 
- can't resolve instance name, did you forget to import?
- the endpoint name can't be found from the instance module, valid pins are: ...
- Also if there are case mismatch errors we should suggest "gf.nfet_03v3 has endpoint `g` instead of `G`
- case sensitive check bypass options?

# can't use variable placeholders in endpoint lists
```
    nets:
      # data chain
      $data: [sw_row<1>.D_in]
      $D_out: [sw_row<{N_ROW}:{N_ROW}>.D_out]
      D<{N_ROW_M1}:1>: [sw_row<{N_ROW}:2>.D_in, sw_row<{N_ROW_M1}:1>.D_out]
```