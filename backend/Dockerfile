# Gunakan image resmi Python 3.10 slim
FROM python:3.10-slim

# Tentukan direktori kerja di dalam container
WORKDIR /app

# Set env variables untuk mencegah penulisan file bytecode .pyc dan buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Optimasi RAM: Batasi jumlah thread CPU yang digunakan oleh PyTorch/Numpy
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV OPENBLAS_NUM_THREADS=1
ENV VECLIB_MAXIMUM_THREADS=1
ENV NUMEXPR_NUM_THREADS=1

# Instal dependensi sistem yang dibutuhkan oleh OpenCV, PyTorch, dan pylibjpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libglib2.0-0 \
    libgomp1 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*
    
# Salin file requirements.txt dan instal dependensi Python
COPY requirement.txt .
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirement.txt

# Salin semua kode sumber backend ke dalam container
COPY . .

# Ekspos port 5003 (sesuai port Flask yang diinginkan di VPS)
EXPOSE 5003

# Jalankan server produksi Gunicorn binding ke port 5003
# Optimasi RAM: Menggunakan hanya 1 worker agar model YOLOv8n-cls hanya dimuat 1 kali di memori
CMD ["gunicorn", "--bind", "0.0.0.0:5003", "--workers", "1", "--threads", "2", "--timeout", "120", "app:create_app()"]
