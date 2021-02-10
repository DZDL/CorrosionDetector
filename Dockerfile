# Download base image ubuntu 18.04
FROM ubuntu:18.04

# streamlit-specific commands for config
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
RUN mkdir -p ~/.streamlit

RUN bash -c 'echo -e "\
[general]\n\
email = \"\"\n\
" > ~/.streamlit/credentials.toml'

RUN bash -c 'echo -e "\
[server]\n\
enableCORS = false\n\
" > ~/.streamlit/config.toml'

# install Python and Pip
# NOTE: libSM.so.6 is required for OpenCV Docker
# or you will get seg fault when import OpenCV
# error libGL.so.1
RUN apt-get update && \
    apt-get install -y \
    python3.7 python3-pip \
    ffmpeg libsm6 libxext6 libxrender-dev libgl1-mesa-dev

# expose port 8501 for streamlit
EXPOSE 8501

# make app directiry
WORKDIR /streamlit-docker

# upgrade for new versions of opencv
RUN pip3 install --upgrade pip

# copy requirements.txt
COPY requirements.txt ./requirements.txt

# install dependencies
RUN pip3 install -r requirements.txt

# copy all files over
COPY . .

# download weights
RUN gdown --id 19WcWF8N7Cvl4Z0bndOKLccG_6egmUKc6 -O checkpoints/weights/frozen_inference_graph.pb
RUN gdown --id 1JdezAXYExJcsqv8xlwvgAe3jUQAYyE54 -O checkpoints/weights/rust_label_map.pbtxt

# launch streamlit app --server.enableCORS false
CMD streamlit run --server.port $PORT app.py