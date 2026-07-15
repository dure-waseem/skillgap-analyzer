# Smaller image due to using slim version of python image.
FROM python:3.13-slim

# Does 2 things:
# 1. Creates the folder if it doesn't exist (same as mkdir -p)
# 2. Also switches the "current directory" for every instruction that comes after it COPY, RUN, CMD, etc
WORKDIR /app  

# Install uv (the package manager) so we can use it to install the dependencies from pyproject.toml and uv.lock
RUN pip install uv

# pyproject.toml = the plan (I need this (eg. crewai) and this)
# uv.lock = the precise plan (I need this exact version of this and this exact version of that)
COPY pyproject.toml uv.lock ./

# do the action → this line CREATES .venv
RUN uv sync --frozen --no-dev

#copy everythin from the directory to the current directory in the container 
COPY . ./

# create both output/ and uploads/ folders if they don't exist (mkdir -p)
RUN mkdir -p output uploads

# Without this, the app runs as root inside the container (unnecessary risk).
RUN useradd -m appuser && chown -R appuser:appuser /app


# bring in the startup script and make it runnable.
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Added documentation that the app listens on port 8000. It doesn't actually open the port by itself,
# but it's the standard way to communicate this to anyone reading/using the image.
EXPOSE 8000



# CHANGED: no "USER appuser" here. The container starts as root SO THAT
# entrypoint.sh is allowed to run chown/chmod on the mounted volumes.
# entrypoint.sh then drops to appuser itself before running the app --
# only appuser ends up with access to /app/uploads and /app/output.
ENTRYPOINT ["/entrypoint.sh"]

# It activates the environment and runs the command in the same single instant,. (uv run (activated environment) )
# uvicorn ko batata hai kahan se FastAPI app object dhoondna hai.Format hai: filename:variable_name. main = main.py file (uvicorn khud .py extension nahi likhta, 
# sirf module name) app = us file ke andar jo variable hai jisme FastAPI instance banaya gaya.
#--host = uvicorn ko batata hai kaun se network interface pe sunna hai
# special value jiska matlab hai "sabhi network interfaces pe suno". yani container ke bahar se koi bhi (host machine, ya EC2 ka public IP, ya browser) connect kar sake
# --port = kaunse port number pe app sunayega. 8000 is the default port for FastAPI, but you can change it if you want.

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]