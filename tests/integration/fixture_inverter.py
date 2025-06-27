import os
import subprocess

def run_ngspice(netlist, sim_dir):
    """Run ngspice simulation with the given netlist"""
    # Create the target directory for simulations
    target_dir = "/headless/.xschem/simulations"
    os.makedirs(target_dir, exist_ok=True)
    
    # Create the simulation directory
    os.makedirs(sim_dir, exist_ok=True)

    with open(f"{sim_dir}/netlist.spice", "w") as f:
        f.write(netlist)
    print(f"Running ngspice simulation in {sim_dir}")
    
    # run ngspice and save the output to a file
    result = subprocess.run(
        ["ngspice", "-b", f"{sim_dir}/netlist.spice"], 
        capture_output=True, 
        text=True
    )

    # check if the result contains the word "Error"
    with open(f"{sim_dir}/ngspice.log", "w") as f:
        f.write(result.stdout)
        f.write(result.stderr)

    # Print summary for debugging
    print(f"  → Netlist: {sim_dir}/netlist.spice")
    print(f"  → Log: {sim_dir}/ngspice.log")
    print(f"  → Exit code: {result.returncode}")

    # assert if the log file contains the word "error" (case-insensitive)
    combined_output = (result.stdout + result.stderr).lower()
    assert "error" not in combined_output, f"ngspice simulation failed. Check {sim_dir}/ngspice.log"

#======================================================
# Testbench Main Circuit
#======================================================
def netlist_test_bench(netlist_file):
    """Read and return the main circuit netlist"""
    with open(netlist_file, "r") as f:
        netlist = f.read()
    
    # For ASDL-generated netlists, we need to modify the main instantiation
    # to connect to our testbench signals
    netlist = netlist.replace(
        "XMAIN in out vdd vss inverter",
        "XMAIN in out vdd vss inverter"
    )
    
    return netlist

#======================================================
# PVT Header - Process, Voltage, Temperature
#======================================================
def netlist_pvt_header(corner="typical", vdda=3.3):
    """Generate PVT header with model files and power supplies"""
    netlist = ""
    netlist += netlist_model(corner)
    netlist += netlist_power(vdda=vdda)
    return netlist

def netlist_model(corner="typical"):
    """Include PDK model files - using GF180MCU for now"""
    return f"""
    * ---------------- Model Files ----------------
    .include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
    .lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice {corner}
    """

def netlist_power(vdda=3.3):
    """Generate power supply connections"""
    return f"""
    * ---------------- Power Supplies ----------------
    V_vss vss 0 0
    V_vdd vdd 0 {vdda}
    """

#======================================================
# Inverter-Specific Stimulus Functions
#======================================================
def netlist_stimulus_dc(vin_dc=1.65):
    """DC stimulus for operating point analysis"""
    return f"""
    * ---------------- DC Stimulus ----------------
    V_in in 0 {vin_dc}
    """

def netlist_stimulus_dc_sweep():
    """DC stimulus for DC transfer characteristic (swept by simulation)"""
    return f"""
    * ---------------- DC Sweep Stimulus ----------------
    V_in in 0 0
    """

def netlist_stimulus_ac(vin_dc=1.65, vac=1e-3):
    """AC stimulus for small-signal analysis"""
    return f"""
    * ---------------- AC Stimulus ----------------
    V_in in 0 {vin_dc} AC {vac}
    """

def netlist_stimulus_pulse(v_low=0, v_high=3.3, t_rise=0.1e-9, t_fall=0.1e-9, t_delay=1e-9, period=10e-9):
    """Pulse stimulus for digital switching analysis"""
    pulse_width = period / 2
    return f"""
    * ---------------- Pulse Stimulus ----------------
    V_in in 0 PULSE({v_low} {v_high} {t_delay} {t_rise} {t_fall} {pulse_width} {period})
    """

def netlist_stimulus_single_pulse(v_low=0, v_high=3.3, t_rise=0.05e-9, t_fall=0.05e-9, t_delay=2e-9, pulse_width=10e-9):
    """Single pulse stimulus for propagation delay measurement"""
    return f"""
    * ---------------- Single Pulse Stimulus ----------------
    V_in in 0 PULSE({v_low} {v_high} {t_delay} {t_rise} {t_fall} {pulse_width} 1)
    """

def netlist_load_capacitor(cap_value=100e-15):
    """Add load capacitance to output"""
    return f"""
    * ---------------- Load Capacitance ----------------
    C_load out 0 {cap_value}
    """

#======================================================
# Simulation Control Blocks
#======================================================
def netlist_sim_op(filename="op.log"):
    """Operating point analysis"""
    return f"""
    * ---------------- Operating Point Analysis ----------------
    .control
    OP
    show all > {filename}
    .endc

    """

def netlist_sim_dc_sweep(start=0, stop=3.3, step=0.01, filename="dc_transfer.raw"):
    """DC sweep analysis for transfer characteristic"""
    return f"""
    * ---------------- DC Sweep Analysis ----------------
    .control
    save all
    DC V_in {start} {stop} {step}
    write {filename}
    .endc

    """

def netlist_sim_ac(start=1e3, stop=1e9, dec=10, filename="ac_response.raw"):
    """AC analysis for frequency response"""
    return f"""
    * ---------------- AC Analysis ----------------
    .control
    save all
    AC DEC {dec} {start} {stop}
    write {filename}
    .endc

    """

def netlist_sim_tran(start=0, stop=50e-9, step=0.1e-9, filename="transient.raw"):
    """Transient analysis"""
    return f"""
    * ---------------- Transient Analysis ----------------
    .control
    save all
    TRAN {step} {stop} {start}
    write {filename}
    .endc

    """

#======================================================
# Inverter-Specific Analysis Functions
#======================================================
def netlist_measure_delay():
    """Add measurement commands for propagation delay"""
    return f"""
    * ---------------- Delay Measurements ----------------
    .control
    * Measure propagation delays
    meas tran tphl trig v(in) val=1.65 rise=1 targ v(out) val=1.65 fall=1
    meas tran tplh trig v(in) val=1.65 fall=1 targ v(out) val=1.65 rise=1
    .endc

    """

def netlist_measure_power():
    """Add measurement commands for power consumption"""
    return f"""
    * ---------------- Power Measurements ----------------
    .control
    * Measure average power consumption
    meas tran p_avg avg p(V_vdd) from=10n to=40n
    .endc

    """

def netlist_measure_noise_margins():
    """Add measurement commands for noise margins"""
    return f"""
    * ---------------- Noise Margin Measurements ----------------
    .control
    * Find switching threshold
    meas dc vth when v(out)=1.65
    * Find VIL and VIH (approximate)
    meas dc vil when v(out)=2.97  
    meas dc vih when v(out)=0.33
    .endc

    """ 