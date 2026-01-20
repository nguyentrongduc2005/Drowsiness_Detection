#!/usr/bin/env python3
"""
Cleanup Script - Tối ưu workspace Drowsiness Detection
Xóa file thừa, cache, và logs cũ
"""
import os
import shutil
from pathlib import Path
from datetime import datetime

class WorkspaceCleanup:
    def __init__(self, workspace_root="."):
        self.root = Path(workspace_root).resolve()
        self.deleted_files = []
        self.deleted_dirs = []
        self.freed_space = 0
        
    def get_file_size(self, path):
        """Tính kích thước file/folder (bytes)"""
        if path.is_file():
            return path.stat().st_size
        elif path.is_dir():
            return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
        return 0
    
    def clean_pycache(self):
        """Xóa tất cả __pycache__ folders"""
        print("\n[1] Cleaning __pycache__ folders...")
        pycache_dirs = list(self.root.rglob('__pycache__'))
        
        for pycache in pycache_dirs:
            size = self.get_file_size(pycache)
            try:
                shutil.rmtree(pycache)
                self.deleted_dirs.append(str(pycache.relative_to(self.root)))
                self.freed_space += size
                print(f"  ✓ Deleted: {pycache.relative_to(self.root)} ({size/1024:.1f} KB)")
            except Exception as e:
                print(f"  ✗ Error deleting {pycache}: {e}")
        
        if not pycache_dirs:
            print("  • No __pycache__ found")
    
    def clean_old_logs(self, keep_latest=3):
        """Xóa log files cũ, giữ lại N files mới nhất"""
        print(f"\n[2] Cleaning old log files (keep latest {keep_latest})...")
        logs_dir = self.root / 'logs'
        
        if not logs_dir.exists():
            print("  • Logs directory not found")
            return
        
        # Lấy tất cả CSV logs
        csv_logs = sorted(logs_dir.glob('drowsiness_log_*.csv'), 
                         key=lambda x: x.stat().st_mtime, 
                         reverse=True)
        
        # Xóa logs cũ
        deleted_count = 0
        for log_file in csv_logs[keep_latest:]:
            size = self.get_file_size(log_file)
            try:
                log_file.unlink()
                self.deleted_files.append(str(log_file.relative_to(self.root)))
                self.freed_space += size
                deleted_count += 1
            except Exception as e:
                print(f"  ✗ Error deleting {log_file.name}: {e}")
        
        if deleted_count > 0:
            print(f"  ✓ Deleted {deleted_count} old log files")
        
        # Xóa alerts.txt (duplicate logging)
        alerts_file = logs_dir / 'alerts.txt'
        if alerts_file.exists():
            size = self.get_file_size(alerts_file)
            try:
                alerts_file.unlink()
                self.deleted_files.append(str(alerts_file.relative_to(self.root)))
                self.freed_space += size
                print(f"  ✓ Deleted: alerts.txt ({size/1024:.1f} KB)")
            except Exception as e:
                print(f"  ✗ Error deleting alerts.txt: {e}")
        
        if keep_latest > 0 and csv_logs:
            print(f"\n  • Kept {min(keep_latest, len(csv_logs))} latest logs:")
            for log in csv_logs[:keep_latest]:
                print(f"    - {log.name}")
    
    def clean_lib_folder(self):
        """Xóa thư mục lib/ (chứa dlib wheel không dùng)"""
        print("\n[3] Cleaning lib/ folder (unused dlib)...")
        lib_dir = self.root / 'lib'
        
        if lib_dir.exists():
            size = self.get_file_size(lib_dir)
            try:
                shutil.rmtree(lib_dir)
                self.deleted_dirs.append(str(lib_dir.relative_to(self.root)))
                self.freed_space += size
                print(f"  ✓ Deleted: lib/ ({size/1024/1024:.1f} MB)")
            except Exception as e:
                print(f"  ✗ Error deleting lib/: {e}")
        else:
            print("  • lib/ folder not found")
    
    def clean_pyc_files(self):
        """Xóa compiled Python files (.pyc, .pyo)"""
        print("\n[4] Cleaning compiled Python files...")
        pyc_files = list(self.root.rglob('*.pyc')) + list(self.root.rglob('*.pyo'))
        
        for pyc in pyc_files:
            size = self.get_file_size(pyc)
            try:
                pyc.unlink()
                self.deleted_files.append(str(pyc.relative_to(self.root)))
                self.freed_space += size
            except Exception as e:
                print(f"  ✗ Error deleting {pyc.name}: {e}")
        
        if pyc_files:
            print(f"  ✓ Deleted {len(pyc_files)} .pyc/.pyo files")
        else:
            print("  • No .pyc/.pyo files found")
    
    def create_gitignore(self):
        """Tạo .gitignore file"""
        print("\n[5] Creating .gitignore...")
        gitignore_path = self.root / '.gitignore'
        
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
*.egg
*.egg-info/
dist/
build/

# Logs
logs/*.csv
logs/*.txt

# Data files (models and audio)
data/*.dat
data/*.wav
data/profiles/

# IDE
.vscode/
.idea/
*.swp
*.swo
*.sublime-*

# OS
.DS_Store
Thumbs.db
Desktop.ini

# Virtual environment
venv/
env/
ENV/

# Jupyter Notebook
.ipynb_checkpoints

# PyInstaller
*.manifest
*.spec

# pytest
.pytest_cache/
.coverage
htmlcov/
"""
        
        try:
            with open(gitignore_path, 'w', encoding='utf-8') as f:
                f.write(gitignore_content)
            print(f"  ✓ Created: .gitignore")
        except Exception as e:
            print(f"  ✗ Error creating .gitignore: {e}")
    
    def print_summary(self):
        """In tổng kết"""
        print("\n" + "="*60)
        print("CLEANUP SUMMARY")
        print("="*60)
        print(f"Files deleted: {len(self.deleted_files)}")
        print(f"Directories deleted: {len(self.deleted_dirs)}")
        print(f"Space freed: {self.freed_space/1024/1024:.2f} MB")
        
        if self.deleted_dirs:
            print(f"\nDeleted directories:")
            for d in self.deleted_dirs:
                print(f"  - {d}")
        
        print("\n✓ Cleanup completed!")
    
    def run(self, keep_logs=3, auto_confirm=False):
        """Chạy toàn bộ cleanup process"""
        print("="*60)
        print("DROWSINESS DETECTION - WORKSPACE CLEANUP")
        print("="*60)
        print(f"Root: {self.root}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Xác nhận
        print("\nThis will:")
        print("  - Delete all __pycache__ folders")
        print(f"  - Keep only {keep_logs} latest log files")
        print("  - Delete lib/ folder (unused dlib)")
        print("  - Delete .pyc/.pyo files")
        print("  - Create .gitignore")
        
        if not auto_confirm:
            confirm = input("\nContinue? (y/n): ").strip().lower()
            if confirm != 'y':
                print("Cleanup cancelled.")
                return
        
        # Thực hiện cleanup
        self.clean_pycache()
        self.clean_old_logs(keep_latest=keep_logs)
        self.clean_lib_folder()
        self.clean_pyc_files()
        self.create_gitignore()
        
        # Tổng kết
        self.print_summary()


if __name__ == "__main__":
    import sys
    
    # Khởi động cleanup
    cleaner = WorkspaceCleanup()
    
    # Check if running with --auto flag
    auto = '--auto' in sys.argv or '-y' in sys.argv
    
    cleaner.run(keep_logs=3, auto_confirm=auto)
