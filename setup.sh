mkdir -p ~/.streamlit

bash -c 'echo -e "\
[general]\n\
email = \"\"\n\
" > ~/.streamlit/credentials.toml'

bash -c 'echo -e "\
[server]\n\
enableCORS = false\n\
" > ~/.streamlit/config.toml'

# pb
gdown --id 19WcWF8N7Cvl4Z0bndOKLccG_6egmUKc6 -O checkpoints/weights/frozen_inference_graph.pb
# pbtxt
gdown --id 1JdezAXYExJcsqv8xlwvgAe3jUQAYyE54 -O checkpoints/weights/rust_label_map.pbtxt