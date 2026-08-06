FROM python:3.12.7-slim-bookworm

RUN pip install numpy==2.1.3 \
                scipy==1.1.4.1 \
                pandas==2.2.3 \
                PyYAML==6.0.2

WORKDIR /app
COPY data/ /app/data/
RUN mkdir -p /app/output

CMD ["/bin/bash"]
