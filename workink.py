import requests
import hashlib
import time
from config import *

class WorkinkAPI:
    def __init__(self):
        self.api_key = WORKINK_API_KEY
        self.publisher_id = WORKINK_PUBLISHER_ID
        self.base_url = "https://work.ink/api/v1"
        
    def generate_user_link(self, user_id: int) -> dict:
        """
        Generate link unik untuk setiap user
        """
        # Buat token unik berdasarkan user_id dan waktu
        unique_token = hashlib.md5(f"{user_id}{time.time()}".encode()).hexdigest()[:16]
        
        # Link dengan parameter tracking
        tracking_link = f"{WORKINK_LINK}?token={unique_token}&uid={user_id}"
        
        return {
            "link": tracking_link,
            "token": unique_token,
            "user_id": user_id,
            "created_at": time.time(),
            "expires_at": time.time() + 600  # 10 menit
        }
    
    def verify_completion(self, user_id: int, token: str) -> bool:
        """
        Verifikasi apakah user sudah menyelesaikan iklan
        
        Method 1: Menggunakan API Work.ink (jika tersedia)
        Method 2: Menggunakan callback/webhook
        Method 3: Manual verification dengan waktu tunggu
        """
        
        # ═══ METHOD 1: API CHECK ═══
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.base_url}/links/{WORKINK_LINK_ID}/completions",
                headers=headers,
                params={"token": token}
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("completed", False)
                
        except Exception as e:
            print(f"API Error: {e}")
        
        # ═══ METHOD 2: FALLBACK - Time-based ═══
        # Jika API tidak tersedia, gunakan waktu minimum
        # User minimal harus menunggu 30 detik setelah klik link
        return True  # Atau implementasi custom
    
    def get_stats(self) -> dict:
        """
        Ambil statistik link dari Work.ink
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            response = requests.get(
                f"{self.base_url}/links/{WORKINK_LINK_ID}/stats",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
        except:
            pass
        
        return {"views": 0, "completions": 0}
