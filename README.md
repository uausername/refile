# refile
Give your files meaningful names. Renames files with their content description. 

Graphics (jpg, png, etc.) and Text (txt, pdf, docx).

Runs in Docker (https://www.docker.com/)

Run with a comand (on CPU): docker run --rm -v "C:\your\folder\name:/data" -e DATA_DIR="/data" refile-app

GPU Support: docker run --rm --gpus all -v "C:\your\folder\name:/data" -e DATA_DIR="/data" refile-app