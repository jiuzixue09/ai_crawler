
import os
import geomonitor


def select_item_from_console(items):
    """Display items and let user select by index."""
    for i, item in enumerate(items):
        print(f"{i}: {item}")

    while True:
        try:
            choice = int(input("Select an website by index: "))
            if 0 <= choice < len(items):
                return items[choice]
            print("Invalid index. Try again.")
        except ValueError:
            print("Please enter a valid number.")


def input_and_out_handle():
    # Get file path from user
    file_path = input("Enter the file path to read: ").strip()
    if '/' not in file_path:
        file_path = os.path.join(os.getcwd(), file_path)

    # Check if file exists
    if not os.path.exists(file_path):
        print("File not found!")
        return

    # Get output directory
    output_dir = input("Enter the output directory: ").strip()
    if '/' not in output_dir:
        output_dir = os.path.join(os.getcwd(), output_dir)

    # Create directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Get output filename
    output_name = input("Enter the output Excel filename (without extension): ").strip()
    output_path = os.path.join(output_dir, f"{output_name}.xlsx")

    items = ['baidu', 'deepseek', 'doubao', 'yuanbao', 'chartgpt', 'all']

    selected = select_item_from_console(items)

    return file_path, output_path, selected




if __name__ == '__main__':
    file_path, output_path, selected = input_and_out_handle()
