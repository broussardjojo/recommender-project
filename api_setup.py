import os

def parse_api_kvs(filename = "api-keys"):
    env_vars = {}
    with open(filename) as keyfile:
        for line in keyfile:
            key, value = line.partition("=")[::2] # Don't get the string "="
            env_vars[key.strip()] = value.strip()
    return env_vars


if __name__ == "__main__":
    env_vars = parse_api_kvs()
    for key in env_vars:
        os.environ[key] = env_vars[key]