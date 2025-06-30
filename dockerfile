FROM python:3.9

WORKDIR /app

RUN pip install numpy==1.26.4

RUN pip install --no-cache-dir torch==2.1.2+cpu torchvision==0.16.2+cpu \
    --extra-index-url https://download.pytorch.org/whl/cpu
RUN apt-get update && apt-get install -y tesseract-ocr
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]