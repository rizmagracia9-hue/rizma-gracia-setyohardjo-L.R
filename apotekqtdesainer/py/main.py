import sys
import sqlite3
import datetime
from PyQt5 import QtWidgets, QtCore, QtGui
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas

# --- IMPORT FILE UI ---
# Pastikan file-file ini ada di folder yang sama
try:
    from main_window import Ui_MainWindow as Ui_Dashboard
    from stok import Ui_MainWindow as Ui_Stok
    from penjualan import Ui_MainWindow as Ui_Penjualan
    from data_pembeli import Ui_MainWindow as Ui_Pembeli
    from supplier import Ui_MainWindow as Ui_Supplier
    from pembelian import Ui_MainWindow as Ui_Pembelian
except ImportError as e:
    print(f"ERROR CRITICAL: File UI tidak ditemukan ({e}).")
    sys.exit(1)

# --- DATABASE HANDLER ---
class Database:
    def __init__(self, db_name="db_apotek.db"):
        self.db_name = db_name

    def connect(self):
        return sqlite3.connect(self.db_name)

    def fetch_all(self, query, params=()):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            return cursor.fetchall()
        except Exception as e:
            print(f"DB Error: {e}")
            return []
        finally:
            conn.close()

    def fetch_one(self, query, params=()):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            return cursor.fetchone()
        except Exception as e:
            print(f"DB Error: {e}")
            return None
        finally:
            conn.close()

    def execute_query(self, query, params=()):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            conn.commit()
            return True
        except Exception as e:
            print(f"DB Error: {e}")
            return False
        finally:
            conn.close()

# --- BASE WINDOW (NAVIGATION FIX) ---
class BaseWindow(QtWidgets.QMainWindow):
    """
    Kelas Induk untuk semua halaman.
    Menggunakan deteksi TEKS pada tombol untuk navigasi.
    """
    def setup_navigation(self):
        # Cari semua tombol (QPushButton) yang ada di halaman ini
        all_buttons = self.findChildren(QtWidgets.QPushButton)
        
        for btn in all_buttons:
            # Ambil teks tombol, ubah ke huruf kecil, hilangkan spasi
            text = btn.text().lower().strip()
            
            # --- LOGIKA PENCOCOKAN TEKS ---
            # Sesuaikan kata kunci ini dengan Tulisan di Tombol Aplikasi Anda
            
            if "dashboard" in text or "home" in text:
                try: btn.clicked.disconnect() 
                except: pass
                btn.clicked.connect(self.buka_dashboard)
                
            elif "stok" in text or "obat" in text:
                try: btn.clicked.disconnect() 
                except: pass
                btn.clicked.connect(self.buka_stok)
                
            elif "penjualan" in text or "kasir" in text:
                try: btn.clicked.disconnect() 
                except: pass
                btn.clicked.connect(self.buka_penjualan)
                
            elif "pembeli" in text or "member" in text or "pelanggan" in text:
                try: btn.clicked.disconnect() 
                except: pass
                btn.clicked.connect(self.buka_pembeli)
                
            elif "supplier" in text or "pemasok" in text:
                try: btn.clicked.disconnect() 
                except: pass
                btn.clicked.connect(self.buka_supplier)
                
            elif "pembelian" in text or "restock" in text or "kulakan" in text:
                try: btn.clicked.disconnect() 
                except: pass
                btn.clicked.connect(self.buka_pembelian)
                
            elif "keluar" in text or "exit" in text or "logout" in text:
                btn.clicked.connect(self.close_app)

    # --- FUNGSI PINDAH HALAMAN ---
    def buka_dashboard(self): self.switch_window(DashboardWindow())
    def buka_stok(self): self.switch_window(StokWindow())
    def buka_penjualan(self): self.switch_window(PenjualanWindow())
    def buka_pembeli(self): self.switch_window(PembeliWindow())
    def buka_supplier(self): self.switch_window(SupplierWindow())
    def buka_pembelian(self): self.switch_window(PembelianWindow())
    def close_app(self): sys.exit()

    def switch_window(self, window_class):
        self.new_window = window_class
        self.new_window.show()
        self.close()

