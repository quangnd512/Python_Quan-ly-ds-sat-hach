# controllers/app_controller.py
from datetime import datetime, date
from tkinter import messagebox
import tkinter as tk
import sqlite3  # QUAN TRỌNG: Đã thêm dòng này
from models.db import insert_data, update_record, fetch_all, search_data, delete_record, delete_record_Ev
from services.excel_service import export_template, import_from_excel, export_to_excel

class AppController:
    def __init__(self, view):
        self.view = view
        self.db_path = "hososathach.db"  # Cần cho advanced_search

    def format_row(self, r):
        r = dict(r)
        for field in ["ngay_nop_hoso", "ngay_sh", "ngay_sinh"]:
            if r[field]:
                try:
                    r[field] = datetime.strptime(r[field], "%Y-%m-%d").strftime("%d/%m/%Y")
                except:
                    pass
        return [
            r["id"], r["ho_ten"], r["ngay_sinh"], r["cccd"], r["hang_dao_tao"],
            r["csdt"], r["ngay_nop_hoso"], r["hang_sh"], r["tiep_nhan"],
            r["ngay_sh"], r["trung_tam"], r["noi_dung"], r["ket_qua"], r["ghi_chu"],
            r["trang_thai_thi"]
        ]

    def show_data(self):
        rows = fetch_all()
        formatted_rows = [self.format_row(r) for r in rows]
        self.view.update_tree(formatted_rows)
        self.update_summary(rows)
        self.update_stats(rows)

    def do_search(self, key):
        rows = search_data(key) if key else fetch_all()
        formatted_rows = [self.format_row(r) for r in rows]
        self.view.update_tree(formatted_rows)
        self.update_summary(rows)
        self.update_stats(rows)

    def update_summary(self, rows):
        summary = {}
        for r in rows:
            hang = r["hang_sh"]
            summary[hang] = summary.get(hang, 0) + 1
        self.view.update_summary(summary)

    def update_stats(self, rows):
        total = len(rows)
        dat = sum(1 for r in rows if r["ket_qua"] == "Thi đạt")
        truot = total - dat
        ty_le = round((dat / total * 100), 1) if total else 0
        self.view.update_stats({"total": total, "dat": dat, "truot": truot, "ty_le": ty_le})

    def validate_and_prepare(self):
        data = self.view.get_data()
        missing = [f for f in self.view.required_fields if not data.get(f, "").strip()]
        if missing:
            return False, "Vui lòng nhập đầy đủ các trường bắt buộc:\n" + ", ".join(missing)

        for field, name in [("Ngày sinh", "Ngày sinh"), ("Ngày nộp hồ sơ", "Ngày nộp hồ sơ"), ("Ngày SH", "Ngày SH")]:
            val = data.get(field, "")
            if val:
                try:
                    datetime.strptime(val, "%d/%m/%Y")
                except:
                    return False, f"{name} phải đúng định dạng dd/mm/yyyy."

        return True, data

    def save_record(self):
        ok, res = self.validate_and_prepare()
        if not ok:
            self.view.show_message("Lỗi nhập liệu", res, "warning")
            return
        data = res

        ketqua = self.view.get_result()
        noidung_val = "Đã đạt" if ketqua == "Thi đạt" else data["Nội dung sát hạch"]
        ghi_chu = data.get("Ghi chú", "")
        trang_thai_thi = self.view.get_thi_status()

        ngay_nop_sql = datetime.strptime(data["Ngày nộp hồ sơ"], "%d/%m/%Y").strftime("%Y-%m-%d")
        ngay_sh_sql = None
        if data.get("Ngày SH"):
            try:
                ngay_sh_sql = datetime.strptime(data["Ngày SH"], "%d/%m/%Y").strftime("%Y-%m-%d")
            except: pass

        try:
            if not self.view.get_current_id():
                insert_data(
                    ngay_nop_sql,
                    data["Họ tên người nộp"],
                    data["Ngày sinh"],
                    data["CCCD"],
                    data["Hạng đào tạo"],
                    data["Hạng SH"],
                    data["CSĐT"],
                    data["Tiếp nhận phần mềm"],
                    ngay_sh_sql,
                    data["Trung tâm sát hạch"],
                    noidung_val,
                    ghi_chu,
                    ketqua,
                    trang_thai_thi
                )
                messagebox.showinfo("Thành công", "Đã thêm hồ sơ mới!")
            else:
                update_record(
                    self.view.get_current_id(),
                    ngay_nop_sql,
                    data["Họ tên người nộp"],
                    data["Ngày sinh"],
                    data["CCCD"],
                    data["Hạng đào tạo"],
                    data["Hạng SH"],
                    data["CSĐT"],
                    data["Tiếp nhận phần mềm"],
                    ngay_sh_sql,
                    data["Trung tâm sát hạch"],
                    noidung_val,
                    ghi_chu,
                    ketqua,
                    trang_thai_thi
                )
                messagebox.showinfo("Cập nhật", "Đã cập nhật hồ sơ thành công!")
        except Exception as e:
            messagebox.showerror("Lỗi CSDL", f"Lưu thất bại: {e}")

        self.view.clear_form()
        self.show_data()

    def edit_record(self, item):
        values = self.view.tree.item(item)["values"]
        self.view.set_current_id(values[0])
        self.view.clear_form()

        self.view.entries["Họ tên người nộp"].insert(0, values[1])
        self.view.entries["CCCD"].insert(0, values[3])
        self.view.entries["CSĐT"].insert(0, values[5])
        self.view.entries["Tiếp nhận phần mềm"].insert(0, values[8])
        self.view.entries["Trung tâm sát hạch"].insert(0, values[10])
        self.view.entries["Ghi chú"].insert(0, values[13] if len(values) > 13 else "")

        self.view.entries["Hạng đào tạo"].set(values[4])
        self.view.entries["Hạng SH"].set(values[7])
        self.view.entries["Nội dung sát hạch"].set(values[11])
        self.view.result_var.set(values[12])
        self.view.thi_var.set(values[14] if len(values) > 14 else "Phục hồi")

        try:
            self.view.entries["Ngày sinh"].set_date(datetime.strptime(values[2], "%d/%m/%Y"))
            self.view.entries["Ngày nộp hồ sơ"].set_date(datetime.strptime(values[6], "%d/%m/%Y"))
            if values[9] and values[9].strip():
                self.view.entries["Ngày SH"].set_date(datetime.strptime(values[9], "%d/%m/%Y"))
        except:
            pass

    def delete_record_ui(self, item):
        if self.view.show_message("Xác nhận", "Bạn có chắc chắn muốn xóa hồ sơ này?", "askyesno"):
            delete_record(self.view.tree.item(item)["values"][0])
            self.show_data()

    def delete_record_data(self, item):
        if self.view.show_message("CẢNH BÁO", "XÓA VĨNH VIỄN - Không thể khôi phục!", "askyesno"):
            delete_record_Ev(self.view.tree.item(item)["values"][0])
            self.show_data()

    def export_template(self): export_template()
    def import_from_excel(self):
        if import_from_excel():
            self.show_data()
    def export_to_excel(self): export_to_excel()

    def advanced_search(self, search_text="", noidung=None, trangthai=None):
        """
        TÌM KIẾM NÂNG CAO HOÀN HẢO – DÙNG ĐÚNG CẤU TRÚC CỦA BẠN (models/db.py)
        """
        # Bước 1: Lấy toàn bộ dữ liệu
        all_rows = fetch_all()

        # Bước 2: Lọc theo từ khóa (Họ tên hoặc CCCD)
        if search_text:
            search_text = search_text.lower()
            all_rows = [r for r in all_rows if 
                       search_text in str(r["ho_ten"]).lower() or 
                       search_text in str(r["cccd"]).lower()]

        # Bước 3: Lọc theo Nội dung sát hạch
        if noidung and noidung != "All":
            all_rows = [r for r in all_rows if r["noi_dung"] == noidung]

        # Bước 4: Xử lý trạng thái thi "Thi mới" hoặc "Phục hồi" → chỉ lấy hồ sơ MỚI NHẤT theo CCCD
        if trangthai in ["Thi mới", "Phục hồi"]:
            # Gom nhóm theo CCCD, lấy bản ghi có id lớn nhất
            latest_by_cccd = {}
            for r in all_rows:
                cccd = r["cccd"]
                if cccd not in latest_by_cccd or r["id"] > latest_by_cccd[cccd]["id"]:
                    if r["trang_thai_thi"] == trangthai:  # Chỉ lấy đúng trạng thái
                        latest_by_cccd[cccd] = r
            all_rows = list(latest_by_cccd.values())
        elif trangthai and trangthai != "All":
            all_rows = [r for r in all_rows if r["trang_thai_thi"] == trangthai]

        # Bước 5: Sắp xếp theo ID giảm dần (mới nhất lên đầu)
        all_rows.sort(key=lambda x: x["id"], reverse=True)

        # Bước 6: Format để hiển thị
        formatted_rows = [self.format_row(r) for r in all_rows]

        # Bước 7: Cập nhật giao diện
        self.view.update_tree(formatted_rows)
        self.update_summary(all_rows)
        self.update_stats(all_rows)