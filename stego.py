from PIL import Image
import sys


def text_to_bits(text: str):
    data = text.encode('utf-8')
    return ''.join(format(b, '08b') for b in data)


def bits_to_text(bits: str):
    bytes_list = []
    for i in range(0, len(bits), 8):
        chunk = bits[i:i+8]
        if len(chunk) < 8:
            break
        bytes_list.append(int(chunk, 2))
    return bytes(bytes_list).decode('utf-8', errors='replace')


def embed_text_in_image(image_path: str, message: str, output_path: str):
    img = Image.open(image_path).convert('RGB')
    pixels = img.load()
    width, height = img.size

    bit_string = text_to_bits(message)
    max_bits = width * height * 3

    if len(bit_string) > max_bits:
        raise ValueError(
            f"الرسالة كبيرة جدًا. الحد الأقصى هو {max_bits} بت في هذه الصورة."
        )

    bit_index = 0
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            channels = [r, g, b]

            for i in range(3):
                if bit_index < len(bit_string):
                    channels[i] = (channels[i] & 254) | int(bit_string[bit_index])
                    bit_index += 1

            pixels[x, y] = tuple(channels)

    img.save(output_path)
    print(f"تم إخفاء الرسالة في الصورة بنجاح: {output_path}")


def extract_text_from_image(image_path: str):
    img = Image.open(image_path).convert('RGB')
    pixels = img.load()
    width, height = img.size

    bit_string = ''
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            for channel in (r, g, b):
                bit_string += str(channel & 1)

    # استخراج الرسالة من البتات: سنفترض أن النص غير منتهي بالصفر.
    # في تطبيق أكثر احترافية، من الأفضل إخفاء طول الرسالة أولًا.
    # هنا سنفصل النص ككل من أول bit String إلى النهاية.
    # لاحظ: هذا يعمل على الرسائل الصغيرة دون معالجة الطول.
    # 
    # إذا أردت توسيع المشروع لاحقًا، أضف طول الرسالة أولًا.
    return bits_to_text(bit_string)


def main():
    if len(sys.argv) < 3:
        print("الاستخدام:")
        print("python stego.py encode <input_image> \"النص\" <output_image>")
        print("python stego.py decode <image_with_hidden_text>")
        return

    action = sys.argv[1].lower()

    if action == 'encode':
        if len(sys.argv) != 5:
            print("خطأ: استخدم: python stego.py encode <input_image> \"النص\" <output_image>")
            return

        input_image = sys.argv[2]
        message = sys.argv[3]
        output_image = sys.argv[4]
        embed_text_in_image(input_image, message, output_image)

    elif action == 'decode':
        if len(sys.argv) != 3:
            print("خطأ: استخدم: python stego.py decode <image_with_hidden_text>")
            return

        image_path = sys.argv[2]
        message = extract_text_from_image(image_path)
        print("النص المخفي:")
        print(message)

    else:
        print("إجراء غير معروف. اختر encode أو decode.")


if __name__ == '__main__':
    main()
