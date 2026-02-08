# 使用極輕量的 Alpine Linux
FROM python:3.9-alpine

# 建立非 root 用戶 (安全性關鍵)
RUN adduser -D sandbox_user
WORKDIR /home/sandbox_user

# 安裝基本處理工具 (例如把文字檔轉大寫，模擬清洗過程)
# 在真實場景會安裝 pandoc 或 imagemagick
COPY process_file.py .

# 切換到受限用戶
USER sandbox_user

# 設定進入點
ENTRYPOINT ["python", "process_file.py"]
