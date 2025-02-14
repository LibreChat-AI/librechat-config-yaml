import logging
from pathlib import Path
import convert_yaml_style
import update_models

# Set up logging for console only
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def get_user_choice(prompt):
    """Get user input with validation."""
    while True:
        choice = input(prompt).lower()
        if choice in ['y', 'n']:
            return choice == 'y'
        print("Please enter 'y' or 'n'")

def main():
    print("\nLibreChat YAML Configuration Update Tool")
    print("=======================================\n")

    try:
        # Ask about YAML style conversion
        if get_user_choice("Do you want to update YAML style formatting? (y/n): "):
            print("\nConverting YAML style...")
            convert_yaml_style.main()
            print("YAML style conversion completed.\n")
        else:
            print("Skipping YAML style conversion.\n")

        # Ask about model list updates
        if get_user_choice("Do you want to update model lists? (y/n): "):
            print("\nUpdating model lists...")
            update_models.main()
            print("Model list updates completed.\n")
        else:
            print("Skipping model list updates.\n")

        print("All requested operations completed successfully!")
        return 0

    except Exception as e:
        logging.error(f"Script failed: {str(e)}")
        print(f"\nError: {str(e)}")
        print("Check the log file for details.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        print("\nScript encountered errors. Please check the logs.")
