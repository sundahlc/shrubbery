mkdir -p ~/.streamlit/
echo "[general]
email = \"sundahlc@gmail.com\"
" > ~/.streamlit/credentials.toml
echo "[server]
headless = true
enableCORS=false
port = $PORT
" > ~/.streamlit/config.toml
