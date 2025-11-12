#!/usr/bin/env python3
"""
Metric and Imperial Unit Converter
Converts between various metric and imperial measurements including:
- Length (km, m, cm, mm ↔ miles, yards, feet, inches)
- Weight (kg, g, mg ↔ pounds, ounces)
- Volume (liters, ml ↔ gallons, quarts, pints, cups, fl oz)
- Temperature (Celsius ↔ Fahrenheit, Kelvin)

Architecture:
- UnitConverter: Business logic for conversions
- ConverterUI: User interface and display logic
"""


# ==================== BUSINESS LOGIC CLASS ====================


class UnitConverter:
    """
    Handles all unit conversion logic.
    No display/UI logic - pure business logic only.
    """

    # Conversion factors as class attributes
    LENGTH_TO_METERS = {
        "km": 1000,
        "m": 1,
        "cm": 0.01,
        "mm": 0.001,
        "mile": 1609.344,
        "yard": 0.9144,
        "foot": 0.3048,
        "inch": 0.0254,
    }

    WEIGHT_TO_KG = {
        "kg": 1,
        "g": 0.001,
        "mg": 0.000001,
        "pound": 0.453592,
        "ounce": 0.0283495,
    }

    VOLUME_TO_LITERS = {
        "liter": 1,
        "ml": 0.001,
        "gallon": 3.78541,  # US gallon
        "quart": 0.946353,  # US quart
        "pint": 0.473176,  # US pint
        "cup": 0.236588,  # US cup
        "floz": 0.0295735,  # US fluid ounce
    }

    TEMPERATURE_UNITS = ["celsius", "fahrenheit", "kelvin"]

    def __init__(self):
        """Initialize the converter."""
        # No initialization needed - using class attributes

    def get_available_units(self, category):
        """
        Get list of available units for a category.

        Args:
            category (str): Category name ('length', 'weight', 'volume', 'temperature')

        Returns:
            list: List of available unit names

        Raises:
            ValueError: If category is invalid
        """
        categories = {
            "length": list(self.LENGTH_TO_METERS.keys()),
            "weight": list(self.WEIGHT_TO_KG.keys()),
            "volume": list(self.VOLUME_TO_LITERS.keys()),
            "temperature": self.TEMPERATURE_UNITS,
        }

        if category not in categories:
            raise ValueError(f"Invalid category: {category}")

        return categories[category]

    def convert_length(self, value, from_unit, to_unit):
        """
        Convert length measurements.

        Args:
            value (float): Value to convert
            from_unit (str): Source unit
            to_unit (str): Target unit

        Returns:
            float: Converted value

        Raises:
            ValueError: If units are invalid
        """
        if (
            from_unit not in self.LENGTH_TO_METERS
            or to_unit not in self.LENGTH_TO_METERS
        ):
            raise ValueError("Invalid length unit")

        # Convert to meters first, then to target unit
        meters = value * self.LENGTH_TO_METERS[from_unit]
        result = meters / self.LENGTH_TO_METERS[to_unit]
        return result

    def convert_weight(self, value, from_unit, to_unit):
        """
        Convert weight measurements.

        Args:
            value (float): Value to convert
            from_unit (str): Source unit
            to_unit (str): Target unit

        Returns:
            float: Converted value

        Raises:
            ValueError: If units are invalid
        """
        if from_unit not in self.WEIGHT_TO_KG or to_unit not in self.WEIGHT_TO_KG:
            raise ValueError("Invalid weight unit")

        # Convert to kg first, then to target unit
        kg = value * self.WEIGHT_TO_KG[from_unit]
        result = kg / self.WEIGHT_TO_KG[to_unit]
        return result

    def convert_volume(self, value, from_unit, to_unit):
        """
        Convert volume measurements.

        Args:
            value (float): Value to convert
            from_unit (str): Source unit
            to_unit (str): Target unit

        Returns:
            float: Converted value

        Raises:
            ValueError: If units are invalid
        """
        if (
            from_unit not in self.VOLUME_TO_LITERS
            or to_unit not in self.VOLUME_TO_LITERS
        ):
            raise ValueError("Invalid volume unit")

        # Convert to liters first, then to target unit
        liters = value * self.VOLUME_TO_LITERS[from_unit]
        result = liters / self.VOLUME_TO_LITERS[to_unit]
        return result

    def convert_temperature(self, value, from_unit, to_unit):
        """
        Convert temperature measurements.

        Args:
            value (float): Value to convert
            from_unit (str): Source unit
            to_unit (str): Target unit

        Returns:
            float: Converted value

        Raises:
            ValueError: If units are invalid
        """
        if (
            from_unit not in self.TEMPERATURE_UNITS
            or to_unit not in self.TEMPERATURE_UNITS
        ):
            raise ValueError("Invalid temperature unit")

        # Convert to Celsius first
        celsius = 0.0
        if from_unit == "celsius":
            celsius = value
        elif from_unit == "fahrenheit":
            celsius = (value - 32) * 5 / 9
        elif from_unit == "kelvin":
            celsius = value - 273.15

        # Convert from Celsius to target unit
        result = 0.0
        if to_unit == "celsius":
            result = celsius
        elif to_unit == "fahrenheit":
            result = (celsius * 9 / 5) + 32
        elif to_unit == "kelvin":
            result = celsius + 273.15

        return result

    def convert(self, category, value, from_unit, to_unit):
        """
        Generic conversion method that routes to appropriate converter.

        Args:
            category (str): Category ('length', 'weight', 'volume', 'temperature')
            value (float): Value to convert
            from_unit (str): Source unit
            to_unit (str): Target unit

        Returns:
            float: Converted value

        Raises:
            ValueError: If category or units are invalid
        """
        converters = {
            "length": self.convert_length,
            "weight": self.convert_weight,
            "volume": self.convert_volume,
            "temperature": self.convert_temperature,
        }

        if category not in converters:
            raise ValueError(f"Invalid category: {category}")

        return converters[category](value, from_unit, to_unit)


