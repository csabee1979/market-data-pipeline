This is my data pipeline.

## Database Connection

A PostgreSQL database utility module for connecting to Neon database.

### Setup

1. **Install dependencies:**

```bash
pip install -r requirements.txt
```

2. **Configure database credentials:**

Copy the `env.template` file to `.env` and add your database password:

```bash
# On Windows PowerShell
Copy-Item env.template .env

# On Linux/Mac
cp env.template .env
```

Then edit `.env` and replace `your_password_here` with your actual database password:

```
DB_PASSWORD=your_actual_password
```

### Usage

#### Quick Test

Test the database connection:

```bash
# Run the database module directly
python database.py

# Or run the comprehensive test suite
python test_database.py
```

#### Using in Your Code

```python
from database import get_connection, execute_query, verify_connection

# Method 1: Using context manager (recommended)
with get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM your_table")
    results = cursor.fetchall()

# Method 2: Using execute_query helper
results = execute_query("SELECT * FROM your_table")

# Method 3: Verify connection
success, message = verify_connection()
print(message)
```

### Database Module Features

- **`DatabaseConfig`**: Loads credentials from `.env` file
- **`DatabaseConnection`**: Connection manager with context manager support
- **`get_connection()`**: Context manager for easy connection handling
- **`execute_query()`**: Helper function for executing queries
- **`verify_connection()`**: Test and verify database connectivity

### Connection Details

- **Host**: `ep-polished-moon-agsi4bae-pooler.c-2.eu-central-1.aws.neon.tech`
- **Database**: `neondb`
- **User**: `neondb_owner`
- **SSL Mode**: `require`

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
