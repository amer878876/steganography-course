from PIL import Image
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os


def xor_bytes(data: bytes, key: str) -> bytes:
    if not key:
        return data
    key_bytes = key.encode('utf-8')
    return bytes(b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data))


def bits_to_bytes(bits: str) -> bytes:
    return bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))


def bytes_to_bits(data: bytes) -> str:
    return ''.join(format(b, '08b') for b in data)


def embed_data_in_image(image_path: str, payload: bytes, output_path: str):
    img = Image.open(image_path).convert('RGB')
    pixels = img.load()
    width, height = img.size
    total_capacity = width * height * 3
    bits = bytes_to_bits(payload)

    if len(bits) > total_capacity:
        raise ValueError(
            f"البيانات كبيرة جدًا. السعة الحالية: {total_capacity} بت، بينما تحتاج {len(bits)} بت."
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


def extract_bits_from_image(image_path: str, expected_length: int) -> bytes:
    img = Image.open(image_path).convert('RGB')
    pixels = img.load()
    width, height = img.size
    bit_stream = ''

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            for channel in (r, g, b):
                bit_stream += str(channel & 1)
                if len(bit_stream) >= 32 + expected_length * 8:
                    return bits_to_bytes(bit_stream[32:32 + expected_length * 8])
    return b''


def hide_text(image_path: str, output_path: str, text: str, password: str = ''):
    data = text.encode('utf-8')
    encrypted = xor_bytes(data, password)
    payload = len(data).to_bytes(4, byteorder='big') + encrypted
    embed_data_in_image(image_path, payload, output_path)


def reveal_text(image_path: str, password: str = ''):
    img = Image.open(image_path).convert('RGB')
    pixels = img.load()
    width, height = img.size

    bit_stream = ''
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            for channel in (r, g, b):
                bit_stream += str(channel & 1)
                if len(bit_stream) >= 32:
                    length = int(bit_stream[:32], 2)
                    if len(bit_stream) >= 32 + length * 8:
                        raw = bits_to_bytes(bit_stream[32:32 + length * 8])
                        decrypted = xor_bytes(raw, password)
                        return decrypted.decode('utf-8', errors='replace')
    return ''


class StegoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title('LSB Steganography GUI')
        self.root.geometry('700x550')
        self.root.resizable(False, False)

        style = ttk.Style()
        style.theme_use('clam')

        self.image_path = tk.StringVar(value='')
        self.output_path = tk.StringVar(value='')

        tk.Label(root, text='مسار الصورة الأصلية:', font=('Tahoma', 11), justify='right').pack(anchor='e', padx=20, pady=(20, 5))
        frame1 = tk.Frame(root)
        frame1.pack(fill='x', padx=20)
        tk.Entry(frame1, textvariable=self.image_path, width=60, font=('Tahoma', 10)).pack(side='left', fill='x', expand=True)
        tk.Button(frame1, text='اختيار صورة', command=self.select_image, width=12, bg='#2d7ff9', fg='white').pack(side='right', padx=(10, 0))

        tk.Label(root, text='نص للخفاء:', font=('Tahoma', 11), justify='right').pack(anchor='e', padx=20, pady=(15, 5))
        self.text_box = tk.Text(root, height=8, font=('Tahoma', 10))
        self.text_box.pack(fill='both', padx=20, pady=(0, 10))

        tk.Label(root, text='كلمة المرور (اختياري):', font=('Tahoma', 11), justify='right').pack(anchor='e', padx=20, pady=(0, 5))
        self.password_entry = tk.Entry(root, width=30, font=('Tahoma', 10), show='*')
        self.password_entry.pack(anchor='e', padx=20)

        btns = tk.Frame(root)
        btns.pack(pady=20)
        tk.Button(btns, text='إخفاء', command=self.encode_action, width=15, bg='#1f9d55', fg='white', font=('Tahoma', 10)).pack(side='left', padx=10)
        tk.Button(btns, text='استخراج', command=self.decode_action, width=15, bg='#f39c12', fg='white', font=('Tahoma', 10)).pack(side='left', padx=10)

    def select_image(self):
        path = filedialog.askopenfilename(filetypes=[('Images', '*.png *.jpg *.jpeg *.bmp *.webp')])
        if path:
            self.image_path.set(path)

    def encode_action(self):
        source = self.image_path.get().strip()
        text = self.text_box.get('1.0', 'end').strip()
        password = self.password_entry.get().strip()

        if not source:
            messagebox.showerror('خطأ', 'يرجى اختيار صورة أولاً.')
            return
        if not text:
            messagebox.showerror('خطأ', 'يرجى كتابة نص للإخفاء.')
            return

        directory = os.path.dirname(source) or '.'
        name, ext = os.path.splitext(os.path.basename(source))
        output = os.path.join(directory, f'{name}_hidden{ext}')

        try:
            hide_text(source, output, text, password)
            messagebox.showinfo('تم', f'تم إخفاء النص بنجاح في:\n{output}')
        except Exception as e:
            messagebox.showerror('خطأ', str(e))

    def decode_action(self):
        source = self.image_path.get().strip()
        password = self.password_entry.get().strip()

        if not source:
            messagebox.showerror('خطأ', 'يرجى اختيار الصورة التي تحتوي على رسالة مخفية.')
            return

        try:
            result = reveal_text(source, password)
            if result:
                self.text_box.delete('1.0', 'end')
                self.text_box.insert('1.0', result)
                messagebox.showinfo('تم', 'تم استخراج النص بنجاح.')
            else:
                messagebox.showwarning('تنبيه', 'لم يتم العثور على نص مخفي أو كلمة المرور غير صحيحة.')
        except Exception as e:
            messagebox.showerror('خطأ', str(e))


def main():
    root = tk.Tk()
    app = StegoGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
