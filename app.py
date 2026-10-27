"""
Aplikasi Konverter Teks, Biner, Aksara Jawa, dan Penerjemah Bahasa
-------------------------------------------------------------------
Fitur:
  1. Konversi Teks <-> Biner / Hex / Base64
  2. Terjemahan teks ke berbagai bahasa (termasuk Bahasa Jawa)
  3. Aksara Jawa -> Latin -> Bahasa Indonesia

Kebutuhan:
  - Python 3.8+
  - Tkinter (bawaan Python)
  - deep-translator (hanya untuk fitur terjemahan, perlu internet)

"""

import base64
import binascii
import re
import threading
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox

try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False


# ---------------------------------------------------------------------------
# Logika konversi teks / biner / hex / base64
# ---------------------------------------------------------------------------

def text_to_binary(text: str) -> str:
    return " ".join(format(b, "08b") for b in text.encode("utf-8"))


def binary_to_text(binary: str) -> str:
    bits = "".join(binary.split())
    if not bits:
        raise ValueError("Input biner kosong.")
    if any(c not in "01" for c in bits):
        raise ValueError("Biner hanya boleh berisi karakter 0 dan 1.")
    if len(bits) % 8 != 0:
        raise ValueError("Jumlah bit harus kelipatan 8.")
    data = bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))
    return data.decode("utf-8")


def text_to_hex(text: str) -> str:
    return text.encode("utf-8").hex(" ").upper()


def hex_to_text(hex_str: str) -> str:
    cleaned = "".join(hex_str.split())
    if not cleaned:
        raise ValueError("Input hex kosong.")
    try:
        return bytes.fromhex(cleaned).decode("utf-8")
    except ValueError as exc:
        raise ValueError("Format hex tidak valid.") from exc


def text_to_base64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def base64_to_text(b64: str) -> str:
    try:
        return base64.b64decode(b64.strip(), validate=True).decode("utf-8")
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Format Base64 tidak valid.") from exc


CONVERSIONS = {
    "Teks → Biner": text_to_binary,
    "Biner → Teks": binary_to_text,
    "Teks → Hex": text_to_hex,
    "Hex → Teks": hex_to_text,
    "Teks → Base64": text_to_base64,
    "Base64 → Teks": base64_to_text,
}

LANGUAGES = {
    "Jawa": "jw",
    "Indonesia": "id",
    "Inggris": "en",
    "Sunda": "su",
    "Melayu": "ms",
    "Arab": "ar",
    "Mandarin (Sederhana)": "zh-CN",
    "Jepang": "ja",
    "Korea": "ko",
    "Belanda": "nl",
    "Jerman": "de",
    "Prancis": "fr",
    "Spanyol": "es",
    "Rusia": "ru",
    "Hindi": "hi",
    "Thai": "th",
}


# ---------------------------------------------------------------------------
# Transliterasi Aksara Jawa (Unicode blok U+A980 - U+A9DF) -> Latin
# ---------------------------------------------------------------------------

# Huruf vokal mandiri (aksara swara)
JAVA_INDEPENDENT_VOWELS = {
    0xA984: "a",    # A
    0xA985: "i",    # I Kawi
    0xA986: "i",    # I
    0xA987: "i",    # II
    0xA988: "u",    # U
    0xA989: "re",   # Pa Cerek
    0xA98A: "le",   # Nga Lelet
    0xA98B: "le",   # Nga Lelet Raswadi
    0xA98C: "e",    # E
    0xA98D: "ai",   # AI
    0xA98E: "o",    # O
}

# Huruf konsonan (aksara nglegena, murda, dan mahaprana)
JAVA_CONSONANTS = {
    0xA98F: "k",    # Ka
    0xA990: "k",    # Ka Sasak
    0xA991: "kh",   # Ka Murda
    0xA992: "g",    # Ga
    0xA993: "gh",   # Ga Murda
    0xA994: "ng",   # Nga
    0xA995: "c",    # Ca
    0xA996: "ch",   # Ca Murda
    0xA997: "j",    # Ja
    0xA998: "ny",   # Nya Murda
    0xA999: "jh",   # Ja Mahaprana
    0xA99A: "ny",   # Nya
    0xA99B: "th",   # Tta (tha)
    0xA99C: "th",   # Tta Mahaprana
    0xA99D: "dh",   # Dda (dha)
    0xA99E: "dh",   # Dda Mahaprana
    0xA99F: "n",    # Na Murda
    0xA9A0: "t",    # Ta
    0xA9A1: "t",    # Ta Murda
    0xA9A2: "d",    # Da
    0xA9A3: "dh",   # Da Mahaprana
    0xA9A4: "n",    # Na
    0xA9A5: "p",    # Pa
    0xA9A6: "p",    # Pa Murda
    0xA9A7: "b",    # Ba
    0xA9A8: "b",    # Ba Murda
    0xA9A9: "m",    # Ma
    0xA9AA: "y",    # Ya
    0xA9AB: "r",    # Ra
    0xA9AC: "r",    # Ra Agung
    0xA9AD: "l",    # La
    0xA9AE: "w",    # Wa
    0xA9AF: "s",    # Sa Murda
    0xA9B0: "s",    # Sa Sasak
    0xA9B1: "s",    # Sa
    0xA9B2: "h",    # Ha
}

