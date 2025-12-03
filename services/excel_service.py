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

KETQUA_OPTIONS = ["Đạt", "Trượt M+H+Đ", "Trượt M+Đ", "Trượt H", "Trượt H+Đ", "Trượt Đ"]
TRANGTHAI_OPTIONS = ["Thi mới", "Phục hồi"]

# === HÀM CHUYỂN ĐỔI NGÀY TỪ EXCEL (CẢI TIẾN) ===
def is_valid_date(day, month, year):
    """Kiểm tra ngày có hợp lệ không"""
    try:
        datetime(year, month, day)
        return True
    except ValueError:
        return False
def excel_date_to_str(val):
    """
    Chuyển đổi giá trị ngày từ Excel sang chuỗi YYYY-MM-DD
    Xử lý nhiều định dạng: số serial, datetime object, chuỗi ngày
    """
    if pd.isna(val) or val == "" or str(val).strip() == "":
        return None
    
    # 1. Nếu là datetime object
    if isinstance(val, (datetime, pd.Timestamp)):
        return val.strftime("%Y-%m-%d")
    
    # 2. Nếu là số serial của Excel (như 44927)
    if isinstance(val, (int, float)):
        try:
            # Excel date system (1900 or 1904)
            # Excel bắt đầu từ 1899-12-30 (cho Windows)
            base_date = pd.Timestamp("1899-12-30")
            
            # Excel có bug năm nhuận 1900 (không phải năm nhuận nhưng Excel tính là nhuận)
            # Cần điều chỉnh nếu ngày >= 60 (01/03/1900)
            if val >= 60:
                val = val - 1
            
            result_date = base_date + pd.Timedelta(days=float(val))
            return result_date.strftime("%Y-%m-%d")
        except Exception as e:
            print(f"Lỗi chuyển đổi số serial {val}: {e}")
            return None
    
    # 3. Nếu là chuỗi, thử các định dạng phổ biến
    s = str(val).strip()
    
    # Danh sách định dạng thử (ưu tiên định dạng Việt Nam)
    date_formats = [
        "%d/%m/%Y",    # 01/01/2024
        "%d-%m-%Y",    # 01-01-2024
        "%d/%m/%y",    # 01/01/24
        "%d-%m-%y",    # 01-01-24
        "%Y-%m-%d",    # 2024-01-01 (ISO)
        "%m/%d/%Y",    # 01/01/2024 (US)
        "%m-%d-%Y",    # 01-01-2024 (US)
        "%d.%m.%Y",    # 01.01.2024
        "%d %m %Y",    # 01 01 2024
    ]
    
    for fmt in date_formats:
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%Y-%m-%d")
        except:
            continue
    
    # 4. Thử parse tự động với pandas (trường hợp đặc biệt)
    try:
        dt = pd.to_datetime(s, dayfirst=True)  # Ưu tiên ngày trước
        return dt.strftime("%Y-%m-%d")
    except:
        pass
    
    print(f"Không thể parse ngày: '{s}'")
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
    
