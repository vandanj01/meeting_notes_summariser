import csv
import os
import sys

maxInt = sys.maxsize
while True:
    try:
        csv.field_size_limit(maxInt)
        break
    except OverflowError:
        maxInt = int(maxInt/10)

CSV_FILE_PATH = '../dataset/test_df.csv'

OUTPUT_DIRECTORY = './transcripts'

def split_csv_to_text():
    os.makedirs(OUTPUT_DIRECTORY, exist_ok = True)

    try:
        with open(CSV_FILE_PATH, mode = 'r', encoding = 'utf-8-sig') as csv_file:
            reader = csv.DictReader(csv_file)

            row_count = 0
            for row in reader:
                row_count += 1

                raw_title = row.get('id', f'meeting_{row_count}')
                safe_title = "".join([c for c in raw_title if c.isalpha() or c.isdigit() or c == ' ']).rstrip()
                filename = f"{safe_title.replace(' ', '_')}.txt"
                filepath = os.path.join(OUTPUT_DIRECTORY, filename)

                file_content = ""
                for column_name, cell_data in row.items():
                    if cell_data:
                        file_content += f"{column_name}:\n{cell_data}\n\n"

                with open(filepath, mode = 'w', encoding = 'utf-8') as txt_file:
                    txt_file.write(file_content)
            
            print(f"Success! Generated {row_count} text files in the '{OUTPUT_DIRECTORY}' folder.")

    except FileNotFoundError:
        print(f"Error: Could not find '{CSV_FILE_PATH}'. Make sure it is present at the location.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    split_csv_to_text()