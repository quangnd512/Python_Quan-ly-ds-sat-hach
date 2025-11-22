# services/excel_service.py
from tkinter import filedialog, messagebox
from models.db import insert_data, fetch_export
import pandas as pd
from datetime import datetime
import os

# === DANH SÁCH GIÁ TRỊ HỢP LỆ ===
HANG_OPTIONS = ["B.01", "B", "C1", "C", "D1", "D2", "D", "BE", "C1E", "CE",
                "D1E", "D2E", "DE", "B nâng C", "B nâng D1", "B nâng D2",
                "C1 nâng C", "C1 nâng D1", "C1 nâng D2", "C nâng D1",
                "C nâng D2", "C nâng D", "C nâng CE"]

NOIDUNG_OPTIONS = ["SH lần đầu (L+M+H+Đ)", "SH lại (Đ)", "SH lại (H)", "SH lại (H+Đ)",
                   "SH lại (L+M+H+Đ)", "SH lại (L)", "SH lại (L+M)", "SH lại (L+M+H)",
                   "SH lại (L+M+Đ)", "SH lại (L+H)", "SH lại (L+H+Đ)", "SH lại (L+Đ)",
                   "SH lại (M)", "SH lại (M+H)", "SH lại (M+Đ)", "SH lại (M+H+Đ)"]

KETQUA_OPTIONS = ["Thi đạt", "Thi trượt"]
TRANGTHAI_OPTIONS = ["Thi mới", "Phục hồi"]

# === HÀM CHUYỂN ĐỔI NGÀY (TRẢ VỀ None nếu trống hoặc sai) ===
def excel_date_to_str(val):
    if pd.isna(val) or val == "":
        return None
    if isinstance(val, (datetime, pd.Timestamp)):
        return val.strftime("%Y-%m-%d")
    if isinstance(val, (int, float)):
        try:
            return (pd.Timestamp("1899-12-30") + pd.Timedelta(days=val)).strftime("%Y-%m-%d")
        except:
            return None
    s = str(val).strip()
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except:
            continue
    return None

# === HÀM LẤY GIÁ TRỊ AN TOÀN → Ô TRỐNG = "" (KHÔNG PHẢI NaN) ===
def safe_str(val):
    if pd.isna(val) or val is None:
        return ""
    return str(val).strip()

