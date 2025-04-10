import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# UI 설정 및 유틸리티 임포트
from ui.ui_utils import log_message

from ui.file_manager import FileSelector

# 전역 변수
source_selector = None
target_selector = None
log_box = None

# 보고서 생성 탭 복구

def create_report_tab(parent):
    """보고서 생성 탭 구성"""
    frame = ttk.Frame(parent, padding=20)
    frame.pack(fill=tk.BOTH, expand=True)

    # 파일 선택 섹션
    ttk.Label(frame, text="Base Template File:").pack(anchor="w", padx=10, pady=5)
    base_template_entry = ttk.Entry(frame, width=50)
    base_template_entry.pack(padx=10, pady=5)
    ttk.Button(frame, text="Browse", command=lambda: browse_file(base_template_entry)).pack(pady=5)

    ttk.Label(frame, text="Review Sheet File:").pack(anchor="w", padx=10, pady=5)
    review_sheet_entry = ttk.Entry(frame, width=50)
    review_sheet_entry.pack(padx=10, pady=5)
    ttk.Button(frame, text="Browse", command=lambda: browse_file(review_sheet_entry)).pack(pady=5)

    # Generate Report Button
    def generate_report():
        base_template = base_template_entry.get()
        review_sheet = review_sheet_entry.get()

        if not base_template or not review_sheet:
            messagebox.showwarning("Missing Files", "Please select both files before generating the report.")
            return

        # 보고서 생성 로직 (플레이스홀더)
        try:
            messagebox.showinfo("Success", "Report generated successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report: {e}")

    ttk.Button(frame, text="Generate Report", command=generate_report).pack(pady=10)

    return frame

# 파일 선택 헬퍼 함수
def browse_file(entry_widget):
    from tkinter.filedialog import askopenfilename
    file_path = askopenfilename()
    if file_path:
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, file_path)

# 확장된 보고서 생성 탭 구성
def create_extended_report_tab(parent, app_context=None):
    """Create the extended report tab UI with improved layout."""
    frame = ttk.Frame(parent)
    frame.pack(fill=tk.BOTH, expand=True)

    # Add a canvas and scrollbar for better layout handling
    canvas = tk.Canvas(frame)
    scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Title
    ttk.Label(scrollable_frame, text="Extended Report Tab", font=("Arial", 14)).pack(pady=10)

    # File Selectors
    ttk.Label(scrollable_frame, text="Source File:").pack(anchor="w", padx=10, pady=5)
    source_selector = FileSelector(scrollable_frame, title="Select Source File")
    source_selector.frame.pack(fill=tk.X, padx=10, pady=5)

    ttk.Label(scrollable_frame, text="Target File:").pack(anchor="w", padx=10, pady=5)
    target_selector = FileSelector(scrollable_frame, title="Select Target File")
    target_selector.frame.pack(fill=tk.X, padx=10, pady=5)

    # Generate Report Button
    def generate_report():
        source_path = source_selector.get_file_path()
        target_path = target_selector.get_file_path()

        if not source_path or not target_path:
            messagebox.showwarning("Missing Files", "Please select both source and target files.")
            return

        try:
            log_message(f"Generating report for {source_path} and {target_path}.", "info")
            messagebox.showinfo("Success", "Report generated successfully!")
        except Exception as e:
            log_message(f"Error generating report: {e}", "error")
            messagebox.showerror("Error", f"Failed to generate report: {e}")

    ttk.Button(scrollable_frame, text="Generate Report", command=generate_report).pack(pady=10)

    # Log Box
    log_frame = ttk.LabelFrame(scrollable_frame, text="Log")
    log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    log_box = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=10, state="disabled")
    log_box.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    log_message("Extended report tab created successfully.", "info")

    return frame