def format_date_for_excel(db_date_str):
    """Chuyển đổi ngày từ DB (YYYY-MM-DD) sang định dạng Excel (dd/mm/yyyy)"""
    if not db_date_str:
        return ""
    
    try:
        # Nếu đã là định dạng đúng
        if "/" in str(db_date_str):
            return str(db_date_str)
        
        # Chuyển từ YYYY-MM-DD sang dd/mm/YYYY
        dt = datetime.strptime(str(db_date_str), "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except:
        return str(db_date_str)

# === TẠO MẪU & XUẤT ===
def export_template():
    """Tạo file mẫu - cách tốt nhất"""
    headers = ["Họ tên người nộp", "Ngày sinh", "CCCD", "Hạng đào tạo", "CSĐT", 
               "Ngày nộp hồ sơ", "Hạng SH", "Tiếp nhận phần mềm", "Ngày SH", 
               "Trung tâm sát hạch", "Nội dung sát hạch", "Ghi chú",
               "Kết quả sát hạch", "Trạng thái thi"]
    
    # Tạo DataFrame với 2 dòng:
    # Dòng 1: Hướng dẫn (sẽ được xóa)
    # Dòng 2: Mẫu (sẽ được xóa)
    sample_data = {
        "Họ tên người nộp": [
            "⚠️ XÓA 2 DÒNG NÀY - Dòng 1: Hướng dẫn, Dòng 2: Mẫu",
            "Nguyễn Văn A"
        ],
        "Ngày sinh": ["", "01/01/1990"],
        "CCCD": ["", "001234567890"],
        "Hạng đào tạo": ["", "B"],
        "CSĐT": ["", "CSDT001"],
        "Ngày nộp hồ sơ": ["", datetime.today().strftime("%d/%m/%Y")],
        "Hạng SH": ["", "B"],
        "Tiếp nhận phần mềm": ["", "Đạt"],
        "Ngày SH": ["", ""],
        "Trung tâm sát hạch": ["", "Trung tâm ABC"],
        "Nội dung sát hạch": ["", "SH lần đầu (L+M+H+Đ)"],
        "Ghi chú": ["", ""],
        "Kết quả sát hạch": ["", "Đạt"],
        "Trạng thái thi": ["", "Thi mới"]
    }
    
    df = pd.DataFrame(sample_data, columns=headers)
    
    filename = "MAU_NHAP_HOCVIEN.xlsx"
    df.to_excel(filename, index=False)
    
    messagebox.showinfo("Thành công", 
                       f"Đã tạo file mẫu: {filename}\n\n"
                       f"QUAN TRỌNG:\n"
                       f"• File có 2 dòng đầu tiên\n"
                       f"• Dòng 1: Hướng dẫn\n"
                       f"• Dòng 2: Ví dụ mẫu\n"
                       f"• XÓA CẢ 2 DÒNG NÀY TRƯỚC KHI NHẬP DỮ LIỆU!\n\n"
                       f"Sau khi xóa 2 dòng, nhập dữ liệu từ dòng 1.")
    
    os.startfile(os.path.abspath(filename))

# def export_template():
#     """Tạo file mẫu với 1 dòng ví dụ và hướng dẫn xóa"""
#     headers = ["Họ tên người nộp", "Ngày sinh", "CCCD", "Hạng đào tạo", "CSĐT", 
#                "Ngày nộp hồ sơ", "Hạng SH", "Tiếp nhận phần mềm", "Ngày SH", 
#                "Trung tâm sát hạch", "Nội dung sát hạch", "Ghi chú",
#                "Kết quả sát hạch", "Trạng thái thi"]
    
#     # Tạo 1 dòng dữ liệu mẫu
#     sample_data = {
#         "Họ tên người nộp": ["Nguyễn Văn A (VÍ DỤ - XÓA DÒNG NÀY TRƯỚC KHI NHẬP)"],
#         "Ngày sinh": ["01/01/1990"],
#         "CCCD": ["001234567890"],
#         "Hạng đào tạo": ["B"],
#         "CSĐT": ["CSDT001"],
#         "Ngày nộp hồ sơ": [datetime.today().strftime("%d/%m/%Y")],
#         "Hạng SH": ["B"],
#         "Tiếp nhận phần mềm": ["Đạt"],
#         "Ngày SH": [""],  # Để trống
#         "Trung tâm sát hạch": ["Trung tâm sát hạch ABC"],
#         "Nội dung sát hạch": ["SH lần đầu (L+M+H+Đ)"],
#         "Ghi chú": [""],
#         "Kết quả sát hạch": ["Đạt"],
#         "Trạng thái thi": ["Thi mới"]
#     }
    
#     df = pd.DataFrame(sample_data, columns=headers)
    
#     # Tên file với timestamp
#     filename = f"MAU_NHAP_HOCVIEN_{datetime.now().strftime('%Y%m%d')}.xlsx"
    
#     # Tạo Excel writer để format
#     with pd.ExcelWriter(filename, engine='openpyxl') as writer:
#         # Ghi dữ liệu
#         df.to_excel(writer, sheet_name='Mẫu nhập liệu', index=False)
        
#         # Lấy workbook và worksheet
#         workbook = writer.book
#         worksheet = writer.sheets['Mẫu nhập liệu']
        
#         # Thêm dòng hướng dẫn ở đầu
#         worksheet.insert_rows(1)
#         worksheet['A1'] = "HƯỚNG DẪN:"
#         worksheet['A2'] = "1. XÓA DÒNG VÍ DỤ MÀU ĐỎ TRƯỚC KHI NHẬP DỮ LIỆU"
#         worksheet['A3'] = "2. Chỉ nhập dữ liệu từ dòng 2 trở đi"
#         worksheet['A4'] = "3. Ngày phải đúng định dạng dd/mm/yyyy"
#         worksheet['A5'] = "4. Các trường Combobox: copy giá trị từ dòng mẫu"
        
#         # Format dòng mẫu (dòng 3) thành màu đỏ
#         from openpyxl.styles import PatternFill, Font
        
#         red_fill = PatternFill(start_color='FF9999', end_color='FF9999', fill_type='solid')
#         red_font = Font(color='990000', bold=True)
        
#         for col in range(1, len(headers) + 1):
#             cell = worksheet.cell(row=3, column=col)  # Dòng 3 là dòng mẫu
#             cell.fill = red_fill
#             cell.font = red_font
        
#         # Auto-adjust column widths
#         for column in worksheet.columns:
#             max_length = 0
#             column_letter = column[0].column_letter
#             for cell in column:
#                 try:
#                     if len(str(cell.value)) > max_length:
#                         max_length = len(str(cell.value))
#                 except:
#                     pass
#             adjusted_width = min(max_length + 2, 50)
#             worksheet.column_dimensions[column_letter].width = adjusted_width
    
#     messagebox.showinfo("Thành công", 
#                        f"Đã tạo file mẫu: {filename}\n\n"
#                        f"Lưu ý:\n"
#                        f"1. File có 1 dòng ví dụ màu đỏ\n"
#                        f"2. XÓA dòng ví dụ trước khi nhập dữ liệu thật\n"
#                        f"3. Chỉ nhập từ dòng 2 trở đi")
    
#     # Mở thư mục chứa file
#     os.startfile(os.path.dirname(os.path.abspath(filename)))

# def export_template():
#     headers = ["Họ tên người nộp","Ngày sinh","CCCD","Hạng đào tạo","CSĐT","Ngày nộp hồ sơ","Hạng SH",
#                "Tiếp nhận phần mềm","Ngày SH","Trung tâm sát hạch","Nội dung sát hạch","Ghi chú",
#                "Kết quả sát hạch","Trạng thái thi"]
#     pd.DataFrame(columns=headers).to_excel("MAU_NHAP_HOCVIEN.xlsx", index=False)
#     messagebox.showinfo("Thành công", "Đã tạo file mẫu: MAU_NHAP_HOCVIEN.xlsx")

# def export_to_excel():
#     data = fetch_export() or []
#     if not data:
#         messagebox.showwarning("Rỗng", "Không có dữ liệu")
#         return
#     df = pd.DataFrame(data)
#     fn = f"DS_HOCVIEN_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
#     df.to_excel(fn, index=False)
#     messagebox.showinfo("Thành công", f"Đã xuất:\n{os.path.abspath(fn)}")
#     os.startfile(os.path.dirname(fn))

def export_to_excel():
    """Xuất dữ liệu ra Excel với định dạng giống file mẫu"""
    data = fetch_export() or []
    if not data:
        messagebox.showwarning("Rỗng", "Không có dữ liệu để xuất")
        return
    
    # Chuyển đổi dữ liệu từ DB sang định dạng Excel
    formatted_data = []
    for row in data:
        # row là tuple từ database, chuyển sang dict
        formatted_row = {
            "Họ tên người nộp": row.get("ho_ten", ""),
            "Ngày sinh": format_date_for_excel(row.get("ngay_sinh")),
            "CCCD": row.get("cccd", ""),
            "Hạng đào tạo": row.get("hang_dao_tao", ""),
            "CSĐT": row.get("csdt", ""),
            "Ngày nộp hồ sơ": format_date_for_excel(row.get("ngay_nop_hoso")),
            "Hạng SH": row.get("hang_sh", ""),
            "Tiếp nhận phần mềm": row.get("tiep_nhan", ""),
            "Ngày SH": format_date_for_excel(row.get("ngay_sh")),
            "Trung tâm sát hạch": row.get("trung_tam", ""),
            "Nội dung sát hạch": row.get("noi_dung", ""),
            "Ghi chú": row.get("ghi_chu", ""),
            "Kết quả sát hạch": row.get("ket_qua", ""),
            "Trạng thái thi": row.get("trang_thai_thi", "")
        }
        formatted_data.append(formatted_row)
    
    # Tạo DataFrame
    df = pd.DataFrame(formatted_data)
    
    # Tên file với timestamp
    filename = f"DS_HOCVIEN_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    # Xuất ra Excel với định dạng đẹp
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Danh sách học viên', index=False)
        
        workbook = writer.book
        worksheet = writer.sheets['Danh sách học viên']
        
        # Format header
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        
        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
        center_alignment = Alignment(horizontal="center", vertical="center")
        
        # Định dạng header
        for col in range(1, len(df.columns) + 1):
            cell = worksheet.cell(row=1, column=col)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_alignment
        
        # Auto-adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    cell_len = len(str(cell.value))
                    if cell_len > max_length:
                        max_length = cell_len
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
        
        # Thêm border cho toàn bộ dữ liệu
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        for row in worksheet.iter_rows(min_row=1, max_row=len(df)+1, 
                                      min_col=1, max_col=len(df.columns)):
            for cell in row:
                cell.border = thin_border
    
    messagebox.showinfo("Thành công", 
                       f"Đã xuất {len(data)} hồ sơ ra file:\n{filename}")
    
    # Mở thư mục chứa file
    os.startfile(os.path.dirname(os.path.abspath(filename)))