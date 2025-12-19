import json
import requests
import base64
import time
from config import *

class Database:
    def __init__(self):
        self.github_api = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.file_path = "keys.json"
        self.data = self.load()
    
    def load(self) -> dict:
        """Load database dari GitHub"""
        try:
            url = f"{self.github_api}/repos/{GITHUB_REPO}/contents/{self.file_path}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                content = response.json()
                decoded = base64.b64decode(content["content"]).decode()
                self.sha = content["sha"]
                return json.loads(decoded)
            else:
                # File belum ada, buat baru
                self.sha = None
                return {"keys": {}, "users": {}, "pending": {}}
        except Exception as e:
            print(f"Load error: {e}")
            self.sha = None
            return {"keys": {}, "users": {}, "pending": {}}
    
    def save(self):
        """Simpan database ke GitHub"""
        try:
            url = f"{self.github_api}/repos/{GITHUB_REPO}/contents/{self.file_path}"
            
            content = base64.b64encode(json.dumps(self.data, indent=2).encode()).decode()
            
            payload = {
                "message": f"Update keys database - {time.strftime('%Y-%m-%d %H:%M:%S')}",
                "content": content,
                "branch": GITHUB_BRANCH
            }
            
            if self.sha:
                payload["sha"] = self.sha
            
            response = requests.put(url, headers=self.headers, json=payload)
            
            if response.status_code in [200, 201]:
                self.sha = response.json()["content"]["sha"]
                return True
            else:
                print(f"Save error: {response.text}")
                return False
        except Exception as e:
            print(f"Save exception: {e}")
            return False
    
    # ═══════════════════════════════════════
    # KEY OPERATIONS
    # ═══════════════════════════════════════
    def add_key(self, key: str, user_id: int, is_admin: bool = False):
        """Tambah key baru"""
        self.data["keys"][key] = {
            "user_id": user_id,
            "created_at": time.time(),
            "expires_at": time.time() + KEY_DURATION,
            "is_admin": is_admin,
            "used": False
        }
        self.save()
    
    def validate_key(self, key: str) -> dict:
        """Validasi key"""
        if key not in self.data["keys"]:
            return {"valid": False, "reason": "Key tidak ditemukan"}
        
        key_data = self.data["keys"][key]
        
        if time.time() > key_data["expires_at"]:
            return {"valid": False, "reason": "Key sudah expired"}
        
        remaining = key_data["expires_at"] - time.time()
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        
        return {
            "valid": True,
            "remaining": f"{hours}h {minutes}m",
            "user_id": key_data["user_id"]
        }
    
    def get_user_keys(self, user_id: int) -> list:
        """Ambil semua key milik user"""
        user_keys = []
        for key, data in self.data["keys"].items():
            if data["user_id"] == user_id:
                user_keys.append({"key": key, **data})
        return user_keys
    
    # ═══════════════════════════════════════
    # PENDING VERIFICATION
    # ═══════════════════════════════════════
    def add_pending(self, user_id: int, token: str, link: str):
        """Tambah user ke pending verification"""
        self.data["pending"][str(user_id)] = {
            "token": token,
            "link": link,
            "created_at": time.time(),
            "expires_at": time.time() + 600  # 10 menit
        }
        self.save()
    
    def get_pending(self, user_id: int) -> dict:
        """Ambil data pending user"""
        return self.data["pending"].get(str(user_id))
    
    def remove_pending(self, user_id: int):
        """Hapus pending setelah verifikasi"""
        if str(user_id) in self.data["pending"]:
            del self.data["pending"][str(user_id)]
            self.save()
    
    # ═══════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════
    def get_stats(self) -> dict:
        """Statistik keseluruhan"""
        total_keys = len(self.data["keys"])
        active_keys = sum(1 for k, v in self.data["keys"].items() 
                        if time.time() < v["expires_at"])
        expired_keys = total_keys - active_keys
        
        return {
            "total_keys": total_keys,
            "active_keys": active_keys,
            "expired_keys": expired_keys,
            "pending_users": len(self.data["pending"])
        }
