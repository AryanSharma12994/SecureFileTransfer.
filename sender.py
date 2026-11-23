from encryption import encrypt_file

print("================================")
print("     SECURE FILE TRANSFER")
print("          SENDER")
print("================================")

filename = input("Enter file path: ")

try:
    encrypted_file = encrypt_file(filename)

    print()
    print("Encrypted file is ready for transfer.")
    print("File:", encrypted_file)

except FileNotFoundError:
    print("Error: File not found.")

except Exception as e:
    print("Error:", e)