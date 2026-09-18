"""Convert a flash-linked RP2040 binary into UF2 (base address 0x10000000)."""
import struct
import sys

UF2_MAGIC_START0 = 0x0A324655
UF2_MAGIC_START1 = 0x9E5D5157
UF2_MAGIC_END = 0x0AB16F30
UF2_FAMILY_ID = 0xE48BFF56
BLOCK_SIZE = 256


def bin_to_uf2(bin_path, uf2_path):
    with open(bin_path, "rb") as source:
        data = source.read()
    if not data:
        raise ValueError("Input binary is empty")
    num_blocks = (len(data) + BLOCK_SIZE - 1) // BLOCK_SIZE
    with open(uf2_path, "wb") as output:
        for i in range(num_blocks):
            addr = 0x10000000 + i * BLOCK_SIZE
            chunk = data[i * BLOCK_SIZE:(i + 1) * BLOCK_SIZE].ljust(BLOCK_SIZE, b"\x00")
            header = struct.pack("<IIIIIIII", UF2_MAGIC_START0, UF2_MAGIC_START1,
                                 0x2000, addr, BLOCK_SIZE, i, num_blocks, UF2_FAMILY_ID)
            output.write(header + chunk + b"\x00" * 220 + struct.pack("<I", UF2_MAGIC_END))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: uf2conv.py input.bin output.uf2")
    try:
        bin_to_uf2(sys.argv[1], sys.argv[2])
    except (OSError, ValueError) as error:
        sys.exit(str(error))
