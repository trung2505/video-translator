FROM python:3.12-slim
WORKDIR /app

# Install ffmpeg and dependencies
RUN apt-get update && apt-get install -y \
	ffmpeg \
	gcc \
	g++ \
	make \
	pkg-config \
	libpq-dev \
	libgl1 \
	libglib2.0-0 \
	libavcodec-dev \
	libavformat-dev \
	libswscale-dev \
	libavdevice-dev \
	libavfilter-dev \
	libswresample-dev \
	libavutil-dev \
	&& rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

RUN apt-get update && apt-get install -y postgresql-client \
	&& rm -rf /var/lib/apt/lists/*

COPY . /app
ENV PYTHONPATH=/app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
