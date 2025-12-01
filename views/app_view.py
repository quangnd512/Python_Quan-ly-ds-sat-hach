# views/app_view.py
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import date, datetime

class AppView:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("QUẢN LÝ HỒ SƠ SÁT HẠCH - TRUNG TÂM SÁT HẠCH [TÊN]")
        self.root.geometry("1400x900")
        self.root.configure(bg="#f5f6fa")

        self.entries = {}
        self.result_var = tk.StringVar(value="Đạt")        # ← Mặc định là "Đạt"
        self.thi_var = tk.StringVar(value="Phục hồi")      # Mặc định Phục hồi
        self.search_var = tk.StringVar()
        self.current_id = tk.StringVar()

        self._setup_options()
        self._setup_ui()
        self._setup_bindings()

        # Tự động điền năm sinh = ngày nộp - 18 năm
        self.root.after(100, self.update_nam_sinh_from_ngay_nop)

    def update_nam_sinh_from_ngay_nop(self):
        try:
            ngay_nop_str = self.entries["Ngày nộp hồ sơ"].get()
            if not ngay_nop_str.strip():
                return
            ngay_nop = datetime.strptime(ngay_nop_str, "%d/%m/%Y")
            nam_sinh = ngay_nop.year - 18
            self.entries["Ngày sinh"].set_date(f"01/01/{nam_sinh}")
        except:
            pass

    def _setup_options(self):
        self.labels = [
            "Họ tên người nộp", "Ngày sinh", "CCCD",
            "Hạng đào tạo", "CSĐT", "Ngày nộp hồ sơ",
            "Hạng SH", "Tiếp nhận phần mềm",
            "Ngày SH", "Trung tâm sát hạch",
            "Nội dung sát hạch", "Ghi chú"
        ]
        self.hang_options = ["B.01", "B", "C1", "C", "D1", "D2", "D", "BE", "C1E", "CE",
                             "D1E", "D2E", "DE", "B nâng C", "B nâng D1", "B nâng D2",
                             "C1 nâng C", "C1 nâng D1", "C1 nâng D2", "C nâng D1",
                             "C nâng D2", "C nâng D", "C nâng CE"]
        self.noidung_options = [
            "SH lần đầu (L+M+H+Đ)", "SH lại (Đ)", "SH lại (H)", "SH lại (H+Đ)",
            "SH lại (L+M+H+Đ)", "SH lại (L)", "SH lại (L+M)", "SH lại (L+M+H)",
            "SH lại (L+M+Đ)", "SH lại (L+H)", "SH lại (L+H+Đ)", "SH lại (L+Đ)",
            "SH lại (M)", "SH lại (M+H)", "SH lại (M+Đ)", "SH lại (M+H+Đ)"
        ]
        self.required_fields = ["Họ tên người nộp", "Ngày sinh", "CCCD", "Hạng đào tạo", "Hạng SH", "Nội dung sát hạch"]

        # 6 lựa chọn mới cho Kết quả sát hạch
        self.ketqua_options = [
            "Đạt",
            "Trượt M+H+Đ",
            "Trượt M+Đ",
            "Trượt H",
            "Trượt H+Đ",
            "Trượt Đ"
        ]

    def _setup_ui(self):
        wrapper = tk.Frame(self.root, bg="#f5f6fa")
        wrapper.pack(fill="x", pady=15)
        wrapper.grid_columnconfigure(0, weight=1)
        wrapper.grid_columnconfigure(1, weight=1)
        wrapper.grid_columnconfigure(2, weight=1)

        frame_form = tk.LabelFrame(wrapper, text="Thông tin Hồ sơ", font=("Arial", 12, "bold"), bg="white", padx=30, pady=20)
        frame_form.grid(row=0, column=1, sticky="n")

        for i, label in enumerate(self.labels):
            row, col = divmod(i, 2)
            lbl_frame = tk.Frame(frame_form, bg="white")
            lbl_frame.grid(row=row, column=col*2, sticky="e", padx=10, pady=6)
            tk.Label(lbl_frame, text=label + ":", font=("Arial", 10, "bold"), bg="white").pack(side="left")
            if label in self.required_fields:
                tk.Label(lbl_frame, text="*", fg="red", bg="white", font=("Arial", 10, "bold")).pack(side="left")

            if label in ["Ngày nộp hồ sơ", "Ngày SH"]:
                entry = DateEntry(frame_form, width=22, date_pattern="dd/mm/yyyy", maxdate=date.today())
                entry.set_date(date.today())
            elif label == "Ngày sinh":
                entry = DateEntry(frame_form, width=22, date_pattern="dd/mm/yyyy")
                entry.delete(0, "end")
            elif label in ["Hạng đào tạo", "Hạng SH"]:
                entry = ttk.Combobox(frame_form, values=self.hang_options, width=26, state="readonly")
                entry.set(self.hang_options[0])
            elif label == "Nội dung sát hạch":
                entry = ttk.Combobox(frame_form, values=self.noidung_options, width=26, state="readonly")
                entry.set(self.noidung_options[0])
            else:
                entry = tk.Entry(frame_form, width=28)

            entry.grid(row=row, column=col*2 + 1, padx=10, pady=6)
            self.entries[label] = entry

        # === KẾT QUẢ SÁT HẠCH + TRẠNG THÁI THI ===
        status_row = len(self.labels) // 2 + 1
        status_frame = tk.Frame(frame_form, bg="white")
        status_frame.grid(row=status_row, column=0, columnspan=4, pady=15, sticky="ew")

        # KẾT QUẢ SÁT HẠCH – DẠNG DROPDOWN (COMBOBOX) SIÊU ĐẸP
        result_frame = tk.Frame(status_frame, bg="white")
        result_frame.grid(row=0, column=0, sticky="w", padx=(20, 40))

        tk.Label(result_frame, text="Kết quả sát hạch:", font=("Arial", 10, "bold"), bg="white", fg="#2c3e50").pack(side="left", padx=(0, 10))

        self.ketqua_cb = ttk.Combobox(
            result_frame,
            textvariable=self.result_var,
            values=self.ketqua_options,
            width=18,
            state="readonly",
            font=("Arial", 10),
            justify="center"
        )
        self.ketqua_cb.pack(side="left")
        self.ketqua_cb.set("Đạt")  # Mặc định Đạt

        # Trạng thái thi
        thi_frame = tk.Frame(status_frame, bg="white")
        thi_frame.grid(row=0, column=1, sticky="e", padx=(40, 20))
        tk.Label(thi_frame, text="Trạng thái thi*:", font=("Arial", 10, "bold"), bg="white").pack(side="left")
        tk.Label(thi_frame, text="*", fg="red", bg="white", font=("Arial", 10, "bold")).pack(side="left")
        tk.Radiobutton(thi_frame, text="Thi mới", variable=self.thi_var, value="Thi mới", bg="white").pack(side="right", padx=8)
        tk.Radiobutton(thi_frame, text="Phục hồi", variable=self.thi_var, value="Phục hồi", bg="white").pack(side="right", padx=8)

        # Search
        search_frame = tk.Frame(self.root, bg="#f5f6fa")
        search_frame.pack(fill="x", pady=10)
        tk.Label(search_frame, text="Tìm kiếm (Họ tên / CCCD):", bg="#f5f6fa", font=("Arial", 10, "bold")).pack(side="left", padx=10)
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=40)
        self.search_entry.pack(side="left", padx=10)
        ttk.Button(search_frame, text="Hiển thị tất cả", command=self.reset_search, width=18).pack(side="left", padx=6)

        # Summary & Stats
        self.summary_frame = tk.Frame(self.root, bg="#f5f6fa")
        self.summary_frame.pack(pady=8, fill="x")

        self.stats_frame = tk.LabelFrame(self.root, text="Thống kê", font=("Arial", 11, "bold"), bg="white", padx=10, pady=5)
        self.stats_frame.pack(fill="x", padx=15, pady=5)

        # Buttons
        btn_frame = tk.Frame(self.root, bg="#f5f6fa")
        btn_frame.pack(fill="x", pady=8)
        self.btn_save = ttk.Button(btn_frame, text="Lưu hồ sơ", width=18)
        self.btn_save.pack(side="left", padx=6)
        self.btn_edit = ttk.Button(btn_frame, text="Sửa hồ sơ", width=18)
        self.btn_edit.pack(side="left", padx=6)
        self.btn_del_soft = ttk.Button(btn_frame, text="Xóa hồ sơ", width=18)
        self.btn_del_soft.pack(side="left", padx=6)
        self.btn_template = ttk.Button(btn_frame, text="Tải mẫu Excel", width=18)
        self.btn_template.pack(side="right", padx=6)
        self.btn_import = ttk.Button(btn_frame, text="Nhập Excel", width=18)
        self.btn_import.pack(side="right", padx=6)
        self.btn_export = ttk.Button(btn_frame, text="Xuất Excel", width=18)
        self.btn_export.pack(side="right", padx=6)
        self.btn_duplicate = ttk.Button(btn_frame, text="Nhân bản hồ sơ", width=22)
        self.btn_duplicate.pack(side="left", padx=8)
        ttk.Button(btn_frame, text="Hủy nhập", command=self.clear_form, width=14).pack(side="left", padx=6)

        # Table
        frame_table = tk.LabelFrame(self.root, text="Danh sách hồ sơ", font=("Arial", 12, "bold"), bg="white", padx=10, pady=10)
        frame_table.pack(fill="both", expand=True, padx=15, pady=10)

        cols = ["ID", "Họ tên", "Ngày sinh", "CCCD", "Hạng ĐT", "CSĐT", "Ngày nộp", 
                "Hạng SH", "Tiếp nhận", "Ngày SH", "Trung tâm", "Nội dung", 
                "Kết quả", "Ghi chú", "Trạng thái thi"]

        scroll_y = ttk.Scrollbar(frame_table, orient="vertical")
        scroll_x = ttk.Scrollbar(frame_table, orient="horizontal")

        self.tree = ttk.Treeview(
            frame_table,
            columns=cols,
            show="headings",
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set
        )

        self.tree.column("ID", width=0, minwidth=0, stretch=False)
        self.tree.heading("ID", text="")
        self.tree["displaycolumns"] = ("Họ tên", "Ngày sinh", "CCCD", "Hạng ĐT", "CSĐT", "Ngày nộp",
                                       "Hạng SH", "Tiếp nhận", "Ngày SH", "Trung tâm", "Nội dung",
                                       "Kết quả", "Ghi chú", "Trạng thái thi")

        for col in cols[1:]:
            self.tree.heading(col, text=col)
            width = 150 if col in ["Họ tên", "CCCD", "Trung tâm", "Nội dung", "Ghi chú"] else 110
            anchor = "w" if col in ["Họ tên", "CCCD", "Trung tâm", "Nội dung", "Ghi chú"] else "center"
            self.tree.column(col, width=width, anchor=anchor)

        scroll_y.config(command=self.tree.yview)
        scroll_y.pack(side="right", fill="y")
        scroll_x.config(command=self.tree.xview)
        scroll_x.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))
        style.configure("Treeview", font=("Arial", 9))

    def set_controller(self, controller):
        self.controller = controller
        self.setup_controller_commands()

    def setup_controller_commands(self):
        self.btn_save.config(command=self.controller.save_record)
        self.btn_edit.config(command=lambda: self.edit_record())
        self.btn_del_soft.config(command=lambda: self.delete_record_ui())
        self.btn_template.config(command=lambda: self.export_template())
        self.btn_import.config(command=lambda: self.import_from_excel())
        self.btn_export.config(command=lambda: self.export_to_excel())
        self.btn_duplicate.config(command=self.duplicate_record)

    def _setup_bindings(self):
        # ĐÃ XÓA update_noidung → Kết quả và Nội dung giờ độc lập hoàn toàn
        self.entries["Hạng đào tạo"].bind("<<ComboboxSelected>>", self.on_hang_dt_change)
        self.entries["Ngày nộp hồ sơ"].bind("<<DateEntrySelected>>", lambda e: self.root.after(100, self.update_nam_sinh_from_ngay_nop))
        self.search_entry.bind("<KeyRelease>", self.do_search)
        self.tree.bind("<Double-1>", self.edit_record)
        self.root.bind("<Control-s>", lambda e: self.controller.save_record())
        self.root.bind("<Escape>", lambda e: self.clear_form())

    def on_hang_dt_change(self, event):
        hang_dt = self.entries["Hạng đào tạo"].get()
        hang_sh = self.entries["Hạng SH"]
        if not hang_sh.get() or hang_sh.get() == getattr(event.widget, "_last", ""):
            hang_sh.set(hang_dt)
        event.widget._last = hang_dt

    def get_data(self):
        return {k: v.get().strip() for k, v in self.entries.items()}

    def get_result(self):
        return self.result_var.get()

    def get_thi_status(self):
        return self.thi_var.get()

    def get_current_id(self):
        return self.current_id.get()

    def set_current_id(self, value):
        self.current_id.set(value)

    def show_message(self, title, message, type="info"):
        if type == "info":
            messagebox.showinfo(title, message)
        elif type == "warning":
            messagebox.showwarning(title, message)
        elif type == "error":
            messagebox.showerror(title, message)
        elif type == "askyesno":
            return messagebox.askyesno(title, message)

    def clear_form(self, event=None):
        self.current_id.set("")
        for entry in self.entries.values():
            if isinstance(entry, DateEntry):
                if entry == self.entries["Ngày nộp hồ sơ"]:
                    entry.set_date(date.today())
                else:
                    entry.delete(0, "end")
            elif isinstance(entry, ttk.Combobox):
                entry.set(entry["values"][0] if entry["values"] else "")
            else:
                entry.delete(0, tk.END)
        self.result_var.set("Đạt")        # ← Mặc định Đạt
        self.thi_var.set("Phục hồi")
        self.root.after(100, self.update_nam_sinh_from_ngay_nop)

    def reset_search(self):
        self.search_var.set("")
        self.controller.show_data()

    def do_search(self, event=None):
        self.controller.do_search(self.search_var.get().strip())

    def edit_record(self, *args):
        sel = self.tree.selection()
        if sel:
            self.controller.edit_record(sel[0])

    def delete_record_ui(self):
        sel = self.tree.selection()
        if sel:
            self.controller.delete_record_ui(sel[0])

    def export_template(self):
        self.controller.export_template()

    def import_from_excel(self):
        self.controller.import_from_excel()

    def export_to_excel(self):
        self.controller.export_to_excel()

    def update_tree(self, rows):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for r in rows:
            self.tree.insert("", "end", values=r)

    def update_summary(self, summary_data):
        for w in self.summary_frame.winfo_children():
            w.destroy()
        ttk.Label(self.summary_frame, text="TỔNG SỐ HỒ SƠ THEO HẠNG:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", padx=10)
        col = 1
        for hang, count in summary_data.items():
            ttk.Label(self.summary_frame, text=f"{hang}: {count}", font=("Arial", 10, "bold")).grid(row=0, column=col, padx=8)
            col += 1

    def update_stats(self, stats_data):
        for w in self.stats_frame.winfo_children():
            w.destroy()
        labels = [f"Tổng: {stats_data['total']}", f"Đạt: {stats_data['dat']}", f"Trượt: {stats_data['truot']}", f"Tỷ lệ đạt: {stats_data['ty_le']:.1f}%"]
        for i, text in enumerate(labels):
            ttk.Label(self.stats_frame, text=text, font=("Arial", 10, "bold"), foreground="blue").grid(row=0, column=i, padx=15)
    
    def duplicate_record(self):
        """Click nút → copy dữ liệu dòng đang chọn → điền vào form để tạo hồ sơ mới"""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn 1 hồ sơ trong bảng để copy!")
            return
        
        item = self.tree.item(sel[0])
        values = item["values"]

        # Clear form trước
        self.clear_form()

        try:
            from datetime import datetime

            # Điền dữ liệu cũ vào form
            self.entries["Họ tên người nộp"].insert(0, values[1])
            self.entries["Ngày sinh"].set_date(datetime.strptime(values[2], "%d/%m/%Y"))
            self.entries["CCCD"].insert(0, values[3])
            self.entries["Hạng đào tạo"].set(values[4])
            self.entries["CSĐT"].insert(0, values[5])
            self.entries["Ngày nộp hồ sơ"].set_date(datetime.strptime(values[6], "%d/%m/%Y"))
            self.entries["Hạng SH"].set(values[7])
            self.entries["Tiếp nhận phần mềm"].insert(0, values[8])
            self.entries["Ngày SH"].set_date(datetime.strptime(values[9], "%d/%m/%Y"))
            self.entries["Trung tâm sát hạch"].insert(0, values[10])
            self.entries["Nội dung sát hạch"].set(values[11])
            
            # Kết quả sát hạch (dùng Combobox mới)
            self.result_var.set(values[12])
            
            self.entries["Ghi chú"].insert(0, values[13])
            self.thi_var.set(values[14])  # Trạng thái thi

            # Bắt buộc để tạo bản ghi MỚI
            self.current_id.set("")

            messagebox.showinfo(
                "THÀNH CÔNG!", 
                "Đã copy toàn bộ dữ liệu hồ sơ cũ vào form!\n"
                "Bạn chỉ cần sửa lại các thông tin cần thiết rồi nhấn LƯU HỒ SƠ là xong!"
            )

        except Exception as e:
            messagebox.showerror("Lỗi copy", f"Chi tiết lỗi:\n{e}")

    def run(self):
        self.root.mainloop()