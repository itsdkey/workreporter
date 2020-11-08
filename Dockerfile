FROM python:3.9.0-slim

WORKDIR /workreporter

# extra dependencies (over what python-slim deps already includes)
RUN apt-get update && apt-get install -y --no-install-recommends \
                gcc \
                libc-dev \
	&& rm -rf /var/lib/apt/lists/*

COPY . /workreporter

RUN pip install -r requirements.txt && rm requirements.txt

CMD ["python3.9", "-u", "app.py", "--port=8888"]
