from fixture import *


# get the testbench directory and name
script_path = os.path.abspath(__file__)
TB_DIR = os.path.dirname(script_path)
TB_NAME = os.path.basename(TB_DIR)
NETLIST_FILE = f"{TB_DIR}/{TB_NAME}.spice"

def test_op():
    sim_dir = f"/foss/designs/simulations/{TB_NAME}/test_op"
    netlist = ""
    netlist += netlist_pvt_header()
    netlist += netlist_feedback_unity()
    netlist += netlist_stimulus_dc(vin_dc=1.5)
    netlist += netlist_sim_op(filename=f"{sim_dir}/op.log")
    
    # read main netlist 
    netlist += netlist_test_bench(NETLIST_FILE)

    run_ngspice(netlist, sim_dir)
    assert os.path.exists(f"{sim_dir}/op.log")

def test_dc():
    sim_dir = f"/foss/designs/simulations/{TB_NAME}/test_dc"
    netlist = ""
    netlist += netlist_pvt_header()
    netlist += netlist_feedback_unity()
    netlist += netlist_stimulus_dc()
    netlist += netlist_sim_dc(filename=f"{sim_dir}/results.raw")
    
    # read main netlist 
    netlist += netlist_test_bench(NETLIST_FILE)

    run_ngspice(netlist, sim_dir)
    assert os.path.exists(f"{sim_dir}/results.raw")

def test_ac():
    sim_dir = f"/foss/designs/simulations/{TB_NAME}/test_ac"
    netlist = ""
    netlist += netlist_pvt_header()
    netlist += netlist_feedback_unity()
    netlist += netlist_stimulus_ac()
    netlist += netlist_sim_ac(filename=f"{sim_dir}/results.raw")
    
    # read main netlist 
    netlist += netlist_test_bench(NETLIST_FILE)

    run_ngspice(netlist, sim_dir)
    assert os.path.exists(f"{sim_dir}/results.raw")

def test_tran():
    sim_dir = f"/foss/designs/simulations/{TB_NAME}/test_tran"
    netlist = ""
    netlist += netlist_pvt_header()
    netlist += netlist_feedback_unity()
    netlist += netlist_stimulus_sin()
    netlist += netlist_sim_tran(filename=f"{sim_dir}/results.raw")

    # read main netlist 
    netlist += netlist_test_bench(NETLIST_FILE)

    run_ngspice(netlist, sim_dir)
    assert os.path.exists(f"{sim_dir}/results.raw")

def test_tran_square():
    """Transient analysis with square wave stimulus
    - 100mV peak-to-peak square wave at 10MHz
    - Centered around 1.5V DC bias
    - Unity gain feedback configuration
    - 3 cycles simulation
    """
    sim_dir = f"/foss/designs/simulations/{TB_NAME}/test_tran_square"
    
    # Calculate simulation parameters
    freq = 10e6  # 10MHz
    period = 1/freq
    sim_time = 3 * period  # 3 cycles
    
    # Calculate voltage levels for 100mV peak-to-peak around 1.5V
    dc_bias = 1.5
    v_pp = 100e-3
    v_low = dc_bias - v_pp/2
    v_high = dc_bias + v_pp/2
    
    netlist = ""
    netlist += netlist_pvt_header()
    netlist += netlist_feedback_unity()
    netlist += netlist_stimulus_square(
        v_low=v_low,        # 1.45V
        v_high=v_high,      # 1.55V
        t_rise=0,           # Instant rise
        t_fall=0,           # Instant fall
        t_delay=0,          # No delay
        period=period       # 10MHz period
    )
    netlist += netlist_sim_tran(
        start=0,
        stop=sim_time,
        step=period/100,    # 100 points per period
        filename=f"{sim_dir}/results.raw"
    )
    
    # read main netlist 
    netlist += netlist_test_bench(NETLIST_FILE)

    run_ngspice(netlist, sim_dir)
    assert os.path.exists(f"{sim_dir}/results.raw")


if __name__ == "__main__":
    
    test_op()
    test_dc()
    test_ac()
    test_tran()
    test_tran_square()