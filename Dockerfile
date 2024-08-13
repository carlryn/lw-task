FROM python:3.10.12

# System deps:
RUN apt-get update \
    && apt-get install curl -y \
    && curl -sSL https://install.python-poetry.org | python - --version 1.7.1

ENV PATH="/root/.local/bin:$PATH"

# Copy only requirements to cache them in docker layer
WORKDIR /workdir
COPY poetry.lock pyproject.toml /workdir/

# install only dependencies:
RUN poetry config virtualenvs.create false && poetry install --no-root --no-interaction --no-ansi

# Creating folders, and files for a project:
COPY . .

# Project initialization:
RUN poetry install --no-interaction --no-ansi

ENTRYPOINT ["fastapi", "run", "lw_task/entrypoint.py", "--workers", "10" ]
