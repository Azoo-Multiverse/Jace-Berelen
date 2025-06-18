import os
import shutil
import stat
from pathlib import Path
from typing import Union, List

class FileOps:
    @staticmethod
    def safe_copy(src: Union[str, Path], dst: Union[str, Path]) -> None:
        src_path = Path(src)
        dst_path = Path(dst)
        
        if not src_path.exists():
            raise FileNotFoundError(f"Source {src} does not exist")
            
        if src_path.is_file():
            os.makedirs(dst_path.parent, exist_ok=True)
            shutil.copy2(src_path, dst_path)
        else:
            shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
            
    @staticmethod
    def safe_move(src: Union[str, Path], dst: Union[str, Path]) -> None:
        src_path = Path(src)
        dst_path = Path(dst)
        
        if not src_path.exists():
            raise FileNotFoundError(f"Source {src} does not exist")
            
        os.makedirs(dst_path.parent, exist_ok=True)
        shutil.move(str(src_path), str(dst_path))
        
    @staticmethod
    def safe_delete(path: Union[str, Path]) -> None:
        path = Path(path)
        if not path.exists():
            return
            
        if path.is_file():
            os.chmod(path, stat.S_IWRITE)
            os.remove(path)
        else:
            for item in path.rglob("*"):
                if item.is_file():
                    os.chmod(item, stat.S_IWRITE)
            shutil.rmtree(path)
            
    @staticmethod
    def create_dirs(path: Union[str, Path]) -> None:
        os.makedirs(Path(path), exist_ok=True)
        
    @staticmethod
    def safe_read(file_path: Union[str, Path]) -> str:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
            
    @staticmethod
    def safe_write(file_path: Union[str, Path], content: str) -> None:
        path = Path(file_path)
        os.makedirs(path.parent, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
            
    @staticmethod
    def list_files(directory: Union[str, Path], pattern: str = "*") -> List[Path]:
        return list(Path(directory).rglob(pattern))
        
    @staticmethod
    def ensure_permissions(path: Union[str, Path], mode: int = 0o755) -> None:
        path = Path(path)
        if path.exists():
            os.chmod(path, mode)
