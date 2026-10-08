from PIL import Image
import argparse


def xor_bytes(data: bytes, key: str) -> bytes:
    if not key:
        return data
    key_bytes = key.encode('utf-8')
    return bytes(b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data))


def bit_string_from_bytes(data: bytes) -> str:
    return ''.join(format(b, '08b') for b in data)


def bytes_from_bit_string(bits: str) -> bytes:
    return bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))


def embed_payload(image_path: str, payload: bytes, output_path: str):
    img = Image.open(image_path).convert('RGB')
    pixels = img.load()
    width, height = img.size
    total_bits_capacity = width * height * 3
    bits = bit_string_from_bytes(payload)

    if len(bits) > total_bits_capacity:
        raise ValueError(
            f"البيانات كبيرة جدًا. السعة الحالية: {total_bits_capacity} بت، والبيانات تحتاج: {len(bits)} بت."
        )

    bit_index = 0
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            channels = [r, g, b]
            for i in range(3):
                if bit_index < len(bits):
                    channels[i] = (channels[i] & 254) | int(bits[bit_index])
                    bit_index += 1
            pixels[x, y] = tuple(channels)

    img.save(output_path)
    print(f"تم إخفاء البيانات بنجاح في: {output_path}")


def extract_payload(image_path: str, expected_length: int) -> bytes:
    img = Image.open(image_path).convert('RGB')
    pixels = img.load()
    width, height = img.size
    bit_string = ''

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            for channel in (r, g, b):
                bit_string += str(channel & 1)
                if len(bit_string) >= (expected_length * 8 + 32):
                    return bytes_from_bit_string(bit_string[32:32 + expected_length * 8])
    return b''


def encode_text(image_path: str, text: str, output_path: str, password: str = ''):
    data = text.encode('utf-8')
    encrypted = xor_bytes(data, password)
    payload = len(data).to_bytes(4, byteorder='big') + encrypted
    embed_payload(image_path, payload, output_path)


def decode_text(image_path: str, password: str = ''):
    img = Image.open(image_path).convert('RGB')
    pixels = img.load()
    width, height = img.size

    bit_string = ''
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            for channel in (r, g, b):
                bit_string += str(channel & 1)
                if len(bit_string) >= 32:
                    length = int(bit_string[:32], 2)
                    if len(bit_string) >= 32 + length * 8:
                        encoded = bytes_from_bit_string(bit_string[32:32 + length * 8])
                        decrypted = xor_bytes(encoded, password)
                        return decrypted.decode('utf-8', errors='replace')
    return ''


def parse_args():
    parser = argparse.ArgumentParser(description='LSB Steganography Advanced')
    subparsers = parser.add_subparsers(dest='command', required=True)

    encode_parser = subparsers.add_parser('encode', help='Hide text in an image')
    encode_parser.add_argument('input_image')
    encode_parser.add_argument('text')
    encode_parser.add_argument('output_image')
    encode_parser.add_argument('--password', default='')

    decode_parser = subparsers.add_parser('decode', help='Extract hidden text from an image')
    decode_parser.add_argument('input_image')
    decode_parser.add_argument('--password', default='')

    return parser.parse_args()


def main():
    args = parse_args()

    if args.command == 'encode':
        encode_text(args.input_image, args.text, args.output_image, args.password)
    elif args.command == 'decode':
        result = decode_text(args.input_image, args.password)
        print(result)


if __name__ == '__main__':
    main()
