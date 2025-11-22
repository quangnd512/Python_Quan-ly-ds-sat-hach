# Nơi lưu: C:\Users\[Tên người dùng]\AppData\Roaming\QuanLySatHach\hoc_vien.db

# models/db.py
import sqlite3
import os
from pathlib import Path

# THƯ MỤC AN TOÀN TUYỆT ĐỐI
APP_NAME = "QuanLySatHach"
BASE_DIR = Path(os.getenv("APPDATA")) / APP_NAME
BASE_DIR.mkdir(parents=True, exist_ok=True)  # Tự động tạo nếu chưa có
DB_PATH = BASE_DIR / "hoc_vien.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def migrate_old_db_if_exists():
    old_paths = [
        Path("hoc_vien.db"),                    # DB nằm cùng thư mục exe
        Path(__file__).parent / "hoc_vien.db",  # DB nằm cùng file Python
    ]
    for old_path in old_paths:
        if old_path.exists() and old_path.name == "hoc_vien.db":
            try:
                import shutil
                shutil.copy2(old_path, DB_PATH)
                print(f"Đã di chuyển hoc_vien cũ về vị trí an toàn: {DB_PATH}")
                # Có thể xóa file cũ nếu muốn (không bắt buộc)
                # old_path.unlink()
            except Exception as e:
                print(f"Lỗi di chuyển DB: {e}")
            break

# GỌI HÀM NÀY NGAY KHI CHƯƠNG TRÌNH KHỞI ĐỘNG (trong main.py)
migrate_old_db_if_exists()

def create_table():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hoc_vien (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ngay_nop_hoso TEXT NOT NULL,
            ho_ten TEXT NOT NULL,
            ngay_sinh TEXT,  -- ĐÃ ĐỔI: nam_sinh → ngay_sinh
            cccd TEXT NOT NULL,
            hang_dao_tao TEXT NOT NULL,
            hang_sh TEXT NOT NULL,
            csdt TEXT,
            tiep_nhan TEXT,
            ngay_sh TEXT,
            trung_tam TEXT,
            noi_dung TEXT NOT NULL,
            ghi_chu TEXT,
            ket_qua TEXT NOT NULL DEFAULT 'Thi trượt',
            trang_thai_thi TEXT NOT NULL,
            deleted INTEGER DEFAULT 0
        )
    ''')

    # ĐỔI TÊN CỘT: nam_sinh → ngay_sinh (CHỈ CHẠY 1 LẦN)
    try:
        cursor.execute("ALTER TABLE hoc_vien RENAME COLUMN nam_sinh TO ngay_sinh")
        print("ĐÃ ĐỔI TÊN CỘT: nam_sinh → ngay_sinh")
    except sqlite3.OperationalError as e:
        if "no such column" in str(e):
            pass  # Cột cũ không tồn tại → bỏ qua
        elif "duplicate column" in str(e):
            pass  # Cột mới đã tồn tại → bỏ qua
        else:
            print(f"Lỗi khi đổi tên cột: {e}")

    conn.commit()
    conn.close()

def insert_data(ngay_nop, ho_ten, ngay_sinh, cccd, hang_dao_tao, hang_sh, csdt, tiep_nhan, ngay_sh, trung_tam, noi_dung, ghi_chu, ket_qua, trang_thai_thi):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO hoc_vien 
        (ngay_nop_hoso, ho_ten, ngay_sinh, cccd, hang_dao_tao, hang_sh, csdt, tiep_nhan, ngay_sh, trung_tam, noi_dung, ghi_chu, ket_qua, trang_thai_thi)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (ngay_nop, ho_ten, ngay_sinh, cccd, hang_dao_tao, hang_sh, csdt, tiep_nhan, ngay_sh, trung_tam, noi_dung, ghi_chu, ket_qua, trang_thai_thi))
    conn.commit()
    conn.close()

def update_record(id, ngay_nop, ho_ten, ngay_sinh, cccd, hang_dao_tao, hang_sh, csdt, tiep_nhan, ngay_sh, trung_tam, noi_dung, ghi_chu, ket_qua, trang_thai_thi):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE hoc_vien SET 
        ngay_nop_hoso=?, ho_ten=?, ngay_sinh=?, cccd=?, hang_dao_tao=?, hang_sh=?,
        csdt=?, tiep_nhan=?, ngay_sh=?, trung_tam=?, noi_dung=?, ghi_chu=?, ket_qua=?, trang_thai_thi=?
        WHERE id=?
    ''', (ngay_nop, ho_ten, ngay_sinh, cccd, hang_dao_tao, hang_sh, csdt, tiep_nhan, ngay_sh, trung_tam, noi_dung, ghi_chu, ket_qua, trang_thai_thi, id))
    conn.commit()
    conn.close()

def fetch_all():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM hoc_vien WHERE deleted = 0 ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return rows

def search_data(keyword):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM hoc_vien 
        WHERE deleted = 0 
        AND (ho_ten LIKE ? OR cccd LIKE ?)
        ORDER BY id DESC
    ''', (f'%{keyword}%', f'%{keyword}%'))
    rows = cursor.fetchall()
    conn.close()
    return rows

def fetch_export():
    """Lấy toàn bộ dữ liệu (kể cả đã xóa mềm) để xuất Excel"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            id, ho_ten, ngay_sinh, cccd, hang_dao_tao, csdt, ngay_nop_hoso,
            hang_sh, tiep_nhan, ngay_sh, trung_tam, noi_dung, ket_qua, ghi_chu, trang_thai_thi
        FROM hoc_vien 
        WHERE deleted = 0 
        ORDER BY id DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_record(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE hoc_vien SET deleted = 1 WHERE id = ?', (id,))
    conn.commit()
    conn.close()

def delete_record_Ev(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM hoc_vien WHERE id = ?', (id,))
    conn.commit()
    conn.close()