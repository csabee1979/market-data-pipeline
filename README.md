This is my data pipeline.

## Unit Converter Script

A Python script for converting between metric and imperial measurements.

### Architecture

The script uses a clean, object-oriented architecture with separated concerns:

- **`UnitConverter` class**: Pure business logic for all conversions (no UI code)
- **`ConverterUI` class**: User interface and display logic (uses UnitConverter for conversions)

This separation makes the code:

- Easy to test
- Easy to maintain
- Extensible (can add GUI, web interface, etc. without changing conversion logic)

### Features

- **Length**: km, m, cm, mm ↔ miles, yards, feet, inches
- **Weight**: kg, g, mg ↔ pounds, ounces
- **Volume**: liters, ml ↔ gallons, quarts, pints, cups, fluid ounces
- **Temperature**: Celsius ↔ Fahrenheit ↔ Kelvin

### Usage

Run the script:

```bash
python converter.py
```

The script provides an interactive menu where you can:

1. Select a measurement category (Length, Weight, Volume, or Temperature)
2. Choose your source unit
3. Choose your target unit
4. Enter the value to convert
5. Get the converted result

### Example

```
--- MAIN MENU ---
1. Length Conversion
2. Weight Conversion
3. Volume Conversion
4. Temperature Conversion
5. Exit

Enter your choice (1-5): 1

Available length units:
  1. km
  2. m
  3. cm
  4. mm
  5. mile
  6. yard
  7. foot
  8. inch

Select source unit: 5 (mile)
Select target unit: 1 (km)
Enter value in mile: 10

✓ RESULT: 10 mile = 16.093440 km
```

### Requirements

- Python 3.x (no external dependencies)

### Code Structure

```python
# Using the converter programmatically
from converter import UnitConverter

converter = UnitConverter()

# Direct conversion methods
result = converter.convert_length(10, "km", "mile")
result = converter.convert_weight(1, "kg", "pound")
result = converter.convert_volume(1, "liter", "gallon")
result = converter.convert_temperature(0, "celsius", "fahrenheit")

# Generic conversion method
result = converter.convert("length", 100, "m", "foot")

# Get available units
units = converter.get_available_units("length")
```
