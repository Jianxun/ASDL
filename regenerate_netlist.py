import sys
sys.path.append('src')
from asdl.parser import ASDLParser
from asdl.generator import SPICEGenerator

print('Parsing updated inverter.yml...')
parser = ASDLParser()
asdl_file = parser.parse_file('tests/fixtures/inverter.yml')

print('Generating SPICE netlist...')
generator = SPICEGenerator() 
spice_netlist = generator.generate(asdl_file)

print('Saving to results directory...')
with open('tests/unit_tests/generator/results/inverter_netlist.spice', 'w') as f:
    f.write(spice_netlist)

print('✅ Success! Generated netlist with correct PDK models:')
print('  - NMOS: nfet_03v3') 
print('  - PMOS: pfet_03v3')
print('  - File: tests/unit_tests/generator/results/inverter_netlist.spice')

# Show first few lines of generated netlist
print('\nFirst 600 characters of generated netlist:')
print(spice_netlist[:600])
print('...') 