# Sandhangan swara (tanda vokal)
JAVA_VOWEL_SIGNS = {
    0xA9B4: "a",    # Tarung
    0xA9B5: "o",    # Tolong
    0xA9B6: "i",    # Wulu
    0xA9B7: "i",    # Wulu Melik
    0xA9B8: "u",    # Suku
    0xA9B9: "u",    # Suku Mendut
    0xA9BA: "e",    # Taling
    0xA9BB: "ai",   # Dirga Mure
    0xA9BC: "e",    # Pepet
}

# Sandhangan panyigeg wanda (tanda penutup suku kata)
JAVA_CODA_SIGNS = {
    0xA980: "ng",   # Candrabindu
    0xA981: "ng",   # Cecak
    0xA982: "r",    # Layar
    0xA983: "h",    # Wignyan
}

JAVA_DIGITS = {0xA9D0 + i: str(i) for i in range(10)}
JAVA_PUNCTUATION = {0xA9C8: ", ", 0xA9C9: ". "}
JAVA_IGNORED = (
    set(range(0xA9C1, 0xA9C8))
    | set(range(0xA9CA, 0xA9CF))
    | {0xA9DE, 0xA9DF, 0x200B, 0x200C, 0x200D, 0xA9B3}
)

PENGKAL = 0xA9BE      # medial -y-
CAKRA = 0xA9BF        # medial -r-
KERET = 0xA9BD        # medial -rê-
PANGKON = 0xA9C0      # penghilang vokal
PANGRANGKEP = 0xA9CF  # tanda pengulangan kata
_REPEAT_MARK = "\uE000"


def is_javanese_script(text: str) -> bool:
    """True jika teks mengandung minimal satu karakter aksara Jawa."""
    return any(0xA980 <= ord(c) <= 0xA9DF for c in text)


def aksara_to_latin(text: str) -> str:
    """Mengubah aksara Jawa (Unicode) menjadi tulisan Latin."""
    out = []
    cur = None  # suku kata yang sedang dibangun

    def flush():
        nonlocal cur
        if cur is not None:
            out.append(cur["onset"] + cur["vowel"] + cur["coda"])
            cur = None

    for ch in text:
        cp = ord(ch)

        if cp in JAVA_CONSONANTS:
            flush()
            cur = {"onset": JAVA_CONSONANTS[cp], "vowel": "a",
                   "coda": "", "taling": False}

        elif cp in JAVA_INDEPENDENT_VOWELS:
            flush()
            cur = {"onset": "", "vowel": JAVA_INDEPENDENT_VOWELS[cp],
                   "coda": "", "taling": False}

        elif cp in JAVA_VOWEL_SIGNS:
            if cur is not None and not cur["coda"]:
                if cp == 0xA9B4 and cur["taling"]:      # taling + tarung = o
                    cur["vowel"] = "o"
                elif cp == 0xA9B4:
                    cur["vowel"] = "a"
                else:
                    cur["vowel"] = JAVA_VOWEL_SIGNS[cp]
                    cur["taling"] = (cp == 0xA9BA)

        elif cp == PENGKAL:
            if cur is not None:
                cur["onset"] += "y"

        elif cp == CAKRA:
            if cur is not None:
                cur["onset"] += "r"

        elif cp == KERET:
            if cur is not None:
                cur["onset"] += "r"
                cur["vowel"] = "e"

        elif cp == PANGKON:
            if cur is not None:
                cur["vowel"] = ""

        elif cp in JAVA_CODA_SIGNS:
            if cur is not None:
                cur["coda"] += JAVA_CODA_SIGNS[cp]
            else:
                out.append(JAVA_CODA_SIGNS[cp])

        elif cp in JAVA_DIGITS:
            flush()
            out.append(JAVA_DIGITS[cp])

        elif cp in JAVA_PUNCTUATION:
            flush()
            out.append(JAVA_PUNCTUATION[cp])

        elif cp == PANGRANGKEP:
            flush()
            out.append(_REPEAT_MARK)

        elif cp in JAVA_IGNORED:
            continue

        else:  # spasi, baris baru, huruf Latin, dll.
            flush()
            out.append(ch)

    flush()
    result = "".join(out)
    # Tanda pengulangan: "bocah" + tanda -> "bocah-bocah"
    result = re.sub(r"(\w+)" + _REPEAT_MARK, r"\1-\1", result)
    return result.replace(_REPEAT_MARK, "")


