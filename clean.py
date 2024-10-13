import re
import os
import base64
import gzip
import argparse

def main():
    parser = argparse.ArgumentParser(description="Deobfuscate a batch file or decode Base64 + GZIP content.")
    parser.add_argument("input_file", help="Path to the obfuscated batch file.")
    parser.add_argument("output_file", help="Path where the result will be saved (either cleaned script or binary).")
    parser.add_argument("--mode", choices=["deobf", "dump"], default="deobfuscate",
                        help="Choose whether to deobfuscate batch file or decode Base64/GZIP (default: deobfuscate).")
    args = parser.parse_args()

    if args.mode == "deobf":
        deobfuscate_batch_file(args.input_file, args.output_file)
    else:
        decode_base64_gzip(args.input_file, args.output_file)

def deobfuscate_batch_file(input_file_path, output_file_path):
    variable_dict = {}

    try:
        with open(input_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except Exception as e:
        print(f"Error reading '{input_file_path}': {e}")
        return

    # Extract variable definitions
    for line in lines:
        line = line.strip()
        if line.startswith(('::', 'REM')) or not line:
            continue
        match = re.match(r'^set\s+"?([^=]+)=([^"]*)"?$', line, re.IGNORECASE)
        if match:
            variable_dict[match.group(1).strip()] = match.group(2).strip()

    # Replace variables in commands
    def replace_var(match):
        return variable_dict.get(match.group(1), f"%{match.group(1)}%")

    cleaned_commands = [
        re.sub(r'%([^%]+)%', replace_var, line.strip())
        for line in lines if not (line.strip().startswith(('::', 'REM', 'set')) or not line.strip())
    ]

    # Save to output file
    try:
        with open(output_file_path, 'w', encoding='utf-8') as out_file:
            out_file.write('\n'.join(cleaned_commands))
        print(f"Deobfuscated script saved as: {output_file_path}")
    except Exception as e:
        print(f"Error writing to '{output_file_path}': {e}")

def decode_base64_gzip(input_file_path, output_file_path):
    last_line = read_last_line(input_file_path)
    if not last_line:
        print(f"Error: No valid content found in '{input_file_path}'")
        return

    base64_string = extract_base64(last_line)
    if not base64_string:
        print("Error: No valid Base64 string found.")
        return

    decoded_bytes = base64.b64decode(base64_string)
    if not decoded_bytes:
        print("Error: Base64 decoding failed.")
        return

    decompressed_bytes = decompress(decoded_bytes)
    if not decompressed_bytes:
        print("Error: GZIP decompression failed.")
        return

    reversed_bytes = reverse_byte_array(decompressed_bytes)
    
    save_to_file(reversed_bytes, output_file_path)
    print(f"Deobfuscated data saved to: {output_file_path}")

def read_last_line(path):
    if not os.path.exists(path):
        print(f"Error: File '{path}' does not exist.")
        return None

    with open(path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        for line in reversed(lines):
            trimmed_line = line.strip()
            if trimmed_line and not trimmed_line.startswith(("::", "REM")):
                return trimmed_line
    return None

def extract_base64(line):
    base64_pattern = re.compile(r'([A-Za-z0-9+/=]{100,})')
    match = base64_pattern.search(line)
    return match.group(1) if match else None

def reverse_byte_array(data):
    return data[::-1]

def decompress(data):
    try:
        return gzip.decompress(data)
    except Exception as e:
        print(f"Error during decompression: {e}")
        return None

def save_to_file(data, path):
    try:
        with open(path, 'wb') as file:
            file.write(data)
    except Exception as e:
        print(f"Error saving to '{path}': {e}")

if __name__ == "__main__":
    main()