# --- DASHBOARD ---
class DashboardWindow(BaseWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Dashboard()
        self.ui.setupUi(self)
        self.db = Database()
        
        self.setup_navigation() # AUTO DETECT TOMBOL
        self.load_statistics()
        self.setup_chart()

    def load_statistics(self):
        # Statistik sederhana
        try:
            cnt_obat = self.db.fetch_one("SELECT COUNT(*) FROM medicines")[0]
            self.ui.label_16.setText(str(cnt_obat))
            
            cnt_sup = self.db.fetch_one("SELECT COUNT(*) FROM suppliers")[0]
            self.ui.label_17.setText(str(cnt_sup))
            
            tgl = datetime.date.today().strftime("%Y-%m-%d")
            omzet = self.db.fetch_one("SELECT SUM(total_harga) FROM sales WHERE tanggal LIKE ?", (f"{tgl}%",))
            omzet_val = omzet[0] if omzet and omzet[0] else 0
            self.ui.label_18.setText(f"Rp {omzet_val:,}")
            
            cnt_trans = self.db.fetch_one("SELECT COUNT(*) FROM sales")[0]
            self.ui.label_19.setText(str(cnt_trans))
            
            # Stok Menipis (Ambil 3 obat stok terendah)
            low = self.db.fetch_all("SELECT nama_obat, stok FROM medicines WHERE stok < 50 ORDER BY stok ASC LIMIT 3")
            
            # Reset
            self.ui.label_10.setText("-"); self.ui.progressBar.setValue(0); self.ui.label_13.setText("")
            self.ui.label_11.setText("-"); self.ui.progressBar_2.setValue(0); self.ui.label_14.setText("")
            self.ui.label_12.setText("-"); self.ui.progressBar_3.setValue(0); self.ui.label_15.setText("")
            
            if len(low) > 0:
                self.ui.label_10.setText(str(low[0][0]))
                self.ui.progressBar.setValue(low[0][1])
                self.ui.label_13.setText(f"{low[0][1]}/50")
            if len(low) > 1:
                self.ui.label_11.setText(str(low[1][0]))
                self.ui.progressBar_2.setValue(low[1][1])
                self.ui.label_14.setText(f"{low[1][1]}/50")
            if len(low) > 2:
                self.ui.label_12.setText(str(low[2][0]))
                self.ui.progressBar_3.setValue(low[2][1])
                self.ui.label_15.setText(f"{low[2][1]}/50")

        except Exception as e:
            print(f"Stat Error: {e}")

    def setup_chart(self):
        # Grafik Penjualan 7 Hari (Anti Error Tanggal)
        query = "SELECT tanggal, total_harga FROM sales WHERE total_harga > 0"
        rows = self.db.fetch_all(query)
        data = {}
        
        for r in rows:
            tgl, val = r[0], r[1]
            if not tgl: continue
            
            key = None
            # Deteksi Format YYYY-MM-DD
            if len(tgl) >= 10 and tgl[4] == '-' and tgl[7] == '-':
                key = tgl[:10]
            # Deteksi Format DD/MM/YYYY
            elif len(tgl) >= 10 and tgl[2] == '/' and tgl[5] == '/':
                try:
                    p = tgl[:10].split('/')
                    key = f"{p[2]}-{p[1]}-{p[0]}"
                except: pass
            
            if key:
                data[key] = data.get(key, 0) + val
                
        sorted_keys = sorted(data.keys())[-7:]
        dates = sorted_keys if sorted_keys else ["No Data"]
        values = [data[k] for k in sorted_keys] if sorted_keys else [0]
        
        self.fig, self.ax = plt.subplots(figsize=(5,3), dpi=100)
        self.ax.bar(dates, values, color='#4e73df')
        self.ax.set_title("Penjualan 7 Hari Terakhir", fontsize=9)
        self.ax.tick_params(axis='x', rotation=20, labelsize=7)
        self.ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
        self.fig.tight_layout()
        
        canvas = FigureCanvas(self.fig)
        if not self.ui.frame_10.layout():
            self.ui.frame_10.setLayout(QtWidgets.QVBoxLayout())
        
        # Bersihkan widget lama
        while self.ui.frame_10.layout().count():
            item = self.ui.frame_10.layout().takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        self.ui.frame_10.layout().addWidget(canvas)

# --- STOK ---
class StokWindow(BaseWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Stok()
        self.ui.setupUi(self)
        self.db = Database()
        self.setup_navigation() # AUTO DETECT TOMBOL
        
        # Mapping Tombol CRUD (Berdasarkan posisi/nama umum di UI Anda)
        try:
            self.ui.pushButton_7.clicked.connect(self.tambah) # Tombol Tambah
            self.ui.pushButton_9.clicked.connect(self.edit)   # Tombol Edit
            self.ui.pushButton_10.clicked.connect(self.hapus) # Tombol Hapus
        except:
            print("Warning: Tombol CRUD Stok tidak ditemukan, cek nama variabel di Qt Designer.")

        self.load_data()

    def load_data(self):
        data = self.db.fetch_all("SELECT id, nama_obat, kategori, satuan, stok, status FROM medicines")
        self.ui.tableWidget.setRowCount(0)
        for r, row in enumerate(data):
            self.ui.tableWidget.insertRow(r)
            self.ui.tableWidget.setItem(r, 0, QtWidgets.QTableWidgetItem(str(row[1]))) # Nama
            self.ui.tableWidget.setItem(r, 1, QtWidgets.QTableWidgetItem(str(row[2]))) # Kategori
            self.ui.tableWidget.setItem(r, 2, QtWidgets.QTableWidgetItem(str(row[3]))) # Satuan
            self.ui.tableWidget.setItem(r, 3, QtWidgets.QTableWidgetItem(str(row[4]))) # Stok
            self.ui.tableWidget.setItem(r, 4, QtWidgets.QTableWidgetItem(str(row[5]))) # Status
            self.ui.tableWidget.item(r, 0).setData(QtCore.Qt.UserRole, row[0]) # Hidden ID

    def tambah(self):
        nama, ok = QtWidgets.QInputDialog.getText(self, "Tambah", "Nama Obat:")
        if ok and nama:
            kat, _ = QtWidgets.QInputDialog.getText(self, "Tambah", "Kategori:")
            sat, _ = QtWidgets.QInputDialog.getText(self, "Tambah", "Satuan:")
            stok, _ = QtWidgets.QInputDialog.getInt(self, "Tambah", "Stok Awal:")
            harga, _ = QtWidgets.QInputDialog.getInt(self, "Tambah", "Harga Jual:")
            self.db.execute_query("INSERT INTO medicines (nama_obat, kategori, satuan, stok, harga_jual) VALUES (?,?,?,?,?)",
                                  (nama, kat, sat, stok, harga))
            self.load_data()

    def edit(self):
        row = self.ui.tableWidget.currentRow()
        if row < 0: return
        oid = self.ui.tableWidget.item(row, 0).data(QtCore.Qt.UserRole)
        nama_lama = self.ui.tableWidget.item(row, 0).text()
        nama_baru, ok = QtWidgets.QInputDialog.getText(self, "Edit", "Nama Obat:", text=nama_lama)
        if ok:
            stok_old = self.ui.tableWidget.item(row, 3).text()
            stok, _ = QtWidgets.QInputDialog.getInt(self, "Edit", "Update Stok:", value=int(stok_old))
            self.db.execute_query("UPDATE medicines SET nama_obat=?, stok=? WHERE id=?", (nama_baru, stok, oid))
            self.load_data()

    def hapus(self):
        row = self.ui.tableWidget.currentRow()
        if row < 0: return
        oid = self.ui.tableWidget.item(row, 0).data(QtCore.Qt.UserRole)
        if QtWidgets.QMessageBox.question(self, "Hapus", "Yakin hapus?") == QtWidgets.QMessageBox.Yes:
            self.db.execute_query("DELETE FROM medicines WHERE id=?", (oid,))
            self.load_data()

# --- PENJUALAN ---
class PenjualanWindow(BaseWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Penjualan()
        self.ui.setupUi(self)
        self.db = Database()
        self.keranjang = []
        self.setup_navigation() # AUTO DETECT TOMBOL

        try:
            self.ui.pushButton_7.clicked.connect(self.add_cart) # Tambah
            self.ui.pushButton_9.clicked.connect(self.bayar)    # Bayar
        except: pass

        # Layout Keranjang
        self.w_cart = QtWidgets.QWidget()
        self.l_cart = QtWidgets.QVBoxLayout(self.w_cart)
        self.l_cart.setAlignment(QtCore.Qt.AlignTop)
        self.ui.scrollArea.setWidget(self.w_cart)
        self.ui.scrollArea.setWidgetResizable(True)

        self.init_combo()
        self.load_hist()

    def init_combo(self):
        self.ui.comboBox.clear()
        self.map_obat = {}
        data = self.db.fetch_all("SELECT id, nama_obat, harga_jual FROM medicines WHERE stok > 0")
        for r in data:
            lbl = f"{r[1]} - Rp {r[2]:,}"
            self.ui.comboBox.addItem(lbl)
            self.map_obat[lbl] = {'id': r[0], 'nama': r[1], 'harga': r[2]}

    def add_cart(self):
        txt = self.ui.comboBox.currentText()
        if not txt: return
        d = self.map_obat.get(txt)
        qty = 1
        sub = d['harga'] * qty
        self.keranjang.append({'id': d['id'], 'nama': d['nama'], 'qty': qty, 'sub': sub})
        
        lb = QtWidgets.QLabel(f"{d['nama']} x{qty} = Rp {sub:,}")
        lb.setStyleSheet("border-bottom:1px solid #ddd;")
        self.l_cart.addWidget(lb)
        
        tot = sum(x['sub'] for x in self.keranjang)
        self.ui.label_37.setText(f"Rp {tot:,}")

    def bayar(self):
        tot = sum(x['sub'] for x in self.keranjang)
        if tot == 0: return
        try:
            val = self.ui.lineEdit.text().replace(".","").replace("Rp","").strip()
            bayar = int(val)
        except: 
            QtWidgets.QMessageBox.warning(self, "Error", "Input angka salah")
            return
        
        if bayar < tot:
            QtWidgets.QMessageBox.warning(self, "Gagal", "Uang Kurang")
            return
            
        kemb = bayar - tot
        self.ui.label_34.setText(f"Kembalian: Rp {kemb:,}")
        
        tgl = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.db.execute_query("INSERT INTO sales (tanggal, total_harga, uang_bayar, kembalian) VALUES (?,?,?,?)",
                              (tgl, tot, bayar, kemb))
        sid = self.db.fetch_one("SELECT MAX(id) FROM sales")[0]
        
        for i in self.keranjang:
            self.db.execute_query("INSERT INTO sale_details (sale_id, medicine_id, jumlah, subtotal) VALUES (?,?,?,?)",
                                  (sid, i['id'], i['qty'], i['sub']))
            self.db.execute_query("UPDATE medicines SET stok = stok - ? WHERE id = ?", (i['qty'], i['id']))
        
        QtWidgets.QMessageBox.information(self, "Sukses", "Transaksi Berhasil")
        self.keranjang = []
        for i in reversed(range(self.l_cart.count())): 
            self.l_cart.itemAt(i).widget().setParent(None)
        self.ui.lineEdit.clear()
        self.ui.label_37.setText("Rp 0")
        self.init_combo()
        self.load_hist()

    def load_hist(self):
        d = self.db.fetch_all("SELECT id, tanggal, total_harga FROM sales ORDER BY id DESC LIMIT 5")
        self.ui.tableWidget.setRowCount(0)
        for r_idx, row in enumerate(d):
            self.ui.tableWidget.insertRow(r_idx)
            self.ui.tableWidget.setItem(r_idx, 0, QtWidgets.QTableWidgetItem(str(row[0])))
            self.ui.tableWidget.setItem(r_idx, 1, QtWidgets.QTableWidgetItem(str(row[1])))
            self.ui.tableWidget.setItem(r_idx, 2, QtWidgets.QTableWidgetItem("Umum"))
            self.ui.tableWidget.setItem(r_idx, 3, QtWidgets.QTableWidgetItem(f"Rp {row[2]:,}"))

# --- PEMBELI ---
class PembeliWindow(BaseWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Pembeli()
        self.ui.setupUi(self)
        self.db = Database()
        self.setup_navigation() # AUTO DETECT TOMBOL
        
        try:
            self.ui.pushButton_7.clicked.connect(self.add)
            self.ui.pushButton_20.clicked.connect(self.delete)
            self.ui.pushButton_9.clicked.connect(self.print_pdf)
        except: pass
        self.load()

    def load(self):
        d = self.db.fetch_all("SELECT id, nama_member, alamat, telepon, email FROM members")
        self.ui.tableWidget.setRowCount(0)
        for r, row in enumerate(d):
            self.ui.tableWidget.insertRow(r)
            for c in range(1,5):
                self.ui.tableWidget.setItem(r, c-1, QtWidgets.QTableWidgetItem(str(row[c])))
            self.ui.tableWidget.item(r, 0).setData(QtCore.Qt.UserRole, row[0])

    def add(self):
        nm, ok = QtWidgets.QInputDialog.getText(self, "Baru", "Nama:")
        if ok:
            al, _ = QtWidgets.QInputDialog.getText(self, "Baru", "Alamat:")
            tl, _ = QtWidgets.QInputDialog.getText(self, "Baru", "Telp:")
            em, _ = QtWidgets.QInputDialog.getText(self, "Baru", "Email:")
            self.db.execute_query("INSERT INTO members (nama_member, alamat, telepon, email) VALUES (?,?,?,?)",
                                  (nm, al, tl, em))
            self.load()
    
    def delete(self):
        row = self.ui.tableWidget.currentRow()
        if row >= 0:
            mid = self.ui.tableWidget.item(row, 0).data(QtCore.Qt.UserRole)
            self.db.execute_query("DELETE FROM members WHERE id=?", (mid,))
            self.load()

    def print_pdf(self):
        fn = "Data_Member.pdf"
        try:
            c = canvas.Canvas(fn)
            c.drawString(50, 800, "DATA MEMBER APOTEK")
            c.line(50, 790, 500, 790)
            y = 770
            data = self.db.fetch_all("SELECT nama_member, telepon, alamat FROM members")
            for d in data:
                c.drawString(50, y, f"Nama: {d[0]} | Telp: {d[1]} | Alamat: {d[2]}")
                y -= 20
                if y < 50: c.showPage(); y = 800
            c.save()
            QtWidgets.QMessageBox.information(self, "Sukses", f"PDF Tersimpan: {fn}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))

# --- SUPPLIER ---
class SupplierWindow(BaseWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Supplier()
        self.ui.setupUi(self)
        self.db = Database()
        self.setup_navigation() # AUTO DETECT TOMBOL
        
        try: self.ui.pushButton_7.clicked.connect(self.add)
        except: pass
        self.load()

    def load(self):
        d = self.db.fetch_all("SELECT nama_supplier, alamat, telepon, email FROM suppliers")
        self.ui.tableWidget.setRowCount(0)
        for r, row in enumerate(d):
            self.ui.tableWidget.insertRow(r)
            for c, v in enumerate(row):
                self.ui.tableWidget.setItem(r, c, QtWidgets.QTableWidgetItem(str(v)))

    def add(self):
        nm, ok = QtWidgets.QInputDialog.getText(self, "Supplier", "Nama:")
        if ok:
            al, _ = QtWidgets.QInputDialog.getText(self, "Supplier", "Alamat:")
            tl, _ = QtWidgets.QInputDialog.getText(self, "Supplier", "Telp:")
            self.db.execute_query("INSERT INTO suppliers (nama_supplier, alamat, telepon) VALUES (?,?,?)", (nm, al, tl))
            self.load()

# --- PEMBELIAN ---
class PembelianWindow(BaseWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Pembelian()
        self.ui.setupUi(self)
        self.db = Database()
        self.setup_navigation() # AUTO DETECT TOMBOL
        self.load()

    def load(self):
        q = "SELECT p.id, p.tanggal, s.nama_supplier, p.total_bayar FROM purchases p LEFT JOIN suppliers s ON p.supplier_id = s.id"
        d = self.db.fetch_all(q)
        self.ui.tableWidget.setRowCount(0)
        for r, row in enumerate(d):
            self.ui.tableWidget.insertRow(r)
            self.ui.tableWidget.setItem(r, 0, QtWidgets.QTableWidgetItem(str(row[0])))
            self.ui.tableWidget.setItem(r, 1, QtWidgets.QTableWidgetItem(str(row[1])))
            self.ui.tableWidget.setItem(r, 2, QtWidgets.QTableWidgetItem(str(row[2]) if row[2] else "-"))
            self.ui.tableWidget.setItem(r, 3, QtWidgets.QTableWidgetItem(f"Rp {row[3]:,}"))

# --- MAIN ---
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    
    db_test = Database()
    if not db_test.connect():
        print("GAGAL KONEKSI DATABASE! Pastikan file db_apotek.db ada.")
    else:
        # Mulai dari Dashboard
        win = DashboardWindow()
        win.show()
        sys.exit(app.exec_())