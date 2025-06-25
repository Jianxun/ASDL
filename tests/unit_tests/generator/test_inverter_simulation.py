from .fixture_inverter import *
import os


# get the testbench directory and name
script_path = os.path.abspath(__file__)
TEST_DIR = os.path.dirname(script_path)
NETLIST_FILE = f"{TEST_DIR}/results/inverter_netlist.spice"

def test_op():
    """Operating point analysis - check DC bias points of NMOS and PMOS transistors"""
    sim_dir = f"/foss/designs/simulations/inverter_asdl/test_op"
    netlist = ""
    netlist += netlist_pvt_header()
    netlist += netlist_stimulus_dc(vin_dc=1.65)  # Mid-supply bias point
    netlist += netlist_sim_op(filename=f"{sim_dir}/op.log")
    
    # read main netlist 
    netlist += netlist_test_bench(NETLIST_FILE)

    run_ngspice(netlist, sim_dir)
    assert os.path.exists(f"{sim_dir}/op.log")

def test_dc_transfer():
    """DC transfer characteristic - input sweep from 0V to VDD"""
    sim_dir = f"/foss/designs/simulations/inverter_asdl/test_dc_transfer"
    netlist = ""
    netlist += netlist_pvt_header()
    netlist += netlist_stimulus_dc_sweep()  # No fixed DC value, swept by simulation
    netlist += netlist_sim_dc_sweep(start=0, stop=3.3, step=0.01, filename=f"{sim_dir}/dc_transfer.raw")
    
    # read main netlist 
    netlist += netlist_test_bench(NETLIST_FILE)

    run_ngspice(netlist, sim_dir)
    assert os.path.exists(f"{sim_dir}/dc_transfer.raw")

def test_switching_transient():
    """Transient switching analysis with digital pulse input"""
    sim_dir = f"/foss/designs/simulations/inverter_asdl/test_switching"
    
    # Digital switching: 0V to 3.3V pulse
    netlist = ""
    netlist += netlist_pvt_header()
    netlist += netlist_stimulus_pulse(
        v_low=0,           # Logic 0
        v_high=3.3,        # Logic 1  
        t_rise=0.1e-9,     # 100ps rise time
        t_fall=0.1e-9,     # 100ps fall time
        t_delay=1e-9,      # 1ns delay
        period=10e-9       # 10ns period (100MHz)
    )
    netlist += netlist_sim_tran(
        start=0,
        stop=50e-9,        # 50ns simulation (5 cycles)
        step=0.1e-9,       # 100ps time steps
        filename=f"{sim_dir}/switching.raw"
    )
    
    # read main netlist 
    netlist += netlist_test_bench(NETLIST_FILE)

    run_ngspice(netlist, sim_dir)
    assert os.path.exists(f"{sim_dir}/switching.raw")

def test_ac_response():
    """AC small-signal analysis around DC operating point"""
    sim_dir = f"/foss/designs/simulations/inverter_asdl/test_ac"
    netlist = ""
    netlist += netlist_pvt_header()
    netlist += netlist_stimulus_ac(vin_dc=1.65)  # Bias at switching threshold
    netlist += netlist_sim_ac(
        start=1e3,         # 1kHz
        stop=1e9,          # 1GHz  
        dec=10,            # 10 points per decade
        filename=f"{sim_dir}/ac_response.raw"
    )
    
    # read main netlist 
    netlist += netlist_test_bench(NETLIST_FILE)

    run_ngspice(netlist, sim_dir)
    assert os.path.exists(f"{sim_dir}/ac_response.raw")

def test_propagation_delay():
    """Transient analysis optimized for propagation delay measurement"""
    sim_dir = f"/foss/designs/simulations/inverter_asdl/test_prop_delay"
    
    # Fast single pulse for delay measurement
    netlist = ""
    netlist += netlist_pvt_header()
    netlist += netlist_stimulus_single_pulse(
        v_low=0,
        v_high=3.3,
        t_rise=0.05e-9,    # Very fast 50ps edges
        t_fall=0.05e-9,
        t_delay=2e-9,      # 2ns delay before pulse
        pulse_width=10e-9  # 10ns pulse width
    )
    netlist += netlist_sim_tran(
        start=0,
        stop=20e-9,        # 20ns total
        step=0.01e-9,      # 10ps resolution for accurate delay measurement
        filename=f"{sim_dir}/prop_delay.raw"
    )
    
    # read main netlist 
    netlist += netlist_test_bench(NETLIST_FILE)

    run_ngspice(netlist, sim_dir)
    assert os.path.exists(f"{sim_dir}/prop_delay.raw")

def test_load_capacitance():
    """Transient analysis with load capacitance to test drive capability"""
    sim_dir = f"/foss/designs/simulations/inverter_asdl/test_load_cap"
    
    netlist = ""
    netlist += netlist_pvt_header()
    netlist += netlist_load_capacitor(cap_value=100e-15)  # 100fF load
    netlist += netlist_stimulus_pulse(
        v_low=0,
        v_high=3.3,
        t_rise=0.1e-9,
        t_fall=0.1e-9,
        t_delay=1e-9,
        period=20e-9       # 50MHz for loaded analysis
    )
    netlist += netlist_sim_tran(
        start=0,
        stop=100e-9,       # 100ns (5 cycles)
        step=0.1e-9,
        filename=f"{sim_dir}/load_cap.raw"
    )
    
    # read main netlist 
    netlist += netlist_test_bench(NETLIST_FILE)

    run_ngspice(netlist, sim_dir)
    assert os.path.exists(f"{sim_dir}/load_cap.raw")


if __name__ == "__main__":
    print("Running ASDL Inverter Testbench...")
    
    test_op()
    print("✓ Operating Point Analysis")
    
    test_dc_transfer()
    print("✓ DC Transfer Characteristic")
    
    test_switching_transient()
    print("✓ Switching Transient Analysis")
    
    test_ac_response()
    print("✓ AC Small-Signal Response")
    
    test_propagation_delay()
    print("✓ Propagation Delay Measurement")
    
    test_load_capacitance()
    print("✓ Load Capacitance Analysis")
    
    print("All tests passed! ✅") 