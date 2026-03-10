import akshare as ak
import pandas as pd

# List all functions in akshare module
funcs = [attr for attr in dir(ak) if attr.startswith('stock_')]
print(f"Found {len(funcs)} stock-related functions:")
for f in sorted(funcs):
    print(f"  {f}")

# Also list functions with 'fund', 'flow', 'sector'
print("\nFunctions containing 'fund', 'flow', 'sector', 'north':")
for attr in dir(ak):
    if any(keyword in attr.lower() for keyword in ['fund', 'flow', 'sector', 'north', 'hsgt']):
        print(f"  {attr}")

# Check for index functions
print("\nIndex functions:")
for attr in dir(ak):
    if attr.startswith('index_'):
        print(f"  {attr}")