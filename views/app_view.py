# views/app_view.py
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import date, datetime

class AppView:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("QUẢN LÝ HỒ SƠ SÁT HẠCH - TRUNG TÂM SÁT HẠCH [TÊN]")
        self.root.geometry("1550x900")
        self.root.configure(bg="#f0f2f5")
        self.root.state('zoomed')  # Mở full màn hình nhưng vẫn đẹp
        self.root.minsize(1400, 800)

        self.entries = {}
        self.result_var = tk.StringVar(value="Đạt")
        self.thi_var = tk.StringVar(value="Phục hồi")
        self.search_var = tk.StringVar()
        self.noidung_search_var = tk.StringVar(value="All")
        self.trangthai_search_var = tk.StringVar(value="All")
        self.current_id = tk.StringVar()

        self._setup_options()
        self._create_main_layout()
        self._setup_bindings()

        self.root.after(100, self.update_nam_sinh_from_ngay_nop)

    def update_nam_sinh_from_ngay_nop(self):
        try:
            ngay_nop_str = self.entries["Ngày nộp hồ sơ"].get()
            if not ngay_nop_str.strip(): return
            ngay_nop = datetime.strptime(ngay_nop_str, "%d/%m/%Y")
            nam_sinh = ngay_nop.year - 18
            self.entries["Ngày sinh"].set_date(f"01/01/{nam_sinh}")
        except: pass

    def _setup_options(self):
        self.labels = [
            "Họ tên người nộp", "Ngày sinh", "CCCD",
            "Hạng đào tạo", "CSĐT", "Ngày nộp hồ sơ",
            "Hạng SH", "Tiếp nhận phần mềm",
            "Ngày SH", "Trung tâm sát hạch",
            "Nội dung sát hạch", "Ghi chú"
        ]
        self.hang_options = ["B.01","B","C1","C","D1","D2","D","BE","C1E","CE",
                             "D1E","D2E","DE","B nâng C","B nâng D1","B nâng D2",
                             "C1 nâng C","C1 nâng D1","C1 nâng D2","C nâng D1",
                             "C nâng D2","C nâng D","C nâng CE"]
        self.noidung_options = [
            "SH lần đầu (L+M+H+Đ)", "SH lại (Đ)", "SH lại (H)", "SH lại (H+Đ)",
            "SH lại (L+M+H+Đ)", "SH lại (L)", "SH lại (L+M)", "SH lại (L+M+H)",
            "SH lại (L+M+Đ)", "SH lại (L+H)", "SH lại (L+H+Đ)", "SH lại (L+Đ)",
            "SH lại (M)", "SH lại (M+H)", "SH lại (M+Đ)", "SH lại (M+H+Đ)"
        ]
        self.required_fields = ["Họ tên người nộp", "Ngày sinh", "CCCD", "Hạng đào tạo", "Hạng SH", "Nội dung sát hạch"]
        self.ketqua_options = ["Đạt", "Trượt M+H+Đ", "Trượt M+Đ", "Trượt H", "Trượt H+Đ", "Trượt Đ"]

    def _create_main_layout(self):
        # ================== KHUNG CHÍNH BAO QUANH 3 PHẦN TRÊN ==================
        main_container = tk.Frame(self.root, bg="#f0f2f5")
        main_container.pack(fill="both", expand=True, padx=15, pady=10)

        main_container.grid_columnconfigure(0, weight=2)   # Thống kê
        main_container.grid_columnconfigure(1, weight=6)   # Form chính
        main_container.grid_columnconfigure(2, weight=2)   # Tìm kiếm
        main_container.grid_rowconfigure(0, weight=1)

        # ================== 1. THỐNG KÊ (BÊN TRÁI) ==================
        left_panel = tk.LabelFrame(main_container, text=" Thống kê & Tổng hợp ", font=("Arial", 12, "bold"),
                                   bg="white", fg="#2c3e50", relief="groove", bd=3)
        left_panel.grid(row=0, column=0, sticky="nswe", padx=(0, 10))

        self.summary_frame = tk.Frame(left_panel, bg="white")
        self.summary_frame.pack(fill="x", padx=15, pady=15)

        self.stats_frame = tk.LabelFrame(left_panel, text=" Thống kê kết quả ", font=("Arial", 11, "bold"),
                                         bg="white", fg="#e74c3c", bd=2)
        self.stats_frame.pack(fill="x", padx=15, pady=10)

        # ================== 2. THÔNG TIN HỒ SƠ (GIỮA) ==================
        center_panel = tk.LabelFrame(main_container, text=" Thông tin Hồ sơ ", font=("Arial", 13, "bold"),
                                     bg="white", fg="#2c3e50", relief="groove", bd=4, padx=25, pady=15)
        center_panel.grid(row=0, column=1, sticky="nswe", padx=8)

        for i, label in enumerate(self.labels):
            row, col = divmod(i, 2)
            lbl_frame = tk.Frame(center_panel, bg="white")
            lbl_frame.grid(row=row, column=col*2, sticky="e", padx=10, pady=8)
            tk.Label(lbl_frame, text=label + ":", font=("Arial", 10, "bold"), bg="white").pack(side="left")
            if label in self.required_fields:
                tk.Label(lbl_frame, text=" *", fg="red", bg="white", font=("Arial", 11, "bold")).pack(side="left")

            if label in ["Ngày nộp hồ sơ", "Ngày SH"]:
                entry = DateEntry(center_panel, width=20, date_pattern="dd/mm/yyyy", maxdate=date.today())
                entry.set_date(date.today())
            elif label == "Ngày sinh":
                entry = DateEntry(center_panel, width=20, date_pattern="dd/mm/yyyy")
                entry.delete(0, "end")
            elif label in ["Hạng đào tạo", "Hạng SH"]:
                entry = ttk.Combobox(center_panel, values=self.hang_options, width=24, state="readonly")
                entry.set(self.hang_options[0])
            elif label == "Nội dung sát hạch":
                entry = ttk.Combobox(center_panel, values=self.noidung_options, width=24, state="readonly")
                entry.set(self.noidung_options[0])
            else:
                entry = tk.Entry(center_panel, width=26, font=("Arial", 10))

            entry.grid(row=row, column=col*2 + 1, padx=10, pady=8, sticky="w")
            self.entries[label] = entry

        # Kết quả + Trạng thái thi
        status_frame = tk.Frame(center_panel, bg="white")
        status_frame.grid(row=len(self.labels)//2 + 1, column=0, columnspan=4, pady=25, sticky="ew")

        tk.Label(status_frame, text="Kết quả sát hạch:", font=("Arial", 10, "bold"), bg="white").grid(row=0, column=0, padx=20, sticky="e")
        self.ketqua_cb = ttk.Combobox(status_frame, textvariable=self.result_var, values=self.ketqua_options, width=20, state="readonly")
        self.ketqua_cb.grid(row=0, column=1, padx=10)
        self.ketqua_cb.set("Đạt")

        tk.Label(status_frame, text="Trạng thái thi:", font=("Arial", 10, "bold"), bg="white").grid(row=0, column=2, padx=(50,10))
        tk.Radiobutton(status_frame, text="Thi mới", variable=self.thi_var, value="Thi mới", bg="white").grid(row=0, column=3, padx=5)
        tk.Radiobutton(status_frame, text="Phục hồi", variable=self.thi_var, value="Phục hồi", bg="white").grid(row=0, column=4)

        # ================== 3. TÌM KIẾM & LỌC (BÊN PHẢI) ==================
        right_panel = tk.LabelFrame(main_container, text=" Tìm kiếm & Lọc dữ liệu ", font=("Arial", 12, "bold"),
                                    bg="white", fg="#2c3e50", relief="groove", bd=3, padx=20, pady=20)
        right_panel.grid(row=0, column=2, sticky="nswe", padx=(10, 0))

        tk.Label(right_panel, text="Tìm kiếm (Tên/CCCD):", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0,8))
        tk.Entry(right_panel, textvariable=self.search_var, width=35, font=("Arial", 11)).pack(pady=5, fill="x")

        tk.Label(right_panel, text="Nội dung sát hạch:", font=("Arial", 10, "bold"), bg="white").pack(anchor="w", pady=(20,5))
        ttk.Combobox(right_panel, textvariable=self.noidung_search_var,
                     values=["All"] + self.noidung_options, width=38, state="readonly").pack(pady=5, fill="x")

        tk.Label(right_panel, text="Trạng thái thi:", font=("Arial", 10, "bold"), bg="white").pack(anchor="w", pady=(20,5))
        ttk.Combobox(right_panel, textvariable=self.trangthai_search_var,
                     values=["All", "Thi mới", "Phục hồi"], width=20, state="readonly").pack(pady=5, fill="x")

        btn_search_frame = tk.Frame(right_panel, bg="white")
        btn_search_frame.pack(pady=25)
        ttk.Button(btn_search_frame, text="TÌM KIẾM NGAY", width=16, command=self.trigger_search).pack(pady=6)
        ttk.Button(btn_search_frame, text="HIỂN THỊ TẤT CẢ", width=16, command=self.reset_search).pack(pady=6)

        # ================== KHUNG NÚT BẤM RIÊNG ==================
        button_container = tk.Frame(self.root, bg="#3498db", relief="raised", bd=2)
        button_container.pack(fill="x", pady=8, padx=15)

        btn_left = tk.Frame(button_container, bg="#3498db")
        btn_left.pack(side="left", padx=20, pady=8)

        self.btn_save = ttk.Button(btn_left, text="Lưu hồ sơ", width=16)
        self.btn_save.pack(side="left", padx=5)
        self.btn_edit = ttk.Button(btn_left, text="Sửa hồ sơ", width=16)
        self.btn_edit.pack(side="left", padx=5)
        self.btn_del_soft = ttk.Button(btn_left, text="Xóa hồ sơ", width=16)
        self.btn_del_soft.pack(side="left", padx=5)
        self.btn_duplicate = ttk.Button(btn_left, text="Thêm mới từ hồ sơ cũ", width=26)
        self.btn_duplicate.pack(side="left", padx=15)
        ttk.Button(btn_left, text="Hủy nhập", command=self.clear_form, width=14).pack(side="left", padx=5)

        btn_right = tk.Frame(button_container, bg="#3498db")
        btn_right.pack(side="right", padx=20, pady=8)
        self.btn_export = ttk.Button(btn_right, text="Xuất Excel", width=16)
        self.btn_export.pack(side="right", padx=5)
        self.btn_import = ttk.Button(btn_right, text="Nhập Excel", width=16)
        self.btn_import.pack(side="right", padx=5)
        self.btn_template = ttk.Button(btn_right, text="Tải mẫu Excel", width=16)
        self.btn_template.pack(side="right", padx=5)

        # ================== DANH SÁCH HỒ SƠ (CHIẾM TOÀN BỘ PHẦN DƯỚI) ==================
        table_frame = tk.LabelFrame(self.root, text=" Danh sách hồ sơ sát hạch ", font=("Arial", 13, "bold"),
                                    bg="white", fg="#2c3e50", bd=4, padx=10, pady=10)
        table_frame.pack(fill="both", expand=True, padx=15, pady=(0,15))

        cols = ["ID", "Họ tên", "Ngày sinh", "CCCD", "Hạng ĐT", "CSĐT", "Ngày nộp",
                "Hạng SH", "Tiếp nhận", "Ngày SH", "Trung tâm", "Nội dung",
                "Kết quả", "Ghi chú", "Trạng thái thi"]

        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        self.tree.column("ID", width=0, stretch=False)
        self.tree["displaycolumns"] = cols[1:]

        for col in cols[1:]:
            self.tree.heading(col, text=col)
            w = 180 if col in ["Họ tên", "CCCD", "Trung tâm", "Nội dung", "Ghi chú"] else 120
            a = "w" if col in ["Họ tên", "CCCD", "Trung tâm", "Nội dung", "Ghi chú"] else "center"
            self.tree.column(col, width=w, anchor=a)

        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview.Heading", background="#34495e", foreground="white", font=("Arial", 10, "bold"))
        style.configure("Treeview", rowheight=30, font=("Arial", 10))

    # ================== CÁC HÀM KHÁC (GIỮ NGUYÊN) ==================
    def trigger_search(self):
        search_text = self.search_var.get().strip()
        noidung = self.noidung_search_var.get() if self.noidung_search_var.get() != "All" else None
        trangthai = self.trangthai_search_var.get() if self.trangthai_search_var.get() != "All" else None
        self.controller.advanced_search(search_text, noidung, trangthai)

    def reset_search(self):
        self.search_var.set("")
        self.noidung_search_var.set("All")
        self.trangthai_search_var.set("All")
        self.controller.show_data()

    def duplicate_record(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn 1 hồ sơ trong bảng để copy!")
            return
        values = self.tree.item(sel[0], "values")
        self.clear_form()
        try:
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
            self.result_var.set(values[12])
            self.entries["Ghi chú"].insert(0, values[13])
            self.thi_var.set(values[14])
            self.current_id.set("")
            messagebox.showinfo("THÀNH CÔNG!", "Đã copy dữ liệu cũ!\nChỉ cần sửa ngày → nhấn Lưu là xong!")
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def set_controller(self, controller):
        self.controller = controller
        self.setup_controller_commands()

    def setup_controller_commands(self):
        self.btn_save.config(command=self.controller.save_record)
        self.btn_edit.config(command=lambda: self.edit_record())
        self.btn_del_soft.config(command=lambda: self.delete_record_ui())
        self.btn_duplicate.config(command=self.duplicate_record)
        self.btn_template.config(command=self.controller.export_template)
        self.btn_import.config(command=self.controller.import_from_excel)
        self.btn_export.config(command=self.controller.export_to_excel)

    def _setup_bindings(self):
        self.entries["Hạng đào tạo"].bind("<<ComboboxSelected>>", self.on_hang_dt_change)
        self.entries["Ngày nộp hồ sơ"].bind("<<DateEntrySelected>>", lambda e: self.root.after(100, self.update_nam_sinh_from_ngay_nop))
        self.search_var.trace("w", lambda *_: self.trigger_search())
        self.noidung_search_var.trace("w", lambda *_: self.trigger_search())
        self.trangthai_search_var.trace("w", lambda *_: self.trigger_search())
        self.tree.bind("<Double-1>", self.edit_record)
        self.root.bind("<Control-s>", lambda e: self.controller.save_record())
        self.root.bind("<Escape>", lambda e: self.clear_form())

    def on_hang_dt_change(self, event):
        hang_dt = self.entries["Hạng đào tạo"].get()
        hang_sh = self.entries["Hạng SH"]
        if not hang_sh.get() or hang_sh.get() == getattr(event.widget, "_last", ""):
            hang_sh.set(hang_dt)
        event.widget._last = hang_dt

    def get_data(self): return {k: v.get().strip() for k, v in self.entries.items()}
    def get_result(self): return self.result_var.get()
    def get_thi_status(self): return self.thi_var.get()
    def get_current_id(self): return self.current_id.get()
    def set_current_id(self, value): self.current_id.set(value)

    def show_message(self, title, message, type="info"):
        {"info": messagebox.showinfo, "warning": messagebox.showwarning,
         "error": messagebox.showerror, "askyesno": messagebox.askyesno}[type](title, message)

    def clear_form(self, event=None):
        self.current_id.set("")
        for entry in self.entries.values():
            if isinstance(entry, DateEntry):
                entry.set_date(date.today()) if "Ngày nộp" in entry.winfo_name() else entry.delete(0, "end")
            elif isinstance(entry, ttk.Combobox):
                entry.set(entry["values"][0] if entry["values"] else "")
            else:
                entry.delete(0, "end")
        self.result_var.set("Đạt")
        self.thi_var.set("Phục hồi")
        self.root.after(100, self.update_nam_sinh_from_ngay_nop)

    def edit_record(self, *args):
        sel = self.tree.selection()
        if not sel:
            return
        item = sel[0]                     # ← lấy phần tử đầu tiên của tuple
        self.controller.edit_record(item)   # ← truyền thẳng iid (là id thật)

    def delete_record_ui(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn 1 hồ sơ để xóa!")
            return
        item = sel[0]                     # ← lấy iid thật
        self.controller.delete_record_ui(item)

    def update_tree(self, rows):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for r in rows:
            self.tree.insert("", "end", iid=str(r[0]), values=r[1:])

    def update_summary(self, data):
        for w in self.summary_frame.winfo_children(): w.destroy()
        tk.Label(self.summary_frame, text="TỔNG SỐ HỒ SƠ THEO HẠNG:", font=("Arial", 10, "bold"), bg="white", fg="#2c3e50").pack(anchor="w", padx=10, pady=8)
        frame = tk.Frame(self.summary_frame, bg="white")
        frame.pack(fill="x", pady=5)
        col = 0
        for hang, count in data.items():
            tk.Label(frame, text=f"{hang}: {count}", font=("Arial", 10, "bold"), bg="#ecf0f1", padx=15, pady=8, relief="solid").grid(row=0, column=col, padx=5)
            col += 1

    def update_stats(self, data):
        # Xóa hết nội dung cũ
        for w in self.stats_frame.winfo_children():
            w.destroy()

        # Danh sách thống kê
        stats = [
            ("TỔNG HỒ SƠ", data['total'], "#34495e"),
            ("ĐẠT", data['dat'], "#27ae60"),
            ("TRƯỢT", data['truot'], "#e74c3c"),
            ("TỶ LỆ ĐẠT", f"{data['ty_le']:.1f}%", "#3498db")
        ]

        # Hiển thị theo chiều dọc (mỗi dòng 1 label đẹp)
        for i, (label_text, value, color) in enumerate(stats):
            # Frame bao mỗi dòng để dễ căn chỉnh
            row_frame = tk.Frame(self.stats_frame, bg="white")
            row_frame.pack(fill="x", padx=10, pady=6)

            # Nhãn tiêu đề (Tổng, Đạt, Trượt...)
            tk.Label(
                row_frame,
                text=label_text,
                font=("Arial", 10, "bold"),
                bg="white",
                fg="#2c3e50",
                width=15,
                anchor="w"
            ).pack(side="left")

            # Giá trị (số liệu lớn, đậm, nổi bật)
            tk.Label(
                row_frame,
                text=value,
                font=("Arial", 10, "bold"),
                bg=color,
                fg="white",
                padx=12,
                # pady=8,
                relief="raised",
                bd=2
            ).pack(side="right")

    def run(self):
        self.root.mainloop()