from parsing import parse_zip_file

def main():
    print("This is the main flow of the system!")

    zip_path = get_zip_path_from_user()
    print(f"Recieved path: {zip_path}")
    parse_zip_file(zip_path)

def get_zip_path_from_user():
    path = input("Please enter the path to your ZIP file: ").strip()
    return path

if __name__ == "__main__":
    main()
