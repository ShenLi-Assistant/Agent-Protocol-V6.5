import sys

def sanitize():
    try:
        # 讀取輸入檔案 (從掛載點)
        with open("/input/file.txt", "r") as f:
            content = f.read()
        
        # 模擬清洗：只保留英數字，移除所有潛在代碼符號
        safe_content = "".join(c for c in content if c.isalnum() or c.isspace())
        
        # 寫入輸出
        with open("/output/clean.txt", "w") as f:
            f.write(f"[SANITIZED BY SANDBOX] {safe_content}")
            
        print("Success")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    sanitize()