# ---------------------------------------------------------------------------
# Antarmuka
# ---------------------------------------------------------------------------

# Papan karakter aksara Jawa (kode Unicode)
PALETTE_LETTERS = [
    0xA9B2, 0xA9A4, 0xA995, 0xA9AB, 0xA98F,   # ha na ca ra ka
    0xA9A2, 0xA9A0, 0xA9B1, 0xA9AE, 0xA9AD,   # da ta sa wa la
    0xA9A5, 0xA99D, 0xA997, 0xA9AA, 0xA99A,   # pa dha ja ya nya
    0xA9A9, 0xA992, 0xA9A7, 0xA99B, 0xA994,   # ma ga ba tha nga
]
PALETTE_SIGNS = [
    0xA9B6, 0xA9B8, 0xA9BA, 0xA9B4, 0xA9BC,   # wulu suku taling tarung pepet
    0xA9BE, 0xA9BF, 0xA981, 0xA982, 0xA983,   # pengkal cakra cecak layar wignyan
    0xA9C0,                                   # pangkon
]
PALETTE_VOWELS = [0xA984, 0xA986, 0xA988, 0xA98C, 0xA98E]  # a i u e o


class KonverterApp(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        self.master = master
        self.pack(fill="both", expand=True)

        master.title("Konverter Teks, Biner, Aksara Jawa, dan Penerjemah")
        master.geometry("820x700")
        master.minsize(700, 560)

        self.jawa_family = self._find_javanese_font()
        style = ttk.Style()
        if self.jawa_family:
            style.configure("Aksara.TButton", font=(self.jawa_family, 13))

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        self.tab_konversi = ttk.Frame(notebook, padding=10)
        self.tab_terjemah = ttk.Frame(notebook, padding=10)
        self.tab_aksara = ttk.Frame(notebook, padding=10)
        notebook.add(self.tab_konversi, text="Konversi Kode")
        notebook.add(self.tab_terjemah, text="Terjemahan")
        notebook.add(self.tab_aksara, text="Aksara Jawa")

        self._build_konversi_tab()
        self._build_terjemah_tab()
        self._build_aksara_tab()

        self.status = tk.StringVar(value="Siap.")
        ttk.Label(self, textvariable=self.status, anchor="w").pack(
            fill="x", pady=(8, 0)
        )

    # ----- Komponen umum ---------------------------------------------------

    @staticmethod
    def _find_javanese_font():
        families = set(tkfont.families())
        for name in ("Javanese Text", "Noto Sans Javanese", "Tuladha Jejeg"):
            if name in families:
                return name
        return None

    @staticmethod
    def _make_text_area(parent, label, readonly=False, height=8, font=None):
        frame = ttk.LabelFrame(parent, text=label, padding=6)
        frame.pack(fill="both", expand=True, pady=4)
        text = tk.Text(frame, height=height, wrap="word",
                       font=font or ("Consolas", 10))
        scroll = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        if readonly:
            text.configure(state="disabled", background="#f3f3f3")
        return text

    @staticmethod
    def _set_output(widget, value):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", value)
        widget.configure(state="disabled")

    def _copy(self, widget):
        content = widget.get("1.0", "end").strip()
        if not content:
            self.status.set("Tidak ada hasil untuk disalin.")
            return
        self.master.clipboard_clear()
        self.master.clipboard_append(content)
        self.status.set("Hasil disalin ke clipboard.")

    def _translate_async(self, text, src, dst, on_done):
        """Menerjemahkan di thread terpisah; on_done(hasil, error) dipanggil di UI."""
        def worker():
            try:
                result = GoogleTranslator(source=src, target=dst).translate(text)
                self.master.after(0, on_done, result, None)
            except Exception as exc:  # jaringan / layanan
                self.master.after(0, on_done, None, exc)

        threading.Thread(target=worker, daemon=True).start()

    @staticmethod
    def _network_error(exc):
        messagebox.showerror(
            "Kesalahan",
            "Terjemahan gagal. Periksa koneksi internet Anda.\n\n"
            f"Detail: {exc}",
        )

    # ----- Tab konversi ----------------------------------------------------

    def _build_konversi_tab(self):
        top = ttk.Frame(self.tab_konversi)
        top.pack(fill="x")
        ttk.Label(top, text="Jenis konversi:").pack(side="left")
        self.mode_var = tk.StringVar(value="Teks → Biner")
        ttk.Combobox(
            top, textvariable=self.mode_var, values=list(CONVERSIONS),
            state="readonly", width=20,
        ).pack(side="left", padx=8)

        self.k_input = self._make_text_area(self.tab_konversi, "Input")
        self.k_output = self._make_text_area(
            self.tab_konversi, "Hasil", readonly=True
        )

        btns = ttk.Frame(self.tab_konversi)
        btns.pack(fill="x", pady=(6, 0))
        ttk.Button(btns, text="Konversi", command=self.do_convert).pack(side="left")
        ttk.Button(
            btns, text="Salin Hasil", command=lambda: self._copy(self.k_output)
        ).pack(side="left", padx=6)
        ttk.Button(btns, text="Bersihkan", command=self.clear_convert).pack(side="left")

    def do_convert(self):
        source = self.k_input.get("1.0", "end").rstrip("\n")
        if not source.strip():
            messagebox.showwarning("Peringatan", "Input tidak boleh kosong.")
            return
        try:
            result = CONVERSIONS[self.mode_var.get()](source)
        except (ValueError, UnicodeDecodeError) as exc:
            messagebox.showerror("Kesalahan", str(exc))
            self.status.set("Konversi gagal.")
            return
        self._set_output(self.k_output, result)
        self.status.set(f"Konversi berhasil ({self.mode_var.get()}).")

    def clear_convert(self):
        self.k_input.delete("1.0", "end")
        self._set_output(self.k_output, "")
        self.status.set("Siap.")

    # ----- Tab terjemahan --------------------------------------------------

    def _build_terjemah_tab(self):
        top = ttk.Frame(self.tab_terjemah)
        top.pack(fill="x")
        ttk.Label(top, text="Bahasa sumber:").pack(side="left")
        self.src_var = tk.StringVar(value="Otomatis")
        ttk.Combobox(
            top, textvariable=self.src_var,
            values=["Otomatis"] + list(LANGUAGES),
            state="readonly", width=18,
        ).pack(side="left", padx=(6, 16))

        ttk.Label(top, text="Bahasa tujuan:").pack(side="left")
        self.dst_var = tk.StringVar(value="Jawa")
        ttk.Combobox(
            top, textvariable=self.dst_var, values=list(LANGUAGES),
            state="readonly", width=18,
        ).pack(side="left", padx=6)

        self.t_input = self._make_text_area(self.tab_terjemah, "Teks asli")
        self.t_output = self._make_text_area(
            self.tab_terjemah, "Hasil terjemahan", readonly=True
        )

        btns = ttk.Frame(self.tab_terjemah)
        btns.pack(fill="x", pady=(6, 0))
        self.btn_translate = ttk.Button(
            btns, text="Terjemahkan", command=self.do_translate
        )
        self.btn_translate.pack(side="left")
        ttk.Button(
            btns, text="Salin Hasil", command=lambda: self._copy(self.t_output)
        ).pack(side="left", padx=6)
        ttk.Button(btns, text="Bersihkan", command=self.clear_translate).pack(side="left")

        if not TRANSLATOR_AVAILABLE:
            self.btn_translate.state(["disabled"])
            self._set_output(
                self.t_output,
                "Library 'deep-translator' belum terpasang.\n"
                "Jalankan perintah berikut di terminal:\n\n"
                "    pip install deep-translator\n\n"
                "Lalu jalankan ulang aplikasi.",
            )

    def do_translate(self):
        text = self.t_input.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Peringatan", "Teks tidak boleh kosong.")
            return
        if len(text) > 5000:
            messagebox.showwarning(
                "Peringatan", "Teks terlalu panjang (maksimal 5000 karakter)."
            )
            return

        src = "auto" if self.src_var.get() == "Otomatis" else LANGUAGES[self.src_var.get()]
        dst = LANGUAGES[self.dst_var.get()]

        self.btn_translate.state(["disabled"])
        self.status.set("Menerjemahkan...")
        self._translate_async(text, src, dst, self._translate_done)

    def _translate_done(self, result, error):
        self.btn_translate.state(["!disabled"])
        if error is not None:
            self._network_error(error)
            self.status.set("Terjemahan gagal.")
            return
        self._set_output(self.t_output, result or "")
        self.status.set(f"Terjemahan ke {self.dst_var.get()} berhasil.")

    def clear_translate(self):
        self.t_input.delete("1.0", "end")
        self._set_output(self.t_output, "")
        self.status.set("Siap.")

    # ----- Tab aksara Jawa -------------------------------------------------

    def _build_palette(self, parent):
        box = ttk.LabelFrame(parent, text="Papan karakter (klik untuk menyisipkan)",
                             padding=6)
        box.pack(fill="x", pady=(0, 4))

        def add_row(codes, prefix=""):
            row = ttk.Frame(box)
            row.pack(anchor="w", pady=1)
            for cp in codes:
                ttk.Button(
                    row, text=prefix + chr(cp), width=4,
                    style="Aksara.TButton" if self.jawa_family else "TButton",
                    command=lambda c=cp: self.a_input.insert("insert", chr(c)),
                ).pack(side="left", padx=1)

        add_row(PALETTE_LETTERS[:10])
        add_row(PALETTE_LETTERS[10:])
        add_row(PALETTE_VOWELS)
        add_row(PALETTE_SIGNS, prefix="\u25CC")  # lingkaran putus-putus

        if not self.jawa_family:
            ttk.Label(
                box,
                text="Catatan: font aksara Jawa tidak ditemukan. Pasang font "
                     "'Noto Sans Javanese' agar aksara tampil dengan benar.",
                foreground="#8a1f1f",
            ).pack(anchor="w", pady=(4, 0))

    def _build_aksara_tab(self):
        tab = self.tab_aksara
        self._build_palette(tab)

        font = (self.jawa_family, 15) if self.jawa_family else None
        self.a_input = self._make_text_area(tab, "Aksara Jawa", height=4, font=font)
        self.a_latin = self._make_text_area(
            tab, "Transliterasi Latin (Bahasa Jawa)", readonly=True, height=3
        )
        self.a_indo = self._make_text_area(
            tab, "Terjemahan Bahasa Indonesia", readonly=True, height=3
        )

        btns = ttk.Frame(tab)
        btns.pack(fill="x", pady=(6, 0))
        ttk.Button(btns, text="Transliterasi ke Latin",
                   command=self.do_aksara_latin).pack(side="left")
        self.btn_aksara_indo = ttk.Button(
            btns, text="Terjemahkan ke Indonesia", command=self.do_aksara_indo
        )
        self.btn_aksara_indo.pack(side="left", padx=6)
        ttk.Button(btns, text="Salin Terjemahan",
                   command=lambda: self._copy(self.a_indo)).pack(side="left")
        ttk.Button(btns, text="Bersihkan",
                   command=self.clear_aksara).pack(side="left", padx=6)

        if not TRANSLATOR_AVAILABLE:
            self.btn_aksara_indo.state(["disabled"])

    def _get_aksara_input(self):
        source = self.a_input.get("1.0", "end").strip()
        if not source:
            messagebox.showwarning("Peringatan", "Input aksara Jawa kosong.")
            return None
        if not is_javanese_script(source):
            messagebox.showwarning(
                "Peringatan",
                "Teks yang dimasukkan tidak mengandung aksara Jawa.",
            )
            return None
        return source

    def do_aksara_latin(self):
        source = self._get_aksara_input()
        if source is None:
            return
        self._set_output(self.a_latin, aksara_to_latin(source))
        self._set_output(self.a_indo, "")
        self.status.set("Transliterasi ke Latin berhasil.")

    def do_aksara_indo(self):
        source = self._get_aksara_input()
        if source is None:
            return
        latin = aksara_to_latin(source)
        self._set_output(self.a_latin, latin)
        if len(latin) > 5000:
            messagebox.showwarning(
                "Peringatan", "Teks terlalu panjang (maksimal 5000 karakter)."
            )
            return
        self.btn_aksara_indo.state(["disabled"])
        self.status.set("Menerjemahkan ke Bahasa Indonesia...")
        self._translate_async(latin, "jw", "id", self._aksara_done)

    def _aksara_done(self, result, error):
        self.btn_aksara_indo.state(["!disabled"])
        if error is not None:
            self._network_error(error)
            self.status.set("Terjemahan gagal.")
            return
        self._set_output(self.a_indo, result or "")
        self.status.set("Aksara Jawa berhasil diterjemahkan ke Bahasa Indonesia.")

    def clear_aksara(self):
        self.a_input.delete("1.0", "end")
        self._set_output(self.a_latin, "")
        self._set_output(self.a_indo, "")
        self.status.set("Siap.")


def main():
    root = tk.Tk()
    try:
        ttk.Style().theme_use("vista" if "vista" in ttk.Style().theme_names() else "clam")
    except tk.TclError:
        pass
    KonverterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()