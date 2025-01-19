FROM continuumio/miniconda3:latest

WORKDIR /app

COPY telegrambot.yml .

RUN conda env create -f telegrambot.yml
# RUN conda activate telegramBots

COPY . .

CMD ["python", "check_sys.py"]