# ==================== USER INTERFACE CLASS ====================


class ConverterUI:
    """
    Handles all user interface and display logic.
    Uses UnitConverter for actual conversions.
    """

    def __init__(self, converter):
        """
        Initialize the UI with a converter instance.

        Args:
            converter (UnitConverter): The converter to use for conversions
        """
        self.converter = converter

    def display_header(self):
        """Display the program header."""
        print("Initializing Unit Converter...")
        print("\n" + "=" * 60)
        print(" " * 15 + "UNIT CONVERTER")
        print(" " * 10 + "Metric <-> Imperial Converter")
        print("=" * 60 + "\n")

    def display_main_menu(self):
        """Display the main menu."""
        print("\n--- MAIN MENU ---")
        print("1. Length Conversion")
        print("2. Weight Conversion")
        print("3. Volume Conversion")
        print("4. Temperature Conversion")
        print("5. Exit")
        print("-" * 30)

    def display_units(self, category):
        """
        Display available units for a category.

        Args:
            category (str): Category name

        Returns:
            list: List of available units
        """
        try:
            available_units = self.converter.get_available_units(category)
            print(f"\nAvailable {category} units:")
            for i, unit in enumerate(available_units, 1):
                print(f"  {i}. {unit}")
            return available_units
        except ValueError as e:
            print(f"[X] Error: {e}")
            return []

    def get_numeric_input(self, prompt):
        """
        Get and validate numeric input from user.

        Args:
            prompt (str): Input prompt to display

        Returns:
            float: User's numeric input
        """
        while True:
            try:
                value = float(input(prompt))
                return value
            except ValueError:
                print("[X] Invalid input! Please enter a valid number.")

    def get_unit_selection(self, available_units, prompt):
        """
        Get and validate unit selection from user.

        Args:
            available_units (list): List of available units
            prompt (str): Prompt to display

        Returns:
            str: Selected unit name
        """
        while True:
            print(f"\n{prompt}")
            for i, unit in enumerate(available_units, 1):
                print(f"  {i}. {unit}")

            try:
                choice = int(input("\nEnter your choice (number): "))
                if 1 <= choice <= len(available_units):
                    return available_units[choice - 1]
                else:
                    print(
                        f"[X] Please enter a number between 1 and {len(available_units)}"
                    )
            except ValueError:
                print("[X] Invalid input! Please enter a number.")

    def get_yes_no(self, prompt):
        """
        Get yes/no input from user.

        Args:
            prompt (str): Prompt to display

        Returns:
            bool: True for yes, False for no
        """
        while True:
            response = input(prompt).strip().lower()
            if response in ["y", "yes"]:
                return True
            elif response in ["n", "no"]:
                return False
            else:
                print("[X] Please enter 'y' or 'n'")

    def display_result(self, value, from_unit, to_unit, result):
        """
        Display conversion result.

        Args:
            value (float): Original value
            from_unit (str): Source unit
            to_unit (str): Target unit
            result (float): Converted value
        """
        print("\n" + "=" * 60)
        print(f"[RESULT]: {value} {from_unit} = {result:.6f} {to_unit}")
        print("=" * 60)

    def handle_conversion(self, category):
        """
        Handle the conversion process for a given category.

        Args:
            category (str): Category name ('length', 'weight', 'volume', 'temperature')
        """
        print(f"\n{'='*60}")
        print(f" {category.upper()} CONVERSION")
        print("=" * 60)

        # Get available units
        available_units = self.display_units(category)
        if not available_units:
            return

        # Get source unit
        from_unit = self.get_unit_selection(available_units, "Select source unit:")

        # Get target unit
        to_unit = self.get_unit_selection(available_units, "Select target unit:")

        # Get value to convert
        value = self.get_numeric_input(f"\nEnter value in {from_unit}: ")

        # Perform conversion
        try:
            result = self.converter.convert(category, value, from_unit, to_unit)
            self.display_result(value, from_unit, to_unit, result)
        except ValueError as e:
            print(f"[X] Error: {e}")

    def run(self):
        """Main program loop."""
        self.display_header()

        while True:
            self.display_main_menu()

            try:
                choice = input("Enter your choice (1-5): ").strip()

                if choice == "1":
                    self.handle_conversion("length")
                elif choice == "2":
                    self.handle_conversion("weight")
                elif choice == "3":
                    self.handle_conversion("volume")
                elif choice == "4":
                    self.handle_conversion("temperature")
                elif choice == "5":
                    print("\nThank you for using the Unit Converter!")
                    print("=" * 60 + "\n")
                    break
                else:
                    print("[X] Invalid choice! Please enter a number between 1 and 5.")

                # Ask if user wants to perform another conversion
                if choice in ["1", "2", "3", "4"]:
                    if not self.get_yes_no("\nPerform another conversion? (y/n): "):
                        print("\nThank you for using the Unit Converter!")
                        print("=" * 60 + "\n")
                        break

            except KeyboardInterrupt:
                print("\n\nProgram interrupted. Goodbye!")
                print("=" * 60 + "\n")
                break
            except Exception as e:
                print(f"[X] An unexpected error occurred: {e}")


# ==================== MAIN PROGRAM ====================


def main():
    """Main entry point - creates converter and UI, then runs the application."""
    converter = UnitConverter()
    ui = ConverterUI(converter)
    ui.run()


if __name__ == "__main__":
    main()
