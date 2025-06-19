#!/usr/bin/env python3

import sys
sys.path.append('src')
from asdl.parser import ASDLParser
from asdl.expander import PatternExpander

# Parse the diff pair
parser = ASDLParser()
asdl_file = parser.parse_file('tests/fixtures/diff_pair_nmos.yml')

# Get the original module
original_module = asdl_file.modules['diff_pair_nmos']
print('=== ORIGINAL INSTANCES ===')
for instance_id, instance in original_module.instances.items():
    print(f'{instance_id}: {instance.mappings}')

# Expand patterns
expander = PatternExpander()
expanded_file = expander.expand_patterns(asdl_file)
expanded_module = expanded_file.modules['diff_pair_nmos']

print('\n=== EXPANDED INSTANCES ===')
for instance_id, instance in expanded_module.instances.items():
    print(f'{instance_id}: {instance.mappings}')

print('\n=== EXPANDED PORTS ===')
for port_name, port in expanded_module.ports.items():
    print(f'{port_name}: {port}') 