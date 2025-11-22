# controllers/app_controller.py
from datetime import datetime, date
from tkinter import messagebox
import tkinter as tk
from models.db import insert_data, update_record, fetch_all, search_data, delete_record, delete_record_Ev
from services.excel_service import export_template, import_from_excel, export_to_excel

class AppController:
    def __init__(self, view):
        self.view = view

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
        summary = {r["hang_sh"]: 0 for r in rows}
        for r in rows:
            hang = r["hang_sh"]
            summary[hang] = summary.get(hang, 0) + 1
        self.view.update_summary(summary)

    def update_stats(self, rows):
        total = len(rows)
        dat = sum(1 for r in rows if r["ket_qua"] == "Thi đạt")
        truot = total - dat
        ty_le = (dat / total * 100) if total else 0
        self.view.update_stats({"total": total, "dat": dat, "truot": truot, "ty_le": ty_le})

    def validate_and_prepare(self):
        data = self.view.get_data()
        missing = [f for f in self.view.required_fields if not data.get(f)]
        if missing:
            return False, "Vui lòng nhập đầy đủ: " + ", ".join(missing)

        # Ngày sinh
        ngay_sinh = data["Ngày sinh"]
        try:
            d = datetime.strptime(ngay_sinh, "%d/%m/%Y").date()
            if d > date.today():
                return False, "Ngày sinh không được lớn hơn ngày hiện tại."
        except:
            return False, "Ngày sinh phải đúng định dạng dd/mm/yyyy."

        # Ngày nộp hồ sơ
        ngay_nop = data["Ngày nộp hồ sơ"]
        try:
            d = datetime.strptime(ngay_nop, "%d/%m/%Y").date()
            if d > date.today():
                return False, "Ngày nộp hồ sơ không được lớn hơn ngày hiện tại."
        except:
            return False, "Ngày nộp hồ sơ phải đúng định dạng dd/mm/yyyy."

        # NGÀY SH: CHỈ KIỂM TRA ĐỊNH DẠNG, CHO PHÉP TƯƠNG LAI
        ngay_sh = data["Ngày SH"]
        if ngay_sh:
            try:
                datetime.strptime(ngay_sh, "%d/%m/%Y")
            except:
                return False, "Ngày SH phải đúng định dạng dd/mm/yyyy."

        return True, data

    def save_record(self):
        ok, res = self.validate_and_prepare()
        if not ok:
            self.view.show_message("Lỗi", res, "warning")
            return
        data = res

        ketqua = self.view.get_result()
        noidung_val = "Đã đạt" if ketqua == "Thi đạt" else data["Nội dung sát hạch"]
        ghi_chu = data["Ghi chú"]
        trang_thai_thi = self.view.get_thi_status()

        ngay_nop_sql = datetime.strptime(data["Ngày nộp hồ sơ"], "%d/%m/%Y").strftime("%Y-%m-%d")

        # NGÀY SH: LƯU CHÍNH XÁC, KHÔNG MẤT DỮ LIỆU
        ngay_sh_input = data["Ngày SH"]
        ngay_sh_sql = None
        if ngay_sh_input:
            try:
                d = datetime.strptime(ngay_sh_input, "%d/%m/%Y")
                ngay_sh_sql = d.strftime("%Y-%m-%d")
            except:
                pass

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
                messagebox.showinfo("Thành công", "Đã thêm hồ sơ mới.")
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
                messagebox.showinfo("Cập nhật", "Đã cập nhật hồ sơ.")
        except Exception as e:
            messagebox.showerror("Lỗi CSDL", f"Lưu thất bại: {e}")
            return

        self.view.clear_form()
        self.show_data()

    def edit_record(self, item):
        values = self.view.tree.item(item)["values"]
        self.view.set_current_id(values[0])
        self.view.entries["Họ tên người nộp"].delete(0, tk.END); self.view.entries["Họ tên người nộp"].insert(0, values[1])
        try:
            self.view.entries["Ngày sinh"].set_date(datetime.strptime(values[2], "%d/%m/%Y").date())
        except: pass
        self.view.entries["CCCD"].delete(0, tk.END); self.view.entries["CCCD"].insert(0, values[3])
        self.view.entries["Hạng đào tạo"].set(values[4])
        self.view.entries["CSĐT"].delete(0, tk.END); self.view.entries["CSĐT"].insert(0, values[5])
        try:
            self.view.entries["Ngày nộp hồ sơ"].set_date(datetime.strptime(values[6], "%d/%m/%Y").date())
        except: pass
        self.view.entries["Hạng SH"].set(values[7])
        self.view.entries["Tiếp nhận phần mềm"].delete(0, tk.END); self.view.entries["Tiếp nhận phần mềm"].insert(0, values[8])
        try:
            self.view.entries["Ngày SH"].set_date(datetime.strptime(values[9], "%d/%m/%Y").date())
        except: pass
        self.view.entries["Trung tâm sát hạch"].delete(0, tk.END); self.view.entries["Trung tâm sát hạch"].insert(0, values[10])
        self.view.entries["Nội dung sát hạch"].set(values[11])
        self.view.result_var.set(values[12])
        self.view.entries["Ghi chú"].delete(0, tk.END); self.view.entries["Ghi chú"].insert(0, values[13])
        self.view.thi_var.set(values[14])

    def delete_record_ui(self, item):
        if not self.view.show_message("Xác nhận", "Xóa mềm hồ sơ này?", "askyesno"):
            return
        delete_record(self.view.tree.item(item)["values"][0])
        self.show_data()

    def delete_record_data(self, item):
        if not self.view.show_message("CẢNH BÁO", "XÓA VĨNH VIỄN - Không thể khôi phục!", "askyesno"):
            return
        delete_record_Ev(self.view.tree.item(item)["values"][0])
        self.show_data()

    def export_template(self):
        export_template()

    def import_from_excel(self):
        if import_from_excel():
            self.show_data()

    def export_to_excel(self):
        export_to_excel()  # ĐÃ SỬA: GỌI KHÔNG THAM SỐ