def import_from_excel():
    file_path = filedialog.askopenfilename(
        title="Chọn file Excel để nhập",
        filetypes=[("Excel files", "*.xlsx *.xls")]
    )
    if not file_path:
        return False

    try:
        df = pd.read_excel(
            file_path,
            dtype=str,           # ← ĐỌC TẤT CẢ CỘT DƯỚI DẠNG CHUỖI
            keep_default_na=False  # ← Không biến ô trống thành NaN
            )
        
        if 'CCCD' in df.columns:
            df['CCCD'] = df['CCCD'].str.strip()
            df['CCCD'] = df['CCCD'].str.replace(r'\.0$', '', regex=True)  # xóa .0
            df['CCCD'] = df['CCCD'].str.zfill(12)  # thêm 0 vào đầu nếu thiếu

        if df.empty:
            messagebox.showwarning("Lỗi", "File Excel không có dữ liệu!")
            return False

        required_cols = ["Họ tên người nộp", "CCCD", "Hạng đào tạo", "Hạng SH", "Nội dung sát hạch"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            messagebox.showerror("Lỗi", f"Thiếu cột bắt buộc:\n{', '.join(missing_cols)}")
            return False

        success_count = 0
        errors = []

        for idx, row in df.iterrows():
            row_num = idx + 2
            err = []

            # === LẤY DỮ LIỆU VỚI Ô TRỐNG = "" (KHÔNG PHẢI NaN) ===
            ho_ten = safe_str(row.get("Họ tên người nộp"))
            cccd = safe_str(row.get("CCCD"))
            hang_dt = safe_str(row.get("Hạng đào tạo"))
            hang_sh = safe_str(row.get("Hạng SH"))
            noidung = safe_str(row.get("Nội dung sát hạch"))
            csdt = safe_str(row.get("CSĐT"))
            tiep_nhan = safe_str(row.get("Tiếp nhận phần mềm"))
            trung_tam = safe_str(row.get("Trung tâm sát hạch"))
            ghi_chu = safe_str(row.get("Ghi chú"))
            ketqua = safe_str(row.get("Kết quả sát hạch", "Thi trượt"))
            trangthai = safe_str(row.get("Trạng thái thi", "Thi mới"))

            # === KIỂM TRA BẮT BUỘC ===
            if not ho_ten:
                err.append("Họ tên trống")
            if not cccd or len(cccd) < 9:
                err.append("CCCD không hợp lệ")
            if hang_dt not in HANG_OPTIONS:
                err.append("Hạng đào tạo sai")
            if hang_sh not in HANG_OPTIONS:
                err.append("Hạng SH sai")
            if noidung not in NOIDUNG_OPTIONS:
                err.append("Nội dung sát hạch sai")
            if ketqua not in KETQUA_OPTIONS:
                err.append("Kết quả sai")
            if trangthai not in TRANGTHAI_OPTIONS:
                err.append("Trạng thái thi sai")

            if err:
                errors.append(f"Dòng {row_num}: {' | '.join(err)}")
                continue

            # === NGÀY: TRỐNG → None (DB sẽ lưu NULL), SAI → None, ĐÚNG → YYYY-MM-DD ===
            ngay_sinh = excel_date_to_str(row.get("Ngày sinh"))
            ngay_nop = excel_date_to_str(row.get("Ngày nộp hồ sơ"))
            ngay_sh = excel_date_to_str(row.get("Ngày SH"))

            # === LƯU VÀO DB (THEO THỨ TỰ VỊ TRÍ) ===
            try:
                insert_data(
                    ngay_nop or datetime.today().strftime("%Y-%m-%d"),
                    ho_ten,
                    ngay_sinh or "2000-01-01",
                    cccd,
                    hang_dt,
                    hang_sh,
                    csdt,                    # ← Ô trống = ""
                    tiep_nhan,               # ← Ô trống = ""
                    ngay_sh,                 # ← Trống = None
                    trung_tam,               # ← Ô trống = ""
                    noidung,
                    ghi_chu,                 # ← Ô trống = ""
                    ketqua,
                    trangthai
                )
                success_count += 1
            except Exception as e:
                errors.append(f"Dòng {row_num}: Lưu CSDL lỗi → {e}")

        # === THÔNG BÁO ===
        msg = f"NHẬP THÀNH CÔNG {success_count} hồ sơ!"
        if errors:
            err_text = "\n".join(errors[:20])
            if len(errors) > 20:
                err_text += f"\n... và {len(errors)-20} lỗi khác"
            messagebox.showwarning("HOÀN TẤT MỘT PHẦN", f"{msg}\n\nLỖI:\n{err_text}")
        else:
            messagebox.showinfo("HOÀN HẢO!", msg)

        return success_count > 0

    except Exception as e:
        messagebox.showerror("LỖI", f"Không đọc được file:\n{e}")
        return False

# === TẠO MẪU & XUẤT ===
def export_template():
    headers = ["Họ tên người nộp","Ngày sinh","CCCD","Hạng đào tạo","CSĐT","Ngày nộp hồ sơ","Hạng SH",
               "Tiếp nhận phần mềm","Ngày SH","Trung tâm sát hạch","Nội dung sát hạch","Ghi chú",
               "Kết quả sát hạch","Trạng thái thi"]
    pd.DataFrame(columns=headers).to_excel("MAU_NHAP_HOCVIEN.xlsx", index=False)
    messagebox.showinfo("Thành công", "Đã tạo file mẫu: MAU_NHAP_HOCVIEN.xlsx")

def export_to_excel():
    data = fetch_export() or []
    if not data:
        messagebox.showwarning("Rỗng", "Không có dữ liệu")
        return
    df = pd.DataFrame(data)
    fn = f"DS_HOCVIEN_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df.to_excel(fn, index=False)
    messagebox.showinfo("Thành công", f"Đã xuất:\n{os.path.abspath(fn)}")
    os.startfile(os.path.dirname(fn))