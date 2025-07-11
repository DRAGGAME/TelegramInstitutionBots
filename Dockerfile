FROM continuumio/miniconda3:latest

LABEL main='Draggame'

WORKDIR /app

COPY . /app

RUN conda update -n base -c defaults conda \
    && conda env create -f /app/telegrambot.yml  \
    && echo "conda activate telegramBotsClient" > ~/.bashrc  \
    && conda clean -afy

ENV PATH="/opt/conda/envs/telegramBotsClient/bin:$PATH"

EXPOSE 5432

CMD ["python", "run.